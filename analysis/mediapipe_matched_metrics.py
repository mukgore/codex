"""Image-plane error against generated model projections, not human annotations."""
import math


def evaluate(reference,predicted,names):
    if len(reference)!=25 or len(predicted)!=25 or len(names)!=21 or len(set(names))!=21:
        raise ValueError('Complete matched25-frame21-point series required')
    detected=0;errors=[];target=[];normalized=[];in_frame_errors=[];geometry_errors=0;raw_rows=[]
    for i,(truth,model) in enumerate(zip(reference,predicted)):
        if model['frame_idx']!=i or type(model['detected']) is not bool or abs(model['source_pts_ms']-truth['source_pts_ms'])>.01:
            raise ValueError('Predicted/reference frame identity and PTS must match')
        if not model['detected']:
            raw_rows.append({'frame_index':i,'detected':False,'error_mean_pixels':None});continue
        detected+=1;t=truth['landmarks_px'];p=model['landmarks_px']
        if set(t)!=set(names) or set(p)!=set(names) or any(not math.isfinite(d[n][k]) for d in (t,p) for n in names for k in ('x','y')):
            raise ValueError('Finite named reference and actual predictions required')
        values=[math.hypot(t[n]['x']-p[n]['x'],t[n]['y']-p[n]['y']) for n in names]
        scale=math.hypot(t[names[9]]['x']-t[names[0]]['x'],t[names[9]]['y']-t[names[0]]['y'])
        errors.extend(values);target.append(values[10])
        in_frame_errors.extend(v for n,v in zip(names,values) if 0<=t[n]['x']<512 and 0<=t[n]['y']<420)
        if scale<=1e-10:geometry_errors+=1
        else:normalized.extend(v/scale for v in values)
        raw_rows.append({'frame_index':i,'detected':True,'error_mean_pixels':sum(values)/21,
          'middle_PIP_error_pixels':values[10],'reference_scale_pixels':scale})
    mean=lambda x:sum(x)/len(x) if x else None
    return {'attempted_frames_n':25,'detected_frames_n':detected,'missing_frames_n':25-detected,
      'detected_fraction':detected/25,'detected_point_comparisons_n':len(errors),
      'conditional_mean_point_error_pixels':mean(errors),'conditional_middle_PIP_error_pixels':mean(target),
      'conditional_reference_in_frame_point_error_pixels':mean(in_frame_errors),
      'detected_reference_in_frame_points_n':len(in_frame_errors),'normalized_point_comparisons_n':len(normalized),
      'conditional_mean_error_reference_hand_lengths':mean(normalized),'reference_scale_invalid_detected_frames_n':geometry_errors,
      'reference_type':'known generated model projection; not independent human annotation',
      'world_depth_error_evaluated':False,'per_frame':raw_rows}
