"""Train appearance and temporal estimators against offline XY annotations."""

import argparse
import copy
import json
from pathlib import Path

import numpy as np
import torch
from torch import nn

from occluded_pose_benchmark import evaluate, read_recorded, read_synthetic


def image_tensor(rgb, context):
    frames = torch.from_numpy(rgb).permute(0, 3, 1, 2).float().div_(255)
    if not context:
        return frames
    previous = torch.cat((frames[:1], frames[:-1]))
    following = torch.cat((frames[1:], frames[-1:]))
    return torch.cat((previous, frames, following), dim=1)


def network(context):
    return nn.Sequential(
        nn.Conv2d(9 if context else 3, 24, 5, stride=2, padding=2), nn.GroupNorm(4, 24), nn.SiLU(),
        nn.Conv2d(24, 40, 3, stride=2, padding=1), nn.GroupNorm(4, 40), nn.SiLU(),
        nn.Conv2d(40, 64, 3, stride=2, padding=1), nn.GroupNorm(8, 64), nn.SiLU(),
        nn.AdaptiveAvgPool2d((4, 4)), nn.Flatten(), nn.Linear(1024, 128), nn.SiLU(),
        nn.Linear(128, 42), nn.Sigmoid(),
    )


def fit(training, validation, context, epochs, *, select_epoch=True):
    torch.manual_seed(123)
    x = torch.cat([image_tensor(clip['rgb'], context) for clip in training])
    y = torch.from_numpy(np.concatenate([clip['xy'] for clip in training])).reshape(-1, 42)
    valid = torch.isfinite(y).all(dim=1)
    x, y = x[valid], y[valid]
    model = network(context)
    optimizer = torch.optim.AdamW(model.parameters(), lr=.001, weight_decay=.001)
    loss = nn.SmoothL1Loss(beta=.04)

    @torch.inference_mode()
    def predict(rgb):
        return torch.cat([model(batch) for batch in image_tensor(rgb, context).split(32)]).numpy()

    best = None
    for epoch in range(1, epochs + 1):
        model.train()
        for indices in torch.randperm(len(y)).split(32):
            images, landmarks = x[indices], y[indices]
            flip = torch.rand(len(indices)) < .5
            images[flip] = images[flip].flip(-1)
            landmarks[flip, ::2] = 1 - landmarks[flip, ::2]
            optimizer.zero_grad()
            objective = loss(model(images), landmarks)
            objective.backward()
            optimizer.step()
        if select_epoch or epoch == epochs:
            model.eval()
            score = evaluate(validation, predict, None, extract=lambda rgb, _: rgb)
            if best is None or score['nme'] < best[0]['nme']:
                best = score, epoch, copy.deepcopy(model.state_dict())
    score, epoch, state = best
    model.load_state_dict(state)
    return score, epoch, model, predict


def run_domain(clips, epochs, destination):
    groups = {key: [clip for clip in clips if clip['split'] == key]
              for key in ('train', 'validation', 'test')}
    validation = []
    for context in (False, True):
        result, epoch, model, predictor = fit(groups['train'], groups['validation'], context, epochs)
        validation.append((result, context, epoch, model, predictor))
    result, context, epoch, model, predictor = min(validation, key=lambda row: row[0]['nme'])
    with destination.open('xb') as handle:
        torch.save({'weights': model.state_dict(), 'temporal_context': context}, handle)
    return {
        'selected': 'three_frame_cnn' if context else 'frame_cnn', 'epoch': epoch,
        'validation': result,
        'validation_trials': [{'temporal_context': flag, 'epoch': n, **score}
                              for score, flag, n, _, _ in validation],
        'held_out': evaluate(groups['test'], predictor, None, extract=lambda rgb, _: rgb),
        'hamer': {'state': 'not_measured_on_this_pilot'},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--synthetic', type=Path, required=True)
    parser.add_argument('--recorded', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--epochs', type=int, default=16, choices=range(1, 101), metavar='1..100')
    args = parser.parse_args()
    torch.set_num_threads(4)
    args.output_dir.mkdir()
    clips = [*read_synthetic(args.synthetic), *read_recorded(args.recorded)]
    report = {}
    for domain in ('2d', '3d', 'recorded'):
        row = run_domain([clip for clip in clips if clip['mode'] == domain], args.epochs,
                         args.output_dir / (domain + '.pt'))
        report[domain] = row
        print(json.dumps({'domain': domain, 'model': row['selected'], **row['held_out']}), flush=True)
    with (args.output_dir / 'report.json').open('x', encoding='utf8') as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
        handle.write('\n')


if __name__ == '__main__':
    main()
