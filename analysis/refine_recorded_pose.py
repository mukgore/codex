"""Select a recorded-video pose model by leaving out one development clip at a time."""

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from measure_hamer_pose import score_predictions
from occluded_pose_benchmark import MODELS, features, fit_ridge, read_recorded, smooth_temporal
from train_occluded_pose_cnn import fit


RIDGE_PENALTIES = (.0001, .001, .01, .1, 1., 10.)
IMAGE_WEIGHTS = (.5, .75, 1.)
SMOOTH_SIGMAS = (0., .35, .5, .75, 1., 1.5, 2.)
CNN_EPOCHS = 12


def training_mean(clips):
    return np.nanmean(np.concatenate([clip['xy'].reshape(-1, 42) for clip in clips]), axis=0)


def candidates(training, validation):
    labels = np.concatenate([clip['xy'].reshape(-1, 42) for clip in training])
    valid = np.isfinite(labels).all(axis=1)
    for kind in MODELS:
        inputs = np.concatenate([features(clip['rgb'], kind) for clip in training])
        for penalty in RIDGE_PENALTIES:
            weights, offset = fit_ridge(inputs[valid], labels[valid], penalty)
            parameters = {'weights': weights, 'offset': offset, 'feature_kind': kind}
            yield (kind, penalty), lambda rgb: features(rgb, kind) @ weights + offset, parameters
    for temporal in (False, True):
        _, _, model, predict = fit(training, validation, temporal, CNN_EPOCHS, select_epoch=False)
        name = 'three_frame_cnn' if temporal else 'frame_cnn'
        yield (name, None), predict, {'weights': model.state_dict(), 'temporal_context': temporal}


def blend(prediction, average, image_weight):
    return average + image_weight * (prediction - average)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--recorded', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    torch.set_num_threads(4)
    clips = list(read_recorded(args.recorded))
    development = [row for row in clips if row['split'] != 'test']
    test = [row for row in clips if row['split'] == 'test']
    args.output.mkdir()
    results, controls = {}, {}
    for validation in development:
        name = validation['name']
        training = [clip for clip in development if clip['source'] != validation['source']]
        average = training_mean(training)
        control = np.broadcast_to(average, (len(validation['rgb']), 42))
        controls[name] = control
        for (kind, penalty), predict, _ in candidates(training, [validation]):
            prediction = predict(validation['rgb'])
            for image_weight in IMAGE_WEIGHTS:
                blended = blend(prediction, average, image_weight)
                for sigma in SMOOTH_SIGMAS:
                    key = (kind, penalty, image_weight, sigma)
                    results.setdefault(key, {})[name] = smooth_temporal(blended, sigma)
        print(json.dumps({'development_fold': name}), flush=True)
    scores = {key: score_predictions(development, values) for key, values in results.items()}
    selected = min(scores, key=lambda key: scores[key]['nme'])
    name, penalty, image_weight, sigma = selected
    average = training_mean(development)
    # For fixed-epoch retraining this argument only supports the CNN fit API.
    # It cannot affect the chosen weights or use any test source.
    for key, predict, artifact in candidates(development, development[:1]):
        if key == (name, penalty):
            break
    artifact.update({'training_mean': average, 'image_weight': image_weight, 'smoothing_sigma': sigma})
    if penalty is None:
        artifact['training_mean'] = torch.from_numpy(average)
        torch.save(artifact, args.output / 'recorded.pt')
    else:
        np.savez(args.output / 'recorded.npz', **artifact)
    predicted = {clip['name']: smooth_temporal(blend(predict(clip['rgb']), average, image_weight), sigma)
                 for clip in test}
    report = {'selection': 'lowest out-of-fold NME, one development source per fold',
              'reference': 'historical tracker image-plane coordinates',
              'selected_model': name, 'penalty': penalty, 'image_weight': image_weight,
              'smoothing_sigma': sigma,
              'trials': [{'model': key[0], 'penalty': key[1], 'image_weight': key[2],
                          'smoothing_sigma': key[3], 'validation': value}
                         for key, value in scores.items()],
              'validation': scores[selected], 'validation_mean_control': score_predictions(development, controls),
              'test': score_predictions(test, predicted)}
    with (args.output / 'report.json').open('x', encoding='utf8') as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
        handle.write('\n')
    print(json.dumps({key: report[key] for key in ('selected_model', 'image_weight', 'validation', 'test')}))


if __name__ == '__main__':
    main()
