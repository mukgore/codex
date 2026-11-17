'use strict';
// Event/DOM contract checks in Node; this is not a rendered-browser screenshot test.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const html = fs.readFileSync(path.join(__dirname, 'dist/index.html'), 'utf8');
const scripts = [...html.matchAll(/<script([^>]*)>([\s\S]*?)<\/script>/g)];
assert.equal(scripts.length, 2);
const data = JSON.parse(scripts[0][2]), nodes = {}, handlers = {};
class Node {
  constructor(id) { this.id=id;this.hidden=false;this.disabled=false;this.dataset={};this.attrs={};this.listeners={};this.value='';this.options=[];this._html='';this.textContent='';this.dynamic={}; }
  set innerHTML(value) {
    this._html=value;this.dynamic={};
    for(const m of value.matchAll(/<[^>]+data-(stage|month|chain)="([^"]+)"[^>]*>/g)) {
      const node=new Node('dynamic');node.dataset[m[1]]=m[2];
      (this.dynamic[m[1]] ||= []).push(node);
    }
  }
  get innerHTML(){return this._html;}
  setAttribute(key,value){this.attrs[key]=String(value);}
  addEventListener(type,listener){this.listeners[type]=listener;}
  add(option){this.options.push(option);}
  input(value){this.value=value;this.listeners.input();}
}
for(const m of html.matchAll(/<[^>]+\bid="([^"]+)"[^>]*>/g))nodes[m[1]]=new Node(m[1]);
nodes['dashboard-data'].textContent=scripts[0][2];
for(const id of ['month-filter','track-filter','repo-filter','publication-filter','backlog-stage','backlog-state','requirement-kind'])nodes[id].value='all';
const sections=['overview','timeline','findings','backlog','sources'].map(name=>nodes['view-'+name]);
const nav=sections.map(n=>{const b=new Node('nav');b.dataset.view=n.id.slice(5);return b;});
const modes=['story','commits'].map(name=>{const b=new Node('mode');b.dataset.mode=name;return b;});
const sources=[...html.matchAll(/data-source="([^"]+)"/g)].map(m=>{const n=new Node('source');n.dataset.source=m[1];return n;});
const context=vm.createContext({document:{getElementById:id=>{assert.ok(nodes[id],'Missing markup ID '+id);return nodes[id];},
  querySelectorAll:selector=>({'.section':sections,'[data-view]':nav,'[data-mode]':modes,'.source':sources,
    '[data-stage]':nodes['stage-buttons'].dynamic.stage||[], '[data-month]':nodes['activity-chart'].dynamic.month||[],
    '[data-chain]':nodes['decision-chain'].dynamic.chain||[]}[selector]||[])},
  location:{hash:''},addEventListener:(name,fn)=>{handlers[name]=fn;},window:{print(){}},
  Option:function(label,value){this.label=label;this.value=value;},console});
