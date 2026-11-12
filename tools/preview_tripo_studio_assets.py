"""Dimension-authored review models. No remote calls; never replaces game assets."""
import bpy, math, json, sys, hashlib
from pathlib import Path
from mathutils import Vector, Matrix
ROOT=Path(sys.argv[sys.argv.index('--')+1])
OUT=ROOT/'Art/AssetConcepts/tripo-studio-v1';OUT.mkdir(parents=True,exist_ok=True)
layout=json.loads((ROOT/'Art/EnvironmentConcepts/unified-v15/furniture-layout.json').read_text('utf-8'))
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc.render.engine='CYCLES'
sc.cycles.samples=24;sc.cycles.use_denoising=True;sc.cycles.max_bounces=5
sc.render.resolution_x=1000;sc.render.resolution_y=900;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG';sc.view_settings.view_transform='AgX'
world=bpy.data.worlds.new('Review studio');sc.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.34,.38,.42,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.45
def mat(name,color,metal=0,rough=.5,wear=False):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
 p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 if wear:
  noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=55;noise.inputs['Detail'].default_value=3
  ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.2;ramp.color_ramp.elements[0].color=tuple(v*.86 for v in color)+(1,)
  ramp.color_ramp.elements[1].position=.82;ramp.color_ramp.elements[1].color=(*color,1)
  l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Base Color'])
  bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.12;bump.inputs['Distance'].default_value=.00035
  l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal'])
 return m
ceramic=mat('Warm glazed ceramic',(.76,.75,.68),rough=.22,wear=True)
enamel=mat('Old off-white enamel',(.66,.67,.62),.25,.38,True)
steel=mat('Brushed stainless',(.37,.42,.43),.82,.28,True)
dark=mat('Black rubber',(.025,.034,.036),rough=.7)
green=mat('Faded institutional green',(.16,.23,.20),.35,.47,True)
red=mat('Faded toolbox red',(.28,.07,.045),.5,.5,True)
glass=mat('Smoked washer glass',(.025,.055,.065),.3,.16)
floor=mat('Studio ground',(.24,.27,.28),rough=.8)
objects=[];groups={};active=''
def add(o,m):
 o.data.materials.append(m);objects.append(o);groups.setdefault(active,[]).append(o);return o
def box(name,p,d,m,bevel=.5):
 a=[v/200 for v in d];p=[v/100 for v in p]
 vs=[tuple(p[k]+s[k]*a[k] for k in range(3)) for s in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);me.update()
 o=bpy.data.objects.new(name,me);sc.collection.objects.link(o);add(o,m)
 if bevel:
  b=o.modifiers.new('Authored edge radius','BEVEL');b.width=bevel/100;b.segments=3
  o.modifiers.new('Face normals','WEIGHTED_NORMAL')
 return o
def surface(name,rings,m,cy=0,axis='Z',caps=False):
 # Rings are (rx,ry,z), centimetres, directly authored at final dimensions.
 N=64;vs=[]
 for rx,ry,z in rings:
  for i in range(N):
   t=2*math.pi*i/N;x=rx*math.cos(t);y=ry*math.sin(t)
   vs.append((x/100,(cy+y)/100,z/100) if axis=='Z' else (x/100,z/100,(cy+y)/100))
 fs=[]
 for j in range(len(rings)-1):
  for i in range(N):
   a=j*N+i;b=j*N+(i+1)%N;fs.append((a,b,b+N,a+N))
 if caps:fs.extend([tuple(reversed(range(N))),tuple((len(rings)-1)*N+i for i in range(N))])
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);sc.collection.objects.link(o)
 add(o,m)
 for p in me.polygons:p.use_smooth=True
 return o
def rod(name,a,b,r,m):
 a=Vector(a)/100;b=Vector(b)/100;v=b-a
 bpy.ops.mesh.primitive_cylinder_add(vertices=20,radius=r/100,depth=v.length,location=(a+b)/2)
 o=bpy.context.object;o.name=name;o.rotation_euler=v.to_track_quat('Z','Y').to_euler();add(o,m)
 for p in o.data.polygons:p.use_smooth=True
 return o
