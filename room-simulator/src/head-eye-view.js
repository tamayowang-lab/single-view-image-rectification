import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

/** A procedural mannequin, with eye pivots matching the controller's 64 mm IPD. */
export class HeadEyeView {
  constructor(host) {
    this.host=host;
    this.renderer=new THREE.WebGLRenderer({antialias:true,alpha:false});
    this.renderer.setPixelRatio(Math.min(devicePixelRatio,2));
    this.renderer.setClearColor('#e5e9df');
    this.renderer.setSize(host.clientWidth,host.clientHeight);
    host.append(this.renderer.domElement);
    this.scene=new THREE.Scene();
    this.scene.add(new THREE.HemisphereLight('#fafff4','#788679',2.8));
    const key=new THREE.DirectionalLight('#fff4dd',3.3);key.position.set(-1,2,-2);this.scene.add(key);
    const rim=new THREE.DirectionalLight('#b2ddd0',2);rim.position.set(1,.5,1);this.scene.add(rim);
    this.camera=new THREE.PerspectiveCamera(36,host.clientWidth/host.clientHeight,.005,5);
    this.controls=new OrbitControls(this.camera,this.renderer.domElement);
    this.controls.target.set(0,-.015,.015);this.controls.enableDamping=true;this.controls.enablePan=false;
    this.controls.minDistance=.28;this.controls.maxDistance=1.2;
    this.root=new THREE.Group();this.scene.add(this.root);
    const skin=new THREE.MeshStandardMaterial({color:'#c6b99f',roughness:.72});
    const socket=new THREE.MeshStandardMaterial({color:'#8e8877',roughness:.85});
    const white=new THREE.MeshStandardMaterial({color:'#fbfcf1',roughness:.3});
    const iris=new THREE.MeshStandardMaterial({color:'#467b72',roughness:.45});
    const pupil=new THREE.MeshStandardMaterial({color:'#112a28',roughness:.2});
    const highlight=new THREE.MeshBasicMaterial({color:'#fffef6'});
    const sphere=(parent,position,scale,material)=>{
      const mesh=new THREE.Mesh(new THREE.SphereGeometry(1,40,28),material);
      mesh.position.set(...position);mesh.scale.set(...scale);parent.add(mesh);return mesh;
    };
    sphere(this.root,[0,.002,.061],[.075,.1,.077],skin);
    sphere(this.root,[0,-.055,.057],[.057,.056,.062],skin);
    sphere(this.root,[0,-.012,-.014],[.012,.022,.02],skin);
    for(const sign of [-1,1]) {
      sphere(this.root,[sign*.076,-.004,.057],[.013,.026,.018],skin);
      sphere(this.root,[sign*.081,-.004,.048],[.005,.015,.007],socket);
      sphere(this.root,[sign*.032,.023,-.003],[.023,.004,.008],socket);
    }
    this.eyePivots=[-1,1].map(sign=>{
      const pivot=new THREE.Group();pivot.position.set(sign*.032,0,0);this.root.add(pivot);
      sphere(pivot,[0,0,0],[.017,.014,.017],white);
      sphere(pivot,[0,0,-.0156],[.008,.008,.0027],iris);
      sphere(pivot,[0,0,-.018],[.0038,.0038,.001],pupil);
      sphere(pivot,[-.002,.003,-.019],[.0014,.0014,.001],highlight);
      return pivot;
    });
    const mouthPoints=Array.from({length:25},(_,i)=>{
      const x=(i/24-.5)*.035;return new THREE.Vector3(x,-.044+Math.abs(x)*.1,-.008);
    });
    const mouth=new THREE.Line(new THREE.BufferGeometry().setFromPoints(mouthPoints),new THREE.LineBasicMaterial({color:'#817365'}));this.root.add(mouth);
    const neck=new THREE.Mesh(new THREE.CylinderGeometry(.025,.033,.065,32),skin);neck.position.set(0,-.112,.06);this.scene.add(neck);
    sphere(this.scene,[0,-.183,.066],[.15,.065,.068],new THREE.MeshStandardMaterial({color:'#6e857b',roughness:1}));
    const base=new THREE.Mesh(new THREE.CylinderGeometry(.17,.17,.012,48),new THREE.MeshStandardMaterial({color:'#c4cebd',roughness:1}));base.position.set(0,-.24,.06);this.scene.add(base);
    const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(new Float32Array(18),3));
    geometry.setAttribute('color',new THREE.Float32BufferAttribute([.35,.75,.66,.35,.75,.66,.35,.75,.66,.35,.75,.66,.82,.58,.29,.82,.58,.29],3));
    this.rays=new THREE.LineSegments(geometry,new THREE.LineBasicMaterial({vertexColors:true,transparent:true,opacity:.7}));this.rays.frustumCulled=false;this.scene.add(this.rays);
    this.setView('front');
    this.resize=new ResizeObserver(()=>{
      const width=host.clientWidth,height=host.clientHeight;
      if(!width||!height)return;
      this.renderer.setSize(width,height);this.camera.aspect=width/height;this.camera.updateProjectionMatrix();
    });this.resize.observe(host);
  }
  setView(view) {
    const views={front:[-.19,.105,-.55],behind:[.16,.11,.57],side:[.55,.09,-.09]};
    this.camera.position.set(...(views[view]??views.front));this.controls.update();
  }
  update(pose) {
    this.root.quaternion.copy(pose.headQuaternion);
    this.eyePivots.forEach((eye,i)=>eye.quaternion.copy(pose.eyes[i].quaternion));
    const values=[];
    pose.eyes.forEach(eye=>{
      const end=eye.origin.clone().addScaledVector(eye.direction,.23);
      values.push(...eye.origin.toArray(),...end.toArray());
    });
    const headForward=new THREE.Vector3(0,0,-.20).applyQuaternion(pose.headQuaternion);
    values.push(0,0,0,...headForward.toArray());
    this.rays.geometry.attributes.position.array.set(values);this.rays.geometry.attributes.position.needsUpdate=true;
    this.controls.update();this.renderer.render(this.scene,this.camera);
  }
}
