import * as THREE from 'three';
import { HeadEyeModel, pixelForDirection } from './head-eye-model.js';
import { HeadEyeView } from './head-eye-view.js';
import { AttentionSearch } from './attention-search.js';
import { buildAttentionCandidates } from './attention-candidates.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import sampleUrl from '../../images/2.jpg';
import { rayForPixel, depthAt, axialDepth, calibrateDepth, estimateBox, gazeAngles, gazeRing } from './photo-geometry.js';
import './style.css';
import './photo.css';

const $ = id => document.getElementById(id);
const canvas=$('photo'), ctx=canvas.getContext('2d');
const original=document.createElement('canvas'), source=original.getContext('2d',{willReadFrequently:true});
let version=0, data=null, calibration=null, refs=[null,null], picking=null;
let u=.5,v=.5, targetU=.5,targetV=.5, vfov=60, hfov=40, efov=28, running=false,pending=false, filename='photo';
const motor=new HeadEyeModel();
let avatar=null, pose=motor.step(0,true), attentionCandidates=[], targetFromSearch=false;
const attention=new AttentionSearch();
$('instant-motion').checked=matchMedia('(prefers-reduced-motion: reduce)').matches;
try {
  avatar=new HeadEyeView($('head-avatar'));
  $('avatar-placeholder').hidden=true;
} catch {
  $('avatar-placeholder').textContent='WebGL is unavailable. Gaze angles and the photo oval still work; enable hardware acceleration to see the head.';
}
const aspect=()=>original.width/original.height;
function status(text,error=false) { $('status').textContent=text; $('status').classList.toggle('error-text',error); }
const inBox=(x,y,b)=>x>=b[0]&&x<=b[2]&&y>=b[1]&&y<=b[3];
function objectAt(x,y) {
  return data?.objects.filter(o=>inBox(x,y,o.box)).sort((a,b)=>(a.box[2]-a.box[0])*(a.box[3]-a.box[1])-(b.box[2]-b.box[0])*(b.box[3]-b.box[1]))[0];
}
function ring() {return gazeRing(u,v,aspect(),vfov,hfov,efov);}
function draw() {
  if(!original.width || canvas.hidden) return;
  const w=canvas.width,h=canvas.height;
  ctx.clearRect(0,0,w,h);
  ctx.filter='grayscale(1)';ctx.drawImage(original,0,0);ctx.filter='none';
  for(const o of data?.objects??[]) {
    const [x1,y1,x2,y2]=o.box;
    ctx.drawImage(original,x1*w,y1*h,(x2-x1)*w,(y2-y1)*h,x1*w,y1*h,(x2-x1)*w,(y2-y1)*h);
    const selected=o===objectAt(u,v);
    ctx.strokeStyle=selected?'#f2cc76':'#a0e5c0';ctx.lineWidth=selected?3:2;
    ctx.strokeRect(x1*w,y1*h,(x2-x1)*w,(y2-y1)*h);
    ctx.font=`500 ${Math.max(11,w/65)}px system-ui`;
    const title=`${o.label} · ${Math.round(o.confidence*100)}%`;
    const tw=ctx.measureText(title).width;
    const ty=Math.max(0,y1*h-24),tx=Math.min(x1*w,Math.max(0,w-tw-14));
    ctx.fillStyle='#233b30e6';ctx.fillRect(tx,ty,tw+14,24);
    ctx.fillStyle='#e9fae9';ctx.fillText(title,tx+7,ty+16);
  }
  // Unlabeled contrast regions are attention cues, not additional semantic detections.
  for(const region of attentionCandidates.filter(c=>c.kind==='region')){
    const [a,b,c,d]=region.box;
    ctx.save();ctx.strokeStyle='#7bcde099';ctx.lineWidth=1;ctx.setLineDash([4,5]);ctx.strokeRect(a*w,b*h,(c-a)*w,(d-b)*h);ctx.restore();
  }
  if(attention.history.length){
    ctx.save();ctx.strokeStyle='#f2b967bb';ctx.lineWidth=1.5;ctx.beginPath();
    attention.history.forEach((p,i)=>i?ctx.lineTo(p.u*w,p.v*h):ctx.moveTo(p.u*w,p.v*h));ctx.stroke();
    attention.history.forEach((p,i)=>{ctx.beginPath();ctx.arc(p.u*w,p.v*h,8,0,Math.PI*2);ctx.fillStyle='#e4aa60';ctx.fill();ctx.fillStyle='#283b2c';ctx.font='bold 10px system-ui';ctx.fillText(String(i+1),p.u*w-3,p.v*h+3);});ctx.restore();
  }
  // Small amber marker is the requested point; the white crosshair is actual gaze.
  if(Math.hypot(targetU-u,targetV-v)>.004){
    ctx.beginPath();ctx.arc(targetU*w,targetV*h,5,0,Math.PI*2);ctx.strokeStyle='#e9ad58';ctx.lineWidth=2;ctx.stroke();
  }
  const outline=ring();
  ctx.save();ctx.beginPath();ctx.rect(0,0,w,h);ctx.clip();
  ctx.beginPath();let started=false;
  for(const p of outline) {
    if(!p.visible) {started=false;continue;}
    if(!started){ctx.moveTo(p.u*w,p.v*h);started=true;}else ctx.lineTo(p.u*w,p.v*h);
  }
  if(outline.every(p=>p.visible)) ctx.closePath();
  ctx.fillStyle='#95e2bd22';ctx.fill();ctx.strokeStyle='#eaffc9';ctx.lineWidth=2.5;ctx.setLineDash([8,5]);ctx.stroke();ctx.setLineDash([]);
  ctx.beginPath();ctx.arc(u*w,v*h,8,0,Math.PI*2);ctx.strokeStyle='#fff';ctx.lineWidth=2;ctx.stroke();
  ctx.beginPath();ctx.moveTo(u*w-15,v*h);ctx.lineTo(u*w+15,v*h);ctx.moveTo(u*w,v*h-15);ctx.lineTo(u*w,v*h+15);ctx.stroke();
  refs.forEach((r,i)=>{if(!r)return;ctx.beginPath();ctx.arc(r.u*w,r.v*h,10,0,Math.PI*2);ctx.fillStyle=i?'#e4ab65':'#7bcef0';ctx.fill();ctx.fillStyle='#172e2a';ctx.font='bold 13px system-ui';ctx.fillText(String(i+1),r.u*w-4,r.v*h+5);});
  ctx.restore();
}
function updateReadout() {
  if(canvas.hidden) return;
  const angles=gazeAngles(u,v,aspect(),vfov);
  $('photo-yaw').textContent=`${angles.yaw.toFixed(1)}°`;
  $('photo-pitch').textContent=`${angles.pitch.toFixed(1)}°`;
  const object=objectAt(u,v);
  $('photo-object').textContent=object?.label??'Scene surface';
  $('photo-confidence').textContent=object?`${Math.round(object.confidence*100)}% model confidence · visible bounding box`:data?'No recognized object at this pixel.':'Waiting for image analysis.';
  $('depth-unit').textContent=calibration?'CALIBRATED ESTIMATE':'RELATIVE DEPTH';
  if(data) {
    const p=depthAt(data.depth,u,v);
    $('relative-depth').textContent=`${p.toFixed(2)} / 1`;
    const z=calibration?axialDepth(p,calibration):null;
    $('metric-distance').textContent=z===null?(calibration?'Outside calibrated range':'Uncalibrated'):`≈ ${(z/rayForPixel(u,v,aspect(),vfov).axialFactor).toFixed(2)} m`;
    const size=object?estimateBox(object.box,object.relative_inverse_depth,calibration,aspect(),vfov):null;
    $('metric-size').textContent=size?`≈ ${size.width.toFixed(2)} × ${size.height.toFixed(2)} m`:calibration?'Unknown':'Uncalibrated';
    const d=z===null?null:z/rayForPixel(u,v,aspect(),vfov).axialFactor;
    $('footprint').textContent=d===null?'Physical range requires depth calibration.':`At this range: ≈ ${(2*d*Math.tan(hfov*Math.PI/360)).toFixed(2)} × ${(2*d*Math.tan(efov*Math.PI/360)).toFixed(2)} m on a plane perpendicular to gaze.`;
  } else {
    $('relative-depth').textContent='—';$('metric-distance').textContent='Uncalibrated';$('metric-size').textContent='Uncalibrated';
    $('footprint').textContent='Physical range requires depth calibration.';
  }
}
function paintGaze(){draw();updateReadout();updateCone();}
function updateGaze(){
  const direction=rayForPixel(targetU,targetV,aspect(),vfov);
  const z=data&&calibration?axialDepth(depthAt(data.depth,targetU,targetV),calibration):null;
  motor.aim(direction,z===null?null:z/direction.axialFactor,targetFromSearch?{hfov,efov}:null);
  if($('instant-motion').checked)advanceMotion(0,true);
  paintGaze();
}
function stopSearch(){attention.stop();updateSearchReadout();}
function setGazeTarget(x,y,manual=true){
  if(manual)stopSearch();targetFromSearch=!manual;targetU=x;targetV=y;updateGaze();
}
function rebuildCandidates(){
  attention.reset();
  attentionCandidates=data?buildAttentionCandidates(source.getImageData(0,0,original.width,original.height),data.objects,$('search-scope').value==='all'):[];
  const objects=attentionCandidates.filter(c=>c.kind==='object').length,regions=attentionCandidates.length-objects;
  $('candidate-count').textContent=`${objects} recognized objects + ${regions} unlabeled visual regions`;
  $('object-tour').disabled=!data;
  updateSearchReadout();
}
function updateSearchReadout(){
  const summary=attention.summary();
  write('search-state',({idle:'Ready',running:'Searching',paused:'Paused',stopped:'Stopped',complete:'Search complete'})[summary.state]);
  write('search-phase',summary.phase==='saccade'?'Saccade':summary.phase==='fixation'?'Fixation':'—');
  write('search-coverage',`${summary.visited} / ${summary.total} inspected · ${summary.skipped} skipped`);
  write('search-reason',summary.reason);write('search-statistics',`${summary.fixations} completed fixations · current target: ${summary.target}`);
  $('search-progress').max=Math.max(1,summary.total);$('search-progress').value=summary.visited+summary.skipped;
  $('search-pause').disabled=!['running','paused'].includes(summary.state);$('search-pause').textContent=summary.state==='paused'?'Resume':'Pause';
  $('search-stop').disabled=!['running','paused'].includes(summary.state);
  $('object-tour').classList.toggle('running',summary.state==='running');$('object-tour').setAttribute('aria-pressed',String(summary.state==='running'));
  const panel=$('search-state');panel.dataset.visited=summary.visited;panel.dataset.total=summary.total;panel.dataset.skipped=summary.skipped;panel.dataset.fixations=summary.fixations;panel.dataset.state=summary.state;
}
function startSearch(point={u,v}){
  if(!data)return;
  $('follow-pointer').checked=false;
  const event=attention.start(attentionCandidates,point,{aspect:aspect(),vfov,hfov,efov});
  setGazeTarget(event.target.u,event.target.v,false);updateSearchReadout();
}
function write(id,text){if($(id).textContent!==text)$(id).textContent=text;}
function advanceMotion(dt,instant=false){
  pose=motor.step(dt,instant);
  if(!canvas.hidden){
    const point=pixelForDirection(pose.gazeDirection,aspect(),vfov);
    const changed=Math.abs(point.u-u)+Math.abs(point.v-v)>1e-6;
    u=point.u;v=point.v;
    if(changed)paintGaze();
  }
  const pair=a=>`${a.yaw.toFixed(1)}° / ${a.pitch.toFixed(1)}°`;
  write('motion-phase',pose.phase.toUpperCase());
  write('head-angles',pair(pose.head));write('left-eye-angles',pair(pose.eyes[0]));write('right-eye-angles',pair(pose.eyes[1]));
  write('vergence-status',pose.vergence?`Converging · ≈ ${pose.distance.toFixed(2)} m`:'Parallel · no metric scale');
  const host=$('head-avatar');
  host.dataset.headYaw=pose.head.yaw.toFixed(3);host.dataset.headPitch=pose.head.pitch.toFixed(3);
  host.dataset.leftEyeYaw=pose.eyes[0].yaw.toFixed(3);host.dataset.rightEyeYaw=pose.eyes[1].yaw.toFixed(3);
  host.dataset.gazeU=u.toFixed(5);host.dataset.gazeV=v.toFixed(5);host.dataset.targetU=targetU.toFixed(5);host.dataset.targetV=targetV.toFixed(5);
  host.dataset.limited=String(pose.limited);
  avatar?.update(pose);
}
$('movement-mode').onchange=()=>{motor.setMode($('movement-mode').value);updateGaze();};
$('instant-motion').onchange=()=>{if($('instant-motion').checked)advanceMotion(0,true);};
$('avatar-view').onchange=()=>{
  avatar?.setView($('avatar-view').value);
  $('observer-note').textContent=$('avatar-view').value==='front'?'Facing you: the head’s right appears on your left. Drag to inspect.':'External observer view. Drag to orbit the head; this does not change its gaze.';
};
$('object-tour').onclick=()=>startSearch();
$('search-pause').onclick=()=>{if(attention.state==='paused')attention.resume();else attention.pause();updateSearchReadout();};
$('search-stop').onclick=()=>stopSearch();
$('search-scope').onchange=()=>{stopSearch();rebuildCandidates();paintGaze();};
$('search-on-click').onchange=()=>{if($('search-on-click').checked)$('follow-pointer').checked=false;else stopSearch();};
$('follow-pointer').onchange=()=>{if($('follow-pointer').checked){$('search-on-click').checked=false;stopSearch();}};
function resetReferences(message='Relative reconstruction · arbitrary scale.') {
  refs=[null,null];calibration=null;picking=null;
  [0,1].forEach(i=>{$(`reference-${i}`).textContent='Not selected';$(`distance-${i}`).value='';$(`pick-${i}`).classList.remove('active');});
  $('calibration-status').textContent=message;
  $('pointer-hint').textContent='Click to start search · arrow keys aim manually';
}
async function loadImage(blob,name) {
  const id=++version;data=null;pending=false;filename=name;
  stopSearch();attention.reset();attentionCandidates=[];targetFromSearch=false;$('candidate-count').textContent='Analyze a photo to find candidates.';updateSearchReadout();$('object-tour').disabled=true;motor.reset();targetU=targetV=u=v=.5;
  resetReferences();$('object-list').replaceChildren();$('object-count').textContent='0';
  $('analyze').disabled=true;$('download').disabled=true;
  for(const i of [0,1])$(`pick-${i}`).disabled=true;
  clearCloud();status('Opening photograph…');
  try {
    if(blob.size>25*1024*1024) throw new Error('Choose a photo smaller than 25 MB.');
    const image=await createImageBitmap(blob);
    if(id!==version){image.close();return;}
    if(image.width<64||image.height<64){image.close();throw new Error('The photograph must be at least 64 pixels per side.');}
    const scale=Math.min(1,1024/Math.max(image.width,image.height));
    original.width=canvas.width=Math.round(image.width*scale);original.height=canvas.height=Math.round(image.height*scale);
    source.drawImage(image,0,0,original.width,original.height);image.close();
    targetU=targetV=u=v=.5;$('empty-state').hidden=true;canvas.hidden=false;
    $('filename').textContent=`${name} · ${original.width} × ${original.height}`;
    $('analyze').disabled=false;updateGaze();requestAnalysis();
  } catch(error) {if(id===version){status(error.message,true);canvas.hidden=true;$('empty-state').hidden=false;}}
}
async function requestAnalysis() {
  if(canvas.hidden)return;
  pending=true;if(running)return;
  running=true;
  while(pending) {
    pending=false;const id=version;
    status('Analyzing objects and visible depth locally…');
    try {
      const blob=await new Promise(resolve=>original.toBlob(resolve,'image/jpeg',.92));
      if(id!==version)continue;
      const form=new FormData();form.append('image',blob,'photo.jpg');
      const response=await fetch('/api/analyze',{method:'POST',body:form,signal:AbortSignal.timeout(90000)});
      if(!response.ok) {
        let detail='';try{detail=(await response.json()).detail??'';}catch{}
        throw new Error(detail||`Analysis unavailable (${response.status}). Start the local Python analysis server, then retry.`);
      }
      const result=await response.json();if(id!==version)continue;
      if(result.width!==canvas.width||result.height!==canvas.height||!result.depth?.values?.length)throw new Error('Analysis returned an incompatible image.');
      data=result;resetReferences();rebuildCandidates();
      $('object-count').textContent=String(data.objects.length);
      const list=$('object-list');list.replaceChildren();
      for(const o of data.objects) {
        const button=document.createElement('button');
        const label=document.createElement('strong');label.textContent=o.label;
        const confidence=document.createElement('span');confidence.textContent=`${Math.round(o.confidence*100)}%`;
        button.append(label,confidence);button.onclick=()=>setGazeTarget((o.box[0]+o.box[2])/2,(o.box[1]+o.box[3])/2);
        list.append(button);
      }
      if(!data.objects.length){const p=document.createElement('p');p.className='muted';p.textContent='No COCO objects above 45% confidence. Depth is still reconstructed.';list.append(p);}
      [0,1].forEach(i=>$(`pick-${i}`).disabled=false);$('download').disabled=false;
      buildCloud();updateGaze();
      status(`${data.objects.length} objects detected · ${data.elapsed_seconds} s · Local analysis complete. Click the photo to begin spatial search.`);
    } catch(error) {
      if(id===version){status(`Analysis failed: ${error.message}`,true);}
    }
  }
  running=false;
}
$('photo-input').addEventListener('change',event=>{const file=event.target.files[0];if(file)loadImage(file,file.name);event.target.value='';});
$('sample').onclick=async()=>{try{const response=await fetch(sampleUrl);if(!response.ok)throw new Error('Example image is unavailable.');await loadImage(await response.blob(),'Example · courtyard');}catch(error){status(error.message,true);}};
$('analyze').onclick=requestAnalysis;
function pointFromEvent(event) {
  const box=canvas.getBoundingClientRect();
  return {u:THREE.MathUtils.clamp((event.clientX-box.left)/box.width,0,1),v:THREE.MathUtils.clamp((event.clientY-box.top)/box.height,0,1)};
}
canvas.addEventListener('pointermove',event=>{if(!$('follow-pointer').checked||picking!==null)return;const point=pointFromEvent(event);setGazeTarget(point.u,point.v);});
canvas.addEventListener('click',event=>{
  const point=pointFromEvent(event);
  if(picking!==null&&data){
    setGazeTarget(point.u,point.v);
    const i=picking;refs[i]={...point,distance:Number($(`distance-${i}`).value)};
    $(`reference-${i}`).textContent=`Pixel ${Math.round(point.u*canvas.width)}, ${Math.round(point.v*canvas.height)}`;
    $(`pick-${i}`).classList.remove('active');picking=null;$('pointer-hint').textContent='Click to start search · arrow keys aim manually';
    applyCalibration();
  } else if($('search-on-click').checked&&data){startSearch(point);}
  else setGazeTarget(point.u,point.v);
  canvas.focus({preventScroll:true});updateGaze();
});
canvas.addEventListener('keydown',event=>{
  const moves={ArrowLeft:[-.01,0],ArrowRight:[.01,0],ArrowUp:[0,-.01],ArrowDown:[0,.01]};
  if(moves[event.key]){event.preventDefault();setGazeTarget(THREE.MathUtils.clamp(targetU+moves[event.key][0],0,1),THREE.MathUtils.clamp(targetV+moves[event.key][1],0,1));}
});
$('center-gaze').onclick=()=>setGazeTarget(.5,.5);
for(const [id,set] of [['eye-fov',value=>hfov=value],['eye-vfov',value=>efov=value]]) {
  $(id).oninput=()=>{stopSearch();set(Number($(id).value));$(id+'-output').textContent=$(id).value+'°';updateGaze();};
}
$('photo-fov').oninput=()=>{
  stopSearch();vfov=Number($('photo-fov').value);$('photo-fov-output').textContent=vfov+'°';
  resetReferences('Camera FOV changed. Re-enter references to calibrate.');if(data)buildCloud();updateGaze();
};
function applyCalibration() {
  stopSearch();calibration=null;if(!data)return;
  refs.forEach((r,i)=>{if(r)r.distance=Number($(`distance-${i}`).value);});
  try {calibration=calibrateDepth(refs,data.depth,aspect(),vfov);$('calibration-status').textContent='Approximate meters enabled for this photo. Model errors still affect depth and visible size.';}
  catch(error){$('calibration-status').textContent=error.message;}
  buildCloud();updateGaze();
}
for(let i=0;i<2;i++) {
  $(`pick-${i}`).onclick=()=>{stopSearch();picking=picking===i?null:i;[0,1].forEach(j=>$(`pick-${j}`).classList.toggle('active',picking===j));$('pointer-hint').textContent=picking===null?'Click to start search · arrow keys aim manually':`Click surface ${i+1} for calibration`;} ;
  $(`distance-${i}`).oninput=applyCalibration;
}
$('clear-calibration').onclick=()=>{resetReferences();if(data)buildCloud();updateGaze();};
$('download').onclick=()=>{const link=document.createElement('a');link.download=`${filename.replace(/[^a-z0-9.-]/gi,'-')}-gaze.png`;link.href=canvas.toDataURL('image/png');link.click();};

