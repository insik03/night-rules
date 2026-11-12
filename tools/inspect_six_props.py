"""Read-only GLB shape audit in Blender. Does not resize or export meshes."""
import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]/'Art/GeneratedProps/six-v1'
result=[]
for name in ['chair','bedding','sink','shower','slippers','books']:
    source=root/name/'model.glb'
    if not source.exists():continue
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    pts=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
    lo=[min(p[i] for p in pts) for i in range(3)]
    hi=[max(p[i] for p in pts) for i in range(3)]
    dims=[hi[i]-lo[i] for i in range(3)]
    tris=0
    for o in meshes:
        o.data.calc_loop_triangles();tris+=len(o.data.loop_triangles)
    result.append(dict(name=name,objects=len(meshes),triangles=tris,raw_xyz=dims,
      normalized_xyz=[v/max(dims) for v in dims],
      note='Raw world AABB after glTF axis conversion; arbitrary generated units. No physical cm size or orientation guarantee. No scaling applied.'))
(root/'geometry-audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('GEOMETRY_AUDIT '+json.dumps(result))
