"""Held-out-image evaluation, explicit baselines, per-image/participant summaries."""
from dataclasses import replace
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
from active_observer.config import Config
from active_observer.io.image import load_image
from active_observer.io.human import load_manifest
from active_observer.perception.depth import PrecomputedDepth
from active_observer.simulation.runner import run
from .metrics import compare

VARIANTS={"full":{},"random_center":{"policy":"random_center"},"center":{"policy":"center"},"salience":{"policy":"salience"},"salience_ior":{"policy":"salience_ior"},"without_depth":{"depth_enabled":False},"without_memory":{"memory_enabled":False},"without_uncertainty":{"uncertainty_enabled":False},"without_novelty":{"novelty_enabled":False},"without_history":{"history_enabled":False},"without_exploration":{"exploration_enabled":False}}


def predict(record: dict,config: Config) -> dict:
    """Only the declared initial fixation may enter prediction; never future fixations."""
    start=(record['fixations'][0]['x'],record['fixations'][0]['y']) if record['initial_fixation_included'] else None
    provider=PrecomputedDepth(record['depth_path'],kind=record.get('depth_kind','inverse_depth')) if record.get('depth_path') and config.depth_enabled else None
    return run(load_image(record['image_path']),config,image_id=record['image_id'],target=record.get('task',''),start=start,depth_provider=provider)


def evaluate(manifest: str,config: Config,out: str,*,split: str='test',seeds=(11,23,37),ablations: bool=True) -> dict:
    dataset=load_manifest(manifest);records=[r for r in dataset['records'] if r['split']==split]
    if not records:raise ValueError(f"No records in held-out split {split}")
    if split=='train':raise ValueError("evaluate refuses training-split claims; use validation or test")
    out=Path(out);out.mkdir(parents=True,exist_ok=True);rows=[];prediction_hashes=[]
    variants=VARIANTS if ablations else {'full':{}}
    for name,changes in variants.items():
        for rec in records:
            for seed in seeds:
                cfg=replace(config,seed=int(seed),**changes);model=predict(rec,cfg)
                digest=hashlib.sha256(json.dumps(model,sort_keys=True,allow_nan=False).encode()).hexdigest();prediction_hashes.append(dict(variant=name,image_id=rec['image_id'],participant=rec['participant'],seed=seed,sha256=digest))
                rows.append(dict(variant=name,image_id=rec['image_id'],participant=rec['participant'],seed=seed,**compare(model,rec)))
    frame=pd.DataFrame(rows);frame.to_csv(out/'trials.csv',index=False, encoding='utf-8')
    metrics=[k for k in frame.select_dtypes(include='number').columns if k!='seed']
    # Repeated model seeds are averaged before image- and participant-level summaries.
    cells=frame.groupby(['variant','image_id','participant'])[metrics].mean();image_means=cells.groupby(['variant','image_id']).mean();participant_means=cells.groupby(['variant','participant']).mean()
    summary=image_means.groupby('variant').mean();summary.to_csv(out/'summary.csv', encoding='utf-8');image_means.to_csv(out/'by-image.csv', encoding='utf-8');participant_means.to_csv(out/'by-participant.csv', encoding='utf-8')
    depth_supplied=any(r.get('depth_path') for r in records)
    report=dict(status='Pipeline verification only: synthetic reference scanpaths, not empirical human results' if dataset['metadata'].get('synthetic',False) else 'Held-out evaluation of user-supplied records; inspect dataset provenance',dataset=dataset['metadata'],split=split,images=len({r['image_id'] for r in records}),participants=len({r['participant'] for r in records}),trials=len(records),seeds=list(seeds),variants=list(variants),depth_tested=depth_supplied,depth_note='No supplied depth: full and without_depth are identical by construction' if not depth_supplied else 'Relative-depth hypothesis; behavioral agreement does not establish physical accuracy',aggregation='Seeds averaged within image/participant; summary weights images equally. Participant summaries separate. No significance claims from seed repetitions.',metrics={'NSS':'higher better; undefined for constant maps','AUC':'deterministic all nonfixated pixels as negatives; not branded AUC-Judd','spatial_DTW':'custom, lower better, not MultiMatch','amplitude':'pixels; angular amplitudes require calibrated display geometry'},summary=json.loads(summary.to_json(orient='index')),prediction_hashes=prediction_hashes)
    (out/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False), encoding='utf-8');return report
