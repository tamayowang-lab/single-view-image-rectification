import test from 'node:test';
import assert from 'node:assert/strict';
import {rayForPixel,depthAt,calibrateDepth,axialDepth,estimateBox,gazeAngles,gazeRing} from '../src/photo-geometry.js';
const close=(a,b)=>assert.ok(Math.abs(a-b)<1e-8,`${a} != ${b}`);
test('pixel rays and gaze directions follow camera projection',()=>{
  const center=rayForPixel(.5,.5,2,60);close(center.x,0);close(center.y,0);close(center.z,-1);
  assert.ok(gazeAngles(.8,.2,2,60).yaw>0);assert.ok(gazeAngles(.8,.2,2,60).pitch>0);
  close(Math.hypot(...Object.values(center).slice(0,3)),1);
});
test('bilinear depth sampling handles image edges',()=>{
  const grid={width:2,height:2,values:[0,1,.2,.8]};close(depthAt(grid,.5,.5),.5);close(depthAt(grid,1,1),.8);close(depthAt(grid,-1,-1),0);
});
test('two known slant distances recover inverse-depth scale and offset',()=>{
  const grid={width:2,height:2,values:[.2,.8,.2,.8]};
  const refs=[{u:0,v:.5},{u:1,v:.5}].map(p=>({...p,distance:1/(.2+.4*depthAt(grid,p.u,p.v))/rayForPixel(p.u,p.v,1.5,60).axialFactor}));
  const c=calibrateDepth(refs,grid,1.5,60);close(c.a,.4);close(c.b,.2);close(axialDepth(.5,c),2.5);
  const s=estimateBox([.25,.25,.75,.75],.5,c,1.5,60);close(s.distance,2.5);close(s.width,2.5*Math.tan(Math.PI/6)*1.5);
});
test('metric values stay unknown without calibration and invalid references fail',()=>{
  assert.equal(estimateBox([0,0,1,1],.5,null,1,60),null);
  assert.equal(axialDepth(0,{a:1,b:-.1}),null);
  const grid={width:2,height:1,values:[0,1]};
  assert.throws(()=>calibrateDepth([null,null],grid,1,60));
  assert.throws(()=>calibrateDepth([{u:0,v:0,distance:1},{u:1,v:0,distance:5}],grid,1,60));
});
test('projected gaze oval is centered, has the requested angular range, and follows off-center gaze',()=>{
  const ring=gazeRing(.5,.5,1.5,60,40,28);
  close(ring[0].u-.5,Math.tan(20*Math.PI/180)/(2*Math.tan(Math.PI/6)*1.5));close(ring[0].v,.5);
  const offset=gazeRing(.8,.3,1.5,60,40,28);assert.ok(offset.every(p=>Number.isFinite(p.u)&&Number.isFinite(p.v)));assert.ok(offset[0].u>ring[0].u);
});
