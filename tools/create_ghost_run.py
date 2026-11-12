"""Author a separate 0.6-second pursuit run on the existing local ghost rig."""
import bpy,math
from pathlib import Path
R=Path(__file__).resolve().parents[1]; O=R/'Art/Ghost'
bpy.ops.wm.open_mainfile(filepath=str(O/'haedam_ghost.blend'))
rig=bpy.data.objects['HaedamGhostRig'];body=bpy.data.objects['SK_ErasedGhost'];rig.animation_data_clear()
sc=bpy.context.scene;sc.render.fps=30;sc.frame_start=1;sc.frame_end=19
for f in range(1,20):
 phase=(f-1)/18*2*math.pi
 for b in rig.pose.bones:b.rotation_mode='XYZ';b.rotation_euler=(0,0,0);b.location=(0,0,0)
 rig.pose.bones['spine'].rotation_euler[0]=.22
 rig.pose.bones['head'].rotation_euler[0]=-.18
 rig.pose.bones['head'].rotation_euler[1]=.12+.045*math.sin(phase)
 for side,offset in [('l',0),('r',math.pi)]:
  s=math.sin(phase+offset)
  rig.pose.bones['thigh_'+side].rotation_euler[0]=.78*s
  rig.pose.bones['calf_'+side].rotation_euler[0]=-1.15*max(0,-s)-.12
  rig.pose.bones['foot_'+side].rotation_euler[0]=.18*max(0,s)
  rig.pose.bones['upperarm_'+side].rotation_euler[2]=(.45 if side=='l' else -.45)
  rig.pose.bones['upperarm_'+side].rotation_euler[0]=-.5*s
  rig.pose.bones['forearm_'+side].rotation_euler[0]=-.95
 bpy.context.view_layer.update()
 evaluated=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh()
 lowest=min((evaluated.matrix_world@v.co).z for v in mesh.vertices);evaluated.to_mesh_clear()
 rig.pose.bones['root'].location.z=.008-lowest+.025*abs(math.sin(phase*2))
 for b in rig.pose.bones:
  b.keyframe_insert(data_path='rotation_euler',frame=f,group=b.name)
  b.keyframe_insert(data_path='location',frame=f,group=b.name)
rig.animation_data.action.name='GhostRun';sc.frame_set(1)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);body.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(O/'A_GhostRun.fbx'),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,axis_forward='-Y',axis_up='Z',bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0)
bpy.ops.wm.save_as_mainfile(filepath=str(O/'haedam_ghost_run.blend'))
print('GHOST_RUN_COMPLETE',flush=True)
