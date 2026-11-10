import copy
import unittest

from analysis.session_boundaries import reconstruct


class SessionBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.data={'segments':[{'duration':20,'frames':[{'t':0,'lm':[[1,2]]},
                                                             {'t':10,'lm':None},
                                                             {'t':20,'lm':[[3,4]]}]}],
                   'sessionLog':[{'t':100,'phase':'matching','lm':[[1,2]]},
                                 {'t':110,'phase':'recording','lm':None},
                                 {'t':120,'phase':'recording','lm':[[3,4]]}]}

    def test_first_matching_callback_accounts_for_extra_frame(self):
        result=reconstruct(self.data)
        self.assertEqual(result['segment_frames']-result['log_recording_frames'],1)
        self.assertTrue(result['segments'][0]['exact_coordinate_sequence'])
        self.assertFalse(result['segments'][0]['playback_wait_boundary_verified'])
        self.assertEqual(result['missing_segment_frames'],1)

    def test_mismatched_sequence_is_not_silently_aligned(self):
        data=copy.deepcopy(self.data);data['sessionLog'][-1]['lm']=[[4,5]]
        with self.assertRaises(ValueError):reconstruct(data)

    def test_reversed_segment_time_is_rejected(self):
        data=copy.deepcopy(self.data);data['segments'][0]['frames'][-1]['t']=9
        with self.assertRaises(ValueError):reconstruct(data)