def knob(name,x,y,z,r,m):
 o=surface(name,[(r,r,y-.8),(r,r,y+.8)],m,cy=z,axis='Y',caps=True)
 o.location.x=x/100;return o
def pivot(name,p,parts,axis,angle):
 e=bpy.data.objects.new(name,None);sc.collection.objects.link(e);e.location=Vector(p)/100
 e['axis']=axis;e['opening_degrees']=angle
 for o in parts:
  o.parent=e;o.matrix_parent_inverse=Matrix.Translation(-e.location)
 return e
specs=[('A01','변기',[42,70,75],'1·2·3층 화장실 / 9개','본체·변기 뚜껑·좌대·물탱크 뚜껑 분리'),('A02','세면대',[55,60,85],'1·2·3층 화장실 / 3개','볼·받침·수전 분리; 전체85, 볼 상단73cm'),('A03','세탁기',[65,70,95],'옥상 세탁 공간 / 1개','본체·전면 도어·세제 서랍 분리'),('A04','접이식 건조대',[150,60,110],'옥상 빨래 공간 / 1개','상부 프레임·다리 분리; 펼친 상태 외형'),('A05','세제 수납장',[80,40,120],'옥상 세탁 공간 / 1개','본체·양문·선반·손잡이 분리'),('A06','공구함',[50,30,32],'1층 창고 / 1개','본체·뚜껑·잠금쇠 분리; 손잡이 접힌 상태')]
active='A01'
surface('Toilet pedestal',[(15,22,0),(15,22,3),(12,17,8),(11,15,23),(17,22,32)],ceramic,cy=-4,caps=True)
surface('Hollow toilet bowl',[(17,23,27),(20,27,35),(21,28,40),(20,27,42),(16,23,42),(13,19,35),(5,8,28)],ceramic,cy=-7)
surface('Bowl shadow',[(5,8,28),(4.5,7.5,28.2)],dark,cy=-7,caps=True)
surface('Separate seat ring',[(20.5,27.5,42),(20.5,27.5,43.5),(16,23,43.5),(16,23,42),(20.5,27.5,42)],enamel,cy=-7)
box('Separate upright lid',(0,16.5,55),(40,2,25),ceramic,.8)
box('Cistern',(0,26.5,56),(38,17,34),ceramic,2)
box('Separate cistern cap',(0,26.5,74),(40,17,2),ceramic,.7)
rod('Flush button',(10,26.5,74.8),(10,26.5,75),2,steel)
active='A02'
surface('Pedestal foot',[(14,17,0),(14,17,3),(9,12,7),(7.5,10,48),(10,14,63)],ceramic,cy=7,caps=True)
surface('Hollow wash basin',[(17,20,60),(26.5,29,69),(27.5,30,73),(24,26,73),(22,23,69),(8,9,61)],ceramic)
rod('Drain plug',(0,0,61),(0,0,61.3),2.5,steel)
box('Rear faucet deck',(0,24,71.25),(30,10,4.5),ceramic,.8)
rod('Faucet base',(0,24,73),(0,24,81),2,steel)
rod('Faucet spout',(0,24,80),(0,12,80),1.5,steel)
rod('Faucet spout end',(0,12,80),(0,12,77.5),1.5,steel)
box('Tap lever',(0,21,84),(3,11,2),steel,.5)
active='A03'
box('Washer body',(0,1,47),(65,64,90),enamel,1.4)
box('Top slab',(0,0,93.5),(65,70,3),enamel,.6)
box('Dark toe kick',(0,0,4),(62,63,5),dark,.5)
for x in [-26,26]:
 for y in [-27,27]:box('Leveling foot',(x,y,1),(6,6,2),dark,.3)
