import bpy
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'Art/EnvironmentMeshy/v1'
bpy.ops.wm.open_mainfile(filepath=str(BASE/'architecture-modules.blend'))
def render(parts,path):
 for o in bpy.context.scene.objects:
  if o.type=='MESH':o.hide_render=o not in parts
 points=[o.matrix_world@Vector(v) for o in parts for v in o.bound_box]
 lo=Vector([min(v[i] for v in points) for i in range(3)]);hi=Vector([max(v[i] for v in points) for i in range(3)])
 center=(lo+hi)/2;extent=max(hi-lo)
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16
 scene.render.resolution_x=720;scene.render.resolution_y=720;scene.render.resolution_percentage=100
 scene.world=bpy.data.worlds.new('Studio');scene.world.use_nodes=True
 bg=scene.world.node_tree.nodes.new('ShaderNodeBackground');bg.inputs[0].default_value=(.45,.45,.45,1)
 output=scene.world.node_tree.nodes.new('ShaderNodeOutputWorld');scene.world.node_tree.links.new(bg.outputs[0],output.inputs[0])
 bpy.ops.object.camera_add(location=center+Vector((1.8,-3,1.6))*extent);cam=bpy.context.object;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=extent*1.52;scene.camera=cam
 lamps=[]
 for loc,energy,size in [((1,-3,4),350,3),((-3,-1,2),180,2)]:
  bpy.ops.object.light_add(type='AREA',location=center+Vector(loc)*extent);l=bpy.context.object;l.data.energy=energy*extent**2;l.data.shape='DISK';l.data.size=size*extent;l.rotation_euler=(center-l.location).to_track_quat('-Z','Y').to_euler();lamps.append(l)
 scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 for o in lamps+[cam]:bpy.data.objects.remove(o,do_unlink=True)


for name in ['SM_AM_DoorWall','SM_AM_WindowWall','SM_AM_TileWall']:
 o=bpy.data.objects.get(name);o.hide_viewport=False;o.hide_render=False
 render([o],BASE/(name+'-prepared.png'))
