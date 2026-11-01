"""Observed/remembered/uncertain object registry and unexplored spatial grid."""
from dataclasses import dataclass,asdict
import numpy as np
from .association import associate

@dataclass
class ObjectMemory:
    id: str
    bbox: list
    probabilities: dict
    appearance: list
    centroid: list
    confidence: float
    salience: float
    last_seen: float
    visits: int=1
    familiarity: float=.1
    novelty: float=.9
    visibility: float=1.
    state: str="observed"
    relative_depth: float | None=None
    depth_uncertainty: float=1.
    xyz: list | None=None
    covariance: list | None=None
    ior: float=0.
    extent: list | None=None

    def to_dict(self): return asdict(self)

class World:
    def __init__(self,width,height,config):
        self.width=width;self.height=height;self.config=config;self.objects=[];self.counter=0;self.time=0.
        self.grid=[dict(id=f"region-{y}-{x}",x=(x+.5)*width/config.grid_columns,y=(y+.5)*height/config.grid_rows,coverage=0.,last_seen=None,visits=0) for y in range(config.grid_rows) for x in range(config.grid_columns)]

    def update(self,detections,observation,elapsed_ms: float):
        cfg=self.config;self.time+=elapsed_ms
        if not cfg.memory_enabled: self.objects=[]
        for m in self.objects:
            m.confidence*=np.exp(-elapsed_ms/cfg.memory_decay_ms);m.ior*=np.exp(-elapsed_ms/1200);m.visibility=0.;m.state="remembered" if m.confidence>.2 else "uncertain"
        pairs=associate(self.objects,detections,np.hypot(self.width,self.height));matched={j:i for i,j in pairs}
        for j,d in enumerate(detections):
            center=[(d.bbox[0]+d.bbox[2])/2,(d.bbox[1]+d.bbox[3])/2]
            central=bool(observation.central[min(self.height-1,int(center[1])),min(self.width-1,int(center[0]))])
            if j in matched:
                m=self.objects[matched[j]];old=m.confidence;gain=d.confidence/(old+d.confidence+1e-9)
                keys=set(m.probabilities)|set(d.probabilities);m.probabilities={k:(1-gain)*m.probabilities.get(k,0)+gain*d.probabilities.get(k,0) for k in keys}
                m.centroid=((1-gain)*np.array(m.centroid)+gain*np.array(center)).tolist();m.bbox=d.bbox;m.appearance=d.appearance;m.confidence=min(.99,1-(1-old)*(1-d.confidence));m.visits+=int(central);m.familiarity=min(1,m.familiarity+(.15 if central else .03)*d.confidence)
            else:
                self.counter+=1;m=ObjectMemory(f"object-{self.counter}",d.bbox,d.probabilities,d.appearance,center,d.confidence,d.salience,self.time);m.visits=int(central);self.objects.append(m)
            m.last_seen=self.time;m.visibility=d.confidence;m.state="observed";m.novelty=1-m.familiarity;m.ior=1. if central else m.ior;m.extent=[m.bbox[2]-m.bbox[0],m.bbox[3]-m.bbox[1]]
            spread=(1-m.confidence)*max(m.extent)**2;m.covariance=np.diag([spread,spread,m.depth_uncertainty]).tolist()
        # Keep a bounded registry; pruning is explicit in state metadata.
        self.objects=[m for m in self.objects if m.confidence>.02][-128:]
        for cell in self.grid:
            x,y=int(cell['x']),int(cell['y'])
            if observation.central[min(y,self.height-1),min(x,self.width-1)]:
                cell['coverage']=min(1,cell['coverage']+elapsed_ms/300);cell['last_seen']=self.time;cell['visits']+=1

    def snapshot(self): return dict(time_ms=self.time,objects=[m.to_dict() for m in self.objects],regions=[dict(c) for c in self.grid],registry_limit=128)
