"""Code-coordinate exterior review, no changes to runtime or canonical plan."""
from pathlib import Path
import sys,json,re,hashlib,math
ROOT=Path(sys.argv[sys.argv.index('--')+1])
# Reuse only local geometry and material helpers, before any prop models/renders.
helper=(ROOT/'tools/preview_tripo_studio_assets.py').read_text('utf-8').split('specs=[')[0]
exec(helper.replace("'Art/AssetConcepts/tripo-studio-v1'","'Art/AssetConcepts/tripo-studio-v2'"))
code_root=ROOT/'NightRulesPrototype/Source/NightRulesPrototype'
header=(code_root/'NRGame.h').read_text('utf-8');arch=(code_root/'NRArchitecture.cpp').read_text('utf-8');game=(code_root/'NRGame.cpp').read_text('utf-8')
def number(name):return float(re.search(r'\b'+name+r'\s*=\s*(-?[\d.]+)',header).group(1))
FH=number('FloorHeight');RS=number('RoomStartX');RP=number('RoomPitch');RB=number('RoomBack')
required=['const float WinX=Right-51,BackY=RoomBack','FVector(60,3,80)','for(float Y:{-300.f,-520.f,-740.f})','FVector(3100,-615,1180)','Opening(3500,3900,-200,960,3790)']
assert all(t in game+arch for t in required),'Source geometry changed; review formulas before re-running.'
active='EXTERIOR_MATCH'
old=mat('Exterior aged mineral render',(.43,.39,.32),rough=.82,wear=True)
clean=mat('Exterior repaired upper render',(.66,.66,.60),rough=.78,wear=True)
concrete=mat('Roof waterproof grey',(.24,.29,.27),rough=.86,wear=True)
frame=mat('Window anodised aluminium',(.19,.22,.21),.65,.38)
gl=mat('Dark window panes',(.065,.10,.105),.35,.22)
lightgl=mat('Occupied room glass',(.42,.32,.17),rough=.48)
p=lightgl.node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(.48,.30,.12,1);p.inputs['Emission Strength'].default_value=.3
road=mat('Neutral ground',(.17,.19,.19),rough=.9)
box('Ground',(1700,-335,-30),(7500,4300,20),road,1)
windows=[]
for f in range(3):
 z=f*FH;m=clean if f==2 else old
 # Floors have the same stairwell exclusion as the runtime.
 for name,p,d in [('Main slab',(1500,-335,z-10),(4000,1130,20)),('North east slab',(3700,15,z-10),(400,430,20)),('North landing',(3700,-250,z-10),(400,100,20))]:box(name,p,d,concrete,.25)
 box('North ceiling fascia',(1700,230,z+280),(4400,16,40),concrete,.3)
 box('South elevation',(1700,-900,z+130),(4400,16,260),m,.4)
 box('East elevation',(3900,-335,z+130),(16,1130,260),m,.4)
 # West emergency doorway at y=-135; reproduce opening width87 and height205.5.
 for a,b in [(-900,-178.5),(-91.5,230)]:box('West wall segment',(-500,(a+b)/2,z+130),(16,b-a,260),m,.4)
 box('West door header',(-500,-135,z+232.75),(16,87,54.5),m,.3)
 box('Emergency exit door',(-500,-135,z+102),(5,84,204),green,.4)
 for i in range(12):
  left=RS+RP*i;right=left+RP;wx=right-51
  for name,p,d in [('Sill wall',(left+115,RB,z+60),(230,16,120)),('Head wall',(left+115,RB,z+230),(230,16,60)),('Window left',((left+wx-30)/2,RB,z+160),(wx-30-left,16,80)),('Window right',((wx+30+right)/2,RB,z+160),(right-wx-30,16,80))]:box(name,p,d,m,.25)
  pane=box(f'Window_{f+1}{i+1:02d}',(wx,RB,z+160),(60,3,80),lightgl if (i+f)%5==2 else gl,0)
  for xx in [wx-29,wx+29,wx]:box('Thin window jamb',(xx,235,z+160),(2,7,80),frame,.15)
  for zz in [z+121,z+199]:box('Window head sill trim',(wx,235,zz),(60,7,2),frame,.15)
  windows.append({'room':(f+1)*100+i+1,'center_cm':[wx,RB,z+160],'opening_cm':[60,80],'lower_cm':z+120,'upper_cm':z+200,'object':pane.name})
 if f==0:
  for a,b in [(-500,-95),(95,350)]:box('Entrance flank',((a+b)/2,230,130),(b-a,16,260),m,.4)
  box('Entry lintel',(0,230,243),(190,16,34),m,.3)
  for x in [-47.5,47.5]:
   box('Double entrance leaf',(x,230,113),(94,6,226),frame,.3)
   box('Entrance glazing',(x,234,125),(80,2,178),gl,.2)
   rod('Entrance pull',(x*.2,239,95),(x*.2,239,145),1.5,steel)
 else:
  box('Upper access solid wall',(-75,230,z+130),(850,16,260),m,.3)
  # A decorative window panel is behind this uncut runtime wall: do not invent an opening.
 box('North corridor end',(3505,230,z+130),(790,16,260),m,.4)
 # Render the currently closed inter-storey surfaces only where code defines them.
 box('Stairwell south band',(3700,-900,z+290),(400,16,60),m,.3)
 box('Stairwell east band',(3900,-550,z+290),(16,700,60),m,.3)

