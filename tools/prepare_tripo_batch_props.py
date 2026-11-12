"""Optimize the three paid Studio outputs, retaining originals and uniform proportions."""
import bpy, json, math
from pathlib import Path
from mathutils import Vector, Matrix
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'Art/GeneratedProps/tripo-studio-batch-2026-11-09'
OUT=BASE/'Unreal';OUT.mkdir(exist_ok=True)
# Reuse the resident exporter's read-only geometry/material/render helpers only.
source=(ROOT/'tools/prepare_residents_tripo.py').read_text(encoding='utf-8')
scope={'__file__':str(ROOT/'tools/prepare_residents_tripo.py')}
exec(source.split("for item in CONFIG['residents']:")[0],scope)
bounds=scope['bounds'];image_upstream=scope['image_upstream'];render=scope['render']
rows=[('toilet','SM_TS_Toilet',[42,70,75],18000),('washbasin','SM_TS_Washbasin',[55,60,85],18000),('rice-cooker','SM_TS_RiceCooker',[38,32,32],12000)]
reports=[]
for slug,name,target,budget in rows:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(BASE/'models'/slug/'source.glb'))
    bodies=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.data.materials]
    bpy.ops.object.select_all(action='DESELECT')
    for o in bodies:o.select_set(True)
    bpy.context.view_layer.objects.active=bodies[0];bpy.ops.object.join();body=bpy.context.object
    mw=body.matrix_world.copy();body.parent=None;body.matrix_world=mw
    for o in list(bpy.context.scene.objects):
        if o!=body:bpy.data.objects.remove(o,do_unlink=True)
    body.name=name;bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    original=sum(len(p.vertices)-2 for p in body.data.polygons)
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.remove_doubles(threshold=.000005);bpy.ops.object.mode_set(mode='OBJECT')
    mod=body.modifiers.new('GameBudget','DECIMATE');mod.ratio=min(1,budget/max(1,sum(len(p.vertices)-2 for p in body.data.polygons)))
    bpy.ops.object.modifier_apply(modifier=mod.name)
    lo,hi=bounds(body);factor=target[2]/100/(hi.z-lo.z)
    body.scale=Vector((factor,)*3);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    lo,hi=bounds(body);body.location-=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z))
    bpy.ops.object.transform_apply(location=True,rotation=False,scale=False);bpy.context.view_layer.update()
    lo,hi=bounds(body);dims=list((hi-lo)*100)
    materials=[]
    for index,mat in enumerate(body.data.materials):
        bsdf=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
        if not bsdf:continue
        maps={}
        for kind,socket in [('BaseColor','Base Color'),('Normal','Normal'),('ORM','Roughness')]:
            image=image_upstream(bsdf.inputs[socket])
            if image:
                ratio=min(1,2048/max(image.size));image.scale(round(image.size[0]*ratio),round(image.size[1]*ratio))
                tex='T_TS_'+slug.replace('-','_')+'_'+str(index)+'_'+kind
                image.filepath_raw=str(OUT/(tex+'.png'));image.file_format='PNG';image.save();maps[kind]=tex
        materials.append({'slot':index,'maps':maps})
    bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
    bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',bake_anim=False,path_mode='AUTO')
    folder=BASE/'models'/slug;bpy.ops.wm.save_as_mainfile(filepath=str(folder/'prepared.blend'))
    bpy.ops.export_scene.gltf(filepath=str(folder/'preview.glb'),export_format='GLB',use_selection=True,export_animations=False)
    row={'id':slug,'mesh':name,'target_cm':target,'actual_cm':dims,'uniform_scale':factor,'original_triangles':original,'triangles':sum(len(p.vertices)-2 for p in body.data.polygons),'materials':materials,'placement_status':'review required; existing sanitary fixtures not replaced','dimension_delta_cm':[dims[i]-target[i] for i in range(3)]}
    reports.append(row);(BASE/'prepared-props.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
    render(body,folder/'render.png',target[2]/100)
    print('PROP_PREPARED '+json.dumps({k:row[k] for k in ['id','actual_cm','triangles']}),flush=True)
