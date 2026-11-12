"""Inspect and render the downloaded protagonist without changing the source GLBs."""
import bpy
import json
import sys
from pathlib import Path
from mathutils import Vector

root = Path(__file__).resolve().parents[1]
args = sys.argv[sys.argv.index('--') + 1:]
filename = args[0]
out = root / (args[1] if len(args) > 1 else 'Art/Characters/Protagonist-v1')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(out / filename))
scene = bpy.context.scene
meshes = [o for o in scene.objects if o.type == 'MESH']
body_meshes = [o for o in meshes if len(o.data.materials)]
rigs = [o for o in scene.objects if o.type == 'ARMATURE']
report = {
    'source': filename,
    'triangles': sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes),
    'body_triangles': sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in body_meshes),
    'bones': [len(r.data.bones) for r in rigs],
    'actions': [{'name': a.name, 'frames': list(a.frame_range)} for a in bpy.data.actions],
    'textures': [{'name': i.name, 'size': list(i.size)} for i in bpy.data.images],
}
points = [o.matrix_world @ Vector(v) for o in body_meshes for v in o.bound_box]
lo = Vector([min(v[i] for v in points) for i in range(3)])
hi = Vector([max(v[i] for v in points) for i in range(3)])
report['bounds_m'] = {'min': list(lo), 'max': list(hi)}
stem = Path(filename).stem
(out / (stem + '-inspection.json')).write_text(json.dumps(report, indent=2), encoding='utf-8')
print('PROTAGONIST_INSPECTION', json.dumps(report), flush=True)
height = hi.z-lo.z
center = (hi+lo)/2
scene.render.engine = 'CYCLES'
scene.cycles.samples = 20
scene.render.resolution_x, scene.render.resolution_y = 600, 800
scene.render.resolution_percentage = 100
scene.world = bpy.data.worlds.new('PreviewWorld')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.16,.16,.16,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .65
scene.view_settings.view_transform = 'AgX'
bpy.ops.object.camera_add(location=center+Vector((height*.28,-height*2,height*.15)))
camera = bpy.context.object
camera.rotation_euler = (center-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type = 'ORTHO'
camera.data.ortho_scale = height*1.22
scene.camera = camera
for offset, power in [((1,-2,2),170),((-2,-1,1),90),((0,2,2),130)]:
    bpy.ops.object.light_add(type='AREA', location=center+Vector(offset)*height)
    light=bpy.context.object
    light.data.energy=power*height*height
    light.data.size=height*1.5
    light.rotation_euler=(center-light.location).to_track_quat('-Z','Y').to_euler()
if report['actions']:
    start, end = report['actions'][0]['frames']
    frames = [int(start+(end-start)*t) for t in (.15,.4,.65)]
else:
    frames = [0]
for frame in frames:
    scene.frame_set(frame)
    scene.render.filepath=str(out / f'{stem}-frame-{frame:03d}.png')
    bpy.ops.render.render(write_still=True)
if '--details' in args:
    scene.render.resolution_x = 900
    scene.render.resolution_y = 1100
    scene.cycles.samples = 32
    for label, offset, target, scale in [
        ('face', (.08,-1,.86), (0,0,.86), .30),
        ('back', (.20,2,.65), (0,0,.50), 1.22),
    ]:
        aim = Vector((center.x, center.y, lo.z)) + Vector(target)*height
        camera.location = Vector((center.x,center.y,lo.z)) + Vector(offset)*height
        camera.rotation_euler = (aim-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.data.ortho_scale = height*scale
        scene.render.filepath = str(out / f'{stem}-{label}.png')
        bpy.ops.render.render(write_still=True)
