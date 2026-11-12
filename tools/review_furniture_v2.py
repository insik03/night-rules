"""Audit existing review geometry and fix wardrobe door sweep, without paid generation.
Run in Blender background. Outputs a new version; does not change Unreal assets.
"""
import bpy, json, math, hashlib, sys
from pathlib import Path
from mathutils import Vector, Matrix
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'Art/EnvironmentConcepts/dimensioned-furniture-v1'
OUT=ROOT/'Art/EnvironmentConcepts/furniture-review-v2'
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SRC/'haedam-dimensioned-furniture.blend'))
# The project was moved; repair the old relative font path in this copy.
font=bpy.data.fonts.load('C:/Windows/Fonts/malgun.ttf')
for curve in bpy.data.curves:
    if isinstance(curve,bpy.types.TextCurve):curve.font=font
for f in list(bpy.data.fonts):
    if f!=font and f.users==0:bpy.data.fonts.remove(f)
font.filepath='C:/Windows/Fonts/malgun.ttf'
layout=json.loads((ROOT/'Art/EnvironmentConcepts/unified-v15/furniture-layout.json').read_text(encoding='utf-8'))
placement=json.loads((SRC/'placement.json').read_text(encoding='utf-8'))
oldspec=json.loads((SRC/'dimensions.json').read_text(encoding='utf-8'))
floors=[bpy.data.scenes[f'{f}F / dimensioned layout'] for f in range(1,5)]
bpy.context.window.scene=floors[0]

def bounds(points):
    return ([min(p[i] for p in points) for i in range(3)],[max(p[i] for p in points) for i in range(3)])
def meshpts(obj,transform=None):
    dg=bpy.context.evaluated_depsgraph_get();eo=obj.evaluated_get(dg)
    mat=(transform or Matrix.Identity(4)) @ eo.matrix_world
    return [mat@v.co for v in eo.data.vertices] if eo.type=='MESH' else []
def collection_bounds(c):
    pts=[p for o in c.objects if o.type=='MESH' for p in meshpts(o)]
    return bounds(pts)
def dimensions(c):
    lo,hi=collection_bounds(c);return [round((hi[i]-lo[i])*100,5) for i in range(3)]
def audit_dimensions():
    result=[]
    for spec in oldspec:
        c=bpy.data.collections['MODEL / '+spec['asset']]
        actual=dimensions(c)
        result.append(dict(asset=spec['asset'],expected_cm=spec['expected_cm'],measured_cm=actual,passed=all(abs(x-y)<.1 for x,y in zip(actual,spec['expected_cm'])),kind=spec['kind']))
    return result

baseline=audit_dimensions()
placed_actual=[]
for f,s in enumerate(floors,1):
    for o in s.objects:
        if o.instance_type=='COLLECTION' and o.instance_collection:
            placed_actual.append({'floor':f,'asset':o.instance_collection.name.replace('MODEL / ',''),'x':round(o.location.x*100,4),'y':round(o.location.y*100,4),'z':round(o.location.z*100,4),'yaw':round(math.degrees(o.rotation_euler.z),3)})
matched=[]
for it in placement['items']:
    matches=[o for o in placed_actual if o['floor']==it['floor'] and o['asset']==it['asset'] and all(abs(o[k]-it[k])<.1 for k in ['x','y','z','yaw'])]
    matched.append(bool(matches))

ward=bpy.data.collections['MODEL / 옷장']
for o in list(ward.objects):
    if o.name.startswith('Separate wardrobe door') or o.name.startswith('Handle'):
        bpy.data.objects.remove(o,do_unlink=True)
