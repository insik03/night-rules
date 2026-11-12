"""Run with Blender --background --python tools/create_assets.py.
Creates original placeholder meshes, FBX exports and an asset-sheet preview.
All generated files stay in Art/Generated; no third-party assets are used.
"""
from pathlib import Path
import bpy
import math

OUT = Path(__file__).resolve().parent.parent / 'Art' / 'Generated'
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1

def mat(name, color):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = .8
    return m

wood = mat('Worn wood', (.2,.12,.06))
plastic = mat('Old grey plastic', (.15,.17,.16))
metal = mat('Dull metal', (.28,.3,.29))
purple = mat('UV cartridge', (.3,.08,.5))
cream = mat('Cream receiver', (.5,.48,.36))

def box(name, xyz, size, material):
    bpy.ops.mesh.primitive_cube_add(size=1, location=xyz)
    o = bpy.context.object
    o.name = name
    o.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(material)
    bevel=o.modifiers.new('Rounded edges', 'BEVEL'); bevel.width=.003; bevel.segments=2
    bpy.context.view_layer.objects.active=o
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    return o

def export(name, parts):
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts: p.select_set(True)
    bpy.context.view_layer.objects.active=parts[0]
    bpy.ops.object.join()
    o=bpy.context.object; o.name=name
    scene.cursor.location=(0,0,0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')), use_selection=True,
        object_types={'MESH'}, axis_forward='-Y', axis_up='Z', apply_unit_scale=True,
        bake_anim=False, add_leaf_bones=False)
    return o

phone=export('SM_Phone',[
    box('Base',(0,0,.035),(.35,.24,.07),plastic),
    box('Receiver',(0,.065,.105),(.32,.07,.07),cream),
    *[box('Key',(x,y,.075),(.03,.025,.01),metal) for x in [-.05,0,.05] for y in [-.07,-.03,.01]],
])
cartridge=export('SM_Cartridge',[
    box('Body',(0,0,.035),(.18,.08,.07),purple),
    box('Connector',(.1,0,.035),(.035,.05,.04),metal),
])
chair=export('SM_Chair',[
    box('Seat',(0,0,.42),(.45,.45,.05),wood),
    box('Back',(0,.205,.68),(.45,.04,.5),wood),
    *[box('Leg',(x,y,.2),(.035,.035,.4),metal) for x in [-.19,.19] for y in [-.19,.19]],
])
desk=export('SM_Desk',[
    box('Top',(0,0,.735),(1.8,.65,.05),wood),
    *[box('Leg',(x,y,.36),(.06,.06,.72),metal) for x in [-.83,.83] for y in [-.26,.26]],
])
flashlight=export('SM_Flashlight',[
    box('Handle',(0,0,.04),(.22,.065,.07),plastic),
    box('Head',(.14,0,.04),(.08,.09,.09),metal),
])
door=export('SM_Door',[
    box('Panel',(.575,0,1.05),(1.15,.05,2.1),wood),
    box('Handle',(1.03,-.055,1),(.1,.06,.035),metal),
])
# Asset sheet layout is only for inspection; exports above keep local origin.
for o,at in [(desk,(0,0,0)),(phone,(0,0,.77)),(cartridge,(-.6,0,.77)),
             (flashlight,(.6,0,.77)),(chair,(0,-1.1,0)),(door,(-1.6,.7,0))]: o.location=at
box('Preview floor',(0,0,-.035),(6,5,.06),mat('Floor',(.09,.1,.09)))
bpy.ops.object.light_add(type='AREA',location=(1,-1,4))
bpy.context.object.data.energy=700; bpy.context.object.data.shape='DISK'; bpy.context.object.data.size=4
bpy.ops.object.camera_add(location=(3.5,-4.5,3))
camera=bpy.context.object
from mathutils import Vector
camera.rotation_euler=(Vector((0,0,.8))-camera.location).to_track_quat('-Z','Y').to_euler()
scene.camera=camera; scene.render.engine='CYCLES'; scene.cycles.samples=24
scene.render.resolution_x=1100; scene.render.resolution_y=800; scene.render.resolution_percentage=100
scene.world.color=(.12,.12,.12)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'haedam_props.blend'))
scene.render.filepath=str(OUT/'asset_preview.png')
bpy.ops.render.render(write_still=True)
print('ASSETS_OK', OUT)
