"""Fit approved Meshy architecture to the existing centimetre game grid.

Preserve original GLBs; split repeatable skins locally, straighten wall depth,
and fit openings to actual door frames. No paid remesh/retexture operations.
"""
import bpy, bmesh, json, math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'Art/EnvironmentMeshy/v1';OUT=BASE/'Unreal';OUT.mkdir(exist_ok=True)
entries=[];reports=[]
def active(o):
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
def bounds(o):
 return Vector([min(v.co[i] for v in o.data.vertices) for i in range(3)]),Vector([max(v.co[i] for v in o.data.vertices) for i in range(3)])
def cut(src,name,planes):
 o=src.copy();o.data=src.data.copy();bpy.context.collection.objects.link(o);o.name=name
 bm=bmesh.new();bm.from_mesh(o.data)
 for axis,value,greater in planes:
  co=[0,0,0];co[axis]=value;no=[0,0,0];no[axis]=1
  bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.000001,plane_co=co,plane_no=no,clear_inner=greater,clear_outer=not greater)
 loose=[v for v in bm.verts if not v.link_faces]
 if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
 bm.to_mesh(o.data);bm.free();return o
def fit(o,dims):
 lo,hi=bounds(o)
 for v in o.data.vertices:
  for i in range(3):v.co[i]=(v.co[i]-(lo[i]+hi[i])/2)*dims[i]/(hi[i]-lo[i])
 o.data.update()
def simplify(o,budget):
 active(o);tris=sum(len(p.vertices)-2 for p in o.data.polygons)
 if tris>budget:
  m=o.modifiers.new('GameBudget','DECIMATE');m.ratio=budget/tris;bpy.ops.object.modifier_apply(modifier=m.name)
def hole(o,z):
 deps=bpy.context.evaluated_depsgraph_get();tree=BVHTree.FromObject(o,deps);lo,hi=bounds(o)
 hits=[];runs=[]
 for i in range(1000):
  x=lo.x+(hi.x-lo.x)*(i+.5)/1000
  pt,_,_,_=tree.ray_cast(Vector((x,lo.y-1,z)),Vector((0,1,0)),hi.y-lo.y+2)
  if pt is None:hits.append(x)
  elif hits:
   if hits[0]>lo.x+.03:runs.append(hits)
   hits=[]
 if not runs:raise RuntimeError('No through opening in '+o.name)
 # A window can have two panes separated by a mullion; retain significant runs.
 runs=[r for r in runs if r[-1]-r[0]>.10]
 return min(r[0] for r in runs),max(r[-1] for r in runs)
def warp(v,src,dst):
 for i in range(len(src)-1):
  if v<=src[i+1]:return dst[i]+(v-src[i])/(src[i+1]-src[i])*(dst[i+1]-dst[i])
 return dst[-1]
def material_info(o,id):
 mats=[]
 def upstream(sock,seen=None):
  seen=seen or set()
  for l in sock.links:
   n=l.from_node
   if n in seen:continue
   seen.add(n)
   if n.type=='TEX_IMAGE':return n.image
   for inp in n.inputs:
    image=upstream(inp,seen)
    if image:return image
 for slot,m in enumerate(o.data.materials):
  p=m.node_tree.nodes.get('Principled BSDF');tex={}
  for role,socket in [('base','Base Color'),('normal','Normal'),('orm','Roughness')]:
   im=upstream(p.inputs[socket])
   if im:
    fn=f'T_AM_{id}_{slot}_{role}.png'
    # Regeneration must replace the previous bake instead of reusing stale pixels.
    if max(im.size)>2048:im.scale(2048,2048)
    im.filepath_raw=str(OUT/fn);im.file_format='PNG';im.save()
    tex[role]=fn
  mats.append({'name':f'M_AM_{id}_{slot}','slot':slot,'textures':tex,'constants':{'base':list(p.inputs['Base Color'].default_value)[:3],'rough':.8,'metal':0}})
 return mats
def bake_shell(src):
 """Bake the original textured high-poly surface onto a closed planar game shell."""
 name=src.name;src.name=name+'_bake_source';parts=[]
 def box(at,size):
  bpy.ops.mesh.primitive_cube_add(size=1,location=at);o=bpy.context.object;o.scale=size
  bpy.ops.object.transform_apply(location=True,rotation=False,scale=True);parts.append(o)
 if name=='SM_AM_DoorWall':
  box((-1.0925,0,0),(.115,.1,2.6));box((.4925,0,0),(1.315,.1,2.6));box((-.6,0,1.0275),(.87,.1,.545))
 elif name=='SM_AM_WindowWall':
  box((0,0,-.7),(2.3,.16,1.2));box((0,0,1),(2.3,.16,.6))
  box((-.405,0,.3),(1.49,.16,.8));box((1.045,0,.3),(.21,.16,.8));box((.64,0,.3),(.025,.16,.8))
 else:
  lo,hi=bounds(src);box((0,0,0),hi-lo)
 bpy.ops.object.select_all(action='DESELECT')
 for p in parts:p.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=parts[0];o.name=name
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.015);bpy.ops.object.mode_set(mode='OBJECT')
 mat=bpy.data.materials.new(name+'_Baked');mat.use_nodes=True
 p=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Roughness'].default_value=.82
 im=bpy.data.images.new(name+'_baked_base',width=2048,height=2048,alpha=False)
 tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;mat.node_tree.nodes.active=tex
 o.data.materials.clear();o.data.materials.append(mat)
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=1
 scene.render.bake.use_selected_to_active=True;scene.render.bake.cage_extrusion=.2;scene.render.bake.max_ray_distance=.5;scene.render.bake.margin=16
 scene.render.bake.use_pass_direct=False;scene.render.bake.use_pass_indirect=False;scene.render.bake.use_pass_color=True
 bpy.ops.object.select_all(action='DESELECT');src.hide_render=False;src.hide_viewport=False;src.select_set(True);o.select_set(True);bpy.context.view_layer.objects.active=o
 bpy.ops.object.bake(type='DIFFUSE')
 mat.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color'])
 src.hide_render=True;src.hide_viewport=True
 return o
