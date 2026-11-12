"""Prepare Studio rigs without changing body proportions. Blender 5.2 CLI."""
import bpy, json, math, sys
from pathlib import Path
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'Art/Characters/Residents-Tripo-v1'
CONFIG = json.loads((BASE/'manifest.json').read_text(encoding='utf-8'))
selected = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []

def bounds(obj):
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get()); mesh=ev.to_mesh()
    pts=[ev.matrix_world@v.co for v in mesh.vertices]; ev.to_mesh_clear()
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])

def image_upstream(socket, visited=None):
    visited=visited or set()
    for link in socket.links:
        node=link.from_node
        if node in visited: continue
        visited.add(node)
        if node.type=='TEX_IMAGE': return node.image
        for inp in node.inputs:
            image=image_upstream(inp,visited)
            if image: return image

def export(path, rig, body, anim):
    bpy.ops.object.select_all(action='DESELECT')
    rig.select_set(True); body.select_set(True); bpy.context.view_layer.objects.active=rig
    bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'MESH','ARMATURE'},
        add_leaf_bones=False,axis_forward='-Y',axis_up='Z',bake_anim=anim,
        bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,
        bake_anim_simplify_factor=0,path_mode='AUTO')

def render(body, target, height):
    scene=bpy.context.scene
    scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
    scene.render.resolution_x=640;scene.render.resolution_y=880;scene.render.resolution_percentage=100
    world=bpy.data.worlds.new('PreviewWorld');world.use_nodes=True
    world.node_tree.nodes.get('Background').inputs[0].default_value=(.11,.13,.16,1)
    world.node_tree.nodes.get('Background').inputs[1].default_value=.35;scene.world=world
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.006));floor=bpy.context.object
    mat=bpy.data.materials.new('PreviewFloor');mat.diffuse_color=(.06,.075,.09,1);floor.data.materials.append(mat)
    for pos,power,size in [((2,-3,4),500,3),((-3,-1,2),260,3),((1,2,3),420,2)]:
        light=bpy.data.lights.new('PreviewArea','AREA');light.energy=power;light.shape='DISK';light.size=size
        obj=bpy.data.objects.new('PreviewArea',light);scene.collection.objects.link(obj);obj.location=pos
        obj.rotation_euler=(Vector((0,0,height*.5))-obj.location).to_track_quat('-Z','Y').to_euler()
    camera=bpy.data.cameras.new('PreviewCamera');obj=bpy.data.objects.new('PreviewCamera',camera)
    scene.collection.objects.link(obj);obj.location=(height*.95,-height*2.6,height*.9)
    obj.rotation_euler=(Vector((0,0,height*.51))-obj.location).to_track_quat('-Z','Y').to_euler()
    lo,hi=bounds(body)
    camera.type='ORTHO';camera.ortho_scale=max(height*1.2,(hi.x-lo.x)*880/640*1.3,(hi.y-lo.y)*1.25);scene.camera=obj
    scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG'
    scene.render.filepath=str(target);bpy.ops.render.render(write_still=True)

