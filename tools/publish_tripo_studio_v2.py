import json,sys,html
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.font_manager import FontProperties
ROOT=Path(sys.argv[1]);OUT=ROOT/'Art/AssetConcepts/tripo-studio-v2'
a=json.loads((OUT/'exterior-audit.json').read_text('utf-8'))
fp=FontProperties(fname='C:/Windows/Fonts/malgun.ttf')
plt.rcParams.update({'font.family':fp.get_name(),'axes.unicode_minus':False,'figure.facecolor':'#192521','axes.facecolor':'#202e28','text.color':'#ecebde','axes.labelcolor':'#d1dccb','xtick.color':'#b7c3b2','ytick.color':'#b7c3b2','axes.edgecolor':'#647567'})
fig,(ax,roof)=plt.subplots(2,1,figsize=(20,10),gridspec_kw={'height_ratios':[1.1,1]},layout='constrained')
for f in range(3):
 z=f*320;ax.add_patch(Rectangle((-500,z),4400,320,facecolor=['#8b8069','#8b8069','#cacabe'][f],edgecolor='#344a41'))
for w in a['windows']:
 x,y,z=w['center_cm'];ax.add_patch(Rectangle((x-30,z-40),60,80,facecolor='#273f40',edgecolor='#dfd7b9',lw=.6))
ax.add_patch(Rectangle((-95,0),190,226,facecolor='#4f6b61',edgecolor='#ddd3b7'))
ax.add_patch(Rectangle((-500,960),4400,110,facecolor='#a69b7f',edgecolor='#68745e'))
ax.add_patch(Rectangle((3500,960),400,300,facecolor='#c7c6b9',edgecolor='#dfd7b9'))
ax.annotate('옥상 계단실\n최상단1260cm',xy=(3700,1260),xytext=(3350,1420),arrowprops={'arrowstyle':'->','color':'#cdddbe'},ha='center',fontsize=11)
ax.annotate('현관 양문190×226',xy=(0,110),xytext=(-80,-150),arrowprops={'arrowstyle':'->','color':'#cdddbe'},ha='center',fontsize=11)
for z in [480,800]:
 ax.add_patch(Rectangle((-190,z-40),230,80,facecolor='none',edgecolor='#f29d78',lw=1.5,linestyle='--'))
ax.annotate('상층 창문패널2곳:\n뒤쪽 통벽으로 막힘(코드 이슈)',xy=(-75,800),xytext=(-540,1220),arrowprops={'arrowstyle':'->','color':'#f29d78'},ha='center',fontsize=11,color='#f4b79a')
ax.set_xlim(4100,-1000);ax.set_ylim(-220,1550);ax.set_aspect('equal');ax.set_title('정면 대조 · 객실 창36개 / 각60×80cm / 층간320cm',loc='left',fontsize=16,pad=15)
ax.set_xlabel('X (cm) · 정면에서 바라본 방향으로 표시');ax.set_ylabel('Z (cm)')
roof.add_patch(Rectangle((-500,-900),4400,1130,facecolor='#496358',edgecolor='#d2c9b0',lw=2))
roof.add_patch(Rectangle((3500,-900),400,700,facecolor='#9b9f91',edgecolor='#e2dfc9',lw=2))
roof.add_patch(Rectangle((3500,-900),400,600,facecolor='#26352f',edgecolor='#b5c3a5',hatch='//'))
roof.add_patch(Rectangle((3500,-300),400,100,facecolor='#ccc7b6',edgecolor='#f4eacf'))
roof.plot([3746.5,3833.5],[-200,-200],color='#ffbc69',lw=6)
roof.add_patch(Rectangle((2775,-855),650,480,facecolor='#76929b',edgecolor='#bad8df',lw=2,alpha=.8))
for y in [-300,-520,-740]:
 roof.plot([750,2150],[y,y],color='#dfddc7',lw=2);roof.scatter([750,2150],[y,y],s=20,color='#e0dec1')
for f in range(3):
 roof.add_patch(Rectangle((-800,-225),300,180,facecolor='none',edgecolor='#ceb78a',lw=1))