def export(o,id,budget):
 if o.name!='SM_AM_FireEscape':o=bake_shell(o)
 else:simplify(o,budget)
 active(o)
 bpy.ops.export_scene.fbx(filepath=str(OUT/(o.name+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,bake_anim=False,add_leaf_bones=False,mesh_smooth_type='FACE')
 entries.append({'id':id,'mesh':o.name,'materials':material_info(o,o.name),'triangles':sum(len(p.vertices)-2 for p in o.data.polygons),'dimensions_cm':[round(d*100,3) for d in o.dimensions]})
 return o
bpy.ops.wm.read_factory_settings(use_empty=True)
for folder in sorted((BASE/'models').iterdir()):
 if not (folder/'source.glb').exists():continue
 id=folder.name[:3];bpy.ops.import_scene.gltf(filepath=str(folder/'source.glb'))
 meshes=[o for o in bpy.context.selected_objects if o.type=='MESH'];src=meshes[0];active(src);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 src.name='SOURCE_'+id;lo,hi=bounds(src)
 if id=='A01':
  left,right=hole(src,(lo.z+hi.z)*.5)
  # Top of the rectangular opening: vertical ray in the centre.
  tree=BVHTree.FromObject(src,bpy.context.evaluated_depsgraph_get());x=(left+right)/2
  zs=[]
  for k in range(1000):
   z=lo.z+(hi.z-lo.z)*k/1000
   pt,_,_,_=tree.ray_cast(Vector((x,lo.y-1,z)),Vector((0,1,0)),3)
   if pt is None:zs.append(z)
  top=max(z for z in zs if z<hi.z-.08);reports.append({'id':id,'opening':[left,right,top]})
  print('DOOR_OPENING',left,right,top,flush=True)
  wall=cut(src,'SM_AM_Wall',[(0,right+.06,True),(0,hi.x-.025,False)])
  fit(wall,(1,.12,2.6));export(wall,id,1200)
  o=src.copy();o.data=src.data.copy();bpy.context.collection.objects.link(o);o.name='SM_AM_DoorWall'
  for v in o.data.vertices:
   v.co.x=warp(v.co.x,[lo.x,left,right,hi.x],[-1.15,-1.035,-.165,1.15])
   v.co.z=warp(v.co.z,[lo.z,top,hi.z],[-1.3,.755,1.3])
   v.co.y=(v.co.y-(lo.y+hi.y)/2)*.10/(hi.y-lo.y)
  export(o,id,5000)
 elif id=='A02':
  left,right=hole(src,0);tree=BVHTree.FromObject(src,bpy.context.evaluated_depsgraph_get())
  # Probe each pane, not the central mullion.
  x=left+(right-left)*.25;zs=[]
  for k in range(1000):
   z=lo.z+(hi.z-lo.z)*k/1000
   pt,_,_,_=tree.ray_cast(Vector((x,lo.y-1,z)),Vector((0,1,0)),3)
   if pt is None:zs.append(z)
  zs=[z for z in zs if lo.z+.12<z<hi.z-.12]
  # The panes are internal holes, never the thin silhouette gaps at the bounds.
  runs=[];run=[]
  for z in zs:
   if run and z-run[-1]>(hi.z-lo.z)*.003:runs.append(run);run=[]
   run.append(z)
  if run:runs.append(run)
  run=max(runs,key=len);bottom,top=run[0],run[-1]
  print('WINDOW_OPENING',left,right,bottom,top,flush=True)
  o=src.copy();o.data=src.data.copy();bpy.context.collection.objects.link(o);o.name='SM_AM_WindowWall'
  for v in o.data.vertices:
   v.co.x=warp(v.co.x,[lo.x,left,right,hi.x],[-1.15,.34,.94,1.15])
   v.co.z=warp(v.co.z,[lo.z,bottom,top,hi.z],[-1.3,-.1,.7,1.3])
   v.co.y=(v.co.y-(lo.y+hi.y)/2)*.16/(hi.y-lo.y)
  export(o,id,5000);reports.append({'id':id,'opening':[left,right,bottom,top]})
 elif id=='A03':
  # Retain the textured back wall and floor of the actual Meshy corner.
  wall=cut(src,'SM_AM_TileWall',[(1,hi.y-.18,True),(0,lo.x+.18,True),(0,hi.x-.12,False),(2,lo.z+.06,True)])
  fit(wall,(1,.12,2.6));export(wall,id,1200)
  floor=cut(src,'SM_AM_TileFloor',[(2,lo.z+.04,False),(0,lo.x+.2,True),(0,hi.x-.2,False),(1,lo.y+.2,True),(1,hi.y-.2,False)])
  fit(floor,(1,1,.02));export(floor,id,800)
 else:
  o=src.copy();o.data=src.data.copy();bpy.context.collection.objects.link(o);o.name='SM_AM_FireEscape'
  fit(o,(6.8,1.65,4.35));export(o,id,18000)
 src.hide_render=True;src.hide_viewport=True
# Exported objects are centered; runtime supplies location and exact backing collision.
(OUT/'import.json').write_text(json.dumps(entries,indent=2),encoding='utf-8')
(BASE/'preparation.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'architecture-modules.blend'))
print('ARCHITECTURE_PREPARED',[(i['mesh'],i['triangles']) for i in entries])
