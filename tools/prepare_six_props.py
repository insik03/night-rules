"""Rejected preparation, retained for audit only. Original Meshy GLBs are preserved."""
raise SystemExit('DISABLED: rejected dimension corrections. Use build_dimensioned_furniture.py for the separate review scene.')
import bpy,bmesh,json,math,ast
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'Art/GeneratedProps/six-v1'
OUT=BASE/'Unreal';OUT.mkdir(exist_ok=True)
entries=[];reports=[]
# Share established pivot, clipping and FBX export conventions without running its batch.
tree=ast.parse((ROOT/'tools/prepare_core_props.py').read_text(encoding='utf-8'))
for node in tree.body:
 if isinstance(node,ast.FunctionDef) and node.name in ['activate','bounds','constant','box','join','clip','pivot','export','render']:
  exec(compile(ast.Module(body=[node],type_ignores=[]),'core-prop-helpers','exec'))
specs=[('chair','Chair',9000,2,.80),('bedding','Bedding',15000,0,.88),('sink','SinkBody',12000,0,1.2),('shower','Shower',16000,2,1.1),('slippers','Slippers',4000,1,.28),('books','Books',5000,0,.30)]
for key,label,budget,axis,length in specs:
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.gltf(filepath=str(BASE/key/'model.glb'))
 o=join([o for o in bpy.context.scene.objects if o.type=='MESH'],'SM_GP_'+label)
 activate(o);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 o.rotation_mode='XYZ'
 lo,hi=bounds(o);factor=length/(hi[axis]-lo[axis]);origin=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z))
 for v in o.data.vertices:v.co=(v.co-origin)*factor
 o.data.update();bpy.context.view_layer.update()
 note='Uniform scale only; original proportions retained.'
 if key=='bedding':
  lo,hi=bounds(o);extension=1.95-(hi.y-lo.y)
  # Alter only the unadorned middle sheet, leaving the pillow and folded quilt rigid.
  for v in o.data.vertices:
   t=max(0,min(1,(v.co.y+.12)/.24));v.co.y+=extension*(t-.5)
  o.data.update();note='Uniform width 88cm; plain centre sheet extended to 195cm. Pillow/quilt ends translated rigidly, not stretched.'
 # Weld glTF seam duplicates while retaining per-loop UVs before simplification.
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000002)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 before=sum(len(p.vertices)-2 for p in o.data.polygons)
 if before>budget:
  m=o.modifiers.new('Game budget','DECIMATE');m.ratio=budget/before;m.use_collapse_triangulate=True
  activate(o);bpy.ops.object.modifier_apply(modifier=m.name)
 for i,m in enumerate(o.data.materials):
  m.name=f'M_GP_{key}_{i}'
  for node in m.node_tree.nodes:
   if node.type=='TEX_IMAGE' and node.image and max(node.image.size)>2048:
    node.image.scale(2048,2048)
 parts=[o]
 if key=='sink':
  # Determine countertop plane from upward-facing area, rather than scaling the faucet.
  o.data.update();bins={}
  for poly in o.data.polygons:
   if poly.normal.z>.85 and poly.center.z>.55:
    z=round(poly.center.z/.01)*.01;bins[z]=bins.get(z,0)+poly.area
  top=max(bins,key=bins.get) if bins else .75
  raise_by=max(0,.85-top)
  for v in o.data.vertices:v.co.z+=raise_by
  o.data.update();bpy.context.view_layer.update();lo,hi=bounds(o)
  cut=lo.y+.075;bottom=raise_by+.075;upper=.85-.035
  left=clip(o,'SM_GP_SinkLeft',[(1,cut,False),(0,-.004,False),(2,bottom,True),(2,upper,False)])
  right=clip(o,'SM_GP_SinkRight',[(1,cut,False),(0,.004,True),(2,bottom,True),(2,upper,False)])
  back=clip(o,'Rear',[(1,cut,True)])
  topmesh=clip(o,'Top',[(1,cut,False),(2,upper,True)])
  kick=clip(o,'Kick',[(1,cut,False),(2,bottom,False)])
  interior=constant('M_GP_SinkInterior',(.55,.53,.45),.75)
  w=hi.x-lo.x;d=hi.y-lo.y
  panels=[box('Cabinet back',(0,hi.y-.018,.45),(w-.04,.018,.75),interior),box('Cabinet base',(0,.015,bottom),(w-.04,d-.1,.018),interior),box('Left lining',(lo.x+.018,.015,.45),(.018,d-.1,.75),interior),box('Right lining',(hi.x-.018,.015,.45),(.018,d-.1,.75),interior),box('Shelf',(0,.015,.42),(w-.04,d-.1,.018),interior)]
  if raise_by>.005:panels.append(box('Plinth',(0,0,raise_by/2),(w-.06,d-.05,raise_by),constant('M_GP_Plinth',(.035,.035,.03))))
  body=join([back,topmesh,kick]+panels,'SM_GP_SinkBody')
  for door,px in [(left,lo.x+.018),(right,hi.x-.018)]:
   backing=box('Door lining',((px)/2,cut-.008,(bottom+upper)/2),(w/2-.03,.016,upper-bottom),interior)
   name=door.name;door=join([door,backing],name);pivot(door,(px,cut,0))
  bpy.data.objects.remove(o,do_unlink=True);body.name='SM_GP_SinkBody';parts=[body,left,right]
  note=f'Uniform width120cm; countertop plane {top:.3f}m; pedestal lift {raise_by:.3f}m. Doors split, interior lining added.'
 if key=='bedding':
  # A correctly sized simple support replaces the old wide occupied-room bed;
  # vacant story-room frames remain untouched.
  wood=constant('M_GP_BedSupport',(.12,.085,.05))
  support=join([box('Deck',(0,0,.28),(.90,1.97,.06),wood)]+[box('Leg',(x,y,.125),(.055,.055,.25),wood) for x in [-.39,.39] for y in [-.90,.90]],'SM_GP_BedSupport')
  activate(support);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
  export(support,support.name,'bed_support')
  support.hide_render=True
 for part in parts:export(part,part.name,key)
 bpy.ops.wm.save_as_mainfile(filepath=str(BASE/key/'prepared.blend'))
 render(parts,BASE/key/'prepared-preview.png')
 if key=='sink':
  left.rotation_euler.z=math.radians(100);right.rotation_euler.z=math.radians(-100)
  render(parts,BASE/key/'open-preview.png')
 reports.append({'name':key,'source_triangles':before,'note':note,'parts':[p.name for p in parts]})
 (OUT/'import.json').write_text(json.dumps(entries,indent=2),encoding='utf-8')
 (BASE/'preparation.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
 print('SIX_PREPARED',key,flush=True)
