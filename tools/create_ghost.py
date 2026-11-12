"""Local authored geometry and rig, using AI references as projected albedo.
Not an image-to-3D reconstruction. Run Blender --background --python this_file.
"""
import bpy, bmesh, math, json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1]
OUT=R/'Art'/'Ghost'; OUT.mkdir(parents=True,exist_ok=True)
REF=R/'Art'/'GhostReferences'/'v2'
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene; scene.unit_settings.system='METRIC'
parts=[]; mats=[]
for name,file in [('GhostFront','01_front.png'),('GhostBack','02_back.png')]:
    m=bpy.data.materials.new(name); m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Roughness'].default_value=.94
    tex=m.node_tree.nodes.new('ShaderNodeTexImage'); tex.image=bpy.data.images.load(str(REF/file)); tex.extension='EXTEND'
    m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']); mats.append(m)
skin=bpy.data.materials.new('GhostSkin'); skin.diffuse_color=(.29,.30,.29,1); skin.use_nodes=True
skin.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.29,.30,.29,1)
skin.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.9
mats.append(skin)
# Reference pixel coordinates map to metres. Feet at y1468, crown near y15.
S=1.85/1453
def point(x,y,depth=0): return ((x-512)*S,depth,(1468-y)*S)
def build(name,verts,faces,weights,plain=False):
    mesh=bpy.data.meshes.new(name); mesh.from_pydata(verts,[],faces); mesh.update()
    bm=bmesh.new(); bm.from_mesh(mesh); bmesh.ops.recalc_face_normals(bm,faces=bm.faces); bm.to_mesh(mesh); bm.free(); mesh.update()
    ob=bpy.data.objects.new(name,mesh); scene.collection.objects.link(ob)
    for m in mats: mesh.materials.append(m)
    uv=mesh.uv_layers.new(name='ReferenceProjection')
    for p in mesh.polygons:
        p.use_smooth=True; p.material_index=2 if plain else (0 if p.normal.y<0 else 1)
        for li in p.loop_indices:
            v=mesh.vertices[mesh.loops[li].vertex_index].co
            x=v.x/S+512
            if p.material_index==1:x=1024-x
            # Clamp projection into body silhouette through section geometry, not the background.
            uv.data[li].uv=(x/1024,1-(1468-v.z/S)/1536)
    for i,w in enumerate(weights):
        for bone,value in w.items():
            vg=ob.vertex_groups.get(bone) or ob.vertex_groups.new(name=bone); vg.add([i],value,'REPLACE')
    parts.append(ob); return ob
def tube(name,rings,weightfn,plain=False,n=32):
    # rings: (x pixel, y pixel, radius in X pixels, depth metres)
    verts=[]; weights=[]; faces=[]
    for x,y,rx,ry in rings:
        for j in range(n):
            a=2*math.pi*j/n
            # Gentle cloth corrugation keeps the silhouette from being a perfect cylinder.
            wrinkle=1+.016*math.sin(a*7+y*.08) if not plain else 1
            verts.append(point(x+rx*math.cos(a)*wrinkle,y,ry*math.sin(a)*wrinkle)); weights.append(weightfn(y))
    for k in range(len(rings)-1):
        for j in range(n):faces.append((k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j))
    faces.extend([tuple(reversed(range(n))),tuple((len(rings)-1)*n+j for j in range(n))])
    return build(name,verts,faces,weights,plain)
def blend(y,pivot,top,bottom,span=80):
    t=max(0,min(1,(y-pivot)/span+.5)); return {top:1-t,bottom:t}