roof.text(1450,-490,'빨랫줄 3줄\n각14m · 바닥 위180cm',ha='center',va='center',fontsize=13,bbox={'facecolor':'#263a31','alpha':.9,'edgecolor':'none'})
roof.annotate('계단실4×7m\n계단 개구부4×6m',xy=(3690,-650),xytext=(3700,-1150),arrowprops={'arrowstyle':'->','color':'#d9e1c7'},ha='center',fontsize=11)
roof.annotate('차양6.5×4.8m',xy=(3100,-615),xytext=(2930,-1100),arrowprops={'arrowstyle':'->','color':'#d9e1c7'},ha='center',fontsize=11)
roof.annotate('옥상 출입문\n(3790,-200)',xy=(3790,-200),xytext=(3500,500),arrowprops={'arrowstyle':'->','color':'#ffbc69'},ha='center',fontsize=11,color='#ffcd8c')
roof.text(-650,100,'비상계단측\n현관측',ha='center',fontsize=11)
roof.set_xlim(-1000,4100);roof.set_ylim(-1300,650);roof.set_aspect('equal');roof.set_title('옥상 평면 대조 · +X → / +Y ↑ · 바닥Z=960cm',loc='left',fontsize=16,pad=10);roof.set_xlabel('X (cm)');roof.set_ylabel('Y (cm)')
fig.savefig(OUT/'window-roof-audit.png',dpi=140);plt.close(fig)
rel='../Art/AssetConcepts/tripo-studio-v2/'
cards=''
for name,size,img,source,desc in [('세탁기','65×70×95','washer-quality.png','A03.png','드럼·고무 패킹·조작부·판금 이음새'),('세제 수납장','80×40×120','cabinet-quality.png','A05.png','양문 경첩·잠금장치·도장 마모·통풍구'),('공구함','50×30×32','toolbox-quality.png','A06.png','걸쇠·접이식 손잡이·철판 보강·사용 흔적')]:
 cards+=f'<article><a href="{rel}{img}"><img src="{rel}{img}" alt="{name} 고품질 이미지"></a><div><h3>{name}</h3><p>목표 {size} cm · {desc}</p><details><summary>기존 치수 모델 비교</summary><img src="../Art/AssetConcepts/tripo-studio-v1/{source}" alt="기존 치수 모델"><p>AI 이미지는 질감·형태 기준. 실측 치수는 기준 Blender 모델과 별도 검수한다.</p></details></div></article>'
