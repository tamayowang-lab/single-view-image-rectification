"""Build the Porto demonstration from actual Python runs, never synthetic trajectories.

Usage: python scripts/build_photo_preview.py INPUT_PHOTO OUTPUT_DIRECTORY
No object/depth outputs from another model are used. The photo may be shared.
"""
from pathlib import Path
import argparse,json,hashlib,shutil,sys
import cv2,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from active_observer.config import Config
from active_observer.io.image import load_image
from active_observer.simulation.runner import run
from active_observer.perception.foveation import observe
from active_observer.viz.dashboard import dashboard


def build(image_path: str,out_path: str):
    out=Path(out_path);(out/'data').mkdir(parents=True,exist_ok=True);(out/'frames').mkdir(exist_ok=True)
    image=load_image(image_path);scale=min(1.,640/image.shape[1]);image=cv2.resize(image,(round(image.shape[1]*scale),round(image.shape[0]*scale)),interpolation=cv2.INTER_AREA)
    h,w=image.shape[:2];cv2.imwrite(str(out/'scene.png'),cv2.cvtColor(image,cv2.COLOR_RGB2BGR))
    cfg=Config(seed=42,max_fixations=20,time_budget_ms=7500);runs=[];radius=w*cfg.central_fraction
    for row,yf in enumerate([.2,.5,.8]):
        for col,xf in enumerate([.2,.5,.8]):
            key=f'start-{row}-{col}';start=(xf*(w-1),yf*(h-1));result=run(image,cfg,image_id='porto-riverside-rgb',start=start)
            raw=json.dumps(result,separators=(',',':'),allow_nan=False);(out/'data'/f'{key}.json').write_text(raw,encoding='utf-8')
            frames=[]
            for f in result['fixations']:
                obs=observe(image,(f['x_px'],f['y_px']),cfg);digest=hashlib.sha256(obs.rgb.tobytes()).hexdigest()[:20];path=out/'frames'/f'{digest}.jpg'
                if not path.exists():cv2.imwrite(str(path),cv2.cvtColor(obs.rgb,cv2.COLOR_RGB2BGR),[cv2.IMWRITE_JPEG_QUALITY,88])
                frames.append('frames/'+path.name)
            runs.append(dict(id=key,label=f'{row*3+col+1}',start=list(start),frames=frames,fixations=len(result['fixations']),duration_ms=result['duration_ms'],object_count=len(result['fixations'][-1]['memory']['objects']),data='data/'+key+'.json'))
            if row==col==1:dashboard(image,result,out/'dashboard.png')
            print(key,len(result['fixations']),flush=True)
    manifest=dict(title='Porto riverside',width=w,height=h,radius_px=radius,model='RGB Active Observer V1',config=cfg.to_dict(),runs=runs,default_run='start-1-1',data_kind='Real-photograph model demonstration, not human eye tracking',execution='Nine independently generated Python runs; selecting a start replays its prepared run. There is no live Python inference in this static viewer.',perception='Classical color proto-objects from foveated RGB; labels are not semantic object recognition.',depth='No depth supplied; no estimated or synthetic depth is invented.',source=dict(name='Porto panorama perspective photograph, also used as the Gaze Lab input',repository='https://github.com/David-Ef/salient360Toolbox',filename='1_PortoRiverside.png',note='Repository-level MIT license; stimulus-specific license not separately documented. The demonstration crop is not matched to human panorama-viewing trials.'),independence='Only the RGB photograph is shared. Observer code, trajectories and scores come from the new Python implementation.')
    root=Path(__file__).resolve().parents[1]
    manifest['code_sha256']={str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in (root/'active_observer').rglob('*.py')}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    for name in ['index.html','style.css','app.js']:
        source=Path(__file__).resolve().parents[1]/'preview'/name
        if source.exists():shutil.copy2(source,out/name)
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('image');p.add_argument('out');a=p.parse_args();build(a.image,a.out)
