import bpy, json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Art/CoreProps/v1'
report=[]
for source in sorted((OUT/'models').glob('*/source.glb')):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
    points=[o.matrix_world@Vector(v) for o in objects for v in o.bound_box]
    lo=Vector([min(v[i] for v in points) for i in range(3)])
    hi=Vector([max(v[i] for v in points) for i in range(3)])
    report.append({'id':source.parent.name,'lo':list(lo),'hi':list(hi),'triangles':sum(len(o.data.polygons) for o in objects)})
    if not source.parent.name.startswith('O01'): continue
    scene=bpy.context.scene; scene.render.engine='CYCLES'; scene.cycles.samples=12
    scene.render.resolution_x=700;scene.render.resolution_y=500;scene.render.resolution_percentage=100
    scene.world=bpy.data.worlds.new('Studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.5,.5,.5,1)
    target=(lo+hi)/2
    for sign in (-1,1):
        bpy.ops.object.camera_add(location=target+Vector((2.7,sign*4,2)))
        cam=bpy.context.object;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=2.6;scene.camera=cam
        bpy.ops.object.light_add(type='AREA',location=target+Vector((1,sign*3,4)))
        light=bpy.context.object;light.data.energy=500;light.data.shape='DISK';light.data.size=4;light.rotation_euler=(target-light.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(OUT/f'desk-orientation-{sign}.png');bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(cam,do_unlink=True);bpy.data.objects.remove(light,do_unlink=True)
(OUT/'source-geometry.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
