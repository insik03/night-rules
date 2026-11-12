"""Render the actual edited rig and measure animation/ground contact in Blender."""
import bpy
import json
import sys
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Art/GhostMeshy/Approved'
bpy.ops.wm.open_mainfile(filepath=str(OUT / 'A_CaretakerRun.blend'))
scene = bpy.context.scene
rig = bpy.data.objects['Armature']
body = bpy.data.objects['SK_SmilingCaretaker']
samples = []
for frame in range(scene.frame_start, scene.frame_end+1):
    scene.frame_set(frame)
    evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    bottom = min((evaluated.matrix_world @ v.co).z for v in mesh.vertices)
    top = max((evaluated.matrix_world @ v.co).z for v in mesh.vertices)
    evaluated.to_mesh_clear()
    samples.append({'frame': frame, 'bottom_m': bottom, 'top_m': top,
        'left_foot': list(rig.matrix_world @ rig.pose.bones['LeftFoot'].head),
        'right_foot': list(rig.matrix_world @ rig.pose.bones['RightFoot'].head)})
velocities = []
for key in ('left_foot', 'right_foot'):
    lowest = min(s[key][2] for s in samples)
    for a, b in zip(samples[:-2], samples[1:-1]):
        if a[key][2] < lowest+.05 and b[key][2] < lowest+.05:
            velocity = (b[key][1]-a[key][1])*scene.render.fps
            if velocity > .5:
                velocities.append(velocity)
velocities.sort()
speed = velocities[len(velocities)//2] if velocities else None
report = {'frames': samples, 'estimated_stance_speed_mps': speed,
    'minimum_foot_height_m': min(s['bottom_m'] for s in samples),
    'maximum_foot_height_m': max(s['bottom_m'] for s in samples)}
(OUT/'motion-inspection.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('MESHY_MOTION_CHECK', {k:v for k,v in report.items() if k!='frames'}, flush=True)

scene.render.engine = 'CYCLES'
scene.cycles.samples = 24
scene.render.resolution_x = 720
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.world = scene.world or bpy.data.worlds.new('PreviewWorld')
scene.world.color = (.12,.12,.12)
scene.view_settings.view_transform = 'AgX'
bpy.ops.object.camera_add(location=(3.2,-5,2.4))
camera = bpy.context.object
camera.rotation_euler = (Vector((0,0,1.1))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 2.75
scene.camera = camera
for location, energy, size in [((1,-3,4),350,3),((-3,-1,2),200,3),((0,3,3),250,2)]:
    bpy.ops.object.light_add(type='AREA', location=location)
    light=bpy.context.object
    light.data.energy=energy
    light.data.shape='DISK'
    light.data.size=size
    light.rotation_euler=(Vector((0,0,1))-light.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.mesh.primitive_plane_add(size=200)
floor=bpy.context.object
mat=bpy.data.materials.new('PreviewFloor')
mat.diffuse_color=(.08,.08,.08,1)
floor.data.materials.append(mat)
frames = range(scene.frame_start, scene.frame_end) if '--animation' in sys.argv else (4,12)
if '--animation' in sys.argv:
    scene.cycles.samples = 8
    scene.render.resolution_x, scene.render.resolution_y = 480, 600
    (ROOT / 'tools/output/meshy-run-frames').mkdir(exist_ok=True)
for frame in frames:
    scene.frame_set(frame)
    scene.render.filepath=str((ROOT/'tools/output/meshy-run-frames'/f'{frame:03d}.png') if '--animation' in sys.argv else OUT/f'run-pose-{frame:02d}.png')
    bpy.ops.render.render(write_still=True)