// The cloud is a back-projection of visible pixels, not generated hidden geometry.
const host=$('reconstruction');
let renderer=null, scene=null, view=null, controls=null, cloud=null, cone=null, modelCenter=new THREE.Vector3(), modelRadius=5;
try {
  renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));
  renderer.setClearColor('#202c29');renderer.domElement.hidden=true;host.append(renderer.domElement);
  scene=new THREE.Scene();view=new THREE.PerspectiveCamera(50,1,.01,500);
  controls=new OrbitControls(view,renderer.domElement);controls.enableDamping=true;controls.minDistance=.1;
  const head=new THREE.Mesh(new THREE.SphereGeometry(.08,16,12),new THREE.MeshBasicMaterial({color:'#d5edbb',wireframe:true}));scene.add(head);
  scene.add(new THREE.AxesHelper(.4));
  new ResizeObserver(()=>{const {width,height}=host.getBoundingClientRect();renderer.setSize(width,height);view.aspect=width/height;view.updateProjectionMatrix();}).observe(host);
  renderer.setAnimationLoop(()=>{controls.update();renderer.render(scene,view);});
} catch(error) {
  $('reconstruction-placeholder').textContent='WebGL is unavailable. Photo analysis and click-to-aim still work; enable hardware acceleration for the 3D preview.';
}
function dispose(object){if(!object)return;scene.remove(object);object.geometry.dispose();object.material.dispose();}
function clearCloud(){if(!renderer)return;dispose(cloud);dispose(cone);cloud=cone=null;renderer.domElement.hidden=true;$('reconstruction-placeholder').hidden=false;$('reset-3d').disabled=true;}
function buildCloud() {
  if(!renderer||!data)return;
  dispose(cloud);const vertices=[],colors=[];
  const pixels=source.getImageData(0,0,original.width,original.height).data;
  for(let y=0;y<data.depth.height;y++)for(let x=0;x<data.depth.width;x++) {
    const px=(x+.5)/data.depth.width,py=(y+.5)/data.depth.height;
    const p=depthAt(data.depth,px,py),z=axialDepth(p,calibration);
    if(z===null||z>150)continue;
    const ray=rayForPixel(px,py,aspect(),vfov),d=z/ray.axialFactor;
    vertices.push(ray.x*d,ray.y*d,ray.z*d);
    const i=(Math.min(original.height-1,Math.floor(py*original.height))*original.width+Math.min(original.width-1,Math.floor(px*original.width)))*4;
    let r=pixels[i]/255,g=pixels[i+1]/255,b=pixels[i+2]/255;
    if(!objectAt(px,py))r=g=b=.2126*r+.7152*g+.0722*b;
    const color=new THREE.Color(r,g,b).convertSRGBToLinear();colors.push(color.r,color.g,color.b);
  }
  if(!vertices.length){$('reconstruction-placeholder').hidden=false;$('reconstruction-placeholder').textContent='No positive depths in the calibrated range. Clear calibration and check the reference points.';return;}
  const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));geometry.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));
  geometry.computeBoundingSphere();modelCenter.copy(geometry.boundingSphere.center);modelRadius=Math.max(.5,geometry.boundingSphere.radius);
  cloud=new THREE.Points(geometry,new THREE.PointsMaterial({size:modelRadius*.006,vertexColors:true,sizeAttenuation:true}));scene.add(cloud);
  renderer.domElement.hidden=false;$('reconstruction-placeholder').hidden=true;$('reset-3d').disabled=false;
  reset3d();updateCone();
}
function reset3d(){if(!view)return;controls.target.copy(modelCenter);view.position.copy(modelCenter).add(new THREE.Vector3(modelRadius*.95,modelRadius*.45,modelRadius*1.8));controls.update();}
$('reset-3d').onclick=reset3d;
function updateCone() {
  if(!renderer||!data||!cloud)return;
  dispose(cone);const ray=rayForPixel(u,v,aspect(),vfov),z=axialDepth(depthAt(data.depth,u,v),calibration);
  if(z===null){cone=null;return;}
  const distance=Math.min(150,z/ray.axialFactor);
  const segments=[],points=ring();
  for(let i=0;i<points.length-1;i++) {
    const a=points[i].direction,b=points[i+1].direction;
    segments.push(a.x*distance,a.y*distance,a.z*distance,b.x*distance,b.y*distance,b.z*distance);
    if(i%12===0)segments.push(0,0,0,a.x*distance,a.y*distance,a.z*distance);
  }
  segments.push(0,0,0,ray.x*distance,ray.y*distance,ray.z*distance);
  const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(segments,3));
  cone=new THREE.LineSegments(geometry,new THREE.LineBasicMaterial({color:'#b8ed9a',transparent:true,opacity:.75}));scene.add(cone);
}

let previousFrame=performance.now();
function animateHead(now){
  const dt=Math.min(.05,(now-previousFrame)/1000);previousFrame=now;
  advanceMotion(dt,$('instant-motion').checked);
  const event=attention.tick(dt,pose);
  if(event?.type==='target')setGazeTarget(event.target.u,event.target.v,false);
  if(event)paintGaze();
  updateSearchReadout();
  requestAnimationFrame(animateHead);
}
requestAnimationFrame(animateHead);
