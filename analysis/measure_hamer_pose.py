"""Measure the pinned HaMeR core and validation-selected models on matched offline RGB frames."""

import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import sys

import cv2
import numpy as np
import torch

from occluded_pose_benchmark import evaluate, features, read_recorded, read_synthetic
from train_occluded_pose_cnn import image_tensor, network


def hand_side(clip):
    if clip['mode'] == 'recorded':
        return int(clip['handedness'] == 'Right')
    _, seed, slot = clip['source'].split('-')
    return int((int(seed) + int(slot)) % 2 != 0)


def make_estimator(source, checkpoint):
    if sys.platform == 'win32':
        os.environ.setdefault('PYOPENGL_PLATFORM', 'win32')
    sys.path.insert(0, str(source))
    from hamer.configs import get_config
    from hamer.datasets.vitdet_dataset import ViTDetDataset
    from hamer.models.hamer import HAMER

    # The official loader resolves MANO assets relative to its ./_DATA cache.
    previous_directory = Path.cwd()
    try:
        os.chdir(checkpoint.parents[3])
        config = get_config(str(checkpoint.parents[1] / 'model_config.yaml'), update_cachedir=True)
        config.defrost()
        if config.MODEL.BACKBONE.TYPE == 'vit' and 'BBOX_SHAPE' not in config.MODEL:
            if config.MODEL.IMAGE_SIZE != 256:
                raise ValueError('The HaMeR ViT demo expects a 256-pixel input')
            config.MODEL.BBOX_SHAPE = [192, 256]
        config.MODEL.BACKBONE.pop('PRETRAINED_WEIGHTS', None)
        config.freeze()
        # Match the demo's checkpoint configuration without initializing its mesh viewer.
        model = HAMER.load_from_checkpoint(str(checkpoint), map_location='cpu', strict=False,
                                           cfg=config, init_renderer=False)
    finally:
        os.chdir(previous_directory)
    model.eval()

    @torch.inference_mode()
    def predict(images, right, mode):
        height, width = images.shape[1:3]
        # The recorded source is square, but the shared input tensor is 80 x 66.
        # Restore the source proportions before cropping without adding detail.
        if mode == 'recorded' and height != width:
            images = np.stack([cv2.resize(rgb, (width, width), interpolation=cv2.INTER_LINEAR)
                               for rgb in images])
            height = width
        # One centered hand is the dataset protocol. The crop uses only image
        # dimensions. The supplied side is recorded separately in the report.
        box = np.array([[0, 0, width - 1, height - 1]], dtype=np.float32)
        crops = []
        with contextlib.redirect_stdout(io.StringIO()):
            for rgb in images:
                dataset = ViTDetDataset(config, cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR),
                                        box, np.array([right]), rescale_factor=1.)
                crops.append(dataset[0])
        images = torch.from_numpy(np.stack([crop['img'] for crop in crops]))
        output = []
        for batch in images.split(2):
            output.append(model({'img': batch})['pred_keypoints_2d'].cpu().numpy())
        xy = np.concatenate(output)
        if not right:
            xy[:, :, 0] *= -1
        size = np.array([crop['box_size'] for crop in crops])[:, None, None]
        center = np.stack([crop['box_center'] for crop in crops])[:, None, :]
        return (xy * size + center) / np.array([width, height])

    return predict


def load_local_predictor(path):
    if path.suffix == '.pt':
        artifact = torch.load(path, map_location='cpu', weights_only=True)
        context = artifact['temporal_context']
        model = network(context)
        model.load_state_dict(artifact['weights'])
        model.eval()

        @torch.inference_mode()
        def predict(rgb):
            return torch.cat([model(batch) for batch in image_tensor(rgb, context).split(32)]).numpy()

        return predict, artifact

    with np.load(path, allow_pickle=False) as handle:
        artifact = dict(handle)
    weights, offset, kind = artifact['weights'], artifact['offset'], str(artifact['feature_kind'].item())
    return lambda rgb: features(rgb, kind) @ weights + offset, artifact


def local_estimator(mode, ridge_weights, cnn_dir, ridge, cnn):
    if cnn['validation']['nme'] < ridge['selected']['validation']['nme']:
        predict, _ = load_local_predictor(cnn_dir / (mode + '.pt'))
        return cnn['selected'], cnn['validation']['nme'], predict
    predict, _ = load_local_predictor(ridge_weights / (mode + '.npz'))
    return ridge['selected']['model'], ridge['selected']['validation']['nme'], predict


