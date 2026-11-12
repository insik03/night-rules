"""Local Blender geometry, authored in cm. No generation APIs or paid services.
Review only: does not modify Unreal assets or the canonical layout.
Run: blender -b --python tools/build_dimensioned_furniture.py
"""
import bpy, json, math, hashlib
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Art/EnvironmentConcepts/dimensioned-furniture-v1'
OUT.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT/'Art/EnvironmentConcepts/unified-v15/furniture-layout.json'
layout=json.loads(SOURCE.read_text(encoding='utf-8'))
bpy.ops.wm.read_factory_settings(use_empty=True)
font=bpy.data.fonts.load('C:/Windows/Fonts/malgun.ttf')
materials={}
def mat(name,color,metal=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Roughness'].default_value=.65;bs.inputs['Metallic'].default_value=metal
    materials[name]=m;return m
wood=mat('Warm timber',(.33,.21,.12));edge=mat('Dark wood',(.13,.09,.06))
ivory=mat('Cabinet ivory',(.69,.68,.60));cloth=mat('Bedding muted sage',(.30,.40,.37))
white=mat('Linen cream',(.76,.73,.65));metal=mat('Brushed metal',(.30,.34,.35),.65)
dark=mat('Rubber charcoal',(.045,.055,.055));blue=mat('Slate blue',(.16,.23,.30))
green=mat('Floor green grey',(.23,.30,.27));tile=mat('Wet floor',(.38,.42,.41))
wallmat=mat('Walls 1F 2F',(.64,.60,.49));newwall=mat('Renovated 3F',(.78,.77,.70))
glass=mat('Window diagram cyan',(.22,.46,.49));accent=mat('Dimensions mint',(.18,.52,.40))
amber=mat('Door clearance amber',(.64,.42,.15));paper=mat('Paper',(.82,.79,.69))

def box(c,name,pos,dims,m,bevel=0):
    x,y,z=[v/100 for v in pos];a,b,d=[v/200 for v in dims]
    vs=[(x+i*a,y+j*b,z+k*d) for i,j,k in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
    faces=[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vs,[],[tuple(reversed(f)) for f in faces]);mesh.update()
    o=bpy.data.objects.new(name,mesh);c.objects.link(o);o.data.materials.append(m)
    if bevel:
        mod=o.modifiers.new('Edge radius authored in cm','BEVEL');mod.width=bevel/100;mod.segments=2
        o.modifiers.new('Corner normals','WEIGHTED_NORMAL')
    return o
def cyl(c,name,pos,radius,height,m,axis='Z',vertices=32):
    # Vertices are authored directly at final dimensions, object scale stays 1.
    verts=[]
    for z in [-height/2,height/2]:
        for i in range(vertices):
            t=2*math.pi*i/vertices;p=[radius*math.cos(t),radius*math.sin(t),z]
            if axis=='Y':p=[p[0],p[2],p[1]]
            if axis=='X':p=[p[2],p[0],p[1]]
            verts.append(tuple((p[j]+pos[j])/100 for j in range(3)))
    faces=[tuple(reversed(range(vertices))),tuple(range(vertices,2*vertices))]
    faces += [(i,(i+1)%vertices,(i+1)%vertices+vertices,i+vertices) for i in range(vertices)]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    o=bpy.data.objects.new(name,mesh);c.objects.link(o);o.data.materials.append(m);return o
def line(c,name,a,b,r,m):
    d=Vector(b)-Vector(a);o=cyl(c,name,(0,0,0),r,d.length,m,vertices=8)
    rot=d.to_track_quat('Z','Y').to_matrix();mid=(Vector(a)+Vector(b))/200
    for v in o.data.vertices:v.co=rot@v.co+mid
    o.data.update();return o
def text(c,s,pos,size=15,m=dark):
    data=bpy.data.curves.new('Label '+s,'FONT');data.body=s;data.font=font;data.size=size/100;data.align_x='CENTER'
    o=bpy.data.objects.new('Label '+s,data);c.objects.link(o);o.location=Vector(pos)/100;o.data.materials.append(m);return o
def dim(c,a,b,label,offset=0):
    line(c,'Dimension',a,b,.45,accent)
    for p in (a,b):line(c,'Tick',(p[0],p[1]-4,p[2]),(p[0],p[1]+4,p[2]),.45,accent)
    text(c,label,((a[0]+b[0])/2,(a[1]+b[1])/2+7,a[2]+1),11,accent)

assets={};audit=[]
def asset(key,w,d,h,kind):
    if key in assets:return assets[key]
    c=bpy.data.collections.new('MODEL / '+key);assets[key]=c
    if kind=='chair':
        for x in [-w/2+2,w/2-2]:
            for y in [-d/2+2,d/2-2]:box(c,'Leg',(x,y,21),(4,4,42),metal,.4)
        box(c,'Seat',(0,0,43.5),(w,d,3),wood,.8)
        for x in [-w/2+2,w/2-2]:box(c,'Back upright',(x,-d/2+2,(h+45)/2),(4,4,h-45),metal,.3)
        box(c,'Backrest',(0,-d/2+2,h-10),(w,4,20),wood,.7)
    elif kind=='bedding':
        box(c,'Mattress',(0,0,6),(w,d,12),white,2)
        box(c,'Quilt',(0,-20,14),(w-2,d-40,4),cloth,1.3)
        box(c,'Pillow',(0,d/2-25,15),(58,40,6),white,2)
    elif kind=='sink':
        box(c,'Plinth',(0,0,4),(w-6,d-6,8),dark)
        for x in [-w/2+1,w/2-1]:box(c,'Cabinet side',(x,0,45),(2,d,74),ivory)
        box(c,'Cabinet back',(0,d/2-1,45),(w,2,74),ivory)
        box(c,'Cabinet bottom',(0,0,9),(w-4,d-4,2),ivory)
        box(c,'Shelf',(0,0,44),(w-4,d-5,2),ivory)
        for x in [-w/4,w/4]:
            door=box(c,'Separate hinged door',(x,-d/2+1.2,44.5),(w/2-1,2.4,73),ivory,.4)
            door['hinge_local_cm']=[x-w/4+1,-d/2,8]
            box(c,'Recessed handle',(x+12,-d/2+.6,67),(12,1.2,1.5),metal)
        # Countertop 85cm; inset basin is geometry, not a black painted rectangle.
        for pos,sz in [((0,-25,83.5),(w,10,3)),((0,25,83.5),(w,10,3)),((-49,0,83.5),(22,40,3)),((35,0,83.5),(50,40,3))]:box(c,'Counter rim',pos,sz,metal,.4)
        box(c,'Basin base',(-14,0,67),(48,40,2),metal,.8)
        for x in [-38,10]:box(c,'Basin side',(x,0,75),(1,40,16),metal)
        for y in [-20,20]:box(c,'Basin side',(-14,y,75),(48,1,16),metal)
        # Faucet is a separate add-on, excluded from cabinet's 85cm height specification.
    elif kind=='shower':
        cyl(c,'Rail',(0,5.5,h/2),1.5,h,metal)
        for z in [5,h-5]:box(c,'Wall mount',(0,6,z),(8,3,5),metal,.4)
        cyl(c,'Mixer',(0,3,6),2,25,metal,axis='X')
        cyl(c,'Head',(0,-6.5,h-7.5),5.5,2,metal,axis='Y')
        for i in range(12):
            t=i/11;u=(i+1)/11
            def hp(t):return (8*math.sin(math.pi*t),1,7+82*t-20*math.sin(math.pi*t))
            line(c,'Hose',hp(t),hp(u),.7,metal)
    elif kind=='slippers':
        for x in [-6.5,6.5]:
            box(c,'Sole',(x,0,1.5),(11,28,3),dark,1.1)
            box(c,'Strap top',(x,3,9),(11,10,2),blue,1)
            for dx in [-4.7,4.7]:box(c,'Strap side',(x+dx,3,5.5),(1.6,10,5),blue,.4)
    elif kind=='books':
        widths=[4,3,5,3,4,5,6];x=-w/2
        for i,bw in enumerate(widths):
            bh=h-[0,2,1,4,0,3,2][i]
            box(c,'Book pages',(x+bw/2,0,bh/2),(bw-.4,d-.6,bh-.4),paper)
            for dx in [.1,bw-.1]:box(c,'Book cover',(x+dx,0,bh/2),(.2,d,bh),[cloth,blue,wood][i%3])
            box(c,'Book spine',(x+bw/2,-d/2+.15,bh/2),(bw,.3,bh),[cloth,blue,wood][i%3]);x+=bw
    elif kind=='desk':
        box(c,'Desktop',(0,0,h-1.5),(w,d,3),wood,.5)
        if w>200:
            for x in [-w/2+23,w/2-23]:
                box(c,'Pedestal',(x,1,(h-3)/2),(44,d-4,h-3),edge)
                for z in [13,36,59]:
                    box(c,'Separate drawer',(x,-d/2+1.5,z),(42,3,21),wood,.4)
                    box(c,'Drawer handle',(x,-d/2+1, z+5),(12,2,1.5),metal)
        else:
            for x in [-w/2+2,w/2-2]:
                for y in [-d/2+2,d/2-2]:box(c,'Desk leg',(x,y,(h-3)/2),(4,4,h-3),edge,.3)
            box(c,'Rear apron',(0,d/2-2,h-10),(w-8,3,14),wood)
    elif kind=='wardrobe':
        for x in [-w/2+1,w/2-1]:box(c,'Carcass side',(x,0,h/2),(2,d,h),wood)
        for z in [1,h-1]:box(c,'Carcass cap',(0,0,z),(w,d,2),wood)
        box(c,'Back',(0,d/2-1,h/2),(w,2,h),edge)
        box(c,'Separate wardrobe door',(0,-d/2+1,h/2),(w-1,2,h-1),ivory,.3)
        box(c,'Handle',(w/2-6,-d/2+1,h*.5),(1,2,14),metal)
    elif kind=='bed':
        for x in [-w/2+3,w/2-3]:
            for y in [-d/2+3,d/2-3]:box(c,'Bed post',(x,y,h/2),(6,6,h),wood,.3)
        for x in [-w/2+2,w/2-2]:box(c,'Side rail',(x,0,h-5),(4,d,10),wood)
        for y in [-d/2+2,d/2-2]:box(c,'End rail',(0,y,h-5),(w,4,10),wood)
        for i in range(12):box(c,'Bed slat',(0,-d/2+10+i*(d-20)/11,h-1),(w-8,7,2),white)
    elif kind=='table':
        cyl(c,'Round tabletop',(0,0,h-2),w/2,4,wood,vertices=64)
        cyl(c,'Pedestal',(0,0,(h-4)/2),8,h-4,metal)
        cyl(c,'Foot',(0,0,2),48,4,metal,vertices=48)
    elif kind=='shelf':
        for x in [-w/2+1.5,w/2-1.5]:
            for y in [-d/2+1.5,d/2-1.5]:box(c,'Shelf post',(x,y,h/2),(3,3,h),metal)
        for z in [3,h*.33,h*.66,h-1]:box(c,'Shelf tray',(0,0,z),(w,d,2),ivory)
    elif kind=='monitor':
        box(c,'Base',(0,0,2),(w*.7,d,4),dark,.6)
        box(c,'Stand',(0,d*.2,h*.3),(5,5,h*.5),dark)
        box(c,'Screen body',(0,0,h*.65),(w,8,h*.7),dark,1)
        box(c,'Screen',(0,-4.1,h*.65),(w-3,.2,h*.7-3),glass)
    elif kind=='fridge':
        box(c,'Fridge body',(0,0,h/2),(w,d,h),ivory,1.5)
        for z,bh in [(h*.8,h*.39),(h*.3,h*.59)]:box(c,'Fridge door',(0,-d/2+1.5,z),(w-1,3,bh),white,1)
    else:
        box(c,'Dimensional placeholder',(0,0,h/2),(w,d,h),ivory,.5)
    bpy.context.view_layer.update()
    pts=[o.matrix_world@Vector(v) for o in c.objects if o.type=='MESH' for v in o.bound_box]
    actual=[round((max(p[i] for p in pts)-min(p[i] for p in pts))*100,4) for i in range(3)]
    expected=[w,d,h]
    audit.append(dict(asset=key,expected_cm=expected,measured_cm=actual,within_0_1cm=all(abs(a-b)<.1 for a,b in zip(actual,expected)),kind=kind))
    return c

SPECS={
 '의자42':(42,44,80,'chair'),'침구':(88,195,18,'bedding'),'싱크대':(120,60,85,'sink'),
 '샤워수전':(25,15,110,'shower'),'슬리퍼':(24,28,10,'slippers'),'책':(30,22,25,'books'),
 '관리실책상':(264,55,75,'desk'),'객실책상':(106,55,75,'desk'),'옷장':(45,45,175,'wardrobe'),
 '침대프레임':(90,200,45,'bed'),'식탁':(200,200,75,'table'),'총무의자':(45,45,90,'chair')}
for key,spec in SPECS.items():asset(key,*spec)
mapping={'객실 의자':'의자42','주방 의자':'의자42','사건용 의자':'의자42','총무 의자':'총무의자','매트리스·침구':'침구','싱크대·하부장':'싱크대','샤워 수전':'샤워수전','슬리퍼':'슬리퍼','책·문제집':'책','관리실 책상':'관리실책상','객실 책상':'객실책상','옷장':'옷장','싱글 침대 프레임':'침대프레임','원형 식탁':'식탁'}
placed=[]
def instance(c,key,x,y,z=0,yaw=0):
    o=bpy.data.objects.new(key,None);o.instance_type='COLLECTION';o.instance_collection=assets[key];c.objects.link(o)
    o.location=(x/100,y/100,z/100);o.rotation_euler.z=math.radians(yaw);return o
def scene(name):
    s=bpy.data.scenes.new(name);s.unit_settings.system='METRIC';s.unit_settings.length_unit='CENTIMETERS'
    s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.use_denoising=True
    s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
    s.world=bpy.data.worlds.new(name+' sky');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.48,.48,.48,1)
    s.world.node_tree.nodes['Background'].inputs[1].default_value=.8
    s.view_settings.view_transform='AgX'
    ld=bpy.data.lights.new('Soft sunlight','SUN');ld.energy=2;ld.angle=.3
    l=bpy.data.objects.new('Soft sunlight',ld);s.collection.objects.link(l);l.rotation_euler=(.4,-.5,-.3)
    return s
def coll(s,name):
    c=bpy.data.collections.new(name);s.collection.children.link(c);return c
def wall(c,x1,y1,x2,y2,m,opening=None,height=80,thick=10):
    if opening:
        mid,width=opening
        if y1==y2:
            wall(c,x1,y1,mid-width/2,y2,m,height=height,thick=thick);wall(c,mid+width/2,y1,x2,y2,m,height=height,thick=thick)
        else:
            wall(c,x1,y1,x2,mid-width/2,m,height=height,thick=thick);wall(c,x1,mid+width/2,x2,y2,m,height=height,thick=thick)
        return
    box(c,'Cutaway wall',((x1+x2)/2,(y1+y2)/2,height/2),(max(abs(x2-x1),thick),max(abs(y2-y1),thick),height),m)
def floorbuild(f):
    s=scene(f'{f}F / dimensioned layout');a=coll(s,'Architecture');furn=coll(s,'Furniture');labels=coll(s,'Measurements')
    wm=newwall if f==3 else wallmat
    box(a,'Slab',(1700,-335,-8),(4400,1130,16),green)
    wall(a,-500,-900,3900,-900,wm);wall(a,-500,-900,-500,230,wm)
    wall(a,3900,-900,3900,230,wm);wall(a,-500,230,3900,230,wm,opening=(0,190) if f==1 else None)
    if f<4:
        for i in range(12):
            l=350+i*230;wall(a,l,-70,l,230,wm,height=80)
            wall(a,l,-70,l+230,-70,wm,opening=(l+55,87),height=80)
            text(labels,str(f*100+i+1),(l+115,-43,2),27,white)
        wall(a,3110,-70,3110,230,wm)
        kend=1680 if f==1 else 2175;tl,tr=(1680,2550) if f==1 else (2575,3500);sl,sr=(2550,3500) if f==1 else (2175,2575)
        for l,r,n in [(430,kend,'주방'),(tl,tr,'화장실'),(sl,sr,'샤워실')]:
            wall(a,l,-900,l,-200,wm);wall(a,l,-200,r,-200,wm,opening=((l+r)/2,87))
            box(a,n+' floor',((l+r)/2,-550,.4),(r-l-10,690,.8),tile if n!='주방' else ivory)
            text(labels,n,((l+r)/2,-400,2),35)
        wall(a,3500,-900,3500,-200,wm)
        if f==1:
            wall(a,-35,-900,-35,-480,wm)
            wall(a,-500,-480,-35,-480,wm,opening=(-267.5,87))
            wall(a,-35,-480,100,-480,wm,opening=(35,87))
            box(a,'Office half wall',(262,-480,63),(324,10,126),wm)
            for x in [102,262,422]:box(a,'Window post',(x,-480,193),(4,10,134),edge)
            for z in [128,258]:box(a,'Window rail',(262,-480,z),(324,10,4),edge)
            # Glass omitted deliberately in dimensional review to retain visibility.
            text(labels,'관리실',(180,-790,2),27);text(labels,'창고',(-260,-690,2),27)
            for x in [-47.5,47.5]:box(a,'Entrance double leaf',(x,230,40),(90,5,80),wood)
        else:
            wall(a,-140,-480,-140,-200,wm,opening=(-330,87))
            wall(a,140,-480,140,-200,wm,opening=(-310,87))
            wall(a,-500,-200,140,-200,wm)
            wall(a,-500,-480,430,-480,wm,opening=(290,87))
        # Stair massing only, same opening and footprint; no circulation claim.
        for n in range(10):
            box(a,'Stair tread left',(3600,-300-n*50,(n+1)*8),(180,50,(n+1)*16),ivory)
            box(a,'Stair tread right',(3800,-300-n*50,(20-n)*8),(180,50,(20-n)*16),ivory)
        count=4 if f==1 else 2;pitch=(sr-sl-30)/count
        for n in range(1,count):wall(a,sl+15+n*pitch,-900,sl+15+n*pitch,-620,wm,height=65,thick=5)
        pitch=(tr-tl-210)/3
        for n in range(3):wall(a,tl+210+n*pitch,-900,tl+210+n*pitch,-620,wm,height=65,thick=5)
    else:
        wall(a,3500,-900,3500,-200,wm);wall(a,3500,-200,3900,-200,wm,opening=(3790,87))
        for y in [-300,-520,-740]:
            for x in [750,2150]:cyl(a,'Clothesline post',(x,y,100),3,200,metal)
            line(a,'Clothesline',(750,y,190),(2150,y,190),.6,metal)
        for x in [2800,3400]:
            for y in [-830,-400]:cyl(a,'Canopy post',(x,y,120),4,240,metal)
        text(labels,'옥상 세탁·건조 구역',(1700,120,2),40)
    for it in layout['items']:
        if it['floor']!=f:continue
        name=it['name'];w,d,h=[it[k] for k in ['width','depth','height']]
        key=mapping.get(name,name)
        if key not in assets:
            kind='shelf' if '선반' in name else 'monitor' if name in ['입주자 PC','CCTV 모니터 하단'] else 'fridge' if name=='냉장고' else 'wardrobe' if name=='상부장' else 'placeholder'
            asset(key,w,d,h,kind)
        z=45 if name=='매트리스·침구' else 75 if name in ['전화기','입주자 PC','CCTV 모니터 하단','책·문제집'] else 145 if name=='상부장' else 90 if name=='샤워 수전' else 0
        yaw=180 if name=='옷장' else 180 if name in ['주방 의자'] and it['y']< -550 else 0
        # Sink and shower face the room (+Y); office desk/chair front remains -Y/+Y respectively.
        if name in ['싱크대·하부장','조리대','상부장','냉장고','샤워 수전']:yaw=180
        instance(furn,key,it['x'],it['y'],z,yaw)
        placed.append(dict(it,z=z,yaw=yaw,asset=key))
    if f==1:
        box(furn,'Monitor tier shelf',(338,-502,107),(101,29,3),metal)
        for x in [321,355]:instance(furn,'CCTV 모니터 하단',x,-502,108.5)
        dim(labels,(138,-575,76),(402,-575,76),'264 cm')
    dim(labels,(-500,360,1),(3900,360,1),'4,400 cm / 44 m')
    text(labels,'치수 검토용 · 벽체는 일부 높이에서 절단 · 단위 cm',(1650,-1040,0),33)
    return s
floors=[floorbuild(i) for i in range(1,5)]

def render(s,filename,center,offset,scale,width=1600,height=900):
    bpy.context.window.scene=s
    cd=bpy.data.cameras.new(filename);cam=bpy.data.objects.new(filename,cd);s.collection.objects.link(cam)
    target=Vector(center)/100;cam.location=target+Vector(offset)/100
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.ortho_scale=scale/100;cd.clip_end=500
    s.camera=cam;s.render.resolution_x=width;s.render.resolution_y=height;s.render.filepath=str(OUT/(filename+'.png'))
    bpy.ops.render.render(write_still=True);print('RENDER_DONE '+filename,flush=True)

# Verify exact bounds before making review images. Shower's wall mounts and hose must fit its target envelope.
(OUT/'dimensions.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
failed=[a for a in audit if not a['within_0_1cm']]
if failed:raise RuntimeError('Dimension audit failed: '+json.dumps(failed,ensure_ascii=False))
(OUT/'placement.json').write_text(json.dumps(dict(source=str(SOURCE.relative_to(ROOT)),source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),credit_spend=0,items=placed),ensure_ascii=False,indent=2),encoding='utf-8')
catalog=[]
for key in ['의자42','침구','싱크대','샤워수전','슬리퍼','책']:
    s=scene('Asset / '+key);c=coll(s,'Model');instance(c,key,0,0)
    w,d,h=SPECS[key][:3];extent=max(w,d,h)
    box(c,'Studio floor',(0,0,-2),(extent*4,extent*4,4),ivory)
    catalog.append((s,key,w,d,h,extent))
    render(s,'asset-'+str(len(catalog)),(0,0,h/2),(extent*.9,-extent*1.5,extent),extent*1.6,720,720)
for i,s in enumerate(floors,1):render(s,f'floor-{i}',(1700,-335,40),(0,-1600,3200),4800,1920,800)
render(floors[0],'office',(0,-540,65),(450,-950,1400),1180,1500,1100)
render(floors[0],'room',(465,80,50),(440,-600,850),470,1400,1100)
render(floors[0],'kitchen',(1050,-565,45),(450,950,1800),1480,1500,1000)
render(floors[1],'wet-area',(2375,-660,65),(500,850,1100),840,1300,1000)
bpy.context.window.scene=floors[0]
floors[0].camera=bpy.data.objects['floor-1']
bpy.context.preferences.filepaths.save_version=0
bpy.context.preferences.filepaths.file_preview_type='NONE'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'haedam-dimensioned-furniture.blend'))
print('DIMENSIONED_REVIEW_COMPLETE',flush=True)
