// Coordinates: x right, y up, original camera looking down -Z.
export function rayForPixel(u, v, aspect, vfov) {
  const t = Math.tan(vfov * Math.PI / 360);
  const x = (2 * u - 1) * t * aspect;
  const y = (1 - 2 * v) * t;
  const norm = Math.hypot(x, y, 1);
  return { x: x / norm, y: y / norm, z: -1 / norm, axialFactor: 1 / norm };
}
export function depthAt(grid, u, v) {
  const x = Math.max(0, Math.min(grid.width - 1, u * (grid.width - 1)));
  const y = Math.max(0, Math.min(grid.height - 1, v * (grid.height - 1)));
  const x0 = Math.floor(x), y0 = Math.floor(y), x1 = Math.min(x0 + 1, grid.width - 1), y1 = Math.min(y0 + 1, grid.height - 1);
  const p = (xx, yy) => grid.values[yy * grid.width + xx];
  return (p(x0,y0)*(1-x+x0)+p(x1,y0)*(x-x0))*(1-y+y0) + (p(x0,y1)*(1-x+x0)+p(x1,y1)*(x-x0))*(y-y0);
}
export function calibrateDepth(references, grid, aspect, vfov) {
  if (references.some(r => !r || !(r.distance > 0) || !Number.isFinite(r.distance))) throw new Error('Select two points and enter their known distances.');
  const points = references.map(r => ({
    p: depthAt(grid, r.u, r.v),
    inverseZ: 1 / (r.distance * rayForPixel(r.u, r.v, aspect, vfov).axialFactor),
  }));
  if (Math.abs(points[0].p-points[1].p) < .025) throw new Error('Choose points with more distinct predicted depths.');
  const a = (points[0].inverseZ-points[1].inverseZ)/(points[0].p-points[1].p);
  const b = points[0].inverseZ-a*points[0].p;
  if (!(a > 0) || !Number.isFinite(a) || !Number.isFinite(b)) throw new Error('Reference distances disagree with the model’s near/far ordering.');
  return { a, b };
}
export function axialDepth(p, calibration) {
  // The uncalibrated range is deliberately in arbitrary units, never meters.
  const inverse = calibration ? calibration.a*p+calibration.b : .15+.85*p;
  return inverse > .001 ? 1/inverse : null;
}
export function estimateBox(box, p, calibration, aspect, vfov) {
  if (!calibration) return null;
  const z = axialDepth(p, calibration);
  if (z === null) return null;
  const u=(box[0]+box[2])/2, v=(box[1]+box[3])/2;
  const t = Math.tan(vfov*Math.PI/360);
  return { distance:z/rayForPixel(u,v,aspect,vfov).axialFactor,
    width:(box[2]-box[0])*2*z*t*aspect, height:(box[3]-box[1])*2*z*t };
}
export function gazeAngles(u,v,aspect,vfov) {
  const r=rayForPixel(u,v,aspect,vfov);
  return { yaw:Math.atan2(r.x,-r.z)*180/Math.PI, pitch:Math.atan2(r.y,Math.hypot(r.x,r.z))*180/Math.PI };
}
export function gazeRing(u,v,aspect,vfov,horizontal,vertical,steps=96) {
  const forward=rayForPixel(u,v,aspect,vfov);
  const length=Math.hypot(forward.z,forward.x);
  const right={x:-forward.z/length,y:0,z:forward.x/length};
  const up={x:right.y*forward.z-right.z*forward.y,y:right.z*forward.x-right.x*forward.z,z:right.x*forward.y-right.y*forward.x};
  const t=Math.tan(vfov*Math.PI/360);
  const th=Math.tan(horizontal*Math.PI/360), tv=Math.tan(vertical*Math.PI/360);
  return Array.from({length:steps+1},(_,i)=>{
    const a=i/steps*Math.PI*2, h=Math.cos(a)*th, v=Math.sin(a)*tv;
    const d={x:forward.x+right.x*h+up.x*v,y:forward.y+right.y*h+up.y*v,z:forward.z+right.z*h+up.z*v};
    return {u:.5+d.x/(-d.z)/(2*t*aspect),v:.5-d.y/(-d.z)/(2*t),visible:d.z<-.01,direction:d};
  });
}
