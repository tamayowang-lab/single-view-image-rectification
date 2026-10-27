import * as THREE from 'three';
import './style.css';

const $ = (id) => document.getElementById(id);
const viewport = $('viewport');
const scene = new THREE.Scene();
scene.background = new THREE.Color('#d9dfd7');
const camera = new THREE.PerspectiveCamera(70, 1, 0.05, 40);
camera.position.set(0, 1.65, 2.4);
camera.rotation.order = 'YXZ';
let renderer;
try {
  renderer = new THREE.WebGLRenderer({ antialias: true });
} catch {
  $('render-error').hidden = false;
  $('render-error').textContent = 'This simulator needs WebGL. Please open it in a browser with hardware acceleration enabled.';
  throw new Error('WebGL is unavailable');
}
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.2;
viewport.appendChild(renderer.domElement);
scene.add(new THREE.HemisphereLight('#eaf4ff', '#8f7961', 2.2));
const sun = new THREE.DirectionalLight('#fff0d3', 3.2);
sun.position.set(-3, 5, -1);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -6, right: 6, top: 6, bottom: -6, near: 0.1, far: 18 });
sun.shadow.normalBias = 0.025;
scene.add(sun);
const fill = new THREE.PointLight('#ffe7bd', 15, 7);
fill.position.set(2.2, 2.1, -1.7);
scene.add(fill);