box('Control panel',(0,-31.6,84),(60,2,12),enamel,.4)
box('Detergent drawer',(-18,-33.1,84),(22,1,9),enamel,.4)
box('Drawer recessed grip',(-18,-33.7,81),(14,.5,1.2),dark,.2)
knob('Program dial',3,-33.1,84,3.8,steel)
box('Display',(20,-33,84),(15,.8,6),dark,.2)
for x in [15,19,23]:box('Indicator',(x,-33.5,84),(1.5,.2,.7),green,.1)
surface('Rubber door seal',[(23,23,-32),(23,23,-33.5),(19,19,-33.5),(19,19,-32),(23,23,-32)],dark,cy=49,axis='Y')
door=[]
door.append(surface('Separate round door rim',[(22,22,-33),(22,22,-35),(19,19,-35),(19,19,-33),(22,22,-33)],steel,cy=49,axis='Y'))
door.append(surface('Separate smoked door lens',[(19,19,-34),(17,17,-33)],glass,cy=49,axis='Y',caps=True))
door.append(box('Door grip',(19,-34,49),(3,2,12),enamel,.8))
pivot('WasherDoor_Hinge',(-22,-33,49),door,'Z',100)
for z in [13,16,19]:box('Service vent',(18,-31.6,z),(15,.6,.6),dark,.15)
active='A04'
# Rail endpoints and radius are contained in the agreed 150 x 60 x 110 envelope.
for y in [-29,29]:rod('Top long frame',(-74,y,109),(74,y,109),1,steel)
for x in [-74,74]:rod('Top end frame',(x,-29,109),(x,29,109),1,steel)
for x in range(-60,61,15):rod('Drying rail',(x,-28,109),(x,28,109),.55,steel)
for y in [-24,24]:
 rod('Folding leg',(-50,y,2),(50,y,108),1,steel)
 rod('Folding leg',(50,y,2),(-50,y,108),1,steel)
 for x in [-50,50]:box('Rubber shoe',(x,y,1),(6,4,2),dark,.5)
 rod('Joint bolt',(0,y-1.6,55),(0,y+1.6,55),1.8,steel)
rod('Brace',(-25,-24,28),(-25,24,28),.8,steel)
active='A05'
box('Cabinet back',(0,19,60),(80,2,120),green,.4)
for x in [-39,39]:box('Cabinet side',(x,0,60),(2,40,120),green,.5)
for z in [1,119]:box('Cabinet cap',(0,0,z),(80,40,2),green,.4)
for z in [8,47,85]:box('Interior shelf',(0,1,z),(76,35,1.5),enamel,.2)
for side in [-1,1]:
 parts=[box('Separate cabinet door',(side*19.7,-18.5,60),(38.4,2,116),green,.35)]
 parts.append(box('Pull',(side*4,-19.5,65),(1,1,14),steel,.4))
 for z in [14,17,20]:parts.append(box('Vent slot',(side*20,-19.55,z),(23,.3,.6),dark,.1))
 pivot('CabinetDoor_Hinge', (side*39,-18.5,60),parts,'Z',side*100)
active='A06'
box('Toolbox body',(0,0,12),(50,30,24),red,1)
box('Lid gasket',(0,0,24.2),(49.6,29.6,.6),dark,.2)
lid=[box('Separate toolbox lid',(0,0,27.4),(50,30,5.2),red,1)]
for x in [-18,18]:
 for y in [-11.5,11.5]:lid.append(box('Corner bumper',(x,y,29.7),(9,7,.6),dark,.5))
lid.append(box('Folded carry handle',(0,0,31),(20,5,2),dark,.7))
for x in [-15,15]:box('Front latch',(x,-14.3,23),(4,1.4,8),steel,.4)
pivot('ToolboxLid_Hinge',(0,14,25),lid,'X',105)
for x in [-23,23]:
 for z in [4,19]:knob('Rivet',x,-14.2,z,.6,steel)

def measured(parts):
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();points=[]
 for o in parts:
  e=o.evaluated_get(dg);me=e.to_mesh()
  points.extend(e.matrix_world@v.co for v in me.vertices);e.to_mesh_clear()
 mn=[min(p[k] for p in points)*100 for k in range(3)];mx=[max(p[k] for p in points)*100 for k in range(3)]
 return [round(mx[k]-mn[k],3) for k in range(3)]
