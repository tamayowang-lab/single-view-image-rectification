import { Euler, Quaternion, Vector3, MathUtils } from 'three';

const forward = new Vector3(0, 0, -1);
const rad = MathUtils.degToRad;
const deg = MathUtils.radToDeg;
const clamp = MathUtils.clamp;
const quaternion = (yaw, pitch) => new Quaternion().setFromEuler(new Euler(rad(pitch), rad(-yaw), 0, 'YXZ'));
const angles = direction => ({
  yaw: deg(Math.atan2(direction.x, -direction.z)),
  pitch: deg(Math.atan2(direction.y, Math.hypot(direction.x, direction.z))),
});
function approach(current, target, dt, tau, maxSpeed) {
  const step = (target - current) * (1 - Math.exp(-dt / tau));
  return current + clamp(step, -maxSpeed * dt, maxSpeed * dt);
}

/** Demonstration controller, not a fitted physiological or scanpath model.
 * +X right, +Y up, forward -Z. All exposed angles are in degrees.
 * The eye midpoint is the fixed camera origin; head motion is rotation only.
 */
export class HeadEyeModel {
  constructor() {
    this.mode = 'coordinated';
    this.ipd = 0.064;
    this.reset();
  }
  reset() {
    this.head = { yaw: 0, pitch: 0 };
    this.eyes = [{ yaw: 0, pitch: 0 }, { yaw: 0, pitch: 0 }];
    this.target = forward.clone();
    this.distance = null;
    this.elapsed = 1;
    return this.step(0, true);
  }
  setMode(mode) {
    if (!['coordinated', 'eyes-only'].includes(mode)) throw new Error('Unknown head-eye movement mode');
    this.mode = mode;
    this.elapsed = 0;
  }
  aim(direction, metricDistance = null) {
    const next = new Vector3(direction.x, direction.y, direction.z);
    if (![next.x, next.y, next.z].every(Number.isFinite) || next.lengthSq() < 1e-10 || next.z >= 0) {
      throw new Error('Gaze target must be a finite forward-facing direction');
    }
    next.normalize();
    // Continuous pointer tracking must not continually restart the head's delay.
    if (this.target.angleTo(next) > rad(3)) this.elapsed = 0;
    this.target.copy(next);
    this.distance = Number.isFinite(metricDistance) && metricDistance >= .2 && metricDistance <= 150 ? metricDistance : null;
  }
  step(dt, instant = false) {
    dt = clamp(Number.isFinite(dt) ? dt : 0, 0, .05);
    this.elapsed += dt;
    const targetAngles = angles(this.target);
    const headGoal = this.mode === 'eyes-only' ? { yaw: 0, pitch: 0 } : {
      yaw: clamp(targetAngles.yaw * .65, -60, 60), pitch: clamp(targetAngles.pitch * .6, -40, 40),
    };
    if (instant || this.elapsed >= .09 || this.mode === 'eyes-only') {
      for (const axis of ['yaw', 'pitch']) {
        this.head[axis] = instant ? headGoal[axis] : approach(this.head[axis], headGoal[axis], dt, .24, 110);
      }
    }
    const headQuaternion = quaternion(this.head.yaw, this.head.pitch);
    const inverseHead = headQuaternion.clone().invert();
    const finiteTarget = this.distance === null ? null : this.target.clone().multiplyScalar(this.distance);
    let limited = false;
    const eyePoses = this.eyes.map((eye, i) => {
      const localOrigin = new Vector3((i === 0 ? -1 : 1) * this.ipd / 2, 0, 0);
      const origin = localOrigin.clone().applyQuaternion(headQuaternion);
      const localDirection = finiteTarget
        ? finiteTarget.clone().sub(origin).applyQuaternion(inverseHead).normalize()
        : this.target.clone().applyQuaternion(inverseHead);
      const desired = angles(localDirection);
      const goal = { yaw: clamp(desired.yaw, -35, 35), pitch: clamp(desired.pitch, -25, 25) };
      limited ||= Math.abs(desired.yaw - goal.yaw) > .05 || Math.abs(desired.pitch - goal.pitch) > .05;
      for (const axis of ['yaw', 'pitch']) {
        eye[axis] = instant ? goal[axis] : approach(eye[axis], goal[axis], dt, .025, 700);
      }
      const localQuaternion = quaternion(eye.yaw, eye.pitch);
      return { ...eye, quaternion: localQuaternion, origin,
        direction: forward.clone().applyQuaternion(localQuaternion).applyQuaternion(headQuaternion) };
    });
    const gazeDirection = eyePoses[0].direction.clone().add(eyePoses[1].direction).normalize();
    const headMoving = Math.abs(this.head.yaw-headGoal.yaw)+Math.abs(this.head.pitch-headGoal.pitch) > .2;
    const error = deg(gazeDirection.angleTo(this.target));
    const phase = limited ? (this.mode === 'eyes-only' ? 'Eye limit' : 'Head catching up')
      : error > .3 ? 'Eyes turning' : headMoving ? 'Head following' : 'Fixating';
    return { head: { ...this.head }, headQuaternion, eyes: eyePoses, gazeDirection,
      gaze: angles(gazeDirection), target: { ...targetAngles }, distance: this.distance,
      vergence: this.distance !== null, limited, phase, error };
  }
}

export function pixelForDirection(direction, aspect, vfov) {
  const t = Math.tan(rad(vfov) / 2);
  return { u: .5 + direction.x / -direction.z / (2*t*aspect),
    v: .5 - direction.y / -direction.z / (2*t) };
}
