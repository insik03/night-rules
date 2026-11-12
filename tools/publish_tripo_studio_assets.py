import json, sys, html, hashlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(sys.argv[1]);OUT=ROOT/'Art/AssetConcepts/tripo-studio-v1'
audit=json.loads((OUT/'measurements.json').read_text('utf-8'));models=audit['models']
assert len(models)==6 and all(x['within_0_1cm'] for x in models)
extras=[
 ('B01','작은 쓰레기통',[20,20,28],'객실 / 15개','도면 목표'),
 ('B02','청소도구',[35,70,140],'1층 청소 공간 / 1세트','도면 점유 외형'),
 ('B03','보관 상자',[60,40,50],'2·3층 수납실 / 2개','도면 목표'),
 ('B04','밥솥',[38,32,32],'층별 주방 / 3개','신규 제안; 조리대 여유 실측 전'),
 ('B05','식기 건조대',[45,30,18],'층별 싱크대 옆 / 3개','신규 제안; 상판 여유 실측 전'),
 ('B06','빨래 바구니',[40,30,50],'옥상 세탁 공간 / 2개','신규 제안; 배치 미확정'),
 ('B07','세제 용기',[14,9,26],'옥상 수납장 / 2~4개','신규 제안; 선반 칸 간격 검토 전'),
 ('B08','운동화 한 켤레',[25,30,12],'거주실 출입구 안 / 5~8쌍','신규 제안; 복도에는 놓지 않음'),
 ('C01','에어컨 실외기',[80,32,55],'외벽 / 4~6개','신규 제안; 창문과 비상계단 회피'),
 ('C02','전기 계량기함',[45,22,65],'현관 옆 외벽 / 1~2개','신규 제안; 외관 치장용'),
 ('C03','옥상 환기구 캡',[45,45,60],'옥상 설비 구역 / 2~3개','신규 제안; 통행 경로 제외'),
 ('C04','자전거',[60,170,100],'현관 옆 외부 / 1~2개','신규 제안; 양문 개방 공간 제외'),
 ('C05','묶은 쓰레기봉투',[65,45,50],'건물 측면 수거 구역 / 2~3묶음','신규 제안'),
 ('C06','외부 재떨이',[25,25,60],'현관에서 떨어진 외부 / 1개','신규 제안'),
 ('C07','플라스틱 운반 상자',[55,35,30],'옥상·건물 측면 / 3~5개','신규 제안'),
 ('C08','옥상 물탱크',[120,120,140],'옥상 설비 구역 / 1개','신규 제안; 지지대와 배관 별도')]
architecture=[
 ('D01','고시원 외벽·층간 띠','현재 중심선44×11.3m, 층간3.2m, 옥상 바닥9.6m','기존 창·문 좌표와 내부 구조 연결'),
 ('D02','외부 창틀·창턱 모듈','각 창 개구부별 실측 후 확정','객실·공용공간 창 구분, 유리 별도'),
 ('D03','현관 양문·캐노피·간판 구성','현재 현관 개구부190×226cm','문짝·경첩 별도, 간판 글자는 별도 텍스처'),
 ('D04','외부 비상계단·난간','현재 층간320cm 기준 재사용/조정','기존 Meshy 비상계단과 런타임 동선 대조'),
 ('D05','옥상 난간·계단실·빨래 차양','옥상960cm, 현재 차양650×480cm','옥상 출입구와 빨래 동선 유지'),
 ('D06','배관·우수관·전선 모듈','외벽 접속점 측정 후 확정','길이에 따라 반복 조립'),
 ('D07','가까운 주변 건물 2개 변형','배치·크기는 신규 제안','창밖에서 보이는 면 중심; 내부 구현 안 함'),
 ('D08','먼 건물 실루엣·골목 바닥','카메라 시야 범위에 맞춰 결정','낮은 폴리곤·반복 재질, 플레이 구역 확장 아님')]
