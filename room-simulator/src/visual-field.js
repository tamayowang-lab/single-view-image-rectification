/** Elliptical angular field around a unit forward direction. */
export function insideViewingCone(direction, forward, horizontal = 40, vertical = 28) {
  const dot = (a,b) => a.x*b.x+a.y*b.y+a.z*b.z;
  const length = Math.hypot(forward.z, forward.x);
  if(length < 1e-9) return false;
  const right = {x:-forward.z/length,y:0,z:forward.x/length};
  const up = {x:-right.z*forward.y,y:right.z*forward.x-right.x*forward.z,z:right.x*forward.y};
  const denominator = dot(direction,forward);
  if(denominator<=0) return false;
  const x=dot(direction,right)/denominator/Math.tan(horizontal*Math.PI/360);
  const y=dot(direction,up)/denominator/Math.tan(vertical*Math.PI/360);
  return x*x+y*y<=1;
}
