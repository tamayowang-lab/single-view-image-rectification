import test from 'node:test';
import assert from 'node:assert/strict';
import { Vector3, MathUtils } from 'three';
import { HeadEyeModel, pixelForDirection } from '../src/head-eye-model.js';
import { rayForPixel } from '../src/photo-geometry.js';
const direction=(yaw,pitch=0)=>new Vector3(Math.sin(MathUtils.degToRad(yaw))*Math.cos(MathUtils.degToRad(pitch)),Math.sin(MathUtils.degToRad(pitch)),-Math.cos(MathUtils.degToRad(yaw))*Math.cos(MathUtils.degToRad(pitch)));
const settle=model=>{let pose;for(let i=0;i<240;i++)pose=model.step(1/120);return pose;};
test('eyes lead head; settled coordinated gaze points at the requested pixel',()=>{
  const m=new HeadEyeModel(),target=direction(40,20);m.aim(target);
  const early=m.step(.04);assert.equal(early.head.yaw,0);assert.ok(early.eyes[0].yaw>0);
  const settled=settle(m);assert.ok(settled.head.yaw>20);assert.ok(settled.head.pitch>0);
  assert.ok(settled.gazeDirection.angleTo(target)<1e-4);assert.equal(settled.phase,'Fixating');
  assert.ok(settled.eyes[0].yaw<early.eyes[0].yaw,'eyes re-center as the head catches up');
});
test('eyes-only mode holds the head still and exposes unreachable gaze',()=>{
  const m=new HeadEyeModel();m.setMode('eyes-only');m.aim(direction(65,0));
  const pose=settle(m);assert.equal(pose.head.yaw,0);assert.ok(Math.abs(pose.eyes[0].yaw-35)<.001);
  assert.ok(pose.gaze.yaw<36);assert.equal(pose.phase,'Eye limit');assert.equal(pose.limited,true);
});
test('metric target makes both independent eye rays intersect the same point',()=>{
  const m=new HeadEyeModel();m.aim(direction(12,8),.5);const pose=m.step(0,true);
  const target=direction(12,8).multiplyScalar(.5);
  for(const eye of pose.eyes){
    const toward=target.clone().sub(eye.origin).normalize();assert.ok(eye.direction.angleTo(toward)<1e-6);
  }
  assert.ok(pose.eyes[0].yaw>pose.eyes[1].yaw);assert.equal(pose.vergence,true);
});
test('relative depth does not invent metric binocular convergence',()=>{
  const m=new HeadEyeModel();m.aim(direction(10),null);const pose=m.step(0,true);
  assert.ok(pose.eyes[0].direction.angleTo(pose.eyes[1].direction)<1e-6);assert.equal(pose.vergence,false);
  m.aim(direction(10),NaN);assert.equal(m.step(0,true).vergence,false);
});
test('pixel projection round trips and gaze state resets safely',()=>{
  const pixel={u:.8,v:.2};const ray=rayForPixel(pixel.u,pixel.v,1.5,60);const roundtrip=pixelForDirection(ray,1.5,60);
  assert.ok(Math.abs(roundtrip.u-pixel.u)<1e-10&&Math.abs(roundtrip.v-pixel.v)<1e-10);
  const m=new HeadEyeModel();m.aim(ray);m.step(1,true);m.reset();assert.equal(m.head.yaw,0);
  assert.throws(()=>m.aim({x:0,y:0,z:0}));assert.throws(()=>m.setMode('invalid'));
  assert.ok(Number.isFinite(m.step(NaN).head.yaw));
});
