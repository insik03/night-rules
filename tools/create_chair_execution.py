"""Bake chair-drag locomotion and a short one-handed execution on the approved rig."""
import bpy, math, json
from pathlib import Path
from mathutils import Matrix, Vector
R=Path(__file__).resolve().parents[1]; D=R/'Art/GhostMeshy/Approved'; O=D/'Unreal'

def solve_arm(rig,target):
    # Solve in armature space from actual joint heads, not FBX display-bone lengths.
    a,b,c=[rig.pose.bones[n].matrix.translation.copy() for n in ('RightArm','RightForeArm','RightHand')]
    target=rig.matrix_world.inverted()@Vector(target)
    l1,l2=(b-a).length,(c-b).length; direction=(target-a).normalized()
    dist=min((target-a).length,l1+l2-.2); end=a+direction*dist
    along=(l1*l1-l2*l2+dist*dist)/(2*dist)
    pole=Vector((-1,.25,0));pole=(pole-direction*pole.dot(direction)).normalized()
    knee=a+direction*along+pole*math.sqrt(max(0,l1*l1-along*along))
    originals={p.name:p.matrix.copy() for p in rig.pose.bones}
    hand=originals['RightHand'].copy(); hand.translation=end
    targets={}
    for name,old,new,pos in [('RightArm',b-a,knee-a,a),('RightForeArm',c-b,end-knee,knee)]:
        _,q,s=originals[name].decompose(); targets[name]=Matrix.LocRotScale(pos,old.rotation_difference(new)@q,s)
    targets['RightHand']=hand
    for p in rig.pose.bones:
        if p.name in targets:p.matrix=targets[p.name];bpy.context.view_layer.update()
    # Curl fingers around the chair back. Keep wrists stable instead of waving.
    for p in rig.pose.bones:
        if p.name.startswith('RightHand') and p.name!='RightHand':
            p.rotation_mode='XYZ';p.rotation_euler.x+=.35
    bpy.context.view_layer.update()

def bake(name,execution=False):
    bpy.ops.wm.open_mainfile(filepath=str(D/'A_CaretakerRun.blend'))
    rig=bpy.data.objects['Armature'];body=bpy.data.objects['SK_SmilingCaretaker'];scene=bpy.context.scene
    samples=[]
    for f in range(1,21):
        scene.frame_set(f);samples.append({p.name:p.matrix_basis.copy() for p in rig.pose.bones})
    rig.animation_data_clear();rig.animation_data_create();rig.animation_data.action=bpy.data.actions.new(name)
    scene.frame_start=1;scene.frame_end=85 if execution else 20;scene.render.fps=30
    handpositions=[]
    for f in range(1,scene.frame_end+1):
        scene.frame_set(f);t=(f-1)/30
        for p in rig.pose.bones:p.matrix_basis=samples[(f-1)%20][p.name] if not execution else Matrix.Identity(4)
        bpy.context.view_layer.update()
        if execution:
            # Drag/hold .0-.55; lift .55-1.5; ominous hold 1.5-1.72; strike 1.72-1.94.
            keys=[(0,(-.34,.25,1.02)),(.55,(-.34,.25,1.02)),(1.5,(-.32,.02,2.22)),(1.72,(-.32,.02,2.22)),(1.94,(-.18,-.59,1.23)),(2.8,(-.18,-.59,1.23))]
            for (ta,pa),(tb,pb) in zip(keys,keys[1:]):
                if ta<=t<=tb:
                    u=(t-ta)/(tb-ta);u=u*u*(3-2*u);hand=Vector(pa).lerp(Vector(pb),u);break
        else:hand=Vector((-.34,.25,1.02+.015*math.sin((f-1)/19*math.tau)))
        solve_arm(rig,hand)
        for p in rig.pose.bones:
            p.rotation_mode='QUATERNION'
            for prop in ('location','rotation_quaternion','scale'):p.keyframe_insert(data_path=prop,frame=f)
        handpositions.append(list(rig.matrix_world@rig.pose.bones['RightHand'].matrix.translation))
    scene.frame_set(1)
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);body.select_set(True);bpy.context.view_layer.objects.active=rig
    bpy.ops.export_scene.fbx(filepath=str(O/(name+'.fbx')),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,axis_forward='-Y',axis_up='Z',bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0)
    bpy.ops.wm.save_as_mainfile(filepath=str(D/(name+'.blend')))
    return {'frames':scene.frame_end,'fps':30,'hand_positions_m':handpositions}

report={name:bake(name,execution) for name,execution in [('A_CaretakerChairRun',False),('A_CaretakerChairKill',True)]}
(D/'chair-motion.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('CHAIR_MOTION_COMPLETE',flush=True)
