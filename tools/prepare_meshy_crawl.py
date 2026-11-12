"""Bake Meshy's Crawl_and_Look_Back (action 340, task 01a1a174) into a UE FBX clip.

Run: blender -b -P tools/prepare_meshy_crawl.py
Keeps Meshy's motion as-is (root motion included: the ghost actor stays put and the body
crawls forward from it). Writes measurements and preview renders for review.
"""
import bpy, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'Art/GhostMeshy/Approved'
OUT = SOURCE / 'Unreal'

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SOURCE / 'crawl.glb'))
rig = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
body = max((o for o in bpy.context.scene.objects if o.type == 'MESH'), key=lambda o: len(o.data.polygons))
for ob in list(bpy.context.scene.objects):
    if ob not in (rig, body): bpy.data.objects.remove(ob, do_unlink=True)
rig.name = 'Armature'; body.name = 'SK_SmilingCaretaker'
scene = bpy.context.scene
action = rig.animation_data.action
start, end = [int(v) for v in action.frame_range]
scene.frame_start, scene.frame_end = start, end

hips, lows, depsgraph = [], [], bpy.context.evaluated_depsgraph_get()
for f in range(start, end + 1, 3):
    scene.frame_set(f)
    hips.append(list(rig.matrix_world @ rig.pose.bones['Hips'].head))
    mesh = body.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
    lows.append(min((body.matrix_world @ v.co).z for v in mesh.vertices))
    body.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear()

bpy.ops.object.select_all(action='DESELECT'); rig.select_set(True); body.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.fbx(filepath=str(OUT / 'A_CaretakerCrawl.fbx'), use_selection=True,
    object_types={'MESH', 'ARMATURE'}, add_leaf_bones=False, axis_forward='-Y', axis_up='Z',
    bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
    bake_anim_simplify_factor=0, path_mode='AUTO')

# Review renders: side view at a few frames.
cam_data = bpy.data.cameras.new('Cam'); cam = bpy.data.objects.new('Cam', cam_data); scene.collection.objects.link(cam)
cam.location = (4.2, 0, 1.0); cam.rotation_euler = (1.45, 0, 1.5708); scene.camera = cam
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.rotation_euler = (.8, .2, .6); scene.collection.objects.link(sun)
scene.render.engine = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else scene.render.engine
scene.render.resolution_x, scene.render.resolution_y = 480, 320
shots = []
for k in range(4):
    f = start + (end - start) * k // 3; scene.frame_set(f)
    h = rig.matrix_world @ rig.pose.bones['Hips'].head; cam.location = (h.x + 3.6, h.y, .9)
    p = SOURCE / f'crawl-pose-{k}.png'; scene.render.filepath = str(p); bpy.ops.render.render(write_still=True); shots.append(p.name)

report = {'source_task': '01a1a174-d129-76de-83f3-9d2386e6049b', 'action_id': 340, 'consumed_credits': 3,
          'frames': [start, end], 'fps': scene.render.fps, 'duration_s': (end - start) / scene.render.fps,
          'hips_start_m': hips[0], 'hips_end_m': hips[-1], 'hips_max_z_m': max(h[2] for h in hips),
          'lowest_surface_m': [round(min(lows), 4), round(max(lows), 4)], 'renders': shots}
(SOURCE / 'crawl-inspection.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('CRAWL_PREP_COMPLETE', json.dumps(report))
