"""Complementary metrics with explicit undefined cases; no one-score realism claim."""
import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.stats import rankdata


def density(points,width,height,durations=None):
    grid=np.zeros((height,width),float)
    for i,(x,y) in enumerate(points):grid[int(y),int(x)]+=1 if durations is None else durations[i]
    return gaussian_filter(grid,max(1,width*.025))


def nss(saliency,points):
    sd=float(np.std(saliency))
    if not points or sd<1e-12:return None
    z=(saliency-np.mean(saliency))/sd
    return float(np.mean([z[int(y),int(x)] for x,y in points]))


def auc_pixels(saliency,points):
    """Comparable fixation-vs-nonfixation pixel AUC; tie-correct and deterministic.
    Not labeled AUC-Judd because this uses all pixels as deterministic negatives.
    """
    mask=np.zeros(saliency.shape,bool)
    for x,y in points:mask[int(y),int(x)]=True
    pos=saliency[mask];neg=saliency[~mask]
    if not len(pos) or not len(neg):return None
    ranks=rankdata(np.r_[pos,neg]);return float((ranks[:len(pos)].sum()-len(pos)*(len(pos)+1)/2)/(len(pos)*len(neg)))


def sequence_dtw(a,b,width,height):
    """Custom length-normalized spatial DTW; not MultiMatch or ScanMatch."""
    if not a or not b:return None
    diagonal=np.hypot(width,height);dp=np.full(len(b)+1,np.inf);dp[0]=0
    for p in a:
        nxt=np.full(len(b)+1,np.inf)
        for j,q in enumerate(b,1):nxt[j]=np.linalg.norm(np.array(p)-q)/diagonal+min(nxt[j-1],dp[j],dp[j-1])
        dp=nxt
    return float(dp[-1]/(len(a)+len(b)))


def refixation_rate(points,width):
    if len(points)<2:return None
    repeated=sum(any(np.linalg.norm(np.array(p)-q)<width*.04 for q in points[:max(0,i-1)]) for i,p in enumerate(points))
    return float(repeated/(len(points)-1))


def compare(model,record):
    start=1 if record['initial_fixation_included'] else 0;mf=model['fixations'][1:];hf=record['fixations'][start:];w,h=model['width'],model['height']
    mp=[(f['x_px'],f['y_px']) for f in mf];hp=[(f['x'],f['y']) for f in hf]
    a=density(mp,w,h,[f['duration_ms'] for f in mf]);b=density(hp,w,h,[f['duration_ms'] for f in hf]);sa,sb=float(a.std()),float(b.std())
    amplitude=lambda p:float(np.mean(np.linalg.norm(np.diff(np.array(p),axis=0),axis=1))) if len(p)>1 else None
    return dict(nss=nss(a,hp),auc_fixation_vs_nonfixation_pixels=auc_pixels(a,hp),heatmap_correlation=float(np.corrcoef(a.ravel(),b.ravel())[0,1]) if min(sa,sb)>1e-12 else None,spatial_dtw=sequence_dtw(mp,hp,w,h),model_refixation_rate=refixation_rate(mp,w),human_refixation_rate=refixation_rate(hp,w),model_fixation_count=len(mp),human_fixation_count=len(hp),model_mean_duration_ms=float(np.mean([f['duration_ms'] for f in mf])) if mf else None,human_mean_duration_ms=float(np.mean([f['duration_ms'] for f in hf])) if hf else None,model_mean_amplitude_px=amplitude(mp),human_mean_amplitude_px=amplitude(hp))
