"""Reduce the approved Meshy source before rigging, preserving its UV/PBR maps."""
import bpy
import json
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Art/GhostMeshy/Approved'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(OUT / 'textured.glb'))
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
before = sum(len(o.data.polygons) for o in meshes)
for ob in meshes:
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    dec = ob.modifiers.new('GameBudget', 'DECIMATE')
    dec.ratio = min(1.0, 90000 / before)
    dec.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=dec.name)
    for poly in ob.data.polygons:
        poly.use_smooth = True
    ob.select_set(False)
# A 215 cm apparition fits the existing doorways without altering gameplay collision.
points = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
bottom = min(v.z for v in points)
scale = 2.15 / (max(v.z for v in points) - bottom)
for ob in meshes:
    world = ob.matrix_world.copy()
    for v in ob.data.vertices:
        co = world @ v.co
        v.co = (co - Vector((0, 0, bottom))) * scale
    ob.matrix_world.identity()
    ob.select_set(True)
bpy.context.scene.unit_settings.system = 'METRIC'
after = sum(len(o.data.polygons) for o in meshes)
assert after <= 100000, after
bpy.ops.export_scene.gltf(filepath=str(OUT / 'rig-input.glb'), export_format='GLB',
                         use_selection=True, export_animations=False)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'optimized-source.blend'))
(OUT / 'optimization.json').write_text(json.dumps({
    'source_faces': before, 'optimized_faces': after, 'height_m': 2.15,
    'method': 'Blender collapse decimation, existing UV and PBR textures retained',
    'meshy_additional_credits': 0,
}, indent=2), encoding='utf-8')
print('MESHY_OPTIMIZATION_COMPLETE', before, after, flush=True)