beauty=''
if (OUT/'exterior-quality.png').exists():beauty=f'<figure><img src="{rel}exterior-quality.png"><figcaption>AI 외관 재질 시안. 창·옥상 위치의 최종 기준은 아래 코드 대조본이다. 이미지의 미세한 창 개수·간격·난간 변형은 승인된 구조 변경이 아니다.</figcaption></figure>'
page=f'''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>해담고시원 · 이미지 품질 개선과 외관 대조 v2</title><style>*{{box-sizing:border-box}}body{{margin:0;background:#17231e;color:#e6e7db;font-family:'Malgun Gothic',sans-serif;line-height:1.75}}main{{max-width:1450px;margin:auto;padding:45px 28px 80px}}h1{{font-size:35px}}h2{{margin-top:58px}}a{{color:#c4d7a8}}.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}}article{{background:#29392e;border:1px solid #50604d;border-radius:8px;overflow:hidden}}article img,figure img{{width:100%;display:block}}article div{{padding:16px 22px}}article h3{{font-size:23px;margin:0}}figure{{margin:22px 0}}figcaption{{font-size:14px;color:#b9c8b4;padding:12px 0}}.note{{padding:18px 24px;border-left:3px solid #ccb477;background:#30372b}}table{{width:100%;border-collapse:collapse}}th,td{{padding:14px;border-bottom:1px solid #52614e;text-align:left}}summary{{cursor:pointer}}small{{color:#adbf9e}}@media(max-width:800px){{.grid{{grid-template-columns:1fr}}}}</style><main><small>생성 전 이미지 검토 · Tripo 생성0 · 게임 코드 변경0</small><h1>소품 디테일 개선 / 외관과 맵 좌표 대조</h1><p>기존6종 중 조사 화면에서 눈에 띄는3종부터 이미지 생성 도구로 질감을 개선했다. 아래는 Tripo 모델이 아니라 승인 전 참조 이미지다. 목표 치수는 유지하며, AI가 정밀 치수나 개폐 구조를 보장한다는 뜻은 아니다.</p><div class="grid">{cards}</div>
<h2>외관 재질 시안</h2>{beauty}<p>하부 두 층은 사용감 있는 마감,3층은 리모델링한 밝은 마감. 건물 전체 이미지는 디자인 검토용이다. Tripo 제작은 외벽/창문벽·옥상 계단실·차양 등 필요한 모듈로 나누고, 각 모듈 이미지와 비용을 먼저 검토한 뒤 진행한다.</p>
<h2>실제 코드와 달랐던 부분</h2><table><tr><th>항목</th><th>이전 시안</th><th>코드 기준으로 바로잡은 값</th></tr><tr><td>객실 창</td><td>60×90cm / 바닥 기준중심145cm</td><td>60×80cm / 중심160cm / 하단120cm / 총36개</td></tr><tr><td>옥상 계단실</td><td>누락</td><td>4×7m, 출입문(3790,-200), 최상단1260cm</td></tr><tr><td>옥상 바닥</td><td>전체를 막은 판</td><td>계단 개구부4×6m 유지, 북측 참1m</td></tr><tr><td>빨랫줄</td><td>2줄 / 위치 임의</td><td>3줄, Y=-300/-520/-740, Z=1140cm</td></tr><tr><td>빨래 차양</td><td>큰 크기는 같으나 계단실과 관계 누락</td><td>650×480cm, 중심(3100,-615,1180)</td></tr><tr><td>서측 비상계단</td><td>누락</td><td>기존 메시와 런타임 배치 좌표를 검토본에 추가</td></tr></table>
<figure><img src="{rel}window-roof-audit.png"><figcaption>좌표 기반 대조도. 정면은 건물 밖에서 바라본 방향, 옥상 평면은 도면 좌표(+X→,+Y↑)다.</figcaption></figure>
<div class="note"><b>게임 코드에서 추가로 확인한 문제:</b>2·3층 현관 위 접근 공간에 창문 패널을 놓았지만 뒤쪽 벽을 뚫지 않았다. 따라서 두 패널을 정상적인 외부 창으로 계산하지 않았다. 이 문제는 실제 게임 코드 수정·빌드 검증이 별도로 필요하다. 이번에 임의로 창을 추가하지 않았다.</div>
<h2>구조 기준 렌더</h2><figure><img src="{rel}exterior-code-matched.png"><figcaption>현재 코드 좌표로 재구성한 Blender 검토본. 객실 창36개의 실제 메시 경계를 대조했다. 게임 실행 캡처나 런타임 충돌 검증 결과는 아니다.</figcaption></figure>
<figure><img src="{rel}front-code-matched.png"><figcaption>정면36개 객실 창 확인.</figcaption></figure><figure><img src="{rel}roof-code-matched.png"><figcaption>계단실 지붕과 빨래 차양을 잠시 숨긴 옥상 평면 렌더. 계단 구멍과 출입 참을 확인하기 위한 뷰다.</figcaption></figure><figure><img src="{rel}roof-stair-detail.png"><figcaption>옥상 계단실·출입문·차양 위치 확대.</figcaption></figure>
<h2>다음 Tripo 작업 조건</h2><p>현재3종 이미지를 승인하더라도 즉시28종 전체를 생성하는 것으로 해석하지 않는다. Studio의 생성 설정과 공개 범위를 다시 확인한 뒤 승인된 이미지에 한해 진행한다. 현재 페이지에는 생성 주문을 실행하는 기능이 없다.</p><p><a href="{rel}exterior-audit.json">좌표 검증 JSON</a> · <a href="{rel}quality-prompts.json">이미지 생성 프롬프트</a> · <a href="{rel}exterior-code-matched.blend">외관 기준 Blender</a> · <a href="tripo-studio-assets-v1.html">이전 목록·예산</a></p></main></html>'''
(ROOT/'docs/tripo-studio-assets-v2.html').write_text(page,'utf-8')
md='''# 외관 대조 / 이미지 품질 개선 v2

- 사용자 요청: Tripo 생성 전 반드시 이미지 먼저. 이 작업에서 Tripo 생성/업로드0.
- 이미지 도구: 내장 image_gen. 세탁기65×70×95, 수납장80×40×120, 공구함50×30×32cm 기준 렌더를 참조했다.
- 위 치수는 제작 목표이며 생성 이미지/향후 Tripo 결과의 실측값이 아니다.
- 코드 대조: 객실 창36개,60×80cm, 바닥 기준Z120~200. 기존 v1 높이와 크기 수정.
- 옥상Z960, 계단실4×7m, 계단 구멍4×6m, 문(3790,-200,960), 빨랫줄3줄과 차양의 실제 좌표 반영.
- 추가 발견:2/3층 접근 공간 장식 창 패널 뒤 통벽으로 창 막힘. 게임 수정은 미수행.
- 산출물: Art/AssetConcepts/tripo-studio-v2. 이미지와 대조는 docs/tripo-studio-assets-v2.html.
- 코드 좌표 대조/Blender 검토이며 패키지 실플레이/충돌 검증 아님.
- AI 외관 이미지에서 구조가 달라 보이는 부분은 구조 기준 렌더보다 우선하지 않는다.
'''
(ROOT/'docs/tripo-studio-assets-v2.md').write_text(md,'utf-8')
print('PAGE_READY;36 window bounds checked;3 quality prop images;Tripo spent0')
