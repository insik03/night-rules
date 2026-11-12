"""Prepare the approved rig, in-place locomotion and crouch poses for Unreal."""
import bpy, json, math
from pathlib import Path
from mathutils import Matrix, Vector
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'Art/Characters/Protagonist-v2'
OUT=SOURCE/'Unreal'
OUT.mkdir(exist_ok=True)

def load(file):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(SOURCE/file))
    rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
    body=max((o for o in bpy.context.scene.objects if o.type=='MESH'),key=lambda o:len(o.data.polygons))
    for o in list(bpy.context.scene.objects):
        if o not in (rig,body): bpy.data.objects.remove(o,do_unlink=True)
    rig.name='Armature';body.name='SK_Protagonist'
    bpy.context.scene.unit_settings.system='METRIC'
    return rig,body

def export(name,rig,body,animation):
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);body.select_set(True)
    bpy.context.view_layer.objects.active=rig
    bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,
        object_types={'MESH','ARMATURE'},add_leaf_bones=False,axis_forward='-Y',axis_up='Z',
        bake_anim=animation,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,
        bake_anim_simplify_factor=0,path_mode='AUTO')

def ik_leg(target,side,end):
    upper,lower,foot,toe=[side+s for s in ('UpLeg','Leg','Foot','ToeBase')]
    a,b,c=[target[n].translation.copy() for n in (upper,lower,foot)]
    l1,l2=(b-a).length,(c-b).length
    direction=(end-a).normalized();distance=min((end-a).length,l1+l2-.0001)
    end=a+direction*distance
    along=(l1*l1-l2*l2+distance*distance)/(2*distance)
    pole=Vector((0,-1,0));pole=(pole-direction*pole.dot(direction)).normalized()
    knee=a+direction*along+pole*math.sqrt(max(0,l1*l1-along*along))
    oldfoot=target[foot].copy()
    for n,old,new,pos in ((upper,b-a,knee-a,a),(lower,c-b,end-knee,knee)):
        _,rot,scale=target[n].decompose()
        target[n]=Matrix.LocRotScale(pos,old.rotation_difference(new)@rot,scale)
    target[foot].translation=end
    target[toe]=target[foot]@oldfoot.inverted()@target[toe]

rig,body=load('rigged.glb')
bsdf=next(n for n in body.data.materials[0].node_tree.nodes if n.type=='BSDF_PRINCIPLED')
base=bsdf.inputs['Base Color'].links[0].from_node.image
normal=bsdf.inputs['Normal'].links[0].from_node.inputs['Color'].links[0].from_node.image
orm=bsdf.inputs['Roughness'].links[0].from_node.inputs[0].links[0].from_node.image
for kind,img in [('BaseColor',base),('Normal',normal),('ORM',orm)]:
    img.scale(2048,2048);img.filepath_raw=str(OUT/f'T_Player_{kind}.png');img.file_format='PNG';img.save()
rig.animation_data_clear()
for bone in rig.pose.bones: bone.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
export('SK_Protagonist',rig,body,False)
report={'triangles':len(body.data.polygons),'height_m':1.76,'texture_size':2048,'clips':{}}

