"""Prepare approved Meshy props in Blender: scale, simplify, split movable parts.

Sources are never overwritten. Units are metres, front -Y (UE FBX mirrors Y).
Rendered previews are verification of real exported geometry, not concept images.
"""
import bpy, bmesh, json, math, os
from pathlib import Path
from mathutils import Vector, Matrix
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'Art/CoreProps/v1'
OUT=BASE/'Unreal'; OUT.mkdir(exist_ok=True)
SPECS={
 'O01':('DeskBody',(1.0,.55,.75),22000),
 'O03':('Phone',(.32,.26,.14),14000),
 'O05':('CRT',(.32,.30,.30),14000),
 'I01':('Flashlight',(.25,.075,.075),14000),
 'I02':('Cartridge',(.075,.04,.04),6000),
 'B01':('Door',(.78,.075,2.0),9000),
 'K01':('FridgeBody',(.62,.65,1.70),14000),
 'K06':('RoundTable',(1.50,1.50,.75),14000),
 'R01':('BedFrame',(.80,1.95,.70),18000),
 'R04':('WardrobeBody',(.45,.45,1.75),12000),
}
ONLY=set(os.environ.get('NR_CORE_ONLY','').split(','))-{''}
entries=json.loads((OUT/'import.json').read_text()) if ONLY and (OUT/'import.json').exists() else []
reports=json.loads((BASE/'preparation.json').read_text()) if ONLY and (BASE/'preparation.json').exists() else []
entries=[e for e in entries if e['id'] not in ONLY] if ONLY else entries
reports=[e for e in reports if e['id'] not in ONLY] if ONLY else reports
def activate(o):
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
def bounds(o):
 p=[o.matrix_world@Vector(v) for v in o.bound_box]
 return Vector([min(v[i] for v in p) for i in range(3)]),Vector([max(v[i] for v in p) for i in range(3)])
def constant(name,color,rough=.65,metal=0):
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 return m
def box(name,at,size,mat):
 bpy.ops.mesh.primitive_cube_add(size=1,location=at);o=bpy.context.object;o.name=name;o.scale=size
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
 return o
def join(parts,name):
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object;o.name=name
 return o
def clip(src,name,planes):
 o=src.copy();o.data=src.data.copy();bpy.context.collection.objects.link(o);o.name=name
 bm=bmesh.new();bm.from_mesh(o.data)
 for axis,at,keep_greater in planes:
  pt=[0,0,0];pt[axis]=at;normal=[0,0,0];normal[axis]=1
  bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.000001,plane_co=pt,plane_no=normal,clear_inner=keep_greater,clear_outer=not keep_greater)
 loose=[v for v in bm.verts if not v.link_faces]
 if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
 bm.to_mesh(o.data);bm.free();o.data.update()
 return o
def pivot(o,p):
 # Preserve assembled world placement while moving the mesh origin.
 p=Vector(p)
 for v in o.data.vertices:v.co-=p
 o.location+=p
def export(o,name,source_id):
 activate(o);original=o.location.copy();o.location=(0,0,0)
 # Mesh coordinates encode shape relative to its runtime pivot; actor supplies position.
 bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,bake_anim=False,add_leaf_bones=False,mesh_smooth_type='FACE')
 o.location=original
 mats=[]
 for i,slot in enumerate(o.material_slots):
  m=slot.material
  if not m:continue
  p=m.node_tree.nodes.get('Principled BSDF');tex={}
  def upstream_image(socket,seen=None):
   seen=seen or set()
   for l in socket.links:
    n=l.from_node
    if n in seen:continue
    seen.add(n)
    if n.type=='TEX_IMAGE':return n.image
    for inp in n.inputs:
     image=upstream_image(inp,seen)
     if image:return image
   return None
  for role,socket in [('base','Base Color'),('normal','Normal'),('orm','Roughness')]:
   image=upstream_image(p.inputs[socket])
   if image:
    fn=f'T_CP_{source_id}_{role}.png';target=OUT/fn
    if not target.exists():image.filepath_raw=str(target);image.file_format='PNG';image.save()
    tex[role]=fn
  mats.append({'name':m.name,'slot':i,'textures':tex,'constants':{'base':list(p.inputs['Base Color'].default_value)[:3],'rough':p.inputs['Roughness'].default_value,'metal':p.inputs['Metallic'].default_value}})
 entries.append({'id':source_id,'mesh':name,'materials':mats,'triangles':sum(len(p.vertices)-2 for p in o.data.polygons),'pivot_m':list(original),'dimensions_cm':[round(d*100,3) for d in o.dimensions]})
