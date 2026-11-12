"""Single-source review drawings. No runtime map or paid generation changes.
Coordinates in cm, sourced from NRLayout / BuildArchitecture / Room on 2026-10-22.
"""
from pathlib import Path
from html import escape
import json, hashlib

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Art/EnvironmentConcepts/unified-v15'
OUT.mkdir(parents=True, exist_ok=True)
OCC = {101,102,104,105,107,203,204,206,208,211,301,303,305,308,311}
SPARSE = {103,106,109,201,202,209,302,307,310}
inventory = []

def p(x,y): return x+660, 400-y
class Plan:
    def __init__(self,f): self.f=f; self.s=[]
    def add(self,s): self.s.append(s)
    def rect(self,x,y,w,h,fill,stroke='#82918c',sw=5,extra=''):
        a,b=p(x,y+h)
        self.add(f'<rect x="{a}" y="{b}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')
    def line(self,x1,y1,x2,y2,c='#a8b4aa',w=10,extra=''):
        a,b=p(x1,y1);d,e=p(x2,y2)
        self.add(f'<line x1="{a}" y1="{b}" x2="{d}" y2="{e}" stroke="{c}" stroke-width="{w}" {extra}/>')
    def text(self,x,y,t,size=34,c='#e9eadc',anchor='middle'):
        a,b=p(x,y)
        self.add(f'<text x="{a}" y="{b}" font-size="{size}" fill="{c}" text-anchor="{anchor}" dominant-baseline="middle">{escape(t)}</text>')
    def circle(self,x,y,r,fill,stroke='#cfb68b',w=4,extra=''):
        a,b=p(x,y); self.add(f'<circle cx="{a}" cy="{b}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{w}" {extra}/>')
    def route(self,points):
        pts=' '.join(f'{p(x,y)[0]},{p(x,y)[1]}' for x,y in points)
        self.add(f'<polyline class="route" points="{pts}" fill="none" stroke="#a4c5a8" stroke-opacity=".6" stroke-width="9" stroke-dasharray="18 18" marker-end="url(#arrow{self.f})"/>')
    def door(self,x,y,width=87,vertical=False,up=True,hinge_right=False):
        # Opening and schematic 90-degree sweep, not a claim about runtime hinge direction.
        self.add('<g class="doors">')
        if vertical:
            self.line(x,y-width/2,x,y+width/2,'#263a39',22)
            pts=[(x,y-width/2),(x+width,y-width/2),(x,y+width/2)]
        else:
            self.line(x-width/2,y,x+width/2,y,'#263a39',22)
            pts=[(x-width/2,y),(x-width/2,y+(width if up else -width)),(x+width/2,y)]
            if hinge_right:pts=[(x+width/2,y),(x+width/2,y+(width if up else -width)),(x-width/2,y)]
        a,b,c=[p(*v) for v in pts]
        self.add(f'<path d="M {a[0]} {a[1]} L {b[0]} {b[1]} Q {c[0]} {b[1]} {c[0]} {c[1]} Z" fill="#dcb66a" fill-opacity=".09" stroke="#dcb66a" stroke-width="3" stroke-dasharray="7 5"/>')
        self.line(*pts[0],*pts[1],'#dcb66a',5)
        self.add('</g>')
    def item(self,name,x,y,w,d,h,proposed=False,label='',note=''):
        inventory.append(dict(floor=self.f,name=name,x=x,y=y,width=w,depth=d,height=h,status='제작·배치 제안' if proposed else '현행 배치 기준 / 외형 치수 확인 필요',note=note))
        self.add(f'<g class="furniture {"proposed" if proposed else "existing"}"><title>{escape(name)} | {w}×{d}×{h} cm{escape(" · "+note if note else "")}</title>')
        self.rect(x-w/2,y-d/2,w,d,'#33514c' if proposed else '#685943','#80c4ad' if proposed else '#c2a379',3,'stroke-dasharray="9 6"' if proposed else '')
        if label:self.text(x,y,label,min(25,w*.29), '#dfede4')
        self.add('</g>')
    def dim(self,x1,y1,x2,y2,label):
        self.add('<g class="dimensions">')
        self.line(x1,y1,x2,y2,'#8d9b9d',2)
        vertical=x1==x2
        for x,y in [(x1,y1),(x2,y2)]:self.line(x-10 if vertical else x,y if vertical else y-10,x+10 if vertical else x,y if vertical else y+10,'#8d9b9d',2)
        self.text((x1+x2)/2+(60 if vertical else 0),(y1+y2)/2+(0 if vertical else 31),label,30,'#b9c5c2')
        self.add('</g>')