const materials = {};
function mat(color, roughness = 0.85) {
  const key = `${color}:${roughness}`;
  return materials[key] ??= new THREE.MeshStandardMaterial({ color, roughness });
}
const objects = [];
function entity(name, description, size, position, color) {
  const group = new THREE.Group();
  group.position.set(...position);
  group.userData.info = { name, description, size, color };
  scene.add(group);
  objects.push(group);
  return group;
}
function box(parent, size, position, color) {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(...size), mat(color));
  mesh.position.set(...position);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  parent.add(mesh);
  return mesh;
}
function cylinder(parent, rTop, rBottom, height, position, color, segments = 32) {
  const mesh = new THREE.Mesh(new THREE.CylinderGeometry(rTop, rBottom, height, segments), mat(color));
  mesh.position.set(...position);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  parent.add(mesh);
  return mesh;
}
const floor = entity('Oak floor', 'Room surface · origin at floor center', [6, 0.12, 7], [0, -0.06, 0], '#ba9670');
box(floor, [6, 0.12, 7], [0, 0, 0], '#b8936b');
// Wood grain and staggered board joints, built as geometry.
for (let i = 0; i < 24; i++) {
  const x = -2.875 + i * 0.25;
  box(floor, [0.004, 0.001, 7], [x - 0.125, 0.061, 0], '#907353');
  for (let j = 0; j < 3; j++) {
    const z = -3.3 + j * 2.3 + (i % 3) * 0.5;
    box(floor, [0.245, 0.001, 0.004], [x, 0.061, z], '#907353');
    box(floor, [0.0015, 0.001, 1.7], [x + 0.04, 0.061, z + 0.4], '#aa8661');
  }
}
const wallColor = '#e6e2d8';
for (const [name, size, pos] of [
  ['Back wall', [6, 3, 0.12], [0, 1.5, -3.56]],
  ['Right wall', [0.12, 3, 7], [3.06, 1.5, 0]],
  ['Front wall', [6, 3, 0.12], [0, 1.5, 3.56]],
]) {
  const wall = entity(name, 'Room boundary · ceiling height 3 m', size, pos, wallColor);
  box(wall, size, [0, 0, 0], wallColor);
}
// The left wall is assembled around a genuine window opening.
const leftWall = entity('Window wall', 'Room boundary with daylight opening', [0.12, 3, 7], [-3.06, 0, 0], wallColor);
box(leftWall, [0.12, 0.75, 7], [0, 0.375, 0], wallColor);
box(leftWall, [0.12, 0.45, 7], [0, 2.775, 0], wallColor);
box(leftWall, [0.12, 1.8, 2], [0, 1.65, -2.5], wallColor);
box(leftWall, [0.12, 1.8, 2.5], [0, 1.65, 2.25], wallColor);
const ceiling = entity('Ceiling', 'Room boundary · 3 m above floor', [6, 0.12, 7], [0, 3.06, 0], wallColor);
box(ceiling, [6, 0.12, 7], [0, 0, 0], '#eeeae1');
for (const z of [-3.48, 3.48]) box(scene, [6, 0.09, 0.035], [0, 0.045, z], '#f7f4e9');
for (const x of [-2.98, 2.98]) box(scene, [0.035, 0.09, 7], [x, 0.045, 0], '#f7f4e9');
const windowFrame = entity('Window', 'Daylight window overlooking a stylized garden', [0.18, 1.8, 2.5], [-2.99, 1.65, -0.25], '#bcd4d5');
for (const z of [-1.25, 0, 1.25]) box(windowFrame, [0.12, 1.8, 0.045], [0, 0, z], '#f8f5ec');
for (const y of [-0.9, 0.9]) box(windowFrame, [0.18, 0.05, 2.55], [0, y, 0], '#f8f5ec');
box(windowFrame, [0.26, 0.05, 2.7], [0.04, -0.9, 0], '#e5dac7');
const garden = new THREE.Mesh(new THREE.PlaneGeometry(7, 5), new THREE.MeshBasicMaterial({ color: '#c5d8d4', side: THREE.DoubleSide }));
garden.rotation.y = Math.PI / 2;
garden.position.set(-4.4, 2, -0.25);
scene.add(garden);
for (let i = 0; i < 8; i++) {
  const shrub = new THREE.Mesh(new THREE.SphereGeometry(0.55 + (i % 3) * 0.15, 12, 10), mat(i % 2 ? '#789a69' : '#92aa7b'));
  shrub.position.set(-4.1, 0.3 + (i % 3) * 0.25, -3 + i * 0.8);
  scene.add(shrub);
}
const rug = entity('Woven rug', 'Flat woven wool · beneath the coffee table', [3.4, 0.02, 2.5], [-0.2, 0.02, -0.25], '#d7ccb8');
box(rug, [3.4, 0.02, 2.5], [0, 0, 0], '#d9ceba');
for (let i = 0; i < 30; i++) box(rug, [3.32, 0.001, 0.005], [0, 0.011, -1.2 + i * 0.08], '#c7bba6');
const sofa = entity('Sage sofa', 'Three-seat fabric sofa', [2.6, 0.9, 0.95], [0, 0, -2.58], '#81917b');
box(sofa, [2.5, 0.22, 0.9], [0, 0.28, 0], '#657960');
box(sofa, [2.6, 0.66, 0.18], [0, 0.57, -0.385], '#7b8b73');
for (const x of [-1.2, 1.2]) box(sofa, [0.2, 0.6, 0.95], [x, 0.48, 0], '#7d8f77');
for (const x of [-0.73, 0, 0.73]) {
  box(sofa, [0.7, 0.18, 0.7], [x, 0.48, 0.03], '#96a18b');
  const cushion = box(sofa, [0.69, 0.39, 0.16], [x, 0.69, -0.23], '#93a087');
  cushion.rotation.x = -0.14;
}
for (const x of [-1.04, 1.04]) for (const z of [-0.3, 0.3]) cylinder(sofa, 0.035, 0.025, 0.2, [x, 0.1, z], '#594b38');
const pillow = box(sofa, [0.4, 0.4, 0.16], [-0.85, 0.7, 0.03], '#c7a783');
pillow.rotation.z = 0.2;
const table = entity('Coffee table', 'Solid oak coffee table', [1.4, 0.45, 0.7], [0, 0, -0.65], '#a07952');
box(table, [1.4, 0.065, 0.7], [0, 0.4175, 0], '#a98058');
for (const x of [-0.57, 0.57]) for (const z of [-0.23, 0.23]) cylinder(table, 0.035, 0.025, 0.39, [x, 0.195, z], '#926b47');
const books = entity('Books', 'Two books on the coffee table', [0.32, 0.065, 0.24], [-0.3, 0.45, -0.65], '#99745e');
box(books, [0.32, 0.03, 0.24], [0, 0.015, 0], '#ae8263');
box(books, [0.29, 0.035, 0.22], [0.01, 0.0475, 0], '#ded8c5');
const cup = entity('Ceramic cup', 'Small ceramic cup on the table', [0.1, 0.11, 0.1], [0.32, 0.45, -0.62], '#ece6d6');
cylinder(cup, 0.05, 0.04, 0.11, [0, 0.055, 0], '#e9dfcc');
cylinder(cup, 0.041, 0.041, 0.002, [0, 0.111, 0], '#5e4534');
const cabinet = entity('Sideboard', 'Walnut storage cabinet', [0.45, 0.8, 1.8], [2.65, 0, 0], '#896b50');
box(cabinet, [0.45, 0.68, 1.8], [0, 0.46, 0], '#967557');
for (const z of [-0.6, 0, 0.6]) {
  box(cabinet, [0.015, 0.57, 0.565], [-0.23, 0.45, z], '#a48461');
  cylinder(cabinet, 0.012, 0.012, 0.07, [-0.25, 0.57, z], '#cbb987');
}
for (const z of [-0.75, 0.75]) box(cabinet, [0.32, 0.12, 0.06], [0, 0.06, z], '#5d4e3c');
const vase = entity('Terracotta vase', 'Decorative vessel on the sideboard', [0.22, 0.36, 0.22], [2.65, 0.8, -0.5], '#b77c60');
cylinder(vase, 0.075, 0.11, 0.28, [0, 0.14, 0], '#b77c60');
cylinder(vase, 0.065, 0.075, 0.08, [0, 0.32, 0], '#b77c60');
const plant = entity('Indoor plant', 'A leafy plant in a stoneware pot', [0.9, 1.7, 0.9], [2.15, 0, -2.45], '#648258');
cylinder(plant, 0.22, 0.16, 0.42, [0, 0.21, 0], '#d1c2a7');
cylinder(plant, 0.2, 0.2, 0.012, [0, 0.425, 0], '#5c5140');
for (let i = 0; i < 14; i++) {
  const angle = i * 2.4;
  const y = 0.66 + (i % 5) * 0.19;
  const leaf = new THREE.Mesh(new THREE.SphereGeometry(1, 12, 8), mat(i % 2 ? '#617c51' : '#7d945f'));
  leaf.scale.set(0.12, 0.28, 0.055);
  leaf.position.set(Math.sin(angle) * 0.27, y, Math.cos(angle) * 0.27);
  leaf.rotation.set(0.4, angle, Math.sin(angle) * 0.8);
  leaf.castShadow = true;
  plant.add(leaf);
  const start = new THREE.Vector3(0, 0.42, 0);
  const end = leaf.position.clone();
  const stem = cylinder(plant, 0.008, 0.01, start.distanceTo(end), start.clone().add(end).multiplyScalar(0.5).toArray(), '#61714b', 6);
  stem.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), end.sub(start).normalize());
}
const lamp = entity('Floor lamp', 'Linen shade with a brass stand', [0.5, 1.85, 0.5], [-2, 0, -2.5], '#d4bc8c');
cylinder(lamp, 0.2, 0.23, 0.035, [0, 0.018, 0], '#6e6757');
cylinder(lamp, 0.018, 0.018, 1.65, [0, 0.85, 0], '#ae976c');
cylinder(lamp, 0.18, 0.25, 0.38, [0, 1.66, 0], '#f3e3c2');
const art = entity('Wall art', 'Abstract landscape in an oak frame', [1.5, 0.9, 0.045], [0, 1.95, -3.465], '#b5a17e');
box(art, [1.5, 0.9, 0.045], [0, 0, 0], '#8e7457');
box(art, [1.4, 0.8, 0.005], [0, 0, 0.025], '#dfd8c0');
box(art, [1.26, 0.3, 0.008], [0, -0.18, 0.03], '#8e9d84');
box(art, [0.7, 0.16, 0.01], [-0.28, -0.07, 0.037], '#b5bd9f');
const artSun = new THREE.Mesh(new THREE.CircleGeometry(0.105, 32), new THREE.MeshBasicMaterial({ color: '#b98358' }));
artSun.position.set(0.35, 0.17, 0.034);
art.add(artSun);
const door = entity('Door', 'Closed oak door', [0.045, 2.2, 0.95], [2.98, 1.1, 2.35], '#b19b7c');
box(door, [0.045, 2.2, 0.95], [0, 0, 0], '#b19b7c');
box(door, [0.07, 0.04, 0.15], [-0.045, -0.1, -0.3], '#777366');

