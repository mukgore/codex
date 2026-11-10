"""Synthetic visibility counterexample for the A06/A07 screening rationale."""
import json

import numpy as np


def compare():
    # Four frames of a toy scene. The thumb remains fixed and the other
    # fingertip either touches it or leaves a one-pixel gap in the last frame.
    touch = np.zeros((4, 12, 12), dtype=np.uint8)
    gap = touch.copy()
    for frames, end in ((touch, 6), (gap, 7)):
        for frame, tip_x in zip(frames, (9, 8, 7, end), strict=True):
            frame[5, :6] = 200
            frame[5, tip_x:] = 200
    occluder = np.s_[..., 4:10]
    # The optional dot represents an independently visible object response,
    # such as a moving indicator. Its usefulness is conditional on the
    # response actually encoding the hidden event in the real task.
    difference = {}
    for condition in ('unmasked', 'masked_no_cue', 'masked_visible_cue'):
        a, b = touch.copy(), gap.copy()
        if condition.startswith('masked'):
            a[occluder] = b[occluder] = 0
        if condition == 'masked_visible_cue':
            a[-1, 9, 2] = 255
        difference[condition] = int(np.count_nonzero(a != b))
    return {'scope': 'toy_pixel_identifiability', 'frames_per_sequence': len(touch),
            'different_pixels_across_sequences': difference}


if __name__ == '__main__':
    print(json.dumps(compare(), sort_keys=True))
