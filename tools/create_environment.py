"""Original environment props, authored with Blender mesh operations."""
exec(compile((__import__('pathlib').Path(__file__).parent/'create_assets.py').read_text(encoding='utf-8').split('# Asset sheet layout')[0], 'create_assets.py', 'exec'))
screen=mat('Dark screen',(.012,.035,.027))
light=mat('Fluorescent diffuser',(.72,.78,.65))
p=light.node_tree.nodes.get('Principled BSDF'); p.inputs['Emission Color'].default_value=(.65,.75,.55,1); p.inputs['Emission Strength'].default_value=2
monitor=export('SM_Monitor',[
 box('CRT housing',(0,.06,.23),(.43,.32,.34),plastic),
 box('Glass',(0,-.107,.23),(.35,.012,.25),screen),
 box('Foot',(0,.03,.035),(.29,.22,.07),plastic),
 box('Power button',(.16,-.12,.065),(.018,.012,.018),cream),
 *[box('Vent',(.216,.015+i*.027,.23),(.003,.013,.20),metal) for i in range(7)],
])
fixture=export('SM_Fluorescent',[
 box('Tray',(0,0,-.025),(.95,.22,.05),plastic),
 *[box('Diffuser',(0,y,-.06),(.83,.045,.035),light) for y in [-.055,.055]],
 *[box('End',(x,0,-.065),(.035,.20,.035),cream) for x in [-.43,.43]],
])
for o,at in [(desk,(0,0,0)),(phone,(-.5,0,.77)),(monitor,(.4,0,.77)),(chair,(0,-1.1,0)),(door,(-1.6,.7,0)),(fixture,(0,0,2.5)),(cartridge,(-.7,-.1,.77)),(flashlight,(.7,-.1,.77))]:o.location=at
box('Preview floor',(0,0,-.035),(6,5,.06),mat('Floor',(.12,.14,.12)))
bpy.ops.object.light_add(type='AREA',location=(1,-1,4));bpy.context.object.data.energy=700;bpy.context.object.data.size=4
bpy.ops.object.camera_add(location=(3.5,-4.5,3))
from mathutils import Vector
camera=bpy.context.object;camera.rotation_euler=(Vector((0,0,1))-camera.location).to_track_quat('-Z','Y').to_euler();scene.camera=camera
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.render.resolution_x=1100;scene.render.resolution_y=800;scene.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'haedam_environment.blend'))
scene.render.filepath=str(OUT/'environment_preview.png');bpy.ops.render.render(write_still=True)