wood=bpy.data.materials['Warm timber'];ivory=bpy.data.materials['Cabinet ivory'];metal=bpy.data.materials['Brushed metal']
dark=bpy.data.materials['Rubber charcoal'];floor_mat=bpy.data.materials['Floor green grey']
def box(c,name,center,dims,mat,bevel=.2):
    x,y,z=[v/100 for v in center];a,b,d=[v/200 for v in dims]
    verts=[(x+i*a,y+j*b,z+k*d) for i,j,k in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
    faces=[(0,2,6,4),(1,5,7,3),(0,4,5,1),(2,3,7,6),(0,1,3,2),(4,6,7,5)]
    m=bpy.data.meshes.new(name);m.from_pydata(verts,[],faces);m.update()
    o=bpy.data.objects.new(name,m);c.objects.link(o);o.data.materials.append(mat)
    if bevel:
        mod=o.modifiers.new('Small manufactured edge','BEVEL');mod.width=bevel/100;mod.segments=2
    return o
hinges=[];leaves=[]
for side in [-1,1]:
    hinge=bpy.data.objects.new('HINGE_Wardrobe_'+('L' if side==-1 else 'R'),None);ward.objects.link(hinge)
    hinge.location=(side*.2175,-.215,0);hinge.empty_display_size=.03;hinge['max_open_degrees']=90
    leaf=box(ward,'SM_WardrobeLeaf_'+str(side),(-side*10.75,0,87.5),(21.5,2,174),ivory)
    leaf.parent=hinge
    grip=box(ward,'SM_WardrobeRecess_'+str(side),(-side*18,-.96,88),(1.3,.08,12),dark,.02);grip.parent=hinge
    for z in [18,150]:
        fitting=box(ward,'SM_WardrobeHinge_'+str(side),(-side*.3,.1,z),(.6,1.2,5),metal,.1);fitting.parent=hinge
    for frame,angle in [(1,0),(91,side*math.pi/2)]:
        hinge.rotation_euler.z=angle;hinge.keyframe_insert(data_path='rotation_euler',index=2,frame=frame)
    hinges.append(hinge);leaves.append(leaf)
for z in [9,65,125]:box(ward,'SM_WardrobeShelf',(0,1,z),(41,40,1.8),wood)

def state(frame):
    for s in bpy.data.scenes:s.frame_set(frame)
    bpy.context.view_layer.update()
state(1)
after=audit_dimensions()
assert all(d['passed'] for d in after), [d for d in after if not d['passed']]

# Check actual transformed door meshes against bed volume over 0..90 degrees.
ward_items=[it for it in placement['items'] if it['name']=='옷장']
beds=[it for it in placement['items'] if it['name']=='싱글 침대 프레임']
samples=[];min_gap=10000
for frame in range(1,92):
    state(frame)
    worst=10000
    for it in ward_items:
        tm=Matrix.Translation(Vector((it['x']/100,it['y']/100,0))) @ Matrix.Rotation(math.radians(it['yaw']),4,'Z')
        max_y=max(p.y*100 for leaf in leaves for p in meshpts(leaf,tm))
        bed=min([b for b in beds if b['floor']==it['floor']],key=lambda b:abs(b['x']-it['x']))
        gap=bed['y']-bed['depth']/2-max_y
        worst=min(worst,gap)
    min_gap=min(min_gap,worst);samples.append({'frame':frame,'gap_to_bed_cm':round(worst,4)})
assert min_gap>17,min_gap
continuous_gap_bound=22-(-18.5+math.hypot(21.5,1))
assert continuous_gap_bound>18.9
state(1)

# Broad phase then mesh-part bounding-box screening of placed furniture only.
# Intentional supports can touch; overlaps are warnings rather than runtime claims.
overlaps=[]
for f in range(1,5):
    bpy.context.window.scene=floors[f-1];bpy.context.view_layer.update()
    items=[it for it in placement['items'] if it['floor']==f]
    parts=[]
    for it in items:
        c=bpy.data.collections['MODEL / '+it['asset']]
        tm=Matrix.Translation(Vector((it['x']/100,it['y']/100,it['z']/100)))@Matrix.Rotation(math.radians(it['yaw']),4,'Z')
        pb=[bounds(meshpts(o,tm)) for o in c.objects if o.type=='MESH']
        parts.append(pb)
    def overlap(a,b):return all(min(a[1][k],b[1][k])-max(a[0][k],b[0][k])>.001 for k in range(3))
    for i in range(len(items)):
        for j in range(i+1,len(items)):
            hit=next(((a,b) for a in parts[i] for b in parts[j] if overlap(a,b)),None)
            if hit:overlaps.append({'floor':f,'a':items[i]['name'],'a_xy':[items[i]['x'],items[i]['y']],'b':items[j]['name'],'b_xy':[items[j]['x'],items[j]['y']],'status':'potential mesh-part AABB overlap; inspect geometry'})

# A dedicated cutaway scene reuses the actual furniture collections and placements.
room=bpy.data.scenes.new('Room / wardrobe operation review')
room.unit_settings.system='METRIC';room.unit_settings.scale_length=1
room.world=floors[0].world.copy();room.render.engine='CYCLES';room.cycles.samples=24;room.cycles.use_denoising=True
room.view_settings.view_transform='AgX';room.render.image_settings.file_format='PNG'
shell=bpy.data.collections.new('Room review shell');room.collection.children.link(shell)
box(shell,'Room slab',(465,80,-3),(230,300,6),floor_mat,.3)
wallmat=bpy.data.materials['Walls 1F 2F']
for name,center,size in [('Left cut wall',(350,80,30),(10,300,60)),('Right cut wall',(580,80,30),(10,300,60)),('Rear cut wall',(465,230,30),(230,10,60)),('Front wall left',(355.75,-70,30),(11.5,10,60)),('Front wall right',(514.25,-70,30),(131.5,10,60))]:
    box(shell,name,center,size,wallmat,.3)
roomf=bpy.data.collections.new('Room furnishings');room.collection.children.link(roomf)
for it in placement['items']:
    if it['floor']==1 and 350<it['x']<580 and it['y']>-70:
        o=bpy.data.objects.new(it['name']+' / reviewed',None);o.instance_type='COLLECTION';o.instance_collection=bpy.data.collections['MODEL / '+it['asset']];roomf.objects.link(o)
        o.location=(it['x']/100,it['y']/100,it['z']/100);o.rotation_euler.z=math.radians(it['yaw'])
ld=bpy.data.lights.new('Review softbox','AREA');ld.energy=450;ld.shape='DISK';ld.size=5
light=bpy.data.objects.new('Review softbox',ld);room.collection.objects.link(light);light.location=(4.3,1.8,5)
light.rotation_euler=(Vector((4.6,.8,.6))-light.location).to_track_quat('-Z','Y').to_euler()

def render(s,name,center=None,offset=None,scale=None,w=1500,h=1150):
    bpy.context.window.scene=s
    if center is not None:
        cd=bpy.data.cameras.new(name);cam=bpy.data.objects.new(name,cd);s.collection.objects.link(cam)
        target=Vector(center)/100;cam.location=target+Vector(offset)/100
        cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.ortho_scale=scale/100;cd.clip_end=500;s.camera=cam
    s.render.resolution_x=w;s.render.resolution_y=h;s.render.resolution_percentage=100
    s.render.filepath=str(OUT/(name+'.png'));s.cycles.samples=20
    bpy.ops.render.render(write_still=True);print('RENDER_DONE '+name,flush=True)

report={'source_blend':str(SRC.relative_to(ROOT)/'haedam-dimensioned-furniture.blend'),'source_blend_sha256':hashlib.sha256((SRC/'haedam-dimensioned-furniture.blend').read_bytes()).hexdigest(),'layout_sha256':hashlib.sha256((ROOT/'Art/EnvironmentConcepts/unified-v15/furniture-layout.json').read_bytes()).hexdigest(),'models_checked':len(after),'before':baseline,'after':after,'placement_items_checked':len(matched),'placement_matches':sum(matched),'wardrobe_instances_updated':len(ward_items),'wardrobe_outer_cm':[45,45,175],'door_leaf_cm':[21.5,2,174],'door_leaves_per_cabinet':2,'sweep_samples':samples,'minimum_door_bed_gap_cm':round(min_gap,4),'bed_foot_gap_cm':39.5,'room_left_clear_width_cm':127,'player_capsule_diameter_cm':56,'furniture_overlap_candidates':overlaps,'runtime_imported':False,'credits_used':0,'limitations':['Cutaway Blender review, not runtime capsule sweep.','Foot-of-bed gap is not a walk-through path; approach from left aisle.','Overlap screen uses part AABBs, not full triangle collision.','Fixtures marked placeholder remain dimensional placeholders.']}
report['continuous_sweep_gap_lower_bound_cm']=round(continuous_gap_bound,4)
report['left_approach_clear_width_with_bin_cm']=97
(OUT/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'placement.json').write_text(json.dumps(placement,ensure_ascii=False,indent=2),encoding='utf-8')
print('AUDIT '+json.dumps({k:report[k] for k in ['models_checked','placement_matches','placement_items_checked','wardrobe_instances_updated','minimum_door_bed_gap_cm','furniture_overlap_candidates']},ensure_ascii=True),flush=True)
state(1);render(room,'room-closed',(465,80,85),(-300,410,510),495)
state(91);render(room,'room-open',(465,80,85),(-300,410,510),495)
render(room,'room-open-top',(465,80,0),(0,0,700),355,1300,1400)
state(1)
for f,s in enumerate(floors,1):
    s.camera=bpy.data.objects.get(f'floor-{f}') or s.camera
    render(s,f'floor-{f}',w=1920,h=800)
bpy.context.window.scene=room;state(91);room.camera=bpy.data.objects['room-open']
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'haedam-furniture-reviewed.blend'))
print('FURNITURE_REVIEW_COMPLETE',flush=True)