def render(parts,path):
 for o in bpy.context.scene.objects:
  if o.type=='MESH':o.hide_render=o not in parts
 points=[o.matrix_world@Vector(v) for o in parts for v in o.bound_box]
 lo=Vector([min(v[i] for v in points) for i in range(3)]);hi=Vector([max(v[i] for v in points) for i in range(3)])
 center=(lo+hi)/2;extent=max(hi-lo)
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16
 scene.render.resolution_x=720;scene.render.resolution_y=720;scene.render.resolution_percentage=100
 scene.world=bpy.data.worlds.new('Studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.45,.45,.45,1)
 bpy.ops.object.camera_add(location=center+Vector((1.8,-3,1.6))*extent);cam=bpy.context.object;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=extent*1.52;scene.camera=cam
 lamps=[]
 for loc,energy,size in [((1,-3,4),350,3),((-3,-1,2),180,2)]:
  bpy.ops.object.light_add(type='AREA',location=center+Vector(loc)*extent);l=bpy.context.object;l.data.energy=energy*extent**2;l.data.shape='DISK';l.data.size=size*extent;l.rotation_euler=(center-l.location).to_track_quat('-Z','Y').to_euler();lamps.append(l)
 scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 for o in lamps+[cam]:bpy.data.objects.remove(o,do_unlink=True)

for source in sorted((BASE/'models').glob('*/source.glb')):
 id=source.parent.name[:3];label,dims,budget=SPECS[id]
 if ONLY and id not in ONLY:continue
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(source))
 meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];obj=join(meshes,'SM_CP_'+label)
 activate(obj);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 obj.rotation_mode='XYZ'
 if id=='B01':
  # glTF duplicates vertices at UV seams. Decimating those disconnected islands
  # independently tore the door into triangles; weld geometry before reduction.
  # UV coordinates remain per-face-loop, so the original texture seams survive.
  bm=bmesh.new();bm.from_mesh(obj.data)
  bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001)
  bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
  bm.to_mesh(obj.data);bm.free();obj.data.update()
 before=sum(len(p.vertices)-2 for p in obj.data.polygons)
 # Preserve the repaired door's authored shape and UV islands. All instances
 # reference this same 37k-triangle mesh; simplify later against visual captures.
 if before>budget and id!='B01':
  m=obj.modifiers.new('Runtime budget','DECIMATE');m.ratio=budget/before;m.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=m.name)
 if id=='R01':
  obj.rotation_euler.z=math.pi/2;bpy.ops.object.transform_apply(location=False,rotation=True,scale=False)
 if id in ('B01','I01','I02'):
  # B01: handle on free (+X) edge, hinge at -X. Tools point their lens along +X.
  for v in obj.data.vertices:v.co.x=-v.co.x
  bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
 lo,hi=bounds(obj);center=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z))
 for v in obj.data.vertices:v.co=Vector([(v.co[i]-center[i])*dims[i]/(hi[i]-lo[i]) for i in range(3)])
 obj.data.update();bpy.context.view_layer.update()
 for i,m in enumerate(obj.data.materials):m.name=f'M_CP_{id}_{i}'
 wood=constant('M_CP_InteriorWood',(.09,.055,.025));ivory=constant('M_CP_InteriorIvory',(.56,.55,.47));steel=constant('M_CP_InteriorSteel',(.17,.18,.17),.4,.7)
 parts=[obj];moving=[]
 if id=='O01':
  # Cut original textured front into 3 panels; body gets a proper empty pedestal.
  edges=[.052,.37,.535,.704]
  fronts=[]
  for n in range(3):
   front=clip(obj,f'SM_CP_Drawer{n+1}',[(0,.118,True),(0,.471,False),(1,-.232,False),(2,edges[n]+.002,True),(2,edges[n+1]-.002,False)])
   z0=edges[n]+.018;h=min(edges[n+1]-edges[n]-.042,.19);x=.294;y=-.009;w=.317;depth=.434
   walls=[box('Drawer bottom',(x,y,z0),(w,depth,.012),wood),box('Drawer left',(x-w/2+.006,y,z0+h/2),(.012,depth,h),wood),box('Drawer right',(x+w/2-.006,y,z0+h/2),(.012,depth,h),wood),box('Drawer back',(x,y+depth/2-.006,z0+h/2),(w,.012,h),wood),box('Drawer front backing',(x,-.229,z0+h/2),(w,.012,h),wood)]
   fronts.append(join([front]+walls,f'SM_CP_Drawer{n+1}'))
  # Preserve the non-manifold generated shell using disjoint planar partitions.
  # A volumetric boolean on this AI shell can remove the top and left leg.
  left=clip(obj,'Left shell',[(0,.118,False)])
  right=clip(obj,'Right shell',[(0,.471,True)])
  middle=clip(obj,'Rear shell',[(0,.118,True),(0,.471,False),(1,-.211,True)])
  top=clip(obj,'Top trim',[(0,.118,True),(0,.471,False),(1,-.211,False),(2,.704,True)])
  bottom=clip(obj,'Bottom trim',[(0,.118,True),(0,.471,False),(1,-.211,False),(2,.052,False)])
  bpy.data.objects.remove(obj,do_unlink=True)
  obj=join([left,right,middle,top,bottom],'SM_CP_DeskBody')
  # Back and side linings ensure a closed interior even if generated shell is imperfect.
  lining=[box('Pedestal back',(.294,.228,.375),(.35,.015,.65),wood),box('Pedestal left',(.12,.002,.375),(.016,.47,.65),wood),box('Pedestal right',(.468,.002,.375),(.016,.47,.65),wood)]
  obj=join([obj]+lining,'SM_CP_DeskBody');parts=[obj]+fronts;moving=fronts
  # Fit the 268 cm office interior with 2 cm clearance on each side.
  # Preserve drawer/leg widths; extend only the top and knee-space stretch.
  for part in parts:
   for v in part.data.vertices:
    x=v.co.x
    v.co.x=x-.82 if x<=-.43 else x+.82 if x>=.118 else -1.25+(x+.43)*(2.188/.548)
   part.data.update()
  bpy.context.view_layer.update()
 if id in ('K01','R04'):
  fridge=id=='K01';w,d,h=dims;cut=-.190 if fridge else -.145
  body=clip(obj,'SM_CP_'+label,[(1,cut,True)])
  ranges=[(.02,1.185,'FridgeDoor'),(1.185,1.69,'FreezerDoor')] if fridge else [(.025,1.724,'WardrobeDoor')]
  doors=[];inner=ivory if fridge else wood
  for low,high,name in ranges:
   door=clip(obj,'SM_CP_'+name,[(1,cut,False),(2,low,True),(2,high,False)])
   backing=box('Door inner', (0,cut-.005,(low+high)/2),(w-.042,.015,high-low-.025),inner)
   door=join([door,backing],'SM_CP_'+name)
   pivot(door,(w/2-.018,cut,0));doors.append(door)
  panels=[box('Inside back',(0,d/2-.026,h/2),(w-.025,.018,h-.06),inner),box('Inside left',(-w/2+.025,.02,h/2),(.018,d-.1,h-.06),inner),box('Inside right',(w/2-.025,.02,h/2),(.018,d-.1,h-.06),inner),box('Inside base',(0,.015,.055),(w-.04,d-.08,.02),inner),box('Inside top',(0,.015,h-.042),(w-.04,d-.08,.02),inner)]
  for z in ([.37,.68,.99,1.18,1.43] if fridge else [.34,1.43]):panels.append(box('Shelf',(0,.015,z),(w-.05,d-.1,.014),inner))
  if not fridge:panels.append(box('Clothes rail',(0,.01,1.32),(w-.06,.016,.016),steel))
  bpy.data.objects.remove(obj,do_unlink=True);obj=join([body]+panels,'SM_CP_'+label);parts=[obj]+doors;moving=doors
 if id=='B01':
  # Origin at hinge, height offset matches the existing frame and opening.
  for v in obj.data.vertices:v.co.x+=.39;v.co.z+=.005
  obj.data.update()
  bm=bmesh.new();bm.from_mesh(obj.data)
  print('DOOR_TOPOLOGY',len(bm.verts),'boundary_edges',sum(e.is_boundary for e in bm.edges),flush=True)
  bm.free()
 for p in parts:export(p,p.name,id)
 bpy.ops.wm.save_as_mainfile(filepath=str(source.parent/'prepared.blend'))
 render(parts,source.parent/'prepared-preview.png')
 if moving:
  for p in moving:
   if id=='O01':p.location.y-=.38
   else:p.rotation_euler.z=math.radians(100)
  bpy.context.view_layer.update();render(parts,source.parent/'open-preview.png')
  for p in moving:
   if id=='O01':p.location.y+=.38
   else:p.rotation_euler.z=0
 reports.append({'id':id,'source_triangles':before,'prepared_triangles':sum(sum(len(f.vertices)-2 for f in p.data.polygons) for p in parts),'parts':[p.name for p in parts]})
 print('CORE_PREPARED',id,reports[-1],flush=True)
(OUT/'import.json').write_text(json.dumps(entries,indent=2),encoding='utf-8')
(BASE/'preparation.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
print('CORE_PREPARATION_COMPLETE',flush=True)