def build(f):
    q=Plan(f)
    q.add(f'<defs><marker id="arrow{f}" markerWidth="8" markerHeight="8" refX="5" refY="3" orient="auto"><path d="M0 0 L6 3 L0 6" fill="none" stroke="#a4c5a8"/></marker></defs>')
    q.rect(-500,-900,4400,1130,'#243b38',sw=14)
    q.dim(-500,330,3900,330,'외벽 중심선 4,400 cm / 44.0 m')
    q.dim(4000,-900,4000,230,'1,130')
    q.text(4050,-1010,'cm',28,'#9faaa8')
    q.text(-480,-1010,'도면 위쪽 = 현관측 / 객실 창측     ·     +X →  /  +Y ↑',30,'#9faaa8','start')
    q.line(-480,-1110,20,-1110,'#d5ddcd',9)
    for x in [-480,-380,-280,-180,-80,20]:q.line(x,-1098,x,-1122,'#d5ddcd',3)
    q.text(-230,-1160,'축척 막대 500 cm',28,'#9faaa8')
    if f==4:
        q.rect(3500,-900,400,700,'#383f49',sw=12)
        q.door(3790,-200,up=True)
        q.text(3700,-400,'계단실',40)
        q.text(3700,-470,'400 × 700',30)
        q.rect(2800,-830,600,430,'#33454a','#849b9e',5,'stroke-dasharray="14 9"')
        q.text(3100,-490,'차양 아래 세탁 구역',32)
        q.item('세탁기',2900,-750,65,70,95,True,'세탁기')
        q.item('세제 수납장',3300,-750,80,40,120,True,'세제')
        for y in [-300,-520,-740]:
            q.line(750,y,2150,y,'#b9b4a1',5)
            for x in [750,2150]:q.circle(x,y,9,'#c4b99d')
        q.text(1450,-155,'빨랫줄 · 조사 공간',45)
        for x,y in [(1000,-300),(1600,-520),(1900,-740)]:q.item('널린 빨래',x,y,90,8,130,True,'')
        q.item('접이식 건조대',400,-600,150,60,110,True,'건조대')
        q.route([(3790,-130),(2450,-130),(2450,-600),(2300,-600)])
        q.text(1050,130,'난간 유지 · 중앙 이동 동선 비움',34)
        q.text(-300,-300,'서측 난간',32)
        q.text(-300,-365,'비상계단 연결 미구현',24,'#e3ba7e')
        q.text(1800,-1070,'옥상 서측 외부 계단은 현재 코드에서 1~3층만 연결됨. 관통 출입구가 있는 것처럼 표시하지 않음.',27,'#e3ba7e')
    else:
        q.rect(3110,-70,790,300,'#2d4942','#6d847a',3)
        q.text(3490,120,'확장 복도 끝',40)
        q.text(3490,40,'790 × 300 · 가구 비움',30)
        q.text(1710,-130,'단일 복도 · 벽 중심 간격 130 cm',32,'#b8d6c8')
        q.route([(260,-130),(3430,-130),(3700,-130),(3700,-240)])
        for i in range(12):
            l=350+i*230;n=f*100+i+1;occ=n in OCC;sparse=n in SPARSE
            q.rect(l,-70,230,300,'#454b40' if occ else '#3b3736' if sparse else '#293234',sw=8)
            q.door(l+55,-65,up=True)
            q.line(l+149,230,l+209,230,'#87c9d1',10)
            q.text(l+115,280,f'{n}',35,'#e1cc9a' if n in [202,307] else '#e0e6d8')
            q.text(l+115,247,'230 × 300',18,'#9faaa8')
            q.text(l+115,5,'거주' if occ else '조사' if sparse else '공실',27,'#afc6ad' if occ else '#d3ac8d')
            if occ or sparse:
                q.item('싱글 침대 프레임',l+179,122,90,200,45,False,'프레임' if sparse else '')
                if occ:q.item('매트리스·침구',l+179,122,88,195,18,True,'침구')
                q.item('객실 책상',l+58,197,106,55,75,False,'책상','권장 외형; 현행 메시 실측 전')
            if occ:
                for x in [154.5,201.5]:q.item('옷장',l+x,-40,45,45,175,False,'장','침대 발치에 나란히, 간격2cm. 문은 침대 방향. 발치 여유39.5cm로 90도 개방 불가')
                q.item('객실 의자',l+75,185,42,44,80,True,'','책상 아래 유지. 옷장은 침대 발치로 이전하여 의자 뒤쪽 공간 확보')
                q.item('책·문제집',l+88,205,30,22,25,True)
                q.item('슬리퍼',l+115,-30,24,28,10,True)
                q.item('작은 쓰레기통',l+112,35,20,20,28,True)
            if n==202:q.item('사건용 의자',l+95,55,42,44,80,True,'의자')
        q.rect(3500,-900,400,700,'#383f49',sw=12)
        # Stair mouth deliberately open on north side.
        q.line(3510,-200,3890,-200,'#243b38',20)
        for y in range(-325,-700,-50):
            q.line(3520,y,3695,y,'#84918f',3);q.line(3710,y,3880,y,'#84918f',3)
        q.route([(3610,-270),(3610,-780),(3790,-780),(3790,-270)])
        q.text(3700,-860,'계단 400 × 700',29)
        q.door(-500,-135,vertical=True)
        q.text(-600,-310,'외부',27);q.text(-600,-355,'비상계단',24)
        if f==1:
            q.line(-95,230,95,230,'#243b38',22)
            q.door(-50,230,90,up=True);q.door(50,230,90,up=True,hinge_right=True)
            q.text(-190,150,'양문 190',31)
            q.text(-30,-70,'현관 홀',43)
            q.text(-30,-155,'앞쪽 작은 방 2칸 제거',27)
            q.rect(-500,-900,465,420,'#424442',sw=12)
            q.rect(-35,-900,465,420,'#464638',sw=12)
            q.door(-267.5,-480,up=False);q.door(35,-480,up=False)
            q.line(100,-480,424,-480,'#8ccad0',14)
            q.text(260,-430,'반벽 + 유리',27,'#8ccad0')
            q.text(-270,-650,'창고',43);q.text(210,-740,'관리실',43)
            q.text(-270,-700,'465 × 420',28);q.text(200,-790,'465 × 420',28)
            q.item('관리실 책상',270,-515,264,55,75,False,'')
            q.item('전화기',170,-524,30,21,12,False,'전화','상판 위; 외형은 도면 참고치')
            q.item('입주자 PC',215,-504,42,20,38,False,'PC','상판 위; 외형은 도면 참고치')
            for mx in [304,338,372]:q.item('CCTV 모니터 하단',mx,-502,28,27,30,False,'C','하단3대 위 선반에2대 추가; 도면은 상판 점유 기준')
            q.text(290,-572,'책상264×55 / CCTV 3+2단',20,'#c8b48f')
            q.item('총무 의자',270,-650,45,45,90,False,'의자')
            q.item('수납 선반',380,-800,35,80,155,False)
            q.item('청소 선반',-380,-790,80,35,155,False,'선반')
            q.item('공구함',-165,-790,50,30,32,False)
            q.item('청소도구',-440,-620,35,70,140,True)
            q.line(235,-889,305,-889,'#dab766',8)
            q.text(220,-860,'수칙표',25,'#e4ca90')
            q.route([(0,180),(35,-360),(35,-620),(180,-620)])
            q.text(1000,-1070,'현관을 등지고 안쪽을 볼 때: 왼쪽 창고 / 오른쪽 관리실. 이 도면은 좌우 반전하지 않음.',29,'#e3ba7e')
        else:
            q.rect(-500,-480,360,280,'#414441',sw=10)
            q.rect(-140,-480,280,280,'#444637',sw=10)
            q.rect(-500,-900,930,420,'#414441',sw=10)
            q.door(140,-310,vertical=True);q.door(-140,-330,vertical=True);q.door(290,-480,up=False)
            q.text(-320,-270,'옆 수납방',29);q.text(0,-245,'관리 수납실',26)
            q.text(-40,-650,'후면 창고 930 × 420',36)
            q.item('창고 선반',-400,-790,80,35,155,True,'선반')
            q.item('보관 상자',-200,-810,60,40,50,True,'상자')
            q.route([(270,-135),(270,-310),(90,-310),(-200,-330)])
            q.route([(290,-360),(290,-650)])
        kend=1680 if f==1 else 2175
        tl,tr=(1680,2550) if f==1 else (2575,3500)
        sl,sr=(2550,3500) if f==1 else (2175,2575)
        for l,r,name in [(430,kend,'주방'),(tl,tr,'화장실'),(sl,sr,'샤워실')]:
            q.rect(l,-900,r-l,700,'#434842' if name=='주방' else '#35494a',sw=12)
            q.door((l+r)/2,-200,up=False)
            q.text((l+r)/2,-300,name,42 if r-l>500 else 32)
            q.text((l+r)/2,-350,f'{r-l:g} × 700 cm',29 if r-l>500 else 23)
        cx=900 if f==1 else 1350
        q.item('조리대',cx,-840,240,65,88,False,'조리대')
        q.item('싱크대·하부장',cx-195,-840,120,60,85,True,'싱크대')
        q.item('상부장',cx,-875,120,30,70,True,'상부장','벽 부착; 바닥 점유 아님')
        q.item('냉장고',kend-55,-815,70,65,165,False,'냉장고','제작 참고 외형; 기존 메시 확인 필요')
        for tx in ([760,1330] if f==1 else [900,1700]):
            q.add('<g class="furniture existing"><title>원형 식탁 Ø200 × 높이75 cm</title>')
            q.circle(tx,-550,100,'#685943');q.text(tx,-550,'Ø200',32);q.add('</g>')
            inventory.append(dict(floor=f,name='원형 식탁',x=tx,y=-550,width=200,depth=200,height=75,status='현행 확정',note='원본 Ø150을 가로세로 4/3 확대'))
            for cy in [-415,-685]:q.item('주방 의자',tx,cy,42,44,80,True)
        q.route([((430+kend)/2,-245),((430+kend)/2,-690)])
        pitch=(tr-tl-210)/3
        q.item('세면대',tl+60,-620,55,60,85,False,'세면대','현행 중심 위치 / 교체용 권장 외형')
        for n in range(3):
            tx=tl+210+(n+.5)*pitch
            q.line(tx-pitch/2,-900,tx-pitch/2,-620,'#8ba19b',7)
            q.item('변기',tx,-840,42,70,75,False,'변기')
            q.route([(tx,-820),(tx,-730)])
        count=4 if f==1 else 2; pitch=(sr-sl-30)/count
        for n in range(count):
            sx=sl+15+(n+.5)*pitch
            if n:q.line(sx-pitch/2,-900,sx-pitch/2,-620,'#8ba19b',7)
            q.item('샤워 수전',sx,-875,25,15,110,True,'수전','외벽 부착; 레일 길이110, 헤드 높이 약200')
            q.line(sx-pitch/2+5,-620,sx+pitch/2-5,-620,'#81a5aa',4,'stroke-dasharray="10 8"')
            q.route([(sx,-820),(sx,-730)])
        q.text((tl+tr)/2,-530,'안쪽 통로 → 각 칸',27)
        q.text((sl+sr)/2,-530,'탈의·진입',25)
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4900 1650" role="img" aria-label="{f}층 통합 가구 배치도" style="font-family:Malgun Gothic,sans-serif"><rect width="4900" height="1650" fill="#192927"/>'+''.join(q.s)+'</svg>'
    (OUT/f'floor-{f}.svg').write_text(svg,encoding='utf-8')
    return svg