# Roof deck deliberately leaves x3500..3900/y-900..-300 open for the stairs.
roofz=3*FH
for name,p,d in [('Roof main deck',(1500,-335,950),(4000,1130,20)),('Roof north east deck',(3700,15,950),(400,430,20)),('Roof landing',(3700,-250,950),(400,100,20))]:box(name,p,d,concrete,.25)
for x in [-500,3900]:box('Roof side parapet',(x,-335,1015),(16,1130,110),old,.4)
for y in [-900,230]:box('Roof front back parapet',(1700,y,1015),(4400,16,110),old,.4)
box('Stair head west wall',(3500,-550,1090),(16,700,260),clean,.4)
box('Stair head east wall',(3900,-550,1090),(16,700,260),clean,.4)
box('Stair head south wall',(3700,-900,1090),(400,16,260),clean,.4)
for a,b in [(3500,3746.5),(3833.5,3900)]:box('Stair head front flank',((a+b)/2,-200,1090),(b-a,12,260),clean,.3)
box('Stair head front lintel',(3790,-200,1192.75),(87,12,54.5),clean,.3)
box('Roof access door',(3790,-200,1062),(84,5,204),green,.4)
headcap=box('Stair head ceiling',(3700,-550,1240),(400,700,40),concrete,.3)
for half in [0,1]:
 for n in range(8):
  x=3610 if half==0 else 3790;y=-325-n*50 if half==0 else -675+n*50
  box('Third floor stairs',(x,y,640+half*160+(n+1)*20-6),(180,50,12),concrete,.25)
box('Third floor return landing',(3700,-800,790),(400,200,20),concrete,.25)
for x in [2800,3400]:
 for y in [-400,-830]:box('Laundry canopy post',(x,y,1065),(6,6,210),steel,.2)
canopy=box('Laundry canopy',(3100,-615,1180),(650,480,12),concrete,.3)
lines=[]
for y in [-300,-520,-740]:
 for x in [750,2150]:box('Clothesline upright',(x,y,1055),(5,5,190),steel,.15)
 line=rod('Clothesline',(750,y,1140),(2150,y,1140),.5,steel);lines.append({'y_cm':y,'x_range_cm':[750,2150],'z_cm':1140})
# Existing exterior decorative stair model: reproduce runtime size/yaw, not a new redesign.
fbx=ROOT/'Art/EnvironmentMeshy/v1/Unreal/SM_AM_FireEscape.fbx'
if fbx.exists():
 before=set(bpy.data.objects);bpy.ops.import_scene.fbx(filepath=str(fbx));parts=[o for o in bpy.data.objects if o not in before and o.type=='MESH']
 for src in parts:
  vs=[src.matrix_world@v.co for v in src.data.vertices];lo=Vector(tuple(min(v[k] for v in vs) for k in range(3)));hi=Vector(tuple(max(v[k] for v in vs) for k in range(3)));sz=hi-lo;mid=(lo+hi)/2
  for f in range(3):
   me=src.data.copy();ob=bpy.data.objects.new(f'Runtime decorative fire escape {f}',me);sc.collection.objects.link(ob)
   # UE mirrors imported Y; a 90 degree yaw then maps the long X axis down the west side.
   for v,orig in zip(me.vertices,vs):
    q=orig-mid;q=Vector((q.x/sz.x*6.8,-q.y/sz.y*1.65,q.z/sz.z*4.35));v.co=Vector((-q.y,q.x,q.z))+Vector((-6.5,-4.7,f*3.2+2.075))
   ob.data.materials.clear();ob.data.materials.append(steel)
  bpy.data.objects.remove(src,do_unlink=True)
