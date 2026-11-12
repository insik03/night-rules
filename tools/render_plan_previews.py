"""Offline raster previews of our own simple SVG diagrams (no browser needed)."""
from pathlib import Path
import re, math, json
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Art/EnvironmentConcepts/unified-v15'

def render(src,dst,view=(0,0,4900,1650),width=2450):
    x0,y0,w,h=view;s=width/w
    im=Image.new('RGB',(width,round(h*s)),'#192927');d=ImageDraw.Draw(im)
    def xy(x,y):return ((float(x)-x0)*s,(float(y)-y0)*s)
    def stroke(points,col,weight,dash=False):
        if not col or col=='none':return
        points=[xy(*p) for p in points];weight=max(1,round(float(weight)*s))
        if not dash:d.line(points,fill=col,width=weight);return
        for a,b in zip(points,points[1:]):
            dist=math.dist(a,b)
            if not dist:continue
            for k in range(0,math.ceil(dist),max(3,round(15*s))):
                t=k/dist;u=min(1,(k+9*s)/dist)
                d.line([(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t),(a[0]+(b[0]-a[0])*u,a[1]+(b[1]-a[1])*u)],fill=col,width=weight)
    def draw(e):
        tag=e.tag.split('}')[-1];a=e.attrib
        if tag in ('defs','title'):return
        fill=a.get('fill');fill=None if fill=='none' else fill
        outline=a.get('stroke');weight=max(1,round(float(a.get('stroke-width',1))*s))
        if tag=='rect':
            x=float(a.get('x',0));y=float(a.get('y',0));ww=float(a['width']);hh=float(a['height'])
            d.rectangle([xy(x,y),xy(x+ww,y+hh)],fill=fill)
            stroke([(x,y),(x+ww,y),(x+ww,y+hh),(x,y+hh),(x,y)],outline, a.get('stroke-width',1),'stroke-dasharray' in a)
        elif tag=='line':stroke([(a['x1'],a['y1']),(a['x2'],a['y2'])],outline,a.get('stroke-width',1),'stroke-dasharray' in a)
        elif tag=='circle':
            x=float(a['cx']);y=float(a['cy']);r=float(a['r']);d.ellipse([xy(x-r,y-r),xy(x+r,y+r)],fill=fill,outline=outline,width=weight)
        elif tag=='text':
            font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',max(5,round(float(a.get('font-size',30))*s)))
            d.text(xy(a['x'],a['y']),e.text or '',font=font,fill=fill or '#fff',anchor='lm' if a.get('text-anchor')=='start' else 'mm')
        elif tag=='polyline':
            pts=[tuple(map(float,p.split(','))) for p in a['points'].split()]
            stroke(pts,outline,a.get('stroke-width',1),'stroke-dasharray' in a)
        elif tag=='path':
            # Only the M L Q Z door sweeps emitted by create_unified_furnished_plan.
            v=re.findall(r'[MLQZ]|-?\d+(?:\.\d+)?',a['d']);pts=[];i=0
            while i<len(v):
                cmd=v[i];i+=1
                if cmd in ('M','L'):pts.append((float(v[i]),float(v[i+1])));i+=2
                elif cmd=='Q':
                    c=(float(v[i]),float(v[i+1]));b=(float(v[i+2]),float(v[i+3]));i+=4;aa=pts[-1]
                    pts += [((1-t)**2*aa[0]+2*(1-t)*t*c[0]+t*t*b[0],(1-t)**2*aa[1]+2*(1-t)*t*c[1]+t*t*b[1]) for t in [j/16 for j in range(1,17)]]
                elif cmd=='Z':pts.append(pts[0])
                else:break
            if pts:stroke(pts,outline,a.get('stroke-width',1),True)
        for child in e:draw(child)
    draw(ET.parse(src).getroot());im.save(dst)

for f in range(1,5):render(OUT/f'floor-{f}.svg',OUT/f'floor-{f}.png')
for name,view in [('office',(90,20,1040,1360)),('rooms',(965,100,780,480)),('kitchen',(1050,540,1330,800))]:
    render(OUT/'floor-1.svg',OUT/f'detail-{name}.png',view,1300)
# Older review pages remain records, with a single unambiguous current destination.
for name in ['architecture-office-v3.html','architecture-office-v5.html','architecture-reconcile-v2.html','access-renders-v11.html','architecture-built-v1.html']:
    path=ROOT/'docs'/name;source=path.read_text(encoding='utf-8')
    if 'data-unified-v15' not in source:
        banner='<p data-unified-v15 style="padding:18px;background:#25483b;color:#fff"><b>과거 검토 기록입니다.</b> 현재 구조·가구 배치·치수는 <a href="floor-plan.html?v=unified-v15" style="color:#d8eabb">통합 설계도 v15</a>를 기준으로 확인하세요.</p>'
        source=source.replace('<main>','<main>'+banner,1);path.write_text(source,encoding='utf-8')
print('4 full plans + 3 detail PNGs rendered locally; prior pages linked to canonical plan.')
