"""Render the actual imported Blender models as a reviewable asset sheet."""
import bpy, math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Art/ThirdParty/PolyHaven/Prepared'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
positions={'Desk':(-1.5,0,0),'Chair':(.4,0,0),'Shelves':(1.6,.2,0),
           'Microwave':(-1.4,-1.2,0),'Kettle':(0,-1.1,0),'Pot':(.7,-1.1,0)}
for key,position in positions.items():
    file=OUT/('SM_PH_'+key+'.blend')
    with bpy.data.libraries.load(str(file),link=False) as (source,target):
        target.objects=[n for n in source.objects if n.startswith('SM_PH_')]
    for obj in target.objects:
        if obj: bpy.context.collection.objects.link(obj);obj.location=position
bpy.ops.mesh.primitive_plane_add(size=200)
floor=bpy.context.object
m=bpy.data.materials.new('Neutral');m.diffuse_color=(.12,.13,.14,1);floor.data.materials.append(m)
for position,power,size in [((0,-3,6),1500,5),((3,3,4),1200,4)]:
    bpy.ops.object.light_add(type='AREA',location=position)
    light=bpy.context.object;light.data.energy=power;light.data.shape='DISK';light.data.size=size
    light.rotation_euler=(Vector((0,0,.7))-light.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(5,-7,4.8))
cam=bpy.context.object;cam.rotation_euler=(Vector((0,-.25,.7))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.type='ORTHO';cam.data.ortho_scale=5.8
scene=bpy.context.scene;scene.camera=cam;scene.render.engine='CYCLES';scene.cycles.samples=32
scene.render.resolution_x=1400;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.world.color=(.16,.16,.16)
scene.render.filepath=str(ROOT/'Art/Previews/cc0-assets.png')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'asset-review.blend'))
bpy.ops.render.render(write_still=True)
