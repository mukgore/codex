'use strict';
const $=id=>document.getElementById(id);
const escape=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const descriptions={
 A:{title:'A · 기존 원형 기반 움직임',text:'기존 원형의 phase 곡선을 이 비교의 25프레임 격자로 재시간화했습니다. 현재 표시 관문을 통과해 가림 후보와 최종 압축본이 있습니다.'},
 B:{title:'B · 새 정적 자세',text:'원형 없이 제안·수정한 자세를 시간 동안 유지합니다. 움직이지 않는 것이 재생 오류는 아닙니다. 현재 고정 카메라의 가림 관문은 통과하지 못했습니다.'},
 C:{title:'C · 원형 없는 움직임',text:'원형 없는 세 상태 사이를 연결한 제약 경로입니다. 모델·샘플 표면 후보와 실제 사람의 유효한 움직임은 별개입니다. 이 표시 조건의 가림본은 없습니다.'},
 U:{title:'U · 수정 전 PCA 정적 자세',text:'수정 전 제안 자세의 대조군입니다. 모델/샘플 표면 조건을 통과하지 못해 가림·최종 생성을 거부했습니다. 시간 동안 정적 자세를 유지합니다.'}
};
const kindNames={source:'무가림 source',candidate:'가림 후보',final:'최종 압축'};
let data,representatives=[],pipeline=[];
function videoCard(clip,title,text,group=''){
 const copy=clip.converted_for_viewing;
 return `<article class="card"><video controls muted playsinline preload="${group?'metadata':'none'}" poster="/poster/${clip.id}" src="/media/${clip.id}" ${group?`data-group="${group}"`:''} aria-label="${escape(title)}"></video><div class="card-body"><span class="badge ${copy?'copy':''}">${copy?'보기용 MP4 사본':'원래 H.264 직접 재생'}</span><h3>${escape(title)}</h3><p>${escape(text)}</p><small>${escape(clip.hand)} · seed ${clip.seed} · ${escape(clip.view)} · ${clip.frames_n}프레임</small><details><summary>파일·생성 기록 보기</summary><div>원래 형식: ${escape(clip.codec)} / ${escape(clip.original_relative)}</div><div>원래 영상 준비 ${clip.generated_ready_seconds.toFixed(3)}초 · 추가 검산 완료 ${clip.generated_validated_seconds.toFixed(3)}초. 공통 모델 준비는 제외한 당시 기록입니다.</div><div>${copy?'호환용 손실 압축 사본이며 실험 결과를 바꾸지 않습니다.':'이미 호환되는 최종본이므로 재인코딩하지 않았습니다.'}</div><a href="/original/${clip.id}">원본 파일 받기</a></details><p class="video-error" role="status"></p></div></article>`;
}
function selected(arm,kind){return data.clips.find(c=>c.arm===arm&&c.kind===kind&&c.hand===$('hand').value&&String(c.seed)===$('seed').value&&c.view===$('view').value);}
function pause(group){group.forEach(v=>v.pause());}
function seek(group,time){group.forEach(v=>{if(v.readyState>=1)v.currentTime=Math.min(time,v.duration||time);else v.addEventListener('loadedmetadata',()=>v.currentTime=Math.min(time,v.duration),{once:true});});}
async function play(group,restart=false){
 pause(group);seek(group,restart?0:(group[0]?.currentTime||0));group.forEach(v=>v.playbackRate=Number($('speed').value));
 const results=await Promise.allSettled(group.map(v=>v.play()));
 $('play-status').textContent=results.some(r=>r.status==='rejected')?'일부 재생이 차단됐습니다. 영상의 ▶ 버튼을 직접 눌러주세요.':'함께 재생 중 · 보기용 동기화';
}
function attachErrors(container){container.querySelectorAll('video').forEach(v=>v.addEventListener('error',()=>{v.closest('.card').querySelector('.video-error').textContent='브라우저가 재생하지 못했습니다. 원본/보기용 파일 위치는 아래 기록에서 확인할 수 있습니다.';}));}
function renderSelected(){
 pause(representatives);pause(pipeline);
 $('representatives').innerHTML=['A','B','C'].map(arm=>{const c=selected(arm,'source');return c?videoCard(c,descriptions[arm].title,descriptions[arm].text,'representative'):'<p>대응 영상이 없습니다.</p>';}).join('');
 representatives=[...$('representatives').querySelectorAll('video')];
 $('pipeline-cards').innerHTML=['source','candidate','final'].map(kind=>{const c=selected('A',kind);return c?videoCard(c,kindNames[kind],kind==='source'?'가리기 전 원래 모델 렌더입니다.':kind==='candidate'?'가림 제작 직후의 후보입니다. 원래 mp4v 파일은 별도로 보존했습니다.':'표시/QC 후 저장한 원래 H.264 압축본입니다.','pipeline'):'<p>생성되지 않은 영상입니다.</p>';}).join('');
 pipeline=[...$('pipeline-cards').querySelectorAll('video')];
 representatives[0]?.addEventListener('timeupdate',()=>{
  const master=representatives[0];$('seek').value=String(Math.min(master.currentTime,3));$('clock').textContent=master.currentTime.toFixed(2)+'초';
  if(!master.paused)representatives.slice(1).forEach(v=>{if(v.readyState>=1&&Math.abs(v.currentTime-master.currentTime)>.12)v.currentTime=master.currentTime;});
 });
 $('clock').textContent='0.00초';$('seek').value='0';$('play-status').textContent='';
 attachErrors($('representatives'));attachErrors($('pipeline-cards'));
}
function renderAll(){
 $('all-clips').querySelectorAll('video').forEach(v=>v.pause());
 const rows=data.clips.filter(c=>($('kind').value==='all'||c.kind===$('kind').value)&&($('arm').value==='all'||c.arm===$('arm').value));
 $('all-count').textContent=`표시 ${rows.length}개 / 원래 48개 · A/B/C/U 각 무가림 8개, A만 후보 8개·최종 8개`;
 $('all-clips').innerHTML=rows.map(c=>videoCard(c,`${c.arm} · ${kindNames[c.kind]}`,descriptions[c.arm].text)).join('')||'<div class="empty">이 조합의 영상은 생성되지 않았습니다. B/C/U에는 무가림 영상만 있습니다.</div>';
 attachErrors($('all-clips'));
}
async function init(){
 const response=await fetch('/api/manifest');if(!response.ok)throw Error('manifest unavailable');data=await response.json();
 if(data.clips.length!==48)throw Error('incomplete manifest');
 for(const view of [...new Set(data.clips.map(c=>c.view))])$('view').add(new Option(view,view));
 $('integrity').textContent=`원래 실행 ${data.record_verification.state} · ${data.original_experiment_artifacts_n}개 산출물 hash 검산 일치 · 원영상 48개 보존`;
 $('copy-note').textContent=`보기용 H.264 MP4 ${data.viewing_copies_n}개를 별도 생성했고, 원래 최종 H.264 ${data.original_h264_reused_n}개는 그대로 사용합니다. ${data.copy_note}`;
 $('source-root').textContent=data.source_root;$('record-root').textContent=data.record_root;
 const copy=data.clips.find(c=>c.converted_for_viewing);$('viewer-root').textContent=copy.playable_path.replace(/[\\/][^\\/]+$/,'');
 if(/^http:\/\/127\.0\.0\.1:\d+$/.test(data.ui_url))$('ui-link').href=data.ui_url+'/experiments/local_review_20261118/';
 ['hand','seed','view'].forEach(id=>$(id).addEventListener('change',renderSelected));
 ['kind','arm'].forEach(id=>$(id).addEventListener('change',renderAll));
 $('play-all').onclick=()=>play(representatives);$('pause-all').onclick=()=>pause(representatives);
 $('restart-all').onclick=()=>{pause(representatives);seek(representatives,0);$('clock').textContent='0.00초';$('seek').value='0';};
 $('seek').addEventListener('input',()=>{pause(representatives);seek(representatives,Number($('seek').value));$('clock').textContent=Number($('seek').value).toFixed(2)+'초';});
 $('speed').addEventListener('change',()=>[...representatives,...pipeline].forEach(v=>v.playbackRate=Number($('speed').value)));
 $('pipeline-play').onclick=()=>play(pipeline,true);$('pipeline-pause').onclick=()=>pause(pipeline);
 renderSelected();renderAll();
}
init().catch(error=>{$('integrity').textContent='영상 목록을 읽지 못했습니다. 서버와 manifest를 확인해 주세요: '+error.message;});