torso=[(512,y,w,d) for y,w,d in [(250,55,.055),(266,98,.08),(300,130,.105),(350,136,.108),(420,131,.102),(500,128,.095),(590,135,.10),(670,144,.105),(740,147,.11)]]
tube('PajamaShirt',torso,lambda y:blend(y,590,'spine','pelvis',240))
tube('Neck',[(512,195,40,.05),(512,220,36,.046),(512,250,42,.05),(512,273,49,.055)],lambda y:{'head':1},True)
for sign,side in [(-1,'r'),(1,'l')]:
    tube('Sleeve_'+side,[(512+sign*x,y,w,d) for x,y,w,d in [(115,285,50,.072),(143,332,54,.074),(174,400,52,.068),(210,476,48,.063),(244,553,43,.058),(275,620,40,.052),(303,682,39,.05)]],lambda y:blend(y,476,'upperarm_'+side,'forearm_'+side,100))
    tube('Trouser_'+side,[(512+sign*x,y,w,d) for x,y,w,d in [(72,724,71,.092),(73,800,73,.095),(80,900,71,.088),(86,1015,69,.082),(94,1110,66,.075),(99,1230,65,.075),(103,1350,66,.073),(106,1405,61,.068)]],lambda y:blend(y,1050,'thigh_'+side,'calf_'+side,140))
    tube('Palm_'+side,[(512+sign*x,y,w,d) for x,y,w,d in [(309,684,22,.023),(319,720,24,.026),(323,751,21,.022),(325,769,17,.017)]],lambda y:{'hand_'+side:1},True,24)
    # Separate long fingers, thumb and closed feet for real silhouettes.
    for k in range(4):
        x=512+sign*(307+k*12); y=752+abs(k-1)*3
        tube('Finger_'+side+str(k),[(x,y,5,.006),(x+sign*4,y+35,4.5,.006),(x+sign*2,y+65-abs(k-1)*7,2,.003)],lambda y:{'hand_'+side:1},True,12)
    tube('Thumb_'+side,[(512+sign*298,723,7,.008),(512+sign*286,748,6,.007),(512+sign*285,772,2,.003)],lambda y:{'hand_'+side:1},True,12)
    # UV sphere foot, forward is -Y.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=point(512+sign*106,1436,-.045))
    foot=bpy.context.object; foot.scale=(.067,.135,.035); bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for v in foot.data.vertices:v.co+=foot.location
    foot.location=(0,0,0); foot.name='Foot_'+side; foot.data.materials.append(skin)
    g=foot.vertex_groups.new(name='foot_'+side); g.add(list(range(len(foot.data.vertices))),1,'REPLACE')
    for p in foot.data.polygons:p.use_smooth=True
    parts.append(foot)
# Sculpted erased head, with real eye recesses and asymmetric lower face.
verts=[]; faces=[]; n=64; rows=40
for i in range(rows+1):
    t=math.pi*(.001+(i/rows)*.998); z=1.708+.142*math.cos(t)
    for j in range(n):
        a=2*math.pi*j/n; x=.094*math.sin(t)*math.cos(a); y=.089*math.sin(t)*math.sin(a)
        if y<0:
            recess=sum(.031*math.exp(-((x-s*.043)/.021)**2-((z-(1.719+s*.004))/.023)**2) for s in [-1,1])
            nose=.014*math.exp(-(x/.015)**2-((z-1.69)/.035)**2)
            y+=recess-nose
            x+=.006*math.exp(-((z-1.62)/.05)**2)
        verts.append((x,y,z))
for i in range(rows):
    for j in range(n):faces.append((i*n+j,i*n+(j+1)%n,(i+1)*n+(j+1)%n,(i+1)*n+j))
build('ErasedHead',verts,faces,[{'head':1} for v in verts])
# Rig is deliberately simple; all deformation weights authored locally.
arm=bpy.data.armatures.new('HaedamGhostRig'); rig=bpy.data.objects.new('HaedamGhostRig',arm); scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig; rig.select_set(True); bpy.ops.object.mode_set(mode='EDIT')
def bone(name,head,tail,parent=None):
    b=arm.edit_bones.new(name); b.head=head; b.tail=tail
    if parent:b.parent=arm.edit_bones[parent]