report=[]
for code,name,dims,where,parts in specs:
 size=measured(groups[code]);report.append({'id':code,'name':name,'target_cm':dims,'measured_cm':size,'within_0_1cm':all(abs(a-b)<.1 for a,b in zip(size,dims)),'location':where,'parts':parts,'placements':[it for it in layout['items'] if it['name']==name],'estimated_studio_credits':55,'image':code+'.png'})

active='STUDIO';box('Ground',(0,0,-2),(1000,1000,3.8),floor,.1)
for name,loc,power,size in [('Key',(-3,-4,5),650,4),('Fill',(3,-1,3),350,3),('Rim',(0,3,4),550,3)]:
 ld=bpy.data.lights.new(name,'AREA');ld.energy=power;ld.shape='DISK';ld.size=size;o=bpy.data.objects.new(name,ld);sc.collection.objects.link(o);o.location=loc;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
cd=bpy.data.cameras.new('Review camera');cam=bpy.data.objects.new('Review camera',cd);sc.collection.objects.link(cam);sc.camera=cam;cd.type='ORTHO'
for code,name,dims,where,parts in specs:
 if '--only' in sys.argv and code!=sys.argv[sys.argv.index('--only')+1]:continue
 for k,obs in groups.items():
  if k!='STUDIO':
   for o in obs:o.hide_render=(k!=code)
 target=Vector((0,0,dims[2]/210));cam.location=target+Vector((2.6,-3.8,2.6));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
 cd.ortho_scale=max(dims)/100*1.8;sc.render.filepath=str(OUT/(code+'.png'));bpy.ops.render.render(write_still=True)
 print('RENDER_DONE '+code,flush=True)

# New exterior massing proposal. Footprint/storey anchors match the current code.
# Window trim, neighbours and exterior palette are design proposals, not approved geometry.
for obs in groups.values():
 for o in obs:o.hide_render=True
for o in sc.objects:
 if o.type=='LIGHT':o.hide_render=True
active='EXTERIOR'
oldwall=mat('Exterior warm worn render',(.35,.31,.25),rough=.83,wear=True)
cleanwall=mat('Renovated upper floor',(.64,.64,.58),rough=.72,wear=True)
concrete=mat('Concrete roof',(.27,.31,.30),rough=.83,wear=True)
frame=mat('Exterior dark frames',(.10,.12,.12),.4,.55)
nightglass=mat('Night windows',(.055,.075,.075),.25,.35)
warmglass=mat('Occasional lit room',(.45,.30,.12),rough=.6)
p=warmglass.node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(.65,.35,.12,1);p.inputs['Emission Strength'].default_value=.5
asphalt=mat('Street',(.075,.085,.085),rough=.92,wear=True)
box('Street ground',(1700,-335,-25),(9000,6000,20),asphalt,1)
box('Building plinth',(1700,-335,-8),(4400,1130,16),concrete,1)
for f in range(3):
 z=f*320;m=cleanwall if f==2 else oldwall
 box('Floor band',(1700,-335,z+280),(4400,1130,40),concrete,.6)
 box('Rear elevation',(1700,-900,z+130),(4400,16,260),m,.6)
 for x in [-500,3900]:box('Side elevation',(x,-335,z+130),(16,1130,260),m,.6)
 # Front room wall segments and their actual voids.
 for i in range(12):
  left=350+230*i;wx=left+179;a=wx-30;b=wx+30
  box('Front wall left',((left+a)/2,230,z+130),(a-left,16,260),m,.4)
  box('Front wall right',((b+left+230)/2,230,z+130),(left+230-b,16,260),m,.4)
  box('Window apron',(wx,230,z+50),(60,16,100),m,.4)
  box('Window lintel',(wx,230,z+225),(60,16,70),m,.4)
  box('Window glass',(wx,232,z+145),(56,3,86),warmglass if (i+f)%5==2 else nightglass,.1)
  for xx in [wx-29,wx+29]:box('Window jamb',(xx,235,z+145),(2,7,90),frame,.2)
  for zz in [z+101,z+189]:box('Window rail',(wx,235,zz),(60,7,2),frame,.2)
  box('Window mullion',(wx,235,z+145),(2,7,90),frame,.2)
 if f==0:
  for a,b in [(-500,-95),(95,350)]:box('Entrance flanking wall',((a+b)/2,230,130),(b-a,16,260),m,.4)
  box('Entrance header',(0,230,243),(190,16,34),m,.4)
  for x in [-47.5,47.5]:
   box('Entry door',(x,232,113),(93,5,226),frame,.5)
   box('Entry door glass',(x,236,125),(79,2,177),nightglass,.1)
   rod('Entry handle',(x*.2,240,100),(x*.2,240,140),1.5,steel)
 else:box('Front access wall',(-75,230,z+130),(850,16,260),m,.4)
 box('Front hall end',(3505,230,z+130),(790,16,260),m,.4)
