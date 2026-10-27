/** Candidate generation is class-agnostic. Contrast regions have no semantic label. */
export function buildAttentionCandidates(image, objects, includeRegions=true) {
  const candidates=objects.slice(0,20).map((object,i)=>({
    id:`object-${i}`,label:object.label,kind:'object',box:[...object.box],
    u:(object.box[0]+object.box[2])/2,v:(object.box[1]+object.box[3])/2,
    confidence:object.confidence,salience:Math.max(.2,object.confidence),
  }));
  if(!includeRegions)return candidates;
  const width=40,height=Math.max(8,Math.round(40*image.height/image.width));
  const luma=[],color=[];
  for(let y=0;y<height;y++)for(let x=0;x<width;x++){
    const px=Math.min(image.width-1,Math.floor((x+.5)*image.width/width));
    const py=Math.min(image.height-1,Math.floor((y+.5)*image.height/height));
    const index=(py*image.width+px)*4;
    const r=image.data[index]/255,g=image.data[index+1]/255,b=image.data[index+2]/255;
    luma.push(.2126*r+.7152*g+.0722*b);color.push(Math.max(r,g,b)-Math.min(r,g,b));
  }
  const peaks=[];
  for(let y=2;y<height-2;y++)for(let x=2;x<width-2;x++){
    const i=y*width+x;
    const neighbors=[luma[i-2],luma[i+2],luma[i-width*2],luma[i+width*2]];
    const contrast=neighbors.reduce((sum,p)=>sum+Math.abs(luma[i]-p),0)/4;
    const score=contrast*(1+.35*color[i]);
    const u=(x+.5)/width,v=(y+.5)/height;
    if(score<.07||objects.some(o=>u>=o.box[0]&&u<=o.box[2]&&v>=o.box[1]&&v<=o.box[3]))continue;
    peaks.push({u,v,score});
  }
  peaks.sort((a,b)=>b.score-a.score);
  const selected=[];
  for(const peak of peaks){
    if(selected.length>=6)break;
    // Suppress nearby peaks so textured foliage cannot consume the whole search.
    if(selected.some(p=>Math.hypot((p.u-peak.u)*image.width,(p.v-peak.v)*image.height)<Math.min(image.width,image.height)*.22))continue;
    selected.push(peak);
    const rx=.085,ry=.085*image.width/image.height;
    candidates.push({id:`region-${selected.length}`,label:`Visual region ${selected.length}`,kind:'region',
      u:peak.u,v:peak.v,box:[Math.max(0,peak.u-rx),Math.max(0,peak.v-ry),Math.min(1,peak.u+rx),Math.min(1,peak.v+ry)],
      confidence:null,salience:Math.min(1,peak.score*2.5)});
  }
  return candidates;
}
