import { rayForPixel } from './photo-geometry.js';
import { insideViewingCone } from './visual-field.js';
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const angle=(a,b)=>Math.acos(clamp(a.x*b.x+a.y*b.y+a.z*b.z,-1,1))*180/Math.PI;

/** Finite exploratory attention policy; not a fitted EyeSyn/ScanDy model. */
export class AttentionSearch {
  constructor(seed=17){this.initialSeed=seed;this.randomSeed=seed;this.reset();}
  reset(){
    this.state='idle';this.phase='idle';this.candidates=[];this.visited=new Set();this.skipped=new Set();
    this.history=[];this.current=null;this.target=null;this.elapsed=0;this.targetTime=0;this.wait=0;this.dwell=0;this.subfixation=0;this.reason='Click a starting point after analysis.';
  }
  random(){this.randomSeed=(Math.imul(1664525,this.randomSeed)+1013904223)>>>0;return this.randomSeed/4294967296;}
  start(candidates,seed,config={}){
    this.reset();this.randomSeed=this.initialSeed;
    this.config={aspect:1,vfov:60,hfov:40,efov:28,...config};
    this.candidates=candidates.map(c=>({...c,ray:rayForPixel(c.u,c.v,this.config.aspect,this.config.vfov)}));
    this.state='running';this.phase='saccade';
    const hits=this.candidates.filter(c=>seed.u>=c.box[0]&&seed.u<=c.box[2]&&seed.v>=c.box[1]&&seed.v<=c.box[3]);
    hits.sort((a,b)=>(a.box[2]-a.box[0])*(a.box[3]-a.box[1])-(b.box[2]-b.box[0])*(b.box[3]-b.box[1]));
    this.current=hits[0]??null;
    this.target={...seed,label:this.current?.label??'Starting point',id:this.current?.id??'start'};
    this.reason='Orienting to the clicked starting point.';
    return this.event();
  }
  event(){return {type:'target',target:{...this.target}};}
  pause(){if(this.state==='running')this.state='paused';}
  resume(){if(this.state==='paused')this.state='running';}
  stop(){if(['running','paused'].includes(this.state)){this.state='stopped';this.reason='Search stopped. The scanpath is retained.';}}
  duration(){
    if(!this.current)return .5;
    const box=this.current.box,area=(box[2]-box[0])*(box[3]-box[1]);
    // More inspection time for larger/less certain candidates, bounded for exploration.
    return clamp(.42+Math.sqrt(area)*.65+(1-(this.current.confidence??.5))*.3+this.random()*.18,.45,1.1);
  }
  tick(dt,pose){
    if(this.state!=='running')return null;
    dt=clamp(Number.isFinite(dt)?dt:0,0,.1);this.elapsed+=dt;this.targetTime+=dt;
    // A noisy or repeatedly interrupted arrival must not stall exploration forever.
    if(this.targetTime>6){
      if(this.current)this.skipped.add(this.current.id);
      return this.next(pose.gazeDirection);
    }
    const arrived=pose.error<.65&&!pose.limited;
    if(!arrived){
      this.wait+=dt;
      if(this.wait>2.5){
        if(this.current)this.skipped.add(this.current.id);
        return this.next(pose.gazeDirection);
      }
      this.phase='saccade';return null;
    }
    if(this.phase==='saccade'){
      this.phase='fixation';this.dwell=0;this.fixationDuration=this.duration();
      this.reason=`Fixating ${this.target.label.toLowerCase()} · ${Math.round(this.fixationDuration*1000)} ms.`;
    }
    this.wait=0;this.dwell+=dt;
    if(this.dwell<this.fixationDuration)return null;
    this.history.push({...this.target,duration:this.dwell,time:this.elapsed});
    if(this.current&&this.subfixation===0&&this.needsSecondFixation(this.current)){
      this.subfixation=1;this.phase='saccade';this.dwell=0;this.targetTime=0;
      const box=this.current.box,sign=this.random()>.5?1:-1;
      this.target={u:clamp(this.current.u+sign*(box[2]-box[0])*.17,box[0],box[2]),
        v:clamp(this.current.v-(box[3]-box[1])*.1,box[1],box[3]),label:this.current.label,id:this.current.id};
      this.reason=`A second inspection within ${this.current.label.toLowerCase()}.`;
      return this.event();
    }
    if(this.current)this.visited.add(this.current.id);
    return this.next(pose.gazeDirection);
  }
  needsSecondFixation(candidate){
    if(candidate.kind!=='object')return false;
    const box=candidate.box;
    const left=rayForPixel(box[0],candidate.v,this.config.aspect,this.config.vfov);
    const right=rayForPixel(box[2],candidate.v,this.config.aspect,this.config.vfov);
    return angle(left,right)>10||(candidate.confidence??1)<.75;
  }
  next(gaze){
    const remaining=this.candidates.filter(c=>!this.visited.has(c.id)&&!this.skipped.has(c.id));
    if(!remaining.length){
      this.state='complete';this.phase='complete';
      this.reason=!this.candidates.length?'No attention candidates found; only the starting fixation was inspected.':this.skipped.size?`Finished reachable candidates; ${this.skipped.size} could not be fixated.`:'All candidate regions inspected. This does not imply every real object was recognized.';
      return {type:'complete'};
    }
    const scored=remaining.map(c=>{
      const distance=angle(c.ray,gaze);
      const visible=insideViewingCone(c.ray,gaze,this.config.hfov,this.config.efov);
      const recent=this.history.slice(-4).reduce((penalty,p)=>{
        const r=rayForPixel(p.u,p.v,this.config.aspect,this.config.vfov);
        return Math.max(penalty,Math.exp(-angle(c.ray,r)/5));
      },0);
      const weight=(.3+c.salience)*(c.kind==='object'?1.35:1)*(visible?1.7:.65)
        *(.25+Math.exp(-distance/28))*(1-.55*recent);
      return {candidate:c,weight,visible};
    });
    // Seeded weighted sampling gives reproducible variability, rather than a fixed list order.
    let pick=this.random()*scored.reduce((sum,c)=>sum+c.weight,0),chosen=scored.at(-1);
    for(const c of scored){pick-=c.weight;if(pick<=0){chosen=c;break;}}
    this.current=chosen.candidate;this.subfixation=0;this.phase='saccade';this.wait=this.dwell=this.targetTime=0;
    this.target={u:this.current.u,v:this.current.v,label:this.current.label,id:this.current.id};
    this.reason=`Attention shifts to ${this.current.label.toLowerCase()} · ${chosen.visible?'within current eyesight':'beyond current eyesight; head recruitment may be needed'}.`;
    return this.event();
  }
  summary(){return {state:this.state,phase:this.phase,visited:this.visited.size,skipped:this.skipped.size,total:this.candidates.length,fixations:this.history.length,
    target:this.target?.label??'—',reason:this.reason};}
}
