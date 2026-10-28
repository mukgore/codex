// Invoke selected functions from the actual owned HTML; never execute its page,
// imports, camera initialization, fetch calls, or upload handlers.
const fs = require('node:fs');
const vm = require('node:vm');
const readline = require('node:readline');
const html = fs.readFileSync(process.argv[2], 'utf8');
function extractFunction(name) {
  const start = html.indexOf(`function ${name}(`);
  if (start < 0) throw Error(`missing actual function: ${name}`);
  const open = html.indexOf('{', start);
  let depth = 0, quote = null, escape = false, lineComment = false, blockComment = false;
  for (let i = open; i < html.length; i++) {
    const ch = html[i], next = html[i+1];
    if (lineComment) { if (ch === '\n') lineComment = false; continue; }
    if (blockComment) { if (ch === '*' && next === '/') { blockComment = false; i++; } continue; }
    if (quote) { if (escape) escape = false; else if (ch === '\\') escape = true; else if (ch === quote) quote = null; continue; }
    if (ch === '/' && next === '/') { lineComment = true; i++; continue; }
    if (ch === '/' && next === '*') { blockComment = true; i++; continue; }
    if (ch === '"' || ch === "'" || ch === '`') { quote = ch; continue; }
    if (ch === '{') depth++;
    if (ch === '}' && --depth === 0) return html.slice(start, i+1);
  }
  throw Error(`unterminated actual function: ${name}`);
}
function constant(name) {
  const match = html.match(new RegExp(`const ${name} = ([^;]+);`));
  if (!match) throw Error(`missing actual constant: ${name}`);
  return `const ${name} = ${match[1]};`;
}
const names = ['ang','ppSingle','angleErr','pp','rs','mA','mDA','mAc','es','computeScores','findKeyframes','getBaseFromLandmarkData','onRes'];
const source = ['MATCH_ANGLE_THRESH','MATCH_HOLD_MS','THRESHOLD','W2','MX','AT','LN'].map(constant).join('\n') + '\n' + names.map(extractFunction).join('\n');
function run(request) {
  const context = vm.createContext({});
  vm.runInContext(source, context, {timeout: 1000});
  context.request = request;
  if (request.op === 'prepare') return vm.runInContext(`({ ...getBaseFromLandmarkData(request.data, !!request.mirror), constants: {MATCH_ANGLE_THRESH,MATCH_HOLD_MS,THRESHOLD,W2,MX}, keyframeIndices: findKeyframes(getBaseFromLandmarkData(request.data, !!request.mirror).frames) })`, context, {timeout:1000});
  const result = vm.runInContext(`
    const base = request.base;
    // Within-clip keyframe partitions, with shared boundary frames. Replay
    // responses are partitioned by index/phase, not observed browser callbacks.
    const indices = findKeyframes(base);
    const keyframes = indices.map(i=>({clip:{clip_id:'local'},frameIdx:i,allBaseLm:base}));
    const response = request.frames.map(f=>({t:f.t_ms,lm:f.lm}));
    const segments = indices.slice(1).map((end,i)=>({fromKf:i,toKf:i+1,frames:response.slice(Math.round(indices[i]/(base.length-1)*(response.length-1)),Math.round(end/(base.length-1)*(response.length-1))+1)}));
    const scoreResult = computeScores();
    const targets = findKeyframes(base).map(i=>base[i]);
    keyframes.splice(0,keyframes.length,...targets.map(baseLm=>({baseLm})));
    let fakeNow=0, phase='matching', kfIdx=0, targetLm=targets[0], matchHoldStart=null;
    let lastLm=null, sessionLog=[], curSegFrames=[], sessionStart=0, recStart=0;
    const camStream=null, cc={width:640,height:480}, ctx={save(){},restore(){},clearRect(){},drawImage(){},translate(){},scale(){}};
    const framingOverlayDone=true, videoPlaying=false, fading=false;
    const performance={now:()=>fakeNow};
    const document={getElementById:()=>({textContent:''})};
    const HAND_CONNECTIONS=[];
    const drawConnectors=()=>{},drawLandmarks=()=>{},updateFramingGuide=()=>{},maybeShowGhostFallback=()=>{},maybeHideGhostFallback=()=>{},updateMatchIndicator=()=>{};
    const matches=[];
    function matched(){matches.push(fakeNow);kfIdx++;targetLm=targets[kfIdx]||null;phase=kfIdx>=targets.length?'done':'recording';}
    const onFirstKeyframeMatched=matched,onTransitionMatched=matched;
    for(const frame of request.frames){
      fakeNow=frame.t_ms;
      onRes({multiHandLandmarks:frame.lm?[frame.lm.map(p=>({x:p[0],y:p[1],z:0}))]:[],image:{}});
    }
    ({score:scoreResult,score_pass:scoreResult.captcha>=THRESHOLD,gate_pass:kfIdx===targets.length,gate_matches:matches.length,gate_total:targets.length,gate_match_times_ms:matches,score_scope:'within_clip_phase_partition',gate_scope:'onRes_offline_without_video_scheduler'});
  `, context, {timeout:10000});
  return result;
}
readline.createInterface({input:process.stdin,crlfDelay:Infinity}).on('line', line => {
  try { process.stdout.write(JSON.stringify({ok:true,result:run(JSON.parse(line))})+'\n'); }
  catch(error) { process.stdout.write(JSON.stringify({ok:false,error:String(error.message)})+'\n'); }
});
