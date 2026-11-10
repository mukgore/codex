// Execute owned export code with synthetic hands/mock clocks. No browser/camera.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.resolve(process.argv[2]);
const HandSelection=require(path.join(root,'experiments/hand_selection/selection.js'));
const {SessionLog}=require(path.join(root,'experiments/hand_selection/session_log.js'));
const bridge=fs.readFileSync(path.join(root,'experiments/prod_selected_hand/bridge.js'),'utf8');
function runBridge(completed){
  let now=0,calls=0,saved=null;const elements={},timers=new Map();let next=0;
  const element=id=>elements[id]??={textContent:'',addEventListener(name,fn){this[name]=fn;}};
  const context={HandSelection,performance:{now:()=>now},
    document:{querySelector:()=>({closest:()=>({appendChild(){}})}),
      createElement:()=>({click(){}}),getElementById:element},
    setTimeout:(fn,ms)=>{timers.set(++next,{fn,ms});return next;},clearTimeout:id=>timers.delete(id),
    addEventListener(){},cancelAnimationFrame(){},stopGhostLoop(){},rv:{pause(){}},
    camStream:{getTracks:()=>[{stop(){}}]},selectionRunAborted:false,selectionRunFinished:false,
    phase:'matching',matchHoldStart:null,handednessBuffer:[],selectedHand:'left',targetLm:{},
    keyframes:[1],curSegFrames:[],segments:[],animId:1,sessionStart:0,sessionLog:[],
    onRes(){calls++;if(completed && calls===9){context.phase='done';context.showResult();}},
    setS(){},startRealChallenge(){},showResult(){},onTransitionMatched(){},location:{reload(){}},
    Blob:class {constructor(parts){saved=parts.join('');}},
    URL:{createObjectURL:()=>'',revokeObjectURL(){}}};
  vm.createContext(context);vm.runInContext(bridge,context,{timeout:1000});
  const hand=Array.from({length:21},(_,i)=>({x:.1+(i%5)*.05,y:.1+Math.floor(i/5)*.05,z:0}));
  function tick(hands){now+=33;context.onRes({image:{},multiHandLandmarks:hands,
    multiHandedness:hands.length?[{label:'Left',score:.99}]:[]});}
  for(let i=0;i<8;i++)tick([hand]);
  tick(completed?[hand]:[]);
  elements.selectionExport.click();
  if(saved===null)throw Error('Export handler did not create JSON');
  return JSON.parse(saved);
}
let clock=0;const demo=new SessionLog({clock:()=>clock,limit:2});
demo.record('selected');clock=10;demo.record('lost');clock=20;demo.record('reselect');
process.stdout.write(JSON.stringify({data_scope:'synthetic_mock_clock_no_camera',
  fixtures:{bridge_completed:runBridge(true),bridge_aborted:runBridge(false),
            demo_truncated:demo.snapshot()}}));
