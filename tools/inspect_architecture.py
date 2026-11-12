import bpy, json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]/'Art/EnvironmentMeshy/v1'
out=[]
for p in sorted((root/'models').glob('*/source.glb')):
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.gltf(filepath=str(p))
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  points=[o.matrix_world@Vector(v) for v in o.bound_box]
  out.append({'id':p.parent.name,'name':o.name,'bounds':[[min(v[i] for v in points) for i in range(3)],[max(v[i] for v in points) for i in range(3)]],'faces':len(o.data.polygons),'rotation':list(o.rotation_euler)})
(root/'source-inspection.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out))
