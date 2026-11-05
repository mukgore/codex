/* Experimental raw features only. No production score, threshold or camera UI.
 * Same explicit units, contiguous blocks and DTW tie policy as adapters.py.
 */
'use strict';
const triples = [[0,5,6],[5,6,7],[6,7,8],[0,9,10],[9,10,11],[10,11,12],
  [0,13,14],[13,14,15],[14,15,16],[0,17,18],[17,18,19],[18,19,20],[0,1,2],[1,2,3],[2,3,4]];
const finite = x => typeof x === 'number' && Number.isFinite(x);
const positive = x => finite(x) && x > 0;
const fail = message => { throw new Error(message); };
function specWithDefaults(value) {
  const s = {min_scale_pixels:1e-6,min_contiguous_frames:3,...value};
  if (![s.width,s.height,s.max_gap_seconds,s.min_scale_pixels].every(positive) ||
      !['normalized_xy','pixel_xy'].includes(s.coordinate_space) || !['ms','s'].includes(s.time_unit) ||
      typeof s.mirror_x !== 'boolean' || !Number.isInteger(s.min_contiguous_frames) || s.min_contiguous_frames < 3)
    fail('Explicit valid dimensions, units, mirror and continuity policy required');
  return s;
}
function normalizeFrame(points, spec) {
  if (!Array.isArray(points) || points.length !== 21 ||
      !points.every(p=>Array.isArray(p) && [2,3].includes(p.length) && p.slice(0,2).every(finite))) fail('21 finite XY points required');
  let xy = points.map(p=>[p[0]*(spec.coordinate_space==='normalized_xy'?spec.width:1),p[1]*(spec.coordinate_space==='normalized_xy'?spec.height:1)]);
  if (spec.mirror_x) xy = xy.map(p=>[spec.width-p[0],p[1]]);
  const scale = Math.hypot(xy[9][0]-xy[0][0],xy[9][1]-xy[0][1]);
  if (!finite(scale) || scale < spec.min_scale_pixels) fail('Degenerate wrist scale');
  const origin = xy[0]; xy = xy.map(p=>[(p[0]-origin[0])/scale,(p[1]-origin[1])/scale]);
  const angles = triples.map(([a,b,c])=>{
    const u=[xy[a][0]-xy[b][0],xy[a][1]-xy[b][1]], v=[xy[c][0]-xy[b][0],xy[c][1]-xy[b][1]];
    const lengths=Math.hypot(...u)*Math.hypot(...v);
    if (!finite(lengths) || lengths<=1e-12) fail('Degenerate angle bones');
    return Math.acos(Math.min(1,Math.max(-1,(u[0]*v[0]+u[1]*v[1])/lengths)))*180/Math.PI;
  });
  if (!xy.flat().every(finite)) fail('Nonfinite normalization');
  return [xy, angles];
}
function adaptSegment(frames, value) {
  const spec=specWithDefaults(value);
  if (!Array.isArray(frames)) fail('Frames array required');
  const report={attempted_frames:frames.length,detected_frames:0,invalid_geometry_frames:0,missing_frames:0,
    excluded_short_block_frames:0,gap_boundary_count:0,blocks:[]};
  let current=[], previous=null;
  const flush=()=>{
    if (current.length>=spec.min_contiguous_frames) report.blocks.push({source_frame_indices:current.map(x=>x[0]),
      times_seconds:current.map(x=>x[1]),normalized_xy:current.map(x=>x[2]),angles_degrees:current.map(x=>x[3])});
    else report.excluded_short_block_frames+=current.length;
    current=[];
  };
  frames.forEach((frame,index)=>{
    if (!frame || !Object.hasOwn(frame,'t') || !Object.hasOwn(frame,'lm') || !finite(frame.t) || frame.t<0) fail('Explicit timestamp and landmarks required');
    const t=frame.t/(spec.time_unit==='ms'?1000:1);
    if (previous!==null) {
      if (t<=previous) fail('Unordered timestamps');
      if (t-previous>spec.max_gap_seconds) {flush();report.gap_boundary_count++;}
    }
    previous=t;
    if (frame.lm===null) {flush();report.missing_frames++;return;}
    report.detected_frames++;
    let xy,angles;
    try {[xy,angles]=normalizeFrame(frame.lm,spec);} catch (_) {flush();report.invalid_geometry_frames++;return;}
    current.push([index,t,xy,angles]);
  });
  flush();report.analyzed_frames=report.blocks.reduce((sum,b)=>sum+b.times_seconds.length,0);return report;
}
function gradient(values,times,maxGap) {
  if (!positive(maxGap) || times.length<3 || values.length!==times.length || !times.every(finite)) fail('Contiguous time series required');
  const n=times.length, width=values[0].length;
  if (!width || !values.every(row=>row.length===width && row.every(finite))) fail('Finite rectangular series required');
  const h=times.slice(1).map((t,i)=>t-times[i]);
  if (!h.every(x=>x>0 && x<=maxGap)) fail('Invalid time gap');
  return values.map((_,i)=>{
    let a,b,c,k;
    if (i===0) {const [u,v]=h;a=-(2*u+v)/(u*(u+v));b=(u+v)/(u*v);c=-u/(v*(u+v));k=0;}
    else if(i===n-1) {const u=h[n-3],v=h[n-2];a=v/(u*(u+v));b=-(v+u)/(u*v);c=(2*v+u)/(v*(u+v));k=n-3;}
    else {const u=h[i-1],v=h[i];a=-v/(u*(u+v));b=(v-u)/(u*v);c=u/(v*(u+v));k=i-1;}
    return Array.from({length:width},(_,j)=>a*values[k][j]+b*values[k+1][j]+c*values[k+2][j]);
  });
}
function dtw(x,y,radius) {
  const n=x.length,m=y.length,d=x[0]?.length;
  if (!Number.isInteger(radius) || radius<0 || !n || !m || !d || Math.abs(n-m)>radius || n*m>1e6 ||
      ![...x,...y].every(row=>row.length===d && row.every(finite))) fail('Invalid bounded DTW series');
  const cost=Array.from({length:n+1},()=>Array(m+1).fill(Infinity));cost[0][0]=0;
  const prev=Array.from({length:n},()=>Array(m).fill(-1));
  for(let i=1;i<=n;i++) for(let j=Math.max(1,i-radius);j<=Math.min(m,i+radius);j++) {
    const options=[cost[i-1][j-1],cost[i-1][j],cost[i][j-1]];
    let k=0;for(let q=1;q<3;q++) if(options[q]<options[k]) k=q;
    cost[i][j]=options[k]+x[i-1].reduce((sum,v,a)=>sum+(v-y[j-1][a])**2,0);prev[i-1][j-1]=k;
  }
  if (!finite(cost[n][m])) fail('No finite DTW path');
  let i=n,j=m,path=[];
  while(i>0&&j>0) {path.push([i-1,j-1]);const k=prev[i-1][j-1];if(k===0){i--;j--;}else if(k===1)i--;else j--;}
  path.reverse();return {distance:Math.sqrt(cost[n][m]),path_rmse:Math.sqrt(cost[n][m]/(path.length*d)),path};
}
function compareBlocks(reference,response,{dtw_radius,max_gap_seconds,phase_samples=32}) {
  if(!Number.isInteger(phase_samples)||phase_samples<3||phase_samples>1000) fail('Explicit bounded phase samples required');
  const features=[reference,response].map(block=>{
    const t=block.times_seconds,xy=block.normalized_xy,angles=block.angles_degrees;
    if (!Array.isArray(t)||t.length<3||xy.length!==t.length||angles.length!==t.length||
        !xy.every(row=>row.length===21&&row.every(p=>p.length===2&&p.every(finite)))||
        !angles.every(row=>row.length===15&&row.every(finite))) fail('Complete 21 point / 15 angle block required');
    const accel=gradient(gradient(xy.map(row=>row.flat()),t,max_gap_seconds),t,max_gap_seconds);
    const phase=t.map(v=>(v-t[0])/(t[t.length-1]-t[0]));
    const resample=values=>Array.from({length:phase_samples},(_,i)=>{
      const at=i/(phase_samples-1);let k=0;while(k+1<phase.length-1&&phase[k+1]<at) k++;
      const ratio=(at-phase[k])/(phase[k+1]-phase[k]);
      return values[k].map((v,j)=>v+ratio*(values[k+1][j]-v));
    });
    return [angles,resample(angles),resample(accel)];
  });
  const aligned=dtw(features[0][0],features[1][0],dtw_radius);
  const mae=(a,b)=>a.reduce((sum,row,i)=>sum+row.reduce((s,v,j)=>s+Math.abs(v-b[i][j]),0),0)/(a.length*a[0].length);
  return {schema_version:1,endpoint:'candidate_raw_features_only',angle_phase_grid_mae_degrees:mae(features[0][1],features[1][1]),
    dtw_angle_distance:aligned.distance,dtw_angle_path_rmse:aligned.path_rmse,
    acceleration_phase_aligned_mae_hand_lengths_per_second_squared:mae(features[0][2],features[1][2]),
    phase_samples,dtw_radius,score:null};
}
module.exports={adaptSegment,normalizeFrame,specWithDefaults,compareBlocks,dtw,gradient};
if(require.main===module) {
  let raw='';process.stdin.setEncoding('utf8');process.stdin.on('data',chunk=>{raw+=chunk;if(raw.length>2e6)process.exit(2);});
  process.stdin.on('end',()=>{try{const request=JSON.parse(raw);let out;
    if(request.method==='adapt')out=adaptSegment(request.frames,request.spec);
    else if(request.method==='compare')out=compareBlocks(request.reference,request.response,request.options);
    else if(request.method==='dtw')out=dtw(request.x,request.y,request.radius);
    else fail('Unknown method');
    process.stdout.write(JSON.stringify(out));
  }catch(_){process.stderr.write('Invalid raw-feature request\n');process.exitCode=2;}});
}
