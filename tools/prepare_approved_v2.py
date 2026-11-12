"""Prepare approved Tripo assets, retain originals and measure final geometry."""
import bpy,bmesh,json,math,os,sys
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(sys.argv[sys.argv.index('--')+1])
BASE=ROOT/'Art/GeneratedProps/approved-v2'
OUT=BASE/'Unreal';OUT.mkdir(parents=True,exist_ok=True)
entries=[]
helper=(ROOT/'tools/prepare_core_props.py').read_text('utf-8')
exec(helper[helper.index('def activate('):helper.index('for source in sorted(')])
reports=[]
for ident,budget in [('toolbox',16000),('exterior',80000)]:
 source=BASE/'models'/ident/'source.glb'
 if not source.exists():continue
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.gltf(filepath=str(source))
 obj=join([o for o in bpy.context.scene.objects if o.type=='MESH'],'SM_AP_'+ident.title())
 activate(obj);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 lo,hi=bounds(obj);initial=list(hi-lo)
 before=sum(len(f.vertices)-2 for f in obj.data.polygons)
 bm=bmesh.new();bm.from_mesh(obj.data)
 bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
 if before>budget:
  mod=obj.modifiers.new('Runtime reduction','DECIMATE');mod.ratio=budget/before;mod.use_collapse_triangulate=True
  bpy.ops.object.modifier_apply(modifier=mod.name)
 lo,hi=bounds(obj);center=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z))
 factor=(.5 if ident=='toolbox' else 44.0)/(hi.x-lo.x)
 for v in obj.data.vertices:v.co=(v.co-center)*factor
 obj.data.update();bpy.context.view_layer.update()
 if ident=='toolbox':
  # Extend only the plain sheet-metal side band. Lid, latches, handle and feet
  # move rigidly; never distort the complete object with nonuniform scale.
  lo,hi=bounds(obj);extra=.32-hi.z
  for v in obj.data.vertices:
   z=v.co.z;v.co.z+=extra*max(0,min(1,(z-.04)/.10))
  obj.data.update();bpy.context.view_layer.update()
 for i,m in enumerate(obj.data.materials):m.name='M_AP_'+ident.title()+'_'+str(i)
 lo,hi=bounds(obj)
 report={'id':ident,'source_dimensions_m':initial,'source_triangles':before,'triangles':sum(len(p.vertices)-2 for p in obj.data.polygons),'uniform_factor':factor,'dimensions_cm':[round(x*100,3) for x in hi-lo],'runtime_ready':ident=='toolbox','note':'Plain side band height extended; hardware translated rigidly.' if ident=='toolbox' else 'Reference only: AI window positions and roof must be reconciled before integration.'}
 if ident=='toolbox':
  assert abs((hi.x-lo.x)*100-50)<.1 and abs((hi.z-lo.z)*100-32)<.1
  assert abs((hi.y-lo.y)*100-30)<.2,report
  export(obj,obj.name,'APToolbox')
 bpy.ops.wm.save_as_mainfile(filepath=str(source.parent/'prepared.blend'))
 render([obj],source.parent/'prepared-preview.png')
 reports.append(report);print('APPROVED_PREPARED',json.dumps(report),flush=True)
(OUT/'import.json').write_text(json.dumps(entries,indent=2),encoding='utf-8')
(BASE/'preparation.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