box('Roof slab',(1700,-335,955),(4400,1130,10),concrete,.5)
for y in [-900,230]:box('Roof parapet',(1700,y,1015),(4400,16,110),oldwall,.4)
for x in [-500,3900]:box('Roof parapet',(x,-335,1015),(16,1130,110),oldwall,.4)
for x in [2800,3400]:
 for y in [-400,-830]:box('Laundry canopy post',(x,y,1065),(6,6,210),steel,.3)
box('Laundry canopy',(3100,-615,1180),(650,480,12),concrete,.5)
for y in [-400,-650]:
 for x in [750,2150]:box('Laundry line post',(x,y,1055),(5,5,190),steel,.2)
 rod('Clothesline',(750,y,1140),(2150,y,1140),.5,steel)
for x in [1100,1400,1800]:box('Hanging laundry',(x,-400,1080),(75,3,115),enamel,.5)
box('Entrance sign',(0,244,285),(340,10,48),green,.5)
font=bpy.data.fonts.load('C:/Windows/Fonts/malgun.ttf');curve=bpy.data.curves.new('Exterior sign text','FONT');curve.body='해담고시원';curve.font=font;curve.size=.34;curve.align_x='CENTER'
tx=bpy.data.objects.new('Exterior sign text',curve);sc.collection.objects.link(tx);tx.location=(0,2.51,2.73);tx.rotation_euler=(math.pi/2,0,math.pi);curve.materials.append(enamel)
for i,(x,w,h) in enumerate([(-1100,700,1300),(200,900,1550),(1500,1000,1200),(2900,800,1450),(4300,700,1600)]):
 box('Distant non-playable neighbour',(x,-2100,h/2),(w,1000,h),frame,2)
 for f in range(1,int(h/300)):
  for xx in range(int(x-w/2+100),int(x+w/2-60),150):box('Distant window',(xx,-1598,f*300),(55,2,90),nightglass,.1)
ld=bpy.data.lights.new('Exterior sky key','AREA');ld.energy=28000;ld.size=35;lo=bpy.data.objects.new('Exterior sky key',ld);sc.collection.objects.link(lo);lo.location=(5,15,30);lo.rotation_euler=(Vector((17,-3,5))-lo.location).to_track_quat('-Z','Y').to_euler()
target=Vector((16,-3,5));cam.location=target+Vector((-28,48,24));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cd.ortho_scale=61
sc.render.resolution_x=1800;sc.render.resolution_y=1000;sc.render.filepath=str(OUT/'exterior-massing.png');bpy.ops.render.render(write_still=True)
print('RENDER_DONE exterior',flush=True)
# Save the exterior review camera; each object group remains independently named.
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'dimensioned-reference-models.blend'))
(OUT/'measurements.json').write_text(json.dumps({'unit':'cm','source_layout':'unified-v15','credits_used':0,'runtime_imported':False,'models':report,'note':'Local reference geometry; Tripo generation not executed. Targets are design replacement dimensions, not measurements of existing game meshes.'},ensure_ascii=False,indent=2),'utf-8')
print('AUDIT '+json.dumps(report,ensure_ascii=True),flush=True)