for file,name,crouch,idle in [('walking.glb','A_PlayerWalk',False,False),
    ('running.glb','A_PlayerRun',False,False),('walking.glb','A_PlayerIdle',False,True),
    ('walking.glb','A_PlayerCrouchIdle',True,True),('walking.glb','A_PlayerCrouchWalk',True,False)]:
    rig,body=load(file);scene=bpy.context.scene
    action=rig.animation_data.action;start,end=action.frame_range
    duration=(end-start)/scene.render.fps
    count=max(2,round(duration*30));samples=[]
    for i in range(count+1):
        t=start+(end-start)*i/count;scene.frame_set(int(t),subframe=t-int(t))
        samples.append({p.name:p.matrix.copy() for p in rig.pose.bones})
    drift=samples[-1]['Hips'].translation-samples[0]['Hips'].translation
    if idle:
        # Mean walking pose puts the arms at rest; IK returns both shoes to the floor.
        mean={}
        for n in samples[0]:
            loc,rot,scale=samples[0][n].decompose()
            for i,s in enumerate(samples[1:],2):
                l,q,k=s[n].decompose();loc=loc.lerp(l,1/i);rot=rot.slerp(q,1/i);scale=scale.lerp(k,1/i)
            mean[n]=Matrix.LocRotScale(loc,rot,scale)
        for side in ('Left','Right'):
            endpos=mean[side+'Foot'].translation.copy()
            endpos.y=rig.data.bones[side+'Foot'].head_local.y
            endpos.z=rig.data.bones[side+'Foot'].head_local.z
            ik_leg(mean,side,endpos)
        samples=[{n:m.copy() for n,m in mean.items()} for _ in range(61)]
        count=60;duration=2
    rig.animation_data_clear();rig.animation_data_create();rig.animation_data.action=bpy.data.actions.new(name)
    scene.render.fps=30;scene.frame_start=1;scene.frame_end=count+1
    first=None
    for i,sample in enumerate(samples):
        target={n:m.copy() for n,m in sample.items()}
        for m in target.values():
            if not idle:
                m.translation.x-=drift.x*i/count;m.translation.y-=drift.y*i/count
            else: m.translation.z+=math.sin(i/count*2*math.pi)*.002/rig.scale.z
        if crouch:
            feet={side:target[side+'Foot'].translation.copy() for side in ('Left','Right')}
            for m in target.values(): m.translation.z-=.43/rig.scale.z
            for side in feet: ik_leg(target,side,feet[side])
        scene.frame_set(i+1)
        for p in rig.pose.bones:
            kwargs=dict(parent_matrix=target[p.parent.name],parent_matrix_local=p.parent.bone.matrix_local) if p.parent else {}
            p.matrix_basis=p.bone.convert_local_to_pose(target[p.name],p.bone.matrix_local,invert=True,**kwargs)
        if first is None: first={p.name:p.matrix_basis.copy() for p in rig.pose.bones}
        if i>count-3:
            t=(i-(count-3))/3
            for p in rig.pose.bones:
                l,q,s=p.matrix_basis.decompose();fl,fq,fs=first[p.name].decompose()
                p.matrix_basis=Matrix.LocRotScale(l.lerp(fl,t),q.slerp(fq,t),s.lerp(fs,t))
        for p in rig.pose.bones:
            p.rotation_mode='QUATERNION'
            for path in ('location','rotation_quaternion','scale'): p.keyframe_insert(data_path=path,frame=i+1)
    # Correct any floor penetration without changing the locomotion timing.
    bottoms=[]
    for frame in range(1,count+2):
        scene.frame_set(frame)
        evaluated=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh()
        bottom=min((evaluated.matrix_world@v.co).z for v in mesh.vertices);evaluated.to_mesh_clear()
        bottoms.append(bottom)
        if bottom<.002:
            root=rig.pose.bones['Hips'];m=root.matrix.copy();m.translation.z+=(.002-bottom)/rig.scale.z
            root.matrix_basis=root.bone.convert_local_to_pose(m,root.bone.matrix_local,invert=True)
            root.keyframe_insert(data_path='location',frame=frame)
    scene.frame_set(1);export(name,rig,body,True)
    report['clips'][name]={'duration_s':duration,'frames':count+1,'in_place':True,'crouched':crouch,'minimum_bottom_before_fix_m':min(bottoms)}
    # Small GLB previews reuse the same verified poses.
    if name in ('A_PlayerIdle','A_PlayerCrouchWalk','A_PlayerRun'):
        bpy.ops.export_scene.gltf(filepath=str(SOURCE/(name+'.glb')),export_format='GLB',use_selection=True)
    print('PLAYER_CLIP_EXPORTED',name,flush=True)
(SOURCE/'game-preparation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('PROTAGONIST_EXPORT_COMPLETE',flush=True)
