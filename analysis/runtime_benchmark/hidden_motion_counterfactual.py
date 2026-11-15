"""Registered engineering middle-finger perturbations and exact pixel metrics."""
import numpy as np

DELTAS_DEGREES=(0.,-5.,5.,10.)
MIDDLE_NATIVE_NONROOT=(3,4,5)
MIDDLE_CANONICAL=(10,11,12)


def perturb(angles,times,delta_degrees):
    a=np.asarray(angles,float);t=np.asarray(times,float)
    if (a.shape!=(25,15,3) or t.shape!=(25,) or not np.isfinite(a).all() or not np.isfinite(t).all()
            or t[0]!=0 or t[-1] not in (2.,3.) or not (np.diff(t)>0).all()
            or type(delta_degrees) not in (int,float) or delta_degrees not in DELTAS_DEGREES):
        raise ValueError('Registered complete parent sequence and perturbation required')
    def smooth(u):
        u=np.clip(u,0.,1.);return u*u*u*(10.-15.*u+6.*u*u)
    # Existing reveal/fade uses the first STATIC frame before motion playback.
    # Also preserve the first second of source motion as an extra control;
    # this is not the browser UI timeline or validation of UI combinations.
    start=max(t[-1]/3,1.);end=2*t[-1]/3
    u=(t-start)/(end-start)
    pulse=np.where(u<=.5,smooth(2*u),smooth(2*(1-u)))
    result=a.copy()
    for joint,weight in zip(MIDDLE_NATIVE_NONROOT,(1.,.85,.55)):
        result[:,joint,2]+=np.deg2rad(delta_degrees)*weight*pulse
    return result,pulse


def frame_difference(before,after,mask):
    before=np.asarray(before);after=np.asarray(after);mask=np.asarray(mask)
    if (before.shape!=after.shape or before.ndim!=3 or before.shape[2]!=3
            or before.dtype!=np.uint8 or after.dtype!=np.uint8 or mask.shape!=before.shape[:2] or mask.dtype!=bool):
        raise ValueError('Matched decoded uint8 frames and exact boolean mask required')
    delta=np.abs(before.astype(np.int16)-after.astype(np.int16));changed=np.any(delta!=0,axis=2)
    return {'all_changed_pixels_n':int(changed.sum()),
            'outside_mask_changed_pixels_n':int((changed&~mask).sum()),
            'inside_mask_changed_pixels_n':int((changed&mask).sum()),
            'maximum_channel_difference':int(delta.max()),
            'absolute_channel_difference_sum':int(delta.sum()),
            'channel_values_n':int(delta.size)}


def aggregate_differences(rows):
    if not rows:raise ValueError('Actual nonempty decoded frame denominator required')
    result={key:sum(r[key] for r in rows) for key in (
        'all_changed_pixels_n','outside_mask_changed_pixels_n','inside_mask_changed_pixels_n',
        'absolute_channel_difference_sum','channel_values_n')}
    result.update(frames_n=len(rows),changed_frames_n=sum(r['all_changed_pixels_n']>0 for r in rows),
                  maximum_channel_difference=max(r['maximum_channel_difference'] for r in rows))
    result['mean_absolute_channel_difference']=result['absolute_channel_difference_sum']/result['channel_values_n']
    result['exact_decoded_pixels_equal']=result['all_changed_pixels_n']==0
    return result
