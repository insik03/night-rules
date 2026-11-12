import json,math,re
from pathlib import Path
root=Path.cwd();data=root/'NightRulesPrototype/Content/Data';src=root/'NightRulesPrototype/Source/NightRulesPrototype'
d=json.loads((data/'day1.json').read_text(encoding='utf8'))['documents'];v=json.loads((data/'voices.json').read_text(encoding='utf8'))
for k,rows in v.items():
 assert [r['subtitle'] for r in rows]==[x.strip() for x in d[k].splitlines() if x.strip()][1:],k
rows=sum(len(x) for x in v.values());spoken=sum(bool(r['asset']) for x in v.values() for r in x);unique=len({r['asset'] for x in v.values() for r in x if r['asset']})
steps=json.loads((data/'demo-walk.json').read_text(encoding='utf8'))['steps']
assert all(s['kind'] in {'call','use','read','move','open','complaint_choice','complaint_written','investigation_plan','awakening','sprint','end'} for s in steps)
assert all(-850<=s['at'][1]<=80 for s in steps if s['kind']=='move')
assert all(s['at'][2] in {90,250,410} for s in steps if s['kind']=='move')
assert next(i for i,s in enumerate(steps) if s['kind']=='investigation_plan')>next(i for i,s in enumerate(steps) if s.get('evidence')=='manager_call')
walk=(src/'NRDemoWalk.cpp').read_text(encoding='utf8')
assert not re.search(r'\b(?:SetActorLocation|Use|SelectInvestigationPlan|ReplayCCTV|SetMovementMode)\s*\(',walk)
assert not re.search(r'}\s*\w+\s*,\s*\w+\s*;', (src/'NRGame.h').read_text(encoding='utf8'))
# Swept capsule footprint against architecture_collision wall rectangles. This
# supplements, and never replaces, a rebuilt engine run (meshes/hinges not modelled).
blocks={0:[],1:[]}
def wall(f,x,y,sx,sy):blocks[f].append((x-sx/2,y-sy/2,x+sx/2,y+sy/2))
def opening(f,l,r,y,x):
 a,b=x-43.5,x+43.5
 if a>l:wall(f,(l+a)/2,y,a-l,12)
 if r>b:wall(f,(b+r)/2,y,r-b,12)
for f in (0,1):
 wall(f,1700,-900,4400,16);wall(f,3900,-335,16,1130)
 if f==0:
  wall(f,-35,-690,12,420);wall(f,265,-480,330,12)
  opening(f,-35,100,-480,35);opening(f,-500,-35,-480,-267.5)
 else:
  wall(f,0,-200,280,12);wall(f,-320,-200,360,12)
  # Upper storage east/west side openings (not used by this known route).
  for x,top,bottom,dy in [(140,-200,-480,-310),(-140,-200,-480,-330)]:
   wall(f,x,(top+dy+43.5)/2,12,top-dy-43.5);wall(f,x,(bottom+dy-43.5)/2,12,dy-43.5-bottom)
  opening(f,-500,430,-480,290)
 k=1680 if f==0 else 2175;tl=1680 if f==0 else 2575;tr=2550 if f==0 else 3500;sl=2550 if f==0 else 2175;sr=3500 if f==0 else 2575
 for x in {430,k,tl,tr,sl,sr}:wall(f,x,-550,12,700)
 for l,r in [(430,k),(tl,tr),(sl,sr)]:opening(f,l,r,-200,(l+r)/2)
 for i in range(13):wall(f,350+i*230,80,10,300)
 for i in range(12):
  l=350+i*230;r=l+230;x=l+55
  a=l+5;b=x-43.5;wall(f,(a+b)/2,-65,b-a,10)
  a=x+43.5;b=r-5;wall(f,(a+b)/2,-65,b-a,10)
 # Common stall walls, where the tag approach uses the north aisle.
 pitch=(tr-tl-210)/3
 for n in range(3):wall(f,tl+210+n*pitch,-760,8,280)
 sp=(sr-sl-30)/(4 if f==0 else 2)
 for n in range(1,4 if f==0 else 2):wall(f,sl+15+n*sp,-760,7,280)
 wall(f,3500,-550,16,700)

def blocked(a,b,box):
 # Sample more finely than a centimetre at doors/corners, with circular footprint.
 n=max(1,math.ceil(math.dist(a[:2],b[:2])))
 for i in range(n+1):
  t=i/n;x=a[0]+(b[0]-a[0])*t;y=a[1]+(b[1]-a[1])*t
  dx=max(box[0]-x,0,x-box[2]);dy=max(box[1]-y,0,y-box[3])
  if dx*dx+dy*dy<28*28:return (round(x,1),round(y,1),box)
 return None
at=[355,-675,90];checked=0
for i,s in enumerate(steps):
 if s['kind']=='awakening':at=[355,-675,90]
 if s['kind']!='move':continue
 target=s['at']
 if at[2]==target[2] and at[2] in (90,410):
  for box in blocks[0 if at[2]==90 else 1]:
   assert not (hit:=blocked(at,target,box)),(i,at,target,hit)
  checked+=1
 at=target
print(f'REGRESSION_DATA_OK rows={rows} spoken={spoken} clips={unique} walk_steps={len(steps)} clear_wall_segments={checked}; engine meshes and W traversal pending')
