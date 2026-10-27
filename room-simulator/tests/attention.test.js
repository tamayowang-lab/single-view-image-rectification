import test from 'node:test';
import assert from 'node:assert/strict';
import { AttentionSearch } from '../src/attention-search.js';
import { buildAttentionCandidates } from '../src/attention-candidates.js';
import { HeadEyeModel } from '../src/head-eye-model.js';
import { rayForPixel } from '../src/photo-geometry.js';
const objects=[
 {id:'a',label:'chair',kind:'object',u:.2,v:.6,box:[.1,.45,.3,.75],confidence:.65,salience:.8},
 {id:'b',label:'chair',kind:'object',u:.8,v:.3,box:[.7,.2,.9,.4],confidence:.9,salience:.9},
 {id:'c',label:'Visual region',kind:'region',u:.5,v:.15,box:[.45,.1,.55,.2],confidence:null,salience:.6},
];
function runSearch(candidates=objects){
 const search=new AttentionSearch();search.start(candidates,{u:.5,v:.5},{aspect:1.5,vfov:70});
 for(let i=0;i<1500&&search.state==='running';i++){
  search.tick(.05,{error:0,limited:false,gazeDirection:rayForPixel(search.target.u,search.target.v,1.5,70)});
 }
 return search;
}
test('a click is the first fixation and finite candidate coverage completes without cycling',()=>{
 const search=runSearch();assert.equal(search.state,'complete');assert.equal(search.visited.size,3);assert.equal(search.skipped.size,0);
 assert.equal(search.history[0].u,.5);assert.equal(search.history[0].v,.5);
 assert.ok(search.history.length>=4&&search.history.length<=7);
 for(const c of objects)assert.ok(search.history.filter(h=>h.id===c.id).length<=2);
 assert.deepEqual(search.history,runSearch().history,'seeded exploration should be reproducible');
});
test('saccades do not count as completed fixations; pause and resume preserve state',()=>{
 const s=new AttentionSearch();s.start(objects,{u:.5,v:.5});
 s.tick(.1,{error:5,limited:false,gazeDirection:rayForPixel(.5,.5,1,60)});
 assert.equal(s.phase,'saccade');assert.equal(s.history.length,0);assert.equal(s.visited.size,0);
 s.pause();const elapsed=s.elapsed;s.tick(1,{error:0,limited:false});assert.equal(s.elapsed,elapsed);
 s.resume();s.tick(.1,{error:0,limited:false,gazeDirection:rayForPixel(.5,.5,1,60)});assert.equal(s.phase,'fixation');
 assert.equal(s.history.length,0);s.stop();assert.equal(s.state,'stopped');
});
test('unreachable candidates are skipped instead of falsely counted as inspected',()=>{
 const s=new AttentionSearch();s.start(objects,{u:.5,v:.5});
 for(let i=0;i<500&&s.state==='running';i++)s.tick(.1,{error:20,limited:true,gazeDirection:rayForPixel(.5,.5,1,60)});
 assert.equal(s.state,'complete');assert.equal(s.visited.size,0);assert.equal(s.skipped.size,3);assert.equal(s.history.length,0);
});
test('complete exploration works with the actual coordinated motor controller',()=>{
 const s=new AttentionSearch(),motor=new HeadEyeModel();
 let event=s.start(objects,{u:.5,v:.5},{aspect:1.5,vfov:70,hfov:20,efov:16}),maxHead=0;
 motor.aim(rayForPixel(event.target.u,event.target.v,1.5,70),null,{hfov:20,efov:16});
 for(let i=0;i<5000&&s.state==='running';i++){
  const pose=motor.step(1/60);maxHead=Math.max(maxHead,Math.abs(pose.head.yaw));event=s.tick(1/60,pose);
  if(event?.type==='target')motor.aim(rayForPixel(event.target.u,event.target.v,1.5,70),null,{hfov:20,efov:16});
 }
 assert.equal(s.state,'complete');assert.equal(s.visited.size,3);assert.equal(s.skipped.size,0);assert.ok(maxHead>10);
});
test('attention keeps the head still for small visible shifts and recruits it outside eyesight',()=>{
 const m=new HeadEyeModel();m.aim(rayForPixel(.55,.5,1,60),null,{hfov:40,efov:28});
 let pose=m.step(0,true);assert.equal(pose.head.yaw,0);assert.equal(pose.headRecruited,false);assert.ok(pose.eyes[0].yaw>0);
 m.aim(rayForPixel(.95,.5,1.5,70),null,{hfov:20,efov:16});pose=m.step(0,true);
 assert.equal(pose.headRecruited,true);assert.ok(pose.head.yaw>10);
});
test('candidate generation never labels contrast regions as recognized objects',()=>{
 const image={width:80,height:60,data:new Uint8ClampedArray(80*60*4).fill(100)};
 assert.equal(buildAttentionCandidates(image,[]).length,0);
 for(let y=8;y<30;y++)for(let x=45;x<68;x++){
  const i=(y*80+x)*4;image.data[i]=255;image.data[i+1]=200;image.data[i+2]=0;
 }
 const model=[{label:'chair',confidence:.8,box:[.05,.55,.3,.9]}];
 const all=buildAttentionCandidates(image,model);assert.ok(all.length>1&&all.length<=7);
 assert.equal(all[0].label,'chair');assert.ok(all.slice(1).every(c=>c.kind==='region'&&c.confidence===null&&c.label.startsWith('Visual region')));
 assert.equal(buildAttentionCandidates(image,model,false).length,1);
});

test('unstable repeated arrivals cannot keep the search running forever',()=>{
 const s=new AttentionSearch();s.start(objects,{u:.5,v:.5});
 for(let i=0;i<1500&&s.state==='running';i++)s.tick(.1,{error:i%2?0:2,limited:false,gazeDirection:rayForPixel(.5,.5,1,60)});
 assert.equal(s.state,'complete');assert.equal(s.visited.size,0);assert.equal(s.skipped.size,3);
});