def refined_estimator(directory):
    report = json.loads((directory / 'report.json').read_text(encoding='utf8'))
    suffix = '.pt' if report['penalty'] is None else '.npz'
    predict, artifact = load_local_predictor(directory / ('recorded' + suffix))
    average = np.asarray(artifact['training_mean'])
    image_weight = float(artifact['image_weight'])
    if not (0 < image_weight <= 1):
        raise ValueError('The refinement must use pixel input')
    return report['selected_model'], report['validation']['nme'], (
        lambda rgb: average + image_weight * (predict(rgb) - average))


def sample_clip(clip, n):
    indices = np.unique(np.linspace(0, len(clip['xy']) - 1, min(n, len(clip['xy']))).round().astype(int))
    return indices, {
        **clip, 'rgb': clip['rgb'][indices], 'xy': clip['xy'][indices],
        'hidden': clip['hidden'][indices] if clip['hidden'] is not None else None,
    }


def score_predictions(clips, predictions):
    by_input = {id(clip['rgb']): predictions[clip['name']] for clip in clips}
    return evaluate(clips, lambda rgb: by_input[id(rgb)], None, extract=lambda rgb, _: rgb)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('source', 'checkpoint', 'synthetic', 'recorded', 'ridge-weights', 'ridge-report', 'cnn-dir', 'output'):
        parser.add_argument('--' + key, type=Path, required=True)
    parser.add_argument('--recorded-refinement', type=Path)
    parser.add_argument('--frames-per-clip', type=int, default=5, choices=range(1, 301), metavar='1..300')
    parser.add_argument('--domains', nargs='+', choices=('2d', '3d', 'recorded'),
                        default=('2d', '3d', 'recorded'))
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    torch.set_num_threads(4)
    ridge = json.loads(args.ridge_report.read_text(encoding='utf8'))['domains']
    cnn = json.loads((args.cnn_dir / 'report.json').read_text(encoding='utf8'))
    modes = tuple(args.domains)
    estimators = {mode: local_estimator(mode, args.ridge_weights, args.cnn_dir, ridge[mode], cnn[mode])
                  for mode in modes}
    if args.recorded_refinement:
        estimators['recorded'] = refined_estimator(args.recorded_refinement)
    hamer = make_estimator(args.source.resolve(strict=True), args.checkpoint.resolve(strict=True))
    clips = [*read_synthetic(args.synthetic), *read_recorded(args.recorded)]
    report = {'scope': 'offline image-plane coordinates; same score frames; HaMeR given hand side',
              'reference_source': {'2d': 'projected rig', '3d': 'projected rig',
                                   'recorded': 'legacy tracker estimates'},
              'hamer_crop': 'fixed centered full-frame crop without joint annotations',
              'selection_metric': 'validation NME; lower is better',
              'frames_per_clip_requested': args.frames_per_clip, 'domains': {}}
    for mode in modes:
        estimator, validation_nme, predict = estimators[mode]
        training = np.concatenate([clip['xy'] for clip in clips if clip['mode'] == mode and clip['split'] == 'train'])
        train_mean = np.nanmean(training, axis=0)
        sampled, hp, local, mean, frozen = [], {}, {}, {}, {}
        for clip in (row for row in clips if row['mode'] == mode and row['split'] == 'test'):
            indices, sample = sample_clip(clip, args.frames_per_clip)
            sampled.append(sample)
            name = clip['name']
            hp[name] = hamer(sample['rgb'], hand_side(clip), mode)
            local[name] = predict(clip['rgb'])[indices]
            mean[name] = np.broadcast_to(train_mean, sample['xy'].shape)
            frozen[name] = predict(np.repeat(clip['rgb'][:1], len(clip['rgb']), axis=0))[indices]
            print(json.dumps({'domain': mode, 'sampled_clips': len(sampled)}), flush=True)
        report['domains'][mode] = {'hamer': score_predictions(sampled, hp),
                                   'selected': score_predictions(sampled, local),
                                   'train_mean_control': score_predictions(sampled, mean),
                                   'frozen_first_frame_control': score_predictions(sampled, frozen),
                                   'selected_model': estimator, 'validation_nme': validation_nme}
    with args.output.open('x', encoding='utf8') as output:
        json.dump(report, output, indent=2, allow_nan=False)
        output.write('\n')


if __name__ == '__main__':
    main()
