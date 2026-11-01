"""CLI entrypoints; outputs are explicitly reproducible JSON and headless PNG."""
import argparse,json
from pathlib import Path
from .config import Config
from .io.image import load_image
from .simulation.runner import run
from .viz.dashboard import dashboard
from .viz.html import write_html
from .perception.depth import ConstantDepth,PrecomputedDepth,CachedDepth,TransformersDepth
from .perception.objects import FovealTransformersObjects
from .evaluation.batch import evaluate
from .io.human import convert_coco


def main():
    p=argparse.ArgumentParser(prog='active-observer');sub=p.add_subparsers(dest='command',required=True)
    one=sub.add_parser('run-one');one.add_argument('image');one.add_argument('--config');one.add_argument('--out',default='outputs/run');one.add_argument('--target',default='');one.add_argument('--seed',type=int);one.add_argument('--start',nargs=2,type=float);one.add_argument('--depth',help='constant or an aligned .npy/.npz relative-depth file');one.add_argument('--depth-kind',choices=['inverse_depth','relative_range'],default='inverse_depth');one.add_argument('--depth-checkpoint');one.add_argument('--detector-checkpoint');one.add_argument('--revision',default='main');one.add_argument('--allow-model-download',action='store_true')
    vis=sub.add_parser('visualize');vis.add_argument('image');vis.add_argument('result');vis.add_argument('--out',default='outputs/dashboard.png');vis.add_argument('--step',type=int)
    batch=sub.add_parser('run-batch');batch.add_argument('images',nargs='+');batch.add_argument('--config');batch.add_argument('--out',default='outputs/batch')
    ev=sub.add_parser('evaluate');ev.add_argument('manifest');ev.add_argument('--config');ev.add_argument('--out',default='outputs/evaluation');ev.add_argument('--split',choices=['validation','test'],default='test');ev.add_argument('--seeds',nargs='+',type=int,default=[11,23,37])
    cc=sub.add_parser('import-coco');cc.add_argument('raw');cc.add_argument('image_manifest');cc.add_argument('out')
    a=p.parse_args()
    if a.command=='import-coco':convert_coco(a.raw,a.image_manifest,a.out);return
    if a.command=='evaluate':
        r=evaluate(a.manifest,Config.load(a.config),a.out,split=a.split,seeds=a.seeds);print(json.dumps({k:r[k] for k in ['status','images','participants','depth_tested']}));return
    if a.command=='run-batch':
        cfg=Config.load(a.config);root=Path(a.out);root.mkdir(parents=True,exist_ok=True)
        for name in a.images:
            im=load_image(name);r=run(im,cfg,image_id=Path(name).stem);folder=root/Path(name).stem
            if folder.exists():raise ValueError(f'Batch output collision: {folder}')
            folder.mkdir();(folder/'run.json').write_text(json.dumps(r,allow_nan=False));dashboard(im,r,folder/'dashboard.png');write_html(im,r,folder/'inspector.html')
        return
    image=load_image(a.image)
    if a.command=='run-one':
        cfg=Config.load(a.config)
        if a.seed is not None: cfg.seed=a.seed
        provider=ConstantDepth() if a.depth=='constant' else PrecomputedDepth(a.depth,kind=a.depth_kind) if a.depth else None
        if a.depth and a.depth_checkpoint: raise ValueError('Choose precomputed/dummy depth OR pretrained checkpoint')
        if a.depth_checkpoint: provider=CachedDepth(TransformersDepth(a.depth_checkpoint,revision=a.revision,allow_download=a.allow_model_download,output_kind=a.depth_kind),'.cache/depth',a.depth_checkpoint+'@'+a.revision+':'+a.depth_kind)
        detector=FovealTransformersObjects(a.detector_checkpoint,revision=a.revision,allow_download=a.allow_model_download) if a.detector_checkpoint else None
        result=run(image,cfg,depth_provider=provider,object_provider=detector,image_id=Path(a.image).stem,target=a.target,start=a.start);out=Path(a.out);out.mkdir(parents=True,exist_ok=True);(out/'run.json').write_text(json.dumps(result,indent=2,allow_nan=False));dashboard(image,result,out/'dashboard.png');write_html(image,result,out/'inspector.html');print(json.dumps(dict(result=str(out/'run.json'),dashboard=str(out/'dashboard.png'),fixations=len(result['fixations']),reason=result['stop_reason'])))
    else: dashboard(image,json.loads(Path(a.result).read_text()),a.out,a.step)

if __name__=='__main__': main()