svgs=[build(f) for f in range(1,5)]
sources=['NightRulesPrototype/Source/NightRulesPrototype/NRGame.h','NightRulesPrototype/Source/NightRulesPrototype/NRGame.cpp','NightRulesPrototype/Source/NightRulesPrototype/NRArchitecture.cpp']
manifest={'version':'unified-v15','date':'2026-10-22','unit':'cm','source_sha256':{s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in sources},'items':inventory,'note':'구조는 현행 코드. 새 소품·점선 동선·문 회전 영역은 검토 제안. 런타임 충돌 검증 및 메시 외형 실측 미실시.'}
(OUT/'furniture-layout.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')

sizes=[
('건물 외곽','4,400 × 1,130','벽 중심선 기준. 층고 320 / 실내 벽 높이 260','현행 코드'),
('객실 1칸','230 × 300','벽 중심선 면적 6.9㎡; 실제 내부 유효 치수는 벽 두께만큼 작음','현행 코드'),
('단일 복도','폭 130','벽 중심 간격. 마감·충돌 두께 제외 시 약118~119; 최종 메시 검증 필요','현행 코드'),
('관리실 / 창고','각 465 × 420','1층 기존 창고 양분. 초기 280×280 관리실 안은 폐기','현행 코드'),
('1층 주방 / 화장실 / 샤워실','1,250×700 / 870×700 / 950×700','샤워 4칸. 주방 깊이가 큰 현행 비율을 그대로 표시','현행 코드'),
('2·3층 주방 / 샤워실 / 화장실','1,745×700 / 400×700 / 925×700','샤워 층당2칸. 1층과 위생공간 순서 다름','현행 코드'),
('계단실 / 확장 복도 끝','400×700 / 790×300','계단참 진입과 복도 끝에는 고정 가구를 놓지 않음','현행 코드'),
('일반 출입구','폭87 × 높이205.5','문틀 포함 개구부. 문짝은 이보다 작게 맞춤','현행 코드'),
('현관 양문 개구부','폭190 × 높이226','문짝 90씩 2개; 개구부 수치와 구분','현행 코드'),
('관리실 유리 프레임','폭324 × 높이134','X100~424 / 높이126~260. 하부벽 약130','현행 코드'),
('관리실 책상','264 × 55 × 75','창 안쪽 배치. 서랍 분리; 옛 268cm 방 폭 설명은 현행 아님','확정 치수'),
('원형 식탁','지름200 × 높이75','층당2개 / 총6개. 원본150에서 확대된 현재 크기','확정 치수'),
('옷장','45 × 45 × 175, 2개','침대 발치에 나란히. 2cm 간격 포함 총92cm. 발치 여유39.5cm','확정 치수'),
('객실 책상 / 침대 프레임','106×55×75 / 90×200×45','객실 여유에 맞춘 외형 목표. 기존 메시 실측 후 조정','제작 권장'),
('의자 / 침구','42×44×80 / 88×195×18','좌판 높이45. 침구는 90×200 프레임 안에 수용','제작 권장'),
('싱크대 / 상부장','120×60×85 / 120×30×70','문 분리. 상부장 설치 하단 약145cm; 조리대와 높이 맞춤','제작 권장'),
('샤워 수전 / 변기 / 세면대','25×15×110 / 42×70×75 / 55×60×85','샤워 레일 전체 높이110; 헤드 설치 높이 약200','제작 권장'),
('슬리퍼 / 책 묶음 / 쓰레기통','한짝11×28×10 / 30×22×25 / 20×20×28','도면 슬리퍼는 한 쌍24×28. 문 회전 범위 밖에 배치','제작 권장'),
('세탁기 / 건조대','65×70×95 / 150×60×110','옥상 차양 안 세탁기, 빨랫줄 주변 이동 공간 유지','제작 권장'),
]
rows=''.join('<tr>'+''.join(f'<td>{escape(v)}</td>' for v in row)+'</tr>' for row in sizes)
panels=''.join(f'<section class="floor" id="f{i}" {"hidden" if i!=1 else ""}>{s}</section>' for i,s in enumerate(svgs,1))
html='''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>해담고시원 | 통합 설계·가구 배치 v15</title>
<style>
:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#101b19;color:#e8ecdf;font:15px/1.7 'Malgun Gothic',sans-serif}main{max-width:1700px;margin:auto;padding:32px}header{display:flex;align-items:end;justify-content:space-between;gap:30px;border-bottom:1px solid #3b4b44;padding-bottom:22px}small,.sub{color:#9bad9e}h1{font-size:32px;line-height:1.3;margin:8px 0}h2{font-size:21px;margin:30px 0 12px}p{margin:8px 0}.tag{font-size:12px;color:#d4bf8a;letter-spacing:2px}.status{background:#24382f;padding:12px 18px;border:1px solid #476050;max-width:410px}.toolbar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;padding:20px 0}button,select,a.download{background:#21332c;border:1px solid #526557;color:#e1e8d6;border-radius:5px;padding:10px 16px;font:inherit;cursor:pointer;text-decoration:none}button[aria-pressed=true]{background:#d3c29b;color:#17231e;border-color:#d3c29b}.legend{display:flex;gap:24px;flex-wrap:wrap;font-size:13px;color:#b4c1b6}.dot{display:inline-block;width:12px;height:12px;background:#b99b70;margin-right:7px}.new{background:#80c4ad}.win{background:#87c9d1}.door{background:#dcb66a}.viewer{background:#192927;border:1px solid #43574c;border-radius:7px;overflow:hidden;margin:14px 0}.floor svg{width:100%;height:auto;display:block;min-height:280px;max-height:72vh}.viewer.zoom .floor svg{height:66vh}.caption{padding:14px 20px;background:#1f3029;border-top:1px solid #43574c}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.card{background:#1c2d25;border:1px solid #354a3e;padding:18px}.card strong{color:#dac69b}.card p{color:#b5c4b6;font-size:14px}.warning{border-left:3px solid #d1af76;padding:12px 18px;background:#322e22;color:#ddd1b7;margin:20px 0}.tablewrap{overflow:auto}table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;padding:13px 16px;border-bottom:1px solid #35473b}th{background:#25382c;color:#dbccaa}td:nth-child(2){font-variant-numeric:tabular-nums;white-space:nowrap;color:#d2dfcc}td:last-child{white-space:nowrap;color:#a8c8b2}a{color:#a9d6bc}.hide-proposed .proposed,.hide-routes .route,.hide-dimensions .dimensions{display:none}footer{font-size:12px;color:#849b8c;padding:28px 0}label{cursor:pointer;font-size:13px}input{accent-color:#b6c6a6} @media(max-width:800px){main{padding:16px}.cards{grid-template-columns:1fr}header{display:block}h1{font-size:25px}.floor svg{min-height:200px}.status{margin-top:15px}}@media print{.toolbar{display:none}.floor[hidden]{display:block}.floor svg{max-height:none}.cards{display:block}}
</style><main><header><div><div class="tag">HAEDAM GOSIWON / SPATIAL MASTER 15</div><h1>하나의 도면, 같은 배치.</h1><p class="sub">3개 층 + 옥상 · 최신 구조 통합 · 가구 배치와 제작 치수</p></div><div class="status"><b>2026.10.22 기준</b><br>구조: 현행 게임 코드 대조<br>새 소품: 제작·배치 제안 / 게임 적용 전</div></header>
<div class="toolbar"><button data-floor="1" aria-pressed="true">1층</button><button data-floor="2" aria-pressed="false">2층</button><button data-floor="3" aria-pressed="false">3층 · 리모델링</button><button data-floor="4" aria-pressed="false">옥상</button><select id="zoom" aria-label="확대 구역"><option value="all">전체 평면</option><option value="office">현관·관리/수납</option><option value="room">객실 확대</option><option value="kitchen">주방 확대</option><option value="wet">화장실·샤워실</option><option value="stairs">계단·복도 끝</option></select><a class="download" id="download" href="../Art/EnvironmentConcepts/unified-v15/floor-1.svg" download>도면 SVG 저장</a></div>
<div class="legend"><span><i class="dot"></i>기존 가구 기준</span><span><i class="dot new"></i>점선: 새 소품·교체 제안</span><span><i class="dot win"></i>창 / 반벽 유리</span><span><i class="dot door"></i>문 개구부·회전 여유 예시</span><label><input id="proposed" type="checkbox" checked> 새 소품 표시</label><label><input id="routes" type="checkbox" checked> 이동 동선</label><label><input id="dimensions" type="checkbox" checked> 치수</label></div>
<div class="viewer" id="viewer">PANELS<div class="caption" id="caption"></div></div>
<p class="sub">확대는 위 전체 도면의 동일한 도형을 확대합니다. 가구에 마우스를 올리면 크기를 볼 수 있습니다. 길이 단위는 모두 cm입니다.</p>
<div class="cards"><article class="card"><strong>01 / 관리실 방향 확정</strong><p>현관을 등지고 안쪽을 볼 때 왼쪽 창고, 오른쪽 관리실. 중앙 칸막이 유지. 앞쪽 작은 방 두 칸을 없앤 넓은 현관 홀과 양문을 반영했습니다.</p><p>CCTV는 아래 3대·위 2대. 모니터 1=관리실 / 2=1층 / 3=2층 / 4=3층 / 5=옥상계단. 층별 모니터에서 복도·주방만 전환합니다.</p></article><article class="card"><strong>02 / 방마다 사용 흔적</strong><p>층당 거주 5실 / 총15명. 거주실: 침구·책·슬리퍼. 옷장 두 개는 침대 발치에 나란히. 202·307호를 포함한 조사 공실은 빈 프레임과 책상만 유지합니다.</p><p>202호에는 사건용 의자만 추가. 좁은 방에 선풍기·가방 등 모든 소품을 일괄로 넣지 않습니다.</p></article><article class="card"><strong>03 / 공용공간과 옥상</strong><p>층별 원형 식탁2개. 싱크대·조리대는 출입구 반대쪽 벽. 변기와 샤워는 외벽을 등지고 내부 통로를 향합니다. 화장실 안에는 샤워가 없습니다.</p><p>3층은 깨끗한 리모델링 마감. 옥상은 빨랫줄·차양·세탁 공간. 계단과 복도 끝은 비워 둡니다.</p></article></div>
<div class="warning"><b>치수 확인:</b> 관리실은 최신 코드에서 465×420cm입니다. 초기의 아주 작은 관리실과는 크기가 다르지만, 이번 도면에서 임의로 줄이지 않았습니다. 원형 식탁도 현재 게임의 지름200cm를 유지했습니다. 건물 전체44m 길이와 큰 주방 역시 현행 코드 비율입니다.</div>
<h2>공간·가구 제작 치수</h2><p class="sub">공간은 벽 중심선 기준, 가구는 외형 최대 가로×깊이×높이 기준입니다. ‘제작 권장’은 기존 모델 실측값이 아닌 다음 생성·보정 작업의 목표입니다.</p><div class="tablewrap"><table><thead><tr><th>대상</th><th>치수 (cm)</th><th>제작·배치 조건</th><th>근거</th></tr></thead><tbody>ROWS</tbody></table></div>
<h2>생성 후 크기를 맞추는 기준</h2><p>Tripo·Meshy 결과의 크기를 그대로 믿지 않고 Blender에서 위 치수로 맞춘 뒤 스케일을 적용합니다. Unreal은 1유닛=1cm 기준으로 가져옵니다. 문·서랍·옷장문·냉장고문은 본체와 분리하고 회전축·이동축을 잡습니다. 실제 메시의 최대 외형, 문 회전, 서랍을 연 상태, 플레이어 충돌체로 통행을 확인한 후 게임에 반영합니다.</p>
<p class="sub">점선 동선과 문 회전 표시는 배치 검토용입니다. 실제 경첩 방향과 충돌 검증을 완료했다는 의미는 아닙니다. 2·3층 창고 가구와 옥상 세탁 소품은 신규 제안입니다.</p>
<footer>근거: NRGame.h의 NRLayout / NRArchitecture.cpp의 BuildArchitecture / NRGame.cpp의 Room·BuildWorld / 관리실 v5·창틀 v6 수정 기록.<br><a href="../Art/EnvironmentConcepts/unified-v15/furniture-layout.json">가구 좌표·치수 데이터</a> · <a href="floor-plan-unified-v15.md">통합 기록</a> · 기존 v10~v14 이미지는 과거 검토 기록으로 보존하며 제작 기준은 이 페이지로 통일합니다.</footer></main>
<script>
let floor=1; const notes={1:'1층 / 현관 양문 · 창고와 관리실 분리 · 주방 → 화장실 → 샤워실 → 주계단',2:'2층 / 관리 수납실을 통해 옆 수납방 진입 · 주방 → 샤워실 → 화장실 · 202호 공실 / 203호 민서 거주',3:'3층 / 2층과 같은 구조 · 리모델링 마감 · 307호 공실, 침구·옷장 없음',4:'옥상 / 빨랫줄과 차양은 현행 구조 · 세탁기·건조대·빨래는 추가 제안'};
function update(){document.querySelectorAll('.floor').forEach(e=>e.hidden=e.id!=='f'+floor);document.querySelectorAll('[data-floor]').forEach(e=>e.setAttribute('aria-pressed',Number(e.dataset.floor)===floor));document.querySelector('#caption').textContent=notes[floor];document.querySelector('#download').href='../Art/EnvironmentConcepts/unified-v15/floor-'+floor+'.svg';let z=document.querySelector('#zoom').value;const views={all:'0 0 4900 1650',office:'90 20 1040 1360',room:'965 100 780 480',kitchen:floor===1?'1050 540 1330 800':'1050 540 1830 800',wet:floor===1?'2300 540 1900 800':'2790 540 1410 800',stairs:'3710 100 920 1260'};if(floor===4&&z==='room')z='all';document.querySelector('#f'+floor+' svg').setAttribute('viewBox',views[z]);document.querySelector('#viewer').classList.toggle('zoom',z!=='all');}
document.querySelectorAll('[data-floor]').forEach(b=>b.onclick=()=>{floor=Number(b.dataset.floor);update()});document.querySelector('#zoom').onchange=update;['proposed','routes','dimensions'].forEach(id=>document.querySelector('#'+id).onchange=e=>document.querySelector('#viewer').classList.toggle('hide-'+id,!e.target.checked));update();
</script></html>'''.replace('PANELS',panels).replace('ROWS',rows)
(ROOT/'docs/floor-plan.html').write_text(html,encoding='utf-8')
print(f'Wrote canonical floor-plan.html, 4 SVGs, {len(inventory)} furniture footprints')