manifest={'date':'2026-11-01','scope':'Proposed completion asset budget, not an approved generation order or total final game mesh count',
 'source_layout':'Art/EnvironmentConcepts/unified-v15/furniture-layout.json','layout_placement_count':225,
 'studio':{'observed_balance':3200,'observed_model':'H3.1','mode':'geometry and texture','price_per_generation':55,'price_source':'Live Studio model generation UI: 생성 55','paid_part_generation':False,'8k':False,'privacy_observed':'공유 전용','spent':0},
 'stage_A':models,'stage_BC':[dict(id=i,name=n,target_cm=d,location=l,dimension_status=s,estimated_credits=55,preview_ready=False) for i,n,d,l,s in extras],
 'architecture':[dict(id=i,name=n,dimensions=d,note=s,method='Blender / reuse existing modules',studio_credits=0) for i,n,d,s in architecture],
 'npc':{'additional_models':6,'existing_protagonist_and_ghost':'reuse, excluded from new-generation count','base_generation_credits':330,'rigging_animation_credits':'not quoted; requires separate live price check'},
 'budget':{'stage_A':330,'stage_B':440,'stage_C':440,'all_props':1210,'npc_base':330,'base_total':1540,'user_spend_cap':2000,'difference_for_unquoted_processing':460,'balance_after_base_only':1660,'regeneration_included':False,'postprocessing_included':False},
 'limitations':['6 local reference meshes measured, not Tripo outputs.','No game assets changed/imported.','16 later props are candidates; not dimension-approved.','Exterior render is massing only; stair tower, escape stair and detailed sign are omitted.','One AI generation does not guarantee exact dimensions, separate parts, or production quality.','Local fixed-proportion modelling and retopology may be needed; no non-uniform stretch to force a fit.','Current shared-only visibility needs review before generation; nothing uploaded.']}
