"""One-to-one gated spatial/category/appearance matching; no detector IDs."""
import numpy as np
from scipy.optimize import linear_sum_assignment


def associate(memories: list, detections: list, diagonal: float, gate: float=.15) -> list[tuple[int,int]]:
    if not memories or not detections: return []
    cost=np.full((len(memories),len(detections)),1e6)
    for i,m in enumerate(memories):
        for j,d in enumerate(detections):
            center=np.array([(d.bbox[0]+d.bbox[2])/2,(d.bbox[1]+d.bbox[3])/2])
            dist=np.linalg.norm(np.array(m.centroid)-center)/diagonal
            if dist > gate: continue
            overlap=sum(min(v,d.probabilities.get(k,0)) for k,v in m.probabilities.items())
            appearance=np.linalg.norm(np.array(m.appearance)-d.appearance)/np.sqrt(3)
            cost[i,j]=.6*dist/gate+.2*(1-overlap)+.2*appearance
    rows,cols=linear_sum_assignment(cost)
    return [(int(i),int(j)) for i,j in zip(rows,cols) if cost[i,j]<.95]