let yaw = 0;
let pitch = -0.04;
let dragging = false;
let lastX = 0;
let lastY = 0;
const rad = THREE.MathUtils.degToRad;
const deg = THREE.MathUtils.radToDeg;
function look(dx, dy) {
  yaw -= dx * 0.004;
  pitch = THREE.MathUtils.clamp(pitch - dy * 0.004, rad(-85), rad(85));
  yaw = THREE.MathUtils.euclideanModulo(yaw + Math.PI, Math.PI * 2) - Math.PI;
}
viewport.addEventListener('pointerdown', (event) => {
  if (event.target.closest('button') || (event.pointerType === 'mouse' && event.button !== 0)) return;
  dragging = true;
  lastX = event.clientX;
  lastY = event.clientY;
  viewport.setPointerCapture(event.pointerId);
  viewport.classList.add('dragging');
  viewport.focus({ preventScroll: true });
});
viewport.addEventListener('pointermove', (event) => {
  if (!dragging) return;
  look(event.clientX - lastX, event.clientY - lastY);
  lastX = event.clientX;
  lastY = event.clientY;
});
function endDrag() { dragging = false; viewport.classList.remove('dragging'); }
viewport.addEventListener('pointerup', endDrag);
viewport.addEventListener('pointercancel', endDrag);
viewport.addEventListener('lostpointercapture', endDrag);
function reset() {
  yaw = 0; pitch = -0.04;
  camera.position.y = 1.65; camera.fov = 70;
  $('height').value = '1.65'; $('fov').value = '70';
  camera.updateProjectionMatrix();
  updateControls();
}
$('reset').addEventListener('click', reset);
viewport.addEventListener('keydown', (event) => {
  const steps = { ArrowLeft: [-12, 0], ArrowRight: [12, 0], ArrowUp: [0, -12], ArrowDown: [0, 12] };
  if (steps[event.key]) { event.preventDefault(); look(...steps[event.key]); }
  if (event.key.toLowerCase() === 'r') reset();
});
function updateControls() {
  $('height-value').textContent = camera.position.y.toFixed(2);
  $('height-output').textContent = `${camera.position.y.toFixed(2)} m`;
  $('fov-output').textContent = `${camera.fov}°`;
  $('view-fov').textContent = `${camera.fov}° VERTICAL FOV`;
}
$('height').addEventListener('input', (event) => { camera.position.y = Number(event.target.value); updateControls(); });
$('fov').addEventListener('input', (event) => { camera.fov = Number(event.target.value); camera.updateProjectionMatrix(); updateControls(); });
function resize() {
  const { width, height } = viewport.getBoundingClientRect();
  renderer.setSize(width, height);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}