for f in range(3):
 box('Escape landing',(-650,-135,f*320-10),(300,180,20),concrete,.3)
 for y in [-225,-45]:box('Escape landing rail',(-650,y,f*320+55),(300,7,110),steel,.3)
 box('Escape west rail',(-800,-135,f*320+55),(7,180,110),steel,.3)

# Structural evidence is actual generated pane bounds, not a claim about AI pixels.
bpy.context.view_layer.update();checks=[]
for w in windows:
 o=bpy.data.objects[w['object']];vs=[o.matrix_world@v.co for v in o.data.vertices]
 mn=[min(p[k] for p in vs)*100 for k in range(3)];mx=[max(p[k] for p in vs)*100 for k in range(3)]
 checks.append(max(abs((mn[k]+mx[k])/2-w['center_cm'][k]) for k in range(3))<.001 and abs((mx[0]-mn[0])-60)<.001 and abs((mx[2]-mn[2])-80)<.001)
report={'source_sha256':{n:hashlib.sha256((code_root/n).read_bytes()).hexdigest() for n in ['NRGame.h','NRGame.cpp','NRArchitecture.cpp']},'scope':'Code-space audit and Blender reference only; not packaged-game screenshot or collision QA','unit':'cm','windows':windows,'window_bounds_passed':sum(checks),'expected_windows':36,'floor_height_cm':FH,'roof_height_cm':roofz,'roof_stair_opening_xy_cm':[3500,3900,-900,-300],'roof_stair_head_xy_cm':[3500,3900,-900,-200],'roof_door_center_cm':[3790,-200,960],'canopy':{'center_cm':[3100,-615,1180],'size_cm':[650,480,12]},'clotheslines':lines,'parapet_top_cm':1070,'differences_from_v1':['Windows corrected from 60x90 at centerZ145 to60x80 at centerZ160.','Roof stair head added.','Full roof slab replaced with actual stair opening.','Clotheslines corrected from2 to3 at actual Y anchors.','Existing external escape model and landings added.'],'runtime_issue':['Upper access area has decorative window panels on F2/F3 but a full uncut wall behind them. Not counted as functional exterior windows; needs a separate game change if wanted.'],'Tripo_credits_spent':0}
assert all(checks) and len(lines)==3
(OUT/'exterior-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
ld=bpy.data.lights.new('Large daylight softbox','AREA');ld.energy=35000;ld.size=30;l=bpy.data.objects.new('Large daylight softbox',ld);sc.collection.objects.link(l);l.location=(4,14,28);l.rotation_euler=(Vector((17,-3,5))-l.location).to_track_quat('-Z','Y').to_euler()
cd=bpy.data.cameras.new('Exterior audit camera');cam=bpy.data.objects.new('Exterior audit camera',cd);sc.collection.objects.link(cam);sc.camera=cam;cd.type='ORTHO';cd.clip_end=500
def render(name,target,offset,scale,res):
 target=Vector(target);cam.location=target+Vector(offset);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cd.ortho_scale=scale
 sc.render.resolution_x,sc.render.resolution_y=res;sc.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True);print('RENDER_DONE '+name,flush=True)
render('exterior-code-matched',(16,-3,5),(-28,48,29),59,(1900,1100))
render('front-code-matched',(17,0,6),(0,70,0),48,(1900,650))
headcap.hide_render=True;canopy.hide_render=True
render('roof-code-matched',(17,-3.35,9.6),(0,0,80),50,(1900,700))
headcap.hide_render=False;canopy.hide_render=False
render('roof-stair-detail',(34,-5.4,10),(9,12,14),17,(1200,1000))
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'exterior-code-matched.blend'))
print('EXTERIOR_AUDIT_PASS 36 window bounds;3 clotheslines;roof cutout preserved',flush=True)
