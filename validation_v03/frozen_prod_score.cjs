/* Execute pinned local production functions verbatim. Offline diagnostics only. */
'use strict';
const fs=require('node:fs'), crypto=require('node:crypto'), vm=require('node:vm');
const PROD_SHA256='0d82dd439fe7976f8b860eb82e654e6f5637b2d7a3fcce2d02f2f99e5f5bea11';
function loadProduction(path) {
  const raw=fs.readFileSync(path);
  if(crypto.createHash('sha256').update(raw).digest('hex')!==PROD_SHA256)
    throw Error('Pinned production bytes required');
  const source=raw.toString('utf8'), chunks=[], ranges=[];
  function take(start,end) {
    const a=source.indexOf(start), b=source.indexOf(end,a+start.length);
    if(a<0||b<0||source.indexOf(start,a+1)!==-1) throw Error('Unique source boundaries required');
    const text=source.slice(a,b); chunks.push(text);
    ranges.push({start_line:source.slice(0,a).split('\n').length,
      end_line:source.slice(0,b).split('\n').length-1,
      sha256:crypto.createHash('sha256').update(text).digest('hex')});
  }
  for(const name of ['MATCH_ANGLE_THRESH','MATCH_HOLD_MS','THRESHOLD','W2','MX','AT','LN']) {
    const match=source.match(new RegExp('^const '+name+' = .*;$','m'));
    if(!match) throw Error('Pinned constant missing'); chunks.push(match[0]);
  }
  take('function getBaseFromLandmarkData(', 'function getInfoFromLandmarkData(');
  take('function findKeyframes(', '// ===== POSE MATCHING =====');
  take('function ang(', '// ===== GHOST HAND SILHOUETTE');
  take('function pp(f)', 'function showResult(');
  const context=vm.createContext({});
  vm.runInContext(chunks.join('\n')+'\nlet segments=[], keyframes=[];'+
    '\nglobalThis.api={getBaseFromLandmarkData,findKeyframes,ppSingle,angleErr,pp,rs,mA,mDA,mAc,es,computeScores,'+
    'constants:{MATCH_ANGLE_THRESH,MATCH_HOLD_MS,THRESHOLD,W2,MX},'+
    'setState:(s,k)=>{segments=s;keyframes=k;}};',context,{timeout:1000});
  return {api:context.api, extraction:{prod_sha256:PROD_SHA256,ranges}};
}
function finiteSequence(frames, allowMissing=false) {
  if(!Array.isArray(frames)||frames.length<3||frames.length>1000||!frames.every(f=>
    (allowMissing&&f===null)||(Array.isArray(f)&&f.length===21&&f.every(p=>
      Array.isArray(p)&&p.length===2&&p.every(Number.isFinite))))) throw Error('Bounded finite21 XY frames required');
}
function score(api, request) {
  if(request.mode!==undefined&&!['full_interval','auto_keyframes'].includes(request.mode)) throw Error('Unknown segmentation');
  const base=request.base, response=request.response;finiteSequence(base);finiteSequence(response,true);
  if(base.length!==response.length) throw Error('Registered equal index grids required');
  const k=request.mode==='auto_keyframes'?Array.from(api.findKeyframes(base)):[0,base.length-1];
  const keyframes=k.map(frameIdx=>({frameIdx,allBaseLm:base,clip:{clip_id:'offline_reference'}}));
  // Inclusive endpoints match the production base slicing. Boundary response
  // frames are deliberately repeated across adjacent diagnostic segments.
  const segments=k.slice(1).map((to,i)=>({fromKf:i,toKf:i+1,
    frames:response.slice(k[i],to+1).map(lm=>({lm}))}));
  api.setState(segments,keyframes);
  const result=api.computeScores();
  const angles=response.map((f,i)=>f===null?null:api.angleErr(api.ppSingle(f),api.ppSingle(base[i])));
  if(!Object.entries(result).every(([k,v])=>Number.isFinite(v)||(v===null&&['rA','rDA','rAc'].includes(k)))||angles.some(x=>x!==null&&!Number.isFinite(x)))
    throw Error('Nonfinite production result');
  return {score:result,keyframe_indices:k,score_threshold_met:result.captcha>=api.constants.THRESHOLD,
    synchronized_angle_errors_degrees:angles,
    angle_threshold_frames_n:angles.filter(x=>x!==null&&x<api.constants.MATCH_ANGLE_THRESH).length,
    keyframe_angles:k.map(i=>({index:i,error_degrees:angles[i],
      below_threshold:angles[i]!==null&&angles[i]<api.constants.MATCH_ANGLE_THRESH})),
    hold_validated:false,authentication_validated:false};
}
module.exports={loadProduction,score,PROD_SHA256};
if(require.main===module) {
  try {
    const {api,extraction}=loadProduction(process.argv[2]);
    const request=JSON.parse(fs.readFileSync(0,'utf8'));
    const converted=request.landmark_data?api.getBaseFromLandmarkData(request.landmark_data,false):null;
    const results=(request.cases||[]).map(c=>({id:c.id,...score(api,c)}));
    process.stdout.write(JSON.stringify({extraction,constants:api.constants,converted,results}));
  } catch(error) {process.stderr.write(error.message+'\n');process.exitCode=2;}
}