bone('root',(0,0,0),(0,0,.1))
bone('pelvis',point(512,760),point(512,610),'root')
bone('spine',point(512,610),point(512,270),'pelvis')
bone('head',point(512,270),point(512,30),'spine')
for sign,side in [(-1,'r'),(1,'l')]:
    bone('upperarm_'+side,point(512+sign*120,300),point(512+sign*210,476),'spine')
    bone('forearm_'+side,point(512+sign*210,476),point(512+sign*309,690),'upperarm_'+side)
    bone('hand_'+side,point(512+sign*309,690),point(512+sign*325,780),'forearm_'+side)
    bone('thigh_'+side,point(512+sign*72,760),point(512+sign*89,1050),'pelvis')
    bone('calf_'+side,point(512+sign*89,1050),point(512+sign*106,1410),'thigh_'+side)
    bone('foot_'+side,point(512+sign*106,1410),point(512+sign*106,1440,-.14),'calf_'+side)
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='DESELECT')
for ob in parts:ob.select_set(True)
bpy.context.view_layer.objects.active=parts[0]; bpy.ops.object.join(); body=bpy.context.object; body.name='SK_ErasedGhost'
mod=body.modifiers.new('GhostRig','ARMATURE'); mod.object=rig; body.parent=rig
# Export one walking loop. Rotation about bone X swings along the sagittal plane.
scene.render.fps=30; scene.frame_start=1; scene.frame_end=41
for f in range(1,42,2):
    phase=(f-1)/40*2*math.pi
    for b in rig.pose.bones:b.rotation_mode='XYZ'; b.rotation_euler=(0,0,0)
    rig.pose.bones['head'].rotation_euler[1]=.10+.025*math.sin(phase*2)
    rig.pose.bones['spine'].rotation_euler[0]=.07
    for side,offset in [('l',0),('r',math.pi)]:
        s=math.sin(phase+offset)
        rig.pose.bones['thigh_'+side].rotation_euler[0]=.30*s
        rig.pose.bones['calf_'+side].rotation_euler[0]=-.30*max(0,-s)
        rig.pose.bones['upperarm_'+side].rotation_euler[2]=(-.35 if side=='l' else .35)
        rig.pose.bones['upperarm_'+side].rotation_euler[0]=-.11*s
        rig.pose.bones['forearm_'+side].rotation_euler[0]=-.09
    for b in rig.pose.bones:b.keyframe_insert(data_path='rotation_euler',frame=f,group=b.name)
rig.animation_data.action.name='GhostWalk'
scene.frame_set(1)
bpy.ops.object.select_all(action='DESELECT'); body.select_set(True); rig.select_set(True); bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(OUT/'SK_ErasedGhost.fbx'),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,axis_forward='-Y',axis_up='Z',bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,path_mode='COPY',embed_textures=False)
# Save editable model with packed reference textures and a preview setup.
for im in bpy.data.images:
    if im.source=='FILE':im.pack()
def aim(ob,target):ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(2.7,-5,2.1)); cam=bpy.context.object; aim(cam,(0,0,.95)); cam.data.type='ORTHO'; cam.data.ortho_scale=2.3; scene.camera=cam
for loc,power,size in [((1,-3,3),230,3),((-2,-1,2),120,2),((0,2,2.5),250,2)]:
    bpy.ops.object.light_add(type='AREA',location=loc); li=bpy.context.object; li.data.energy=power; li.data.shape='DISK'; li.data.size=size; aim(li,(0,0,1))
scene.world.color=(.08,.08,.08); scene.render.engine='CYCLES'; scene.cycles.samples=24
scene.render.resolution_x=800; scene.render.resolution_y=1000; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.render.filepath=str(OUT/'ghost_blender_preview.png')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'haedam_ghost.blend')); bpy.ops.render.render(write_still=True)
(OUT/'model_info.json').write_text(json.dumps({'height_m':1.85,'vertices':len(body.data.vertices),'triangles':sum(len(p.vertices)-2 for p in body.data.polygons),'bones':len(arm.bones),'method':'locally authored geometry with reference-projected albedo; not Meshy or image-to-3D','animation':'GhostWalk 40-frame loop at 30fps'},indent=2))
print('GHOST_BLENDER_COMPLETE')