(OUT/'asset-plan.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),'utf-8')
# Contact sheet: layout only, using the rendered local geometry as-is.
W,H=2100,1730;im=Image.new('RGB',(W,H),'#17201f');dr=ImageDraw.Draw(im)
font='C:/Windows/Fonts/malgun.ttf';bold='C:/Windows/Fonts/malgunbd.ttf'
def ft(n,b=False):return ImageFont.truetype(bold if b else font,n)
dr.text((55,28),'해담고시원 · 추가 에셋 1차 검토',font=ft(43,True),fill='#f0eadc')
dr.text((55,94),'설계도 목표 비율로 제작한 Blender 프리뷰  /  단위 cm  /  Studio 생성 전',font=ft(25),fill='#b1beb5')
for idx,m in enumerate(models):
 col=idx%3;row=idx//3;x=40+col*690;y=158+row*748
 dr.rounded_rectangle((x,y,x+660,y+722),radius=12,fill='#e4e4dc')
 src=Image.open(OUT/m['image']).convert('RGB');src.thumbnail((640,576));im.paste(src,(x+(660-src.width)//2,y+8))
 dr.text((x+23,y+586),f"{m['id']}  {m['name']}",font=ft(29,True),fill='#202d29')
 dr.text((x+23,y+631),' × '.join(map(str,m['target_cm']))+' cm  |  55 credits',font=ft(24),fill='#344c40')
 dr.text((x+23,y+674),m['location'],font=ft(22),fill='#52645a')
dr.text((55,1674),'6종 기본 생성 예상 330크레딧 · 이번 제작/렌더 비용 0 · 게임 반영 전 검토용',font=ft(26),fill='#dfdfd0')
im.save(OUT/'six-props-overview.jpg',quality=95)
rel='../Art/AssetConcepts/tripo-studio-v1/'
def esc(x):return html.escape(str(x))
cards=''
for m in models:
 coords=' / '.join(f"{p['floor']}F ({p['x']:.1f}, {p['y']:.1f})" for p in m['placements'])
 cards+=f'''<article class="card"><a href="{rel}{m['image']}"><img src="{rel}{m['image']}" alt="{esc(m['name'])} 치수 기준 모델"></a><div class="pad"><small>{m['id']} · 55 credits</small><h3>{esc(m['name'])}</h3><strong>{' × '.join(map(str,m['target_cm']))} cm</strong><p>{esc(m['location'])}</p><p>{esc(m['parts'])}</p><details><summary>도면 좌표와 실측</summary><p>{esc(coords)}</p><p>Blender 평가 메시 실측: {esc(m['measured_cm'])} cm<br>목표 오차 0.1cm 이내 확인. 게임 메시 실측 아님.</p></details></div></article>'''
rows=''.join(f'<tr><td>{i}</td><td>{n}</td><td>{" × ".join(map(str,d))}</td><td>{l}</td><td>{s}</td><td>55</td></tr>' for i,n,d,l,s in extras)
arows=''.join(f'<tr><td>{i}</td><td>{n}</td><td>{d}</td><td>{s}</td></tr>' for i,n,d,s in architecture)
page=f'''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>해담고시원 · Studio 추가 에셋 제작안</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#16201e;color:#e9e9df;font-family:'Malgun Gothic',sans-serif;line-height:1.7}}main{{max-width:1400px;margin:auto;padding:48px 30px 90px}}h1{{font-size:36px;line-height:1.35;margin:12px 0 20px}}h2{{margin-top:64px;font-size:26px}}p{{max-width:1050px}}small,.muted{{color:#adc1b1}}.lead{{font-size:19px}}.badge{{display:inline-block;background:#31473b;color:#d8e7ce;padding:5px 12px;border-radius:3px}}.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:15px;margin:30px 0}}.stat{{padding:22px;background:#26352f;border-top:2px solid #a8bf8f}}.stat b{{display:block;font-size:30px}}.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}}.card{{background:#25342f;border:1px solid #415147;border-radius:9px;overflow:hidden}}.card img{{width:100%;display:block}}.pad{{padding:18px 22px}}.pad h3{{margin:6px 0;font-size:23px}}.pad p{{font-size:14px}}details{{font-size:13px}}summary{{cursor:pointer;color:#c7d9b5}}a{{color:#cadfae}}table{{border-collapse:collapse;width:100%;font-size:14px}}td,th{{padding:13px;border-bottom:1px solid #415147;text-align:left;vertical-align:top}}th{{background:#293c32}}.scroll{{overflow:auto}}.note{{border-left:3px solid #c5aa72;background:#2a3028;padding:18px 23px;margin:25px 0}}.wide{{width:100%;display:block;border:1px solid #415147}}figcaption{{font-size:14px;color:#b2c0b4;padding-top:10px}}figure{{margin:22px 0}}@media(max-width:850px){{.grid,.stats{{grid-template-columns:repeat(2,1fr)}}}}@media(max-width:540px){{.grid,.stats{{grid-template-columns:1fr}}main{{padding:24px 16px}}}}
</style><main><span class="badge">생성 전 검토 · 크레딧 사용 0</span><h1>치수부터 맞추는 추가 에셋 제작안</h1><p class="lead">1차 6종의 기준 이미지와, 외관·배경·주민까지 포함한 추가 제작 예산. 전체 게임의 최종 메시 수가 아니라 <b>앞으로 만들 후보 목록</b>이다.</p>
<div class="stats"><div class="stat">Studio 잔액<b>3,200</b></div><div class="stat">1차 6종 기본 생성<b>330</b></div><div class="stat">소품22 + NPC6 기본 생성<b>1,540</b></div><div class="stat">기존 요청 사용 상한<b>2,000</b></div></div>
<p>2026-11-01 Studio 웹에서 H3.1 · 지오메트리 및 텍스처 · 생성55 표시 확인. 부분별 생성과8K는 끈 상태. 재생성·리깅·추가 텍스처·유료 분할/리토폴로지는 합계에 넣지 않았다. 설정이나 요금이 바뀌면 생성 직전 다시 확인한다.</p>
<div class="note">기존 소품부터 재사용한다. Meshy 핵심10종 + 추가6종, 환경 모듈4종, 주인공·귀신과 Poly Haven 모델11종 및 텍스처가 있다. 서로 역할이 겹치므로 이를 단순 합산한 수를 최종 게임 에셋 수로 보지 않는다. 현행 도면의 가구 배치225개도 새 모델225종을 뜻하지 않는다.</div>
<h2>먼저 볼 6종 · 총16곳에 배치</h2><p>아래는 생성형 이미지가 아니라 목표 치수로 직접 만든 Blender 기준 렌더다. 6종 모두 평가 메시 경계를 측정해 목표와0.1cm 이내임을 확인했다. Tripo가 이 수치를 자동으로 보장하지는 않는다. 비율이 어긋난 결과를 억지로 늘리지 않고 비교 검수한다.</p><div class="grid">{cards}</div>
<h2>외관과 주변 배경도 에셋으로 구성</h2><figure><img class="wide" src="{rel}exterior-massing.png" alt="44m 고시원 건물 외관 비율 초안"><figcaption>현재 중심선44×11.3m · 3개 층(층간3.2m) · 옥상 바닥9.6m를 사용한 외관 비율 초안. 상층은 밝은 리모델링 마감. 주변 건물은 창밖 배경 제안이다. 계단실·비상계단·외관 설비 상세는 이 간이 렌더에 아직 미반영이며 최종 설계도나 게임 캡처가 아니다.</figcaption></figure>
<p>고시원은 기존 내부 좌표와 이어지는 외벽·창틀·계단·옥상 모듈로 제작한다. 주변 건물은 가까운 두 가지 모듈을 변형 배치하고 먼 건물은 낮은 폴리곤 실루엣으로 처리한다. 건물 전체를 한 번에 AI로 생성하면 출입구·창 위치·층 높이가 달라질 수 있어 정밀 골조는 Blender로 구성한다.</p>
<div class="scroll"><table><tr><th>ID</th><th>Blender 작업 묶음</th><th>치수 기준</th><th>구성</th></tr>{arows}</table></div><p class="muted">위8개는 모듈 작업 묶음이며 파일/메시8개라는 뜻이 아니다. Studio 크레딧0; 제작 시간은 필요하다.</p>
<h2>후속 후보16종 · 아직 이미지/배치 승인 전</h2><p>B01~B08은 실내 생활 소품, C01~C08은 외관·옥상 소품이다. 기존 원본으로 충분한 것은 생성에서 빼며, 신규 제안 치수는 설치 위치를 확인한 뒤 확정한다.</p><div class="scroll"><table><tr><th>ID</th><th>에셋</th><th>폭×깊이×높이 cm</th><th>배치 제안</th><th>치수 상태</th><th>예상</th></tr>{rows}</table></div>
<h2>추가 제작 전체 견적</h2><div class="scroll"><table><tr><th>범위</th><th>신규 기본 생성 수</th><th>예상 크레딧</th></tr><tr><td>A / 이번6종</td><td>6</td><td>330</td></tr><tr><td>B / 생활 소품</td><td>8</td><td>440</td></tr><tr><td>C / 외관·옥상 소품</td><td>8</td><td>440</td></tr><tr><td>주민 NPC</td><td>6</td><td>330 (모델 기본 생성만)</td></tr><tr><td>합계</td><td>28종 / 반복 배치 제외</td><td><b>1,540</b></td></tr><tr><td>외관·배경 모듈</td><td>Blender8개 작업 묶음</td><td>0</td></tr></table></div>
<p>주인공·귀신은 기존 모델을 재사용한다. 15명 거주 설정 중 직접 보이는 주민6명을 신규 모델링하고 나머지는 문 뒤 대화로 처리한다. 1,540은 본편 전체 제작비가 아니라 <b>이 추가 후보들의 첫 생성 비용</b>이다. 추가 가공비를 확인하지 않았으므로 2,000 안에 최종 완성까지 된다고 보장하지 않는다. 2,000과의 차이460은 재생성 할당이 아니다.</p>
<h2>배치와 개폐를 지킬 기준</h2><ul><li>변기는 코드처럼 내부 통로(+Y)를 바라보고, 세면대는 오른쪽(+X)을 바라본다. 세면대의55×60은 제품 로컬 폭·깊이이며 배치 회전 후 바닥 점유는60×55가 된다. 도면의 단순 사각형과 구분한다.</li><li>변기 뒤 외벽 중심선y=-900, 앞방향+Y. 제품 후면y=-875와 외벽 안쪽y=-892 사이17cm. 실제 반입 시 배관 접속을 검토한다.</li><li>세면대 중심은 각 화장실 왼쪽 벽+60cm. 깊이60을 회전 적용하면 벽 내면과 후면 사이24cm. 기존 중심을 보존한 값이며 실제 벽밀착 위치/배관은 후속 확정이다.</li><li>옥상 세탁기는 전면 도어 앞 최소90cm, 수납장은39cm 문짝 회전 반경과 통행 공간을 확보한다. 이 값은 설계 기준이며 Unreal 충돌 통과 보고가 아니다.</li><li>1·2층과3층은 같은 메시를 쓰고 마모/색상만 바꾼다. 관리실·객실 옷장 크기와 배치를 이번에 바꾸지 않았다.</li></ul>
<div class="note">현재 Studio 패널의 공개 옵션은 ‘공유 전용’으로 표시됐다. 미리보기와 원본을 아직 업로드하지 않았으며, 실제 생성 전 공개 범위를 함께 확인해야 한다. 이 페이지는 생성 승인 요청을 위한 검토 자료다.</div>
<p><a href="floor-plan.html">기준 통합 설계도</a> · <a href="{rel}measurements.json">6종 실측</a> · <a href="{rel}asset-plan.json">전체 후보/예산 JSON</a> · <a href="{rel}dimensioned-reference-models.blend">Blender 기준 모델</a></p></main></html>'''
(ROOT/'docs/tripo-studio-assets-v1.html').write_text(page,'utf-8')
md='# Tripo Studio 추가 에셋 검토 v1\n\n2026-11-01. 생성/업로드0, UE 변경0.\n\n- 기준: unified-v15 furniture-layout.json / NRArchitecture.cpp.\n- 1차6종330; 추가 실내8종440; 외관소품8종440; 주민6명 기본330. 합계1540. 후처리·리깅·재생성 제외.\n- 외관/배경8개 Blender 작업 묶음은 별도. 최종 게임의 메시 총수와 구분.\n- 전체 후보 및 설정은 Art/AssetConcepts/tripo-studio-v1/asset-plan.json.\n- 이미지와 치수는 docs/tripo-studio-assets-v1.html.\n- 신규16종/NPC의 이미지 및 공간 치수 확인은 다음 차수. 아직 생성 승인된 주문 아님.\n- 실제 Tripo 결과는 별도 비율·문 개폐·축·텍스처·폴리곤 검수.\n- 공개 옵션 공유 전용 관찰; 실제 생성 전 사용자 공개 범위 확인 필요.\n'
(ROOT/'docs/tripo-studio-assets-v1.md').write_text(md,'utf-8')
print(json.dumps({'models':len(models),'dimensions_passed':all(x['within_0_1cm'] for x in models),'placements':sum(len(x['placements']) for x in models),'props':len(models)+len(extras),'npc':6,'base_credits':1540,'paid_credits_used':0,'page':str(ROOT/'docs/tripo-studio-assets-v1.html')},ensure_ascii=False))
