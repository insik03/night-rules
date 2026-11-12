"""Bake Meshy locomotion into in-place UE FBX clips and an asymmetric horror run.

Keeps Meshy's footfall timing and skin weights. Head orientation is held askew,
the torso leans, and the right arm swings less than the left. No new paid tasks.
"""
import bpy
import json
import math
from pathlib import Path
from mathutils import Matrix, Quaternion, Vector

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'Art/GhostMeshy/Approved'
OUT = SOURCE / 'Unreal'
OUT.mkdir(exist_ok=True)

def load(name):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(SOURCE / name))
    rig = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
    body = max((o for o in bpy.context.scene.objects if o.type == 'MESH'), key=lambda o: len(o.data.polygons))
    # Meshy also supplies an unweighted Icosphere used as a bone display shape.
    for ob in list(bpy.context.scene.objects):
        if ob not in (rig, body):
            bpy.data.objects.remove(ob, do_unlink=True)
    rig.name = 'Armature'
    body.name = 'SK_SmilingCaretaker'
    bpy.context.scene.unit_settings.system = 'METRIC'
    return rig, body

def export_fbx(name, rig, body, animation):
    bpy.ops.object.select_all(action='DESELECT')
    rig.select_set(True)
    body.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.export_scene.fbx(filepath=str(OUT / (name + '.fbx')), use_selection=True,
        object_types={'MESH', 'ARMATURE'}, add_leaf_bones=False,
        axis_forward='-Y', axis_up='Z', bake_anim=animation,
        bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
        bake_anim_simplify_factor=0, path_mode='AUTO')

def shorten_stride(target, rig, factor):
    """Two-bone solve keeps knee direction and ankle orientation while reducing stride."""
    for side in ('Left', 'Right'):
        upper, lower, foot, toe = [side + suffix for suffix in ('UpLeg', 'Leg', 'Foot', 'ToeBase')]
        a, b, c = [target[name].translation.copy() for name in (upper, lower, foot)]
        end = c.copy()
        end.y = target['Hips'].translation.y + (c.y-target['Hips'].translation.y)*factor
        length_a, length_b = (b-a).length, (c-b).length
        direction = (end-a).normalized()
        distance = min((end-a).length, length_a+length_b-.001)
        end = a+direction*distance
        along = (length_a**2-length_b**2+distance**2)/(2*distance)
        height = math.sqrt(max(0, length_a**2-along**2))
        pole = (b-a)-direction*(b-a).dot(direction)
        if pole.length < .001:
            pole = Vector((0,-1,0))-direction*direction.dot(Vector((0,-1,0)))
        knee = a+direction*along+pole.normalized()*height
        old_foot = target[foot].copy()
        for name, old_dir, new_dir, position in ((upper,b-a,knee-a,a), (lower,c-b,end-knee,knee)):
            _, rotation, scale = target[name].decompose()
            rotation = old_dir.rotation_difference(new_dir) @ rotation
            target[name] = Matrix.LocRotScale(position, rotation, scale)
        target[foot].translation = end
        target[toe] = target[foot] @ old_foot.inverted() @ target[toe]