new ResizeObserver(resize).observe(viewport);
resize();

const raycaster = new THREE.Raycaster();
const map = $('map');
const ctx = map.getContext('2d');
const scale = 40;
const mx = (x) => 260 + x * scale;
const mz = (z) => 170 + z * scale;
function drawMap() {
  ctx.clearRect(0, 0, 520, 340);
  ctx.fillStyle = '#e8ece3'; ctx.fillRect(0, 0, 520, 340);
  ctx.strokeStyle = '#c1cab9'; ctx.lineWidth = 2;
  ctx.strokeRect(mx(-3), mz(-3.5), 6 * scale, 7 * scale);
  for (const obj of [rug, sofa, table, cabinet, plant, lamp, door]) {
    const { size, color } = obj.userData.info;
    ctx.fillStyle = color;
    ctx.globalAlpha = obj === rug ? 0.5 : 0.85;
    ctx.fillRect(mx(obj.position.x - size[0] / 2), mz(obj.position.z - size[2] / 2), Math.max(3, size[0] * scale), size[2] * scale);
  }
  ctx.globalAlpha = 1;
  const x = mx(camera.position.x); const z = mz(camera.position.z);
  const horizontalFov = 2 * Math.atan(Math.tan(rad(camera.fov) / 2) * camera.aspect);
  ctx.save(); ctx.beginPath(); ctx.rect(mx(-3), mz(-3.5), 6 * scale, 7 * scale); ctx.clip();
  ctx.beginPath(); ctx.moveTo(x, z);
  for (let i = 0; i <= 40; i++) {
    const a = -yaw - horizontalFov / 2 + horizontalFov * i / 40;
    ctx.lineTo(x + Math.sin(a) * 120, z - Math.cos(a) * 120);
  }
  ctx.closePath(); ctx.fillStyle = '#69886830'; ctx.fill();
  ctx.beginPath(); ctx.moveTo(x, z); ctx.lineTo(x - Math.sin(yaw) * 32, z - Math.cos(yaw) * 32);
  ctx.strokeStyle = '#4a7150'; ctx.lineWidth = 2; ctx.stroke(); ctx.restore();
  ctx.beginPath(); ctx.arc(x, z, 6, 0, Math.PI * 2); ctx.fillStyle = '#4a7150'; ctx.fill();
  ctx.strokeStyle = '#f3f4ef'; ctx.lineWidth = 2; ctx.stroke();
}
let lastInfo = '';
function updateHit() {
  raycaster.setFromCamera(new THREE.Vector2(0, 0), camera);
  const hit = raycaster.intersectObjects(scene.children, true)[0];
  let parent = hit?.object;
  while (parent && !parent.userData.info) parent = parent.parent;
  const info = parent?.userData.info;
  const name = info?.name ?? 'Garden view';
  const distance = hit ? `${hit.distance.toFixed(2)} m` : '—';
  $('target-name').textContent = name;
  $('target-distance').textContent = distance;
  $('surface-distance').textContent = distance;
  if (lastInfo !== name) {
    lastInfo = name;
    $('object-name').textContent = name;
    $('object-description').textContent = info?.description ?? 'Outside the room boundary';
    $('object-size').textContent = info ? `${info.size.map(v => v.toFixed(2)).join(' × ')} m` : '—';
  }
}
function frame() {
  camera.rotation.set(pitch, yaw, 0, 'YXZ');
  renderer.render(scene, camera);
  updateHit();
  $('yaw-value').textContent = `${Math.round(-deg(yaw))}°`;
  $('pitch-value').textContent = `${Math.round(deg(pitch))}°`;
  drawMap();
}
renderer.setAnimationLoop(frame);