for item in CONFIG['residents']:
    slug=item['id']
    if selected and slug not in selected: continue
    folder=BASE/'models'/slug;out=folder/'Unreal';out.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(folder/'source-animated.glb'))
    rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
    body=max((o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)),key=lambda o:len(o.data.polygons))
    # Viewer helper sphere and unrelated empties must not reach the game.
    rig_world=rig.matrix_world.copy();body_world=body.matrix_world.copy()
    rig.parent=None;rig.matrix_world=rig_world
    body.parent=rig;body.matrix_world=body_world
    for obj in list(bpy.context.scene.objects):
        if obj not in (rig,body):bpy.data.objects.remove(obj,do_unlink=True)
    rig.name='Armature';body.name='SK_'+slug.title()
    scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
    action=rig.animation_data.action
    if not action:raise RuntimeError('No animation in '+slug)
    slot=rig.animation_data.action_slot
    start,end=action.frame_range
    scene.frame_start=math.floor(start);scene.frame_end=math.ceil(end)
    rig.data.pose_position='REST';bpy.context.view_layer.update()
    low,high=bounds(body);rawheight=high.z-low.z
    factor=item['height_cm']/100/rawheight
    # Retained Mixamo skeleton: imported feet point along Blender -Y.
    forward=rig.matrix_world.to_3x3()@(rig.data.bones['mixamorig:LeftToeBase'].head_local-rig.data.bones['mixamorig:LeftFoot'].head_local)
    yaw=-math.pi/2-math.atan2(forward.y,forward.x)
    rig.matrix_world=Matrix.Rotation(yaw,4,'Z')@Matrix.Scale(factor,4)@rig.matrix_world
    bpy.context.view_layer.update();low,high=bounds(body)
    rig.location-=Vector(((low.x+high.x)/2,(low.y+high.y)/2,low.z))
    bpy.context.view_layer.update();restlo,resthi=bounds(body)
    rig.data.pose_position='POSE';scene.frame_set(scene.frame_start);bpy.context.view_layer.update()
    samples=[]
    for frame in range(scene.frame_start,scene.frame_end+1,max(1,(scene.frame_end-scene.frame_start)//30)):
        scene.frame_set(frame);lo,hi=bounds(body);samples.append({'frame':frame,'floor_cm':lo.z*100,'height_cm':(hi.z-lo.z)*100})
    floor_adjust=max(0,-min(v['floor_cm'] for v in samples))/100
    rig.location.z+=floor_adjust
    # Copy atlas maps at a 2K ceiling; original GLB remains untouched.
    if len(body.data.materials)!=1:raise RuntimeError('Expected one atlas: '+slug)
    bsdf=next(n for n in body.data.materials[0].node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    maps={}
    for kind,socket in [('BaseColor','Base Color'),('Normal','Normal'),('ORM','Roughness')]:
        image=image_upstream(bsdf.inputs[socket])
        if image:
            maxsize=max(image.size);ratio=min(1,2048/maxsize)
            image.scale(round(image.size[0]*ratio),round(image.size[1]*ratio))
            name='T_'+slug.title()+'_'+kind;image.filepath_raw=str(out/(name+'.png'));image.file_format='PNG';image.save()
            maps[kind]=name
    scene.frame_set(scene.frame_start)
    # Export an unposed reference mesh and the original idle on the same skeleton.
    rig.animation_data.action=None
    for bone in rig.pose.bones:bone.matrix_basis=Matrix.Identity(4)
    bpy.context.view_layer.update()
    export(out/('SK_'+slug.title()+'.fbx'),rig,body,False)
    rig.animation_data.action=action;rig.animation_data.action_slot=slot
    scene.frame_set(scene.frame_start);bpy.context.view_layer.update()
    export(out/('A_'+slug.title()+'_Idle.fbx'),rig,body,True)
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);body.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(folder/'preview.glb'),export_format='GLB',use_selection=True,export_animations=True)
    report={'id':slug,'room':item['room'],'height_basis':'temporary game scale, not an approved character biography',
        'reference_height_cm':round((resthi.z-restlo.z)*100,3),'uniform_scale':factor,'yaw_degrees':math.degrees(yaw),
        'triangles':sum(len(p.vertices)-2 for p in body.data.polygons),'bones':len(rig.data.bones),
        'animation_seconds':(end-start)/scene.render.fps,'frames':[scene.frame_start,scene.frame_end],
        'texture_maps':maps,'floor_lift_cm':floor_adjust*100,'sampled_floor':samples,
        'body_bounds_cm':[list(restlo*100),list(resthi*100)],'source':item['task_id']}
    (folder/'prepared.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    bpy.ops.wm.save_as_mainfile(filepath=str(folder/'prepared.blend'))
    render(body,folder/'render.png',item['height_cm']/100)
    print('RESIDENT_PREPARED '+slug+' '+json.dumps({k:report[k] for k in ['triangles','bones','reference_height_cm','animation_seconds']}),flush=True)
