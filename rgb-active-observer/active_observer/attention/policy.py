"""Score deterministically, then sample separately. No human data enters policy."""
import numpy as np
from scipy.special import softmax


def feature_at(obs,x: float,y: float) -> float:
    h,w=obs.rgb.shape[:2];x=int(np.clip(x,0,w-1));y=int(np.clip(y,0,h-1));r=max(2,int(w*.025))
    crop=obs.rgb[max(0,y-r):min(h,y+r+1),max(0,x-r):min(w,x+r+1)].astype(float)/255
    contrast=float(np.std(crop,axis=(0,1)).mean());global_color=obs.rgb.mean(axis=(0,1))/255
    return float(np.clip(contrast*3+np.linalg.norm(crop.mean(axis=(0,1))-global_color)/np.sqrt(3),0,1))


def score(world,obs,target: str,config) -> list[dict]:
    candidates=[];diag=np.hypot(world.width,world.height)
    for m in (world.objects if config.policy not in {'center','random_center'} else []):
        candidates.append(dict(id=m.id,kind="object",x=m.centroid[0],y=m.centroid[1],confidence=m.confidence,probabilities=m.probabilities,salience=m.salience,novelty=m.novelty,history=m.ior,relative_depth=m.relative_depth,depth_uncertainty=m.depth_uncertainty))
    if config.exploration_enabled or config.policy in {'center','random_center'}:
        for g in world.grid:
            history=0 if g['last_seen'] is None else np.exp(-(world.time-g['last_seen'])/1200)
            candidates.append(dict(id=g['id'],kind="region",x=g['x'],y=g['y'],confidence=g['coverage'],probabilities={},salience=feature_at(obs,g['x'],g['y']),novelty=1-g['coverage'],history=float(history),relative_depth=None,depth_uncertainty=1.))
    if not candidates:
        candidates=[dict(id="standby",kind="region",x=obs.gaze[0],y=obs.gaze[1],confidence=0.,probabilities={},salience=0.,novelty=1.,history=0.,relative_depth=None,depth_uncertainty=1.)]
    for c in candidates:
        uncertainty=1-c['confidence'] if config.uncertainty_enabled else .5
        context=0.
        for m in world.objects:
            known=max(m.probabilities,key=m.probabilities.get)
            relation=config.context_priors.get(known,{}).get(target,0) if target else 0
            context=max(context,relation*m.confidence*np.exp(-np.hypot(c['x']-m.centroid[0],c['y']-m.centroid[1])/(.2*diag)))
        terms=dict(salience=c['salience'],task=c['probabilities'].get(target,0)*c['confidence'] if target else 0.,context=float(context),novelty=c['novelty'] if config.novelty_enabled else 0.,info=float(uncertainty*c['novelty']),move=float(np.hypot(c['x']-obs.gaze[0],c['y']-obs.gaze[1])/diag),history=c['history'] if config.history_enabled else 0.)
        if config.depth_enabled and config.uncertainty_enabled and c['relative_depth'] is not None:
            # Depth dispersion is an information-seeking hypothesis, not physical truth.
            terms['info']=float(np.clip(.8*terms['info']+.2*c['depth_uncertainty'],0,1))
        if config.policy in {'center','random_center'}:
            center=np.hypot(c['x']-world.width/2,c['y']-world.height/2)/diag
            utility=-center**2/(2*.22**2)
            if config.policy=='random_center': utility*=.35
        elif config.policy in {'salience','salience_ior'}: utility=terms['salience']-(.6*terms['history'] if config.policy=='salience_ior' else 0)
        else: utility=sum(config.weights[k]*v*(-1 if k in {'move','history'} else 1) for k,v in terms.items())
        # Bounded hysteresis: a small near-gaze preference, never a hard lock.
        persistence=.08*float(np.hypot(c['x']-obs.gaze[0],c['y']-obs.gaze[1])<obs.radius_px/2) if config.policy=='full' else 0.
        contributions={k:float(config.weights[k]*v*(-1 if k in {'move','history'} else 1)) for k,v in terms.items()}
        if config.policy in {'center','random_center'}: contributions={'center_prior':float(utility)}
        elif config.policy in {'salience','salience_ior'}: contributions={'salience':terms['salience'],'history':-.6*terms['history'] if config.policy=='salience_ior' else 0.}
        contributions['persistence']=persistence
        c.update(terms=terms,utility=float(utility+persistence),utility_components=contributions,persistence=persistence,uncertainty=uncertainty)
    probabilities=softmax(np.array([c['utility'] for c in candidates])/config.temperature)
    for c,p in zip(candidates,probabilities): c['probability']=float(p)
    return candidates


def choose(candidates: list[dict],rng: np.random.Generator) -> dict:
    return candidates[int(rng.choice(len(candidates),p=[c['probability'] for c in candidates]))]
