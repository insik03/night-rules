"""Build a local review page from real model renders and sanitized task receipts."""
from pathlib import Path
import json, html
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'Art/CoreProps/v1'
NAMES={'O01':'총무 책상 · 서랍 3개','O03':'유선 전화기','O05':'CCTV 모니터','I01':'손전등','I02':'UV 카트리지','B01':'방문','K01':'냉장고','K06':'원형 식탁','R01':'빈 침대 프레임','R04':'좁은 옷장'}
receipts=[];cards=[]
prep={r['id']:r for r in json.loads((BASE/'preparation.json').read_text())}
for id,name in NAMES.items():
 state=json.loads((BASE/'meshy_output'/f'{id}-state.json').read_text(encoding='utf-8-sig'))
 task=json.loads((BASE/'meshy_output'/f'{id}-wait.json').read_text(encoding='utf-8-sig'))['result']['task']
 slug=state['slug'];folder=BASE/'models'/f'{id}-{slug}'
 receipts.append({'id':id,'name':name,'task_id':state['task_id'],'service':'Meshy','resource':'image-to-3d','status':task['status'],'credits':task['consumed_credits'],'reference':f'references/{id}-{slug}.png','model':f'models/{id}-{slug}/source.glb','postprocessing':'Blender: simplify, scale, split movable parts, add cabinet interiors','date':'2026-10-12'})
 figures=[]
 for file,label in [(BASE/'references'/f'{id}-{slug}.png','승인 이미지'),(folder/'prepared-preview.png','실제 3D 모델'),(folder/'open-preview.png','열린 상태')]:
  if file.exists():
   src='../'+file.relative_to(ROOT).as_posix()
   figures.append(f'<figure><a href="{src}" target="_blank"><img loading="lazy" src="{src}" alt="{html.escape(name)} {label}"></a><figcaption>{label}</figcaption></figure>')
 cards.append(f'<section><header><span>{id}</span><h2>{name}</h2><small>30 크레딧 · {prep[id]["prepared_triangles"]:,} 삼각형</small></header><div class="images">'+''.join(figures)+'</div></section>')
(BASE/'provenance.json').write_text(json.dumps({'total_credits':sum(r['credits'] for r in receipts),'assets':receipts},ensure_ascii=False,indent=2),encoding='utf-8')
if (BASE/'runtime-desk.png').exists():
 cards.insert(0,'<section><header><h2>실제 게임 적용 화면</h2></header><p>관리실 책상 · 서랍 속 UV 카트리지 · 실시간 CCTV</p><img style="aspect-ratio:16/9" src="../Art/CoreProps/v1/runtime-desk.png" alt="새 소품을 적용한 실제 언리얼 게임 화면"></section>')
page='''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>야간수칙 · 핵심 소품 10종</title><style>
*{box-sizing:border-box}body{margin:0;background:#171b1a;color:#e6e6df;font:16px/1.65 system-ui,sans-serif}main{max-width:1280px;margin:auto;padding:48px 28px}h1{font-size:36px;margin:4px 0 10px}p{color:#b4bfb8;max-width:850px}.meta{color:#caba88;letter-spacing:.12em;font-size:12px}section{background:#232926;border:1px solid #3a4540;border-radius:12px;padding:24px;margin:28px 0}header{display:flex;align-items:center;gap:18px;flex-wrap:wrap}header span{color:#caba88}h2{font-size:22px;margin:0}small{margin-left:auto;color:#b4bfb8}.images{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px;margin-top:20px}figure{margin:0}img{width:100%;aspect-ratio:1;object-fit:contain;background:#d2d2cf;border-radius:8px}figcaption{padding-top:8px;color:#b4bfb8}a{color:inherit}@media(max-width:700px){.images{grid-template-columns:1fr}main{padding:24px 16px}small{margin-left:0}}</style><main><div class="meta">HAEDAM GOSIWON / CORE PROPS 01</div><h1>핵심 소품 10종</h1><p>승인 이미지와 실제 3D 모델을 비교하는 검수판. 총 300 크레딧을 사용했습니다. 책상 서랍, 냉장고 문, 옷장 문은 별도 부품으로 분리했습니다. 실제 모델 이미지는 Blender에서 렌더링한 것으로, 게임 내 조명과 화면은 다를 수 있습니다.</p>'''+''.join(cards)+'</main></html>'
(ROOT/'docs/core-props-v1.html').write_text(page,encoding='utf-8')
print('Catalog and sanitized provenance written; total credits',sum(r['credits'] for r in receipts))
