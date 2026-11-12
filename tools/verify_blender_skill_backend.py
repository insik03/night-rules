"""Isolated Blender CLI smoke check: final cm dimensions + FBX round trip.
Never opens/modifies production assets. Run with --background --factory-startup.
"""
import bpy, json, math
from pathlib import Path
from mathutils import Vector
root = Path(__file__).resolve().parents[1]
out = root / 'tools' / 'output' / 'skill-backend-check'
out.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.scale_length = 1.0
expected = [42.0,44.0,80.0]
verts=[(x*.21,y*.22,z*.40) for x,y,z in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
faces=[(0,2,6,4),(1,5,7,3),(0,4,5,1),(2,3,7,6),(0,1,3,2),(4,6,7,5)]
mesh=bpy.data.meshes.new('SkillCheckMesh');mesh.from_pydata(verts,[],faces);mesh.update()
obj=bpy.data.objects.new('SM_SkillCheck',mesh);bpy.context.collection.objects.link(obj)
obj.select_set(True);bpy.context.view_layer.objects.active=obj;bpy.context.view_layer.update()
def measure(o):
    dg=bpy.context.evaluated_depsgraph_get();eo=o.evaluated_get(dg)
    pts=[eo.matrix_world @ Vector(c) for c in eo.bound_box]
    return [(max(p[a] for p in pts)-min(p[a] for p in pts))*100 for a in range(3)]
before=measure(obj)
assert all(abs(a-b)<=.1 for a,b in zip(before,expected)), before
assert all(abs(s-1)<1e-6 for s in obj.scale)
fbx=out/'SM_SkillCheck.fbx'
bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'MESH'},global_scale=1.0,apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Y',axis_up='Z',add_leaf_bones=False,bake_anim=False)
bpy.data.objects.remove(obj,do_unlink=True)
bpy.ops.import_scene.fbx(filepath=str(fbx),use_anim=False)
restored=[o for o in bpy.context.scene.objects if o.type=='MESH']
assert len(restored)==1
bpy.context.view_layer.update();after=measure(restored[0])
passed=all(math.isfinite(v) and abs(v-e)<=.1 for v,e in zip(after,expected))
report={'blender':bpy.app.version_string,'backend':'local-background-python','test':'isolated box / FBX round trip','expected_cm':expected,'before_cm':before,'after_cm':after,'passed':passed,'unreal_import_tested':False,'paid_generations':0}
(out/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=True))
assert passed, report