vm.runInContext(scripts[1][2],context);
assert.equal(data.commits.length,329);assert.equal(data.backlog.length,62);
assert.equal(sections.filter(n=>!n.hidden).length,1);assert.equal(nodes['view-overview'].hidden,false);
assert.equal(nodes['stage-buttons'].dynamic.stage.length,7);
nodes['stage-buttons'].dynamic.stage.find(b=>b.dataset.stage==='4').onclick();
assert.ok(nodes['stage-detail'].innerHTML.includes('1,200'));
assert.equal(nodes['stage-buttons'].dynamic.stage.filter(b=>b.attrs['aria-pressed']==='true').length,1);
context.location.hash='#timeline';handlers.hashchange();assert.equal(nodes['view-timeline'].hidden,false);
assert.equal(nodes['repo-filter'].disabled,true);modes[1].onclick();assert.equal(nodes['repo-filter'].disabled,false);
assert.ok(nodes['timeline-count'].textContent.includes('329'));
nodes['repo-filter'].input('codex');nodes['publication-filter'].input('local');
assert.ok(nodes['timeline-count'].textContent.startsWith('조건에 맞는 21개'));
assert.equal((nodes['timeline-items'].innerHTML.match(/<li>/g)||[]).length,21);
assert.ok(!nodes['timeline-items'].innerHTML.includes('href="https://github.com'));
nodes['repo-filter'].input('all');nodes['publication-filter'].input('all');
assert.equal(nodes['activity-chart'].dynamic.month.length,10);
nodes['activity-chart'].dynamic.month.find(b=>b.dataset.month==='2026-04').onclick();
assert.ok(nodes['timeline-count'].textContent.startsWith('조건에 맞는 0개'));
nodes['month-filter'].input('all');nodes['timeline-search'].input('not-a-real-term-31991');
assert.ok(nodes['timeline-items'].innerHTML.includes('조건에 맞는 기록이 없습니다'));
nodes['timeline-search'].input('');
context.location.hash='#backlog';handlers.hashchange();assert.ok(nodes['backlog-count'].textContent.includes('62개'));
nodes['backlog-search'].input('S05');assert.ok(nodes['backlog-rows'].innerHTML.includes('<td>S05</td>'));
nodes['backlog-search'].input('');nodes['backlog-stage'].input('3A');
assert.ok(!nodes['backlog-rows'].innerHTML.includes('<td>S05</td>'));assert.ok(nodes['backlog-rows'].innerHTML.includes('<td>R07</td>'));
nodes['backlog-stage'].input('all');assert.equal((nodes['backlog-rows'].innerHTML.match(/<tr>/g)||[]).length,62);
assert.equal(data.geometry_requirements.length,44);assert.equal(data.runtime_requirements.length,10);
assert.equal((nodes['geometry-rows'].innerHTML.match(/<tr>/g)||[]).length,44);
assert.equal((nodes['runtime-rows'].innerHTML.match(/<tr>/g)||[]).length,10);
assert.equal(nodes['geometry-panel'].hidden,false);assert.equal(nodes['runtime-panel'].hidden,false);
nodes['requirement-kind'].input('runtime');nodes['requirement-search'].input('R8');
assert.equal(nodes['geometry-panel'].hidden,true);assert.equal(nodes['runtime-panel'].hidden,false);
assert.ok(nodes['runtime-count'].textContent.startsWith('표시 1개'));
assert.ok(nodes['runtime-rows'].innerHTML.includes('11요청'));
nodes['requirement-search'].input('not-a-real-term-31991');assert.ok(nodes['runtime-rows'].innerHTML.includes('조건에 맞는 요구가 없습니다'));
nodes['requirement-kind'].input('geometry');nodes['requirement-search'].input('GEN3D-05');
assert.equal(nodes['generator-note'].hidden,false);assert.ok(nodes['generator-note'].textContent.startsWith('GEN3D-05:'));
nodes['requirement-search'].input('');nodes['requirement-kind'].input('all');
context.location.hash='#findings';handlers.hashchange();nodes['decision-chain'].dynamic.chain[3].onclick();
assert.ok(nodes['chain-detail'].textContent.includes('운영 보안'));
assert.ok(nodes['decision-rows'].innerHTML.includes('0.608'));assert.ok(nodes['decision-rows'].innerHTML.includes('0.987'));
assert.ok(nodes['decision-rows'].innerHTML.includes('미실행'));
context.location.hash='#sources';handlers.hashchange();nodes['doc-search'].input('mediapipe');
assert.ok(nodes['document-list'].innerHTML.toLowerCase().includes('mediapipe'));
assert.equal(context.sourceHref('javascript:alert(1)'),'#sources');
assert.ok(sources.every(a=>a.href.startsWith('../../../')));
console.log('Dashboard contracts OK: 5 views, 7 stages, 10 month bins, local/GitHub filters, 62 backlog rows, 44 geometry rows + GEN3D-05, R0–R9 filters, decision chain, evidence links.');