rig, body = load('rigged.glb')
material = body.data.materials[0]
bsdf = next(n for n in material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
base = bsdf.inputs['Base Color'].links[0].from_node.image
normal_node = bsdf.inputs['Normal'].links[0].from_node
normal = normal_node.inputs['Color'].links[0].from_node.image
separate = bsdf.inputs['Roughness'].links[0].from_node
orm = separate.inputs[0].links[0].from_node.image
for kind, image in [('BaseColor', base), ('Normal', normal), ('ORM', orm)]:
    image.filepath_raw = str(OUT / ('T_Caretaker_' + kind + '.png'))
    image.file_format = 'PNG'
    image.save()
rig.animation_data_clear()
for bone in rig.pose.bones:
    bone.matrix_basis = Matrix.Identity(4)
bpy.context.view_layer.update()
export_fbx('SK_SmilingCaretaker', rig, body, False)

report = {'height_m': 2.15, 'triangles': len(body.data.polygons), 'clips': {}}
for filename, clip, creepy in [('walking.glb', 'A_CaretakerWalk', False),
                                ('running.glb', 'A_CaretakerRun', True)]:
    rig, body = load(filename)
    scene = bpy.context.scene
    old_action = rig.animation_data.action
    start, end = old_action.frame_range
    duration = (end-start)/scene.render.fps
    intervals = max(2, round(duration*30))
    samples = []
    for index in range(intervals+1):
        time = start + (end-start)*index/intervals
        scene.frame_set(int(time), subframe=time-int(time))
        samples.append({p.name: p.matrix_basis.copy() for p in rig.pose.bones})
    # Root drift would double the actor's navigation movement in Unreal.
    root = rig.pose.bones['Hips']
    root_positions = []
    for sample in samples:
        m = root.bone.convert_local_to_pose(sample['Hips'], root.bone.matrix_local)
        root_positions.append(m.translation.copy())
    drift = (root_positions[-1]-root_positions[0]) * rig.scale.x
    report['clips'][clip] = {'duration_s': duration, 'frames': intervals+1,
        'source_root_drift_m': list(drift), 'head_tilt_degrees': 26 if creepy else 12,
        'in_place': True, 'leg_motion': 'Meshy footfall timing, two-bone IK stride compression' if creepy else 'Meshy walking',
        'stride_factor': .56 if creepy else 1}
    rig.animation_data_clear()
    action = bpy.data.actions.new(clip)
    rig.animation_data_create()
    rig.animation_data.action = action
    scene.render.fps = 30
    scene.frame_start, scene.frame_end = 1, intervals+1
    first_basis = None
    head_reference = rig.data.bones['Head'].matrix_local.to_quaternion()
    for index, sample in enumerate(samples):
        scene.frame_set(index+1)
        target = {}
        for p in rig.pose.bones:
            basis = sample[p.name].copy()
            if creepy and p.name in ('RightArm', 'RightForeArm', 'LeftArm'):
                loc, rot, scale = basis.decompose()
                weight = {'RightArm': .26, 'RightForeArm': .38, 'LeftArm': .88}[p.name]
                rot = Quaternion().slerp(rot, weight)
                basis = Matrix.LocRotScale(loc, rot, scale)
            parent_args = dict(parent_matrix=target[p.parent.name],
                               parent_matrix_local=p.parent.bone.matrix_local) if p.parent else {}
            m = p.bone.convert_local_to_pose(basis, p.bone.matrix_local, **parent_args)
            if p.name == 'Hips':
                # Keep the authored vertical bounce and side sway; remove net path travel.
                m.translation.x -= (root_positions[-1].x-root_positions[0].x)*index/intervals
                m.translation.y -= (root_positions[-1].y-root_positions[0].y)*index/intervals
            if creepy and p.name in ('Spine02', 'Spine01'):
                angle = math.radians(12 if p.name == 'Spine02' else 5)
                at = m.translation.copy()
                m = Matrix.Translation(at) @ Matrix.Rotation(angle, 4, 'X') @ Matrix.Translation(-at) @ m
            if p.name == 'Head':
                loc, rot, scale = m.decompose()
                # Stable gaze with a held lateral tilt contrasts with the running body.
                tilt = Quaternion((0, 1, 0), math.radians(26 if creepy else 12))
                rot = tilt @ head_reference
                m = Matrix.LocRotScale(loc, rot, scale)
            target[p.name] = m
        if creepy:
            shorten_stride(target, rig, .56)
        for p in rig.pose.bones:
            parent_args = dict(parent_matrix=target[p.parent.name],
                               parent_matrix_local=p.parent.bone.matrix_local) if p.parent else {}
            p.matrix_basis = p.bone.convert_local_to_pose(target[p.name], p.bone.matrix_local, invert=True, **parent_args)
        # Blend the end gently back into the opening pose for a seamless loop.
        if first_basis is None:
            first_basis = {p.name: p.matrix_basis.copy() for p in rig.pose.bones}
        if index > intervals-3:
            blend = (index-(intervals-3))/3
            for p in rig.pose.bones:
                l, q, s = p.matrix_basis.decompose()
                fl, fq, fs = first_basis[p.name].decompose()
                p.matrix_basis = Matrix.LocRotScale(l.lerp(fl, blend), q.slerp(fq, blend), s.lerp(fs, blend))
        for p in rig.pose.bones:
            p.rotation_mode = 'QUATERNION'
            p.keyframe_insert(data_path='location', frame=index+1)
            p.keyframe_insert(data_path='rotation_quaternion', frame=index+1)
            p.keyframe_insert(data_path='scale', frame=index+1)
    # Keep the surface of the feet above the floor; preserve the authored flight phase.
    offsets = []
    for frame in range(1, intervals+2):
        scene.frame_set(frame)
        evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh()
        bottom = min((evaluated.matrix_world @ v.co).z for v in mesh.vertices)
        evaluated.to_mesh_clear()
        offsets.append(max(0, .004-bottom))
    for index in range(intervals+1):
        scene.frame_set(index+1)
        offset = max(offsets[index], offsets[(index-1)%intervals]*.7, offsets[(index+1)%intervals]*.7)
        root = rig.pose.bones['Hips']
        matrix = root.matrix.copy()
        matrix.translation.z += offset/rig.scale.z
        root.matrix_basis = root.bone.convert_local_to_pose(matrix, root.bone.matrix_local, invert=True)
        root.keyframe_insert(data_path='location', frame=index+1)
    scene.frame_set(1)
    export_fbx(clip, rig, body, True)
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE / (clip + '.blend')))
    print('MESHY_CLIP_PREPARED', clip, report['clips'][clip], flush=True)

(SOURCE / 'animation-manifest.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('MESHY_UNREAL_EXPORT_COMPLETE', flush=True)
