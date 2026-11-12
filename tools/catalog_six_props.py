from pathlib import Path
from html import escape
import json,struct
R=Path(__file__).resolve().parents[1]
P=R/'Art/GeneratedProps/six-v1'
jobs=json.loads((P/'jobs.json').read_text(encoding='utf-8-sig'))
audit={x['name']:x for x in json.loads((P/'geometry-audit.json').read_text())}
names={'chair':'철제·합판 의자','bedding':'싱글 침구','sink':'싱크대·하부장','shower':'샤워 세트','slippers':'슬리퍼 한 쌍','books':'시험 준비용 책 묶음'}
targets={'chair':'42×44×80 / 좌판 높이45','bedding':'매트리스88×195×18','sink':'120×60×85 / 수도꼭지 제외','shower':'25×15×110 / 설치 높이 별도','slippers':'한 짝11×28×10 / 쌍 약24×28','books':'30×22×25'}
notes={
'chair':'높이80cm로 전체를 균일 환산하면 약49.5×54.3×80cm. 목표42×44보다 넓고 깊음. 치수 적합 판정 보류.',
'bedding':'전체 길이195cm 기준 균일 환산하면 폭 약112.4cm. 목표 매트리스 폭88cm보다 넓음. 측정에 베개·이불 포함; 침대에 바로 맞는 상태 아님.',
'sink':'폭120cm 기준 전체 깊이 약60.1cm, 전체 높이 약89.0cm. 전체 높이는 수도꼭지 포함이라 상판 높이85cm 충족 여부는 별도 실측 필요. 문은 아직 본체와 미분리.',
'shower':'전체 높이110cm 기준 약32.2×19.0×110cm. 호스·레일 포함 전체 외형; 목표25×15 및 레일 길이는 별도 검수 필요.',
'slippers':'한 쌍의 전체 길이28cm 기준 약24.4×28×6.9cm. 각 슬리퍼 치수는 분리 후 측정 필요. 두 슬리퍼는 현재 한 메시 오브젝트.',
'books':'전체 폭30cm 기준 약30×21.9×19.2cm. 목표 높이25cm보다 낮음. 여러 책이 한 정적 메시 오브젝트.'}
cards=[];records=[];total=0
for i,j in enumerate(jobs,1):
 n=j['name'];a=audit[n]
 result=json.loads((P/f'{n}-result.json').read_text(encoding='utf-8-sig'))['result']['task']
 cost=result.get('consumed_credits');total+=cost or 0
 model=P/n/'model.glb';preview=P/n/'preview.png'
 assert model.exists() and preview.exists()
 with model.open('rb') as f:magic,version,size=struct.unpack('<4sII',f.read(12))
 assert magic==b'glTF' and version==2 and size==model.stat().st_size
 records.append(dict(name=n,label=names[n],resource='image-to-3d',task_id=j['id'],status=result['status'],consumed_credits=cost,model=str(model),preview=str(preview),target_cm=targets[n],triangles=a['triangles'],review=notes[n]))
 src=f'../Art/GeneratedProps/six-v1/{n}/preview.png'
 ref=f'../Art/GeneratedProps/six-v1/references/{n}.png'
 cards.append(f'''<article><div class="number">{i:02d} / MESHY GENERATED MODEL</div><h2>{names[n]}</h2><a href="{src}"><img src="{src}" alt="{names[n]} 실제 3D 생성 결과" loading="eager"></a><p class="target">목표 {targets[n]} cm</p><p>{notes[n]}</p><p class="meta">{a['triangles']:,} triangles · {cost} credits · GLB</p><details><summary>입력 시안과 비교</summary><img src="{ref}" alt="생성 입력 이미지"></details></article>''')
report={'date':'2026-10-22','provider':'Meshy','starting_balance':500,'ending_balance':320,'total_consumed_credits':total,'regenerations':0,'nonuniform_scaling':False,'game_imported':False,'assets':records}
(P/'delivery.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
html='''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>해담고시원 · 가구 6종 실제 생성 결과</title><style>*{box-sizing:border-box}body{margin:0;background:#17211e;color:#eceadf;font:15px/1.7 'Malgun Gothic',sans-serif}main{max-width:1600px;margin:auto;padding:32px}h1{font-size:30px;margin:8px 0}h2{font-size:21px;margin:5px 0 15px}.sub,.meta{color:#a4b4aa}.notice{border-left:3px solid #d7b06f;background:#332f23;padding:18px 22px;margin:24px 0}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}article{background:#223029;border:1px solid #465448;padding:20px;border-radius:7px}img{width:100%;aspect-ratio:1;object-fit:contain;background:#101814;display:block}.number{color:#b6bb9e;font-size:11px;letter-spacing:1px}.target{color:#e6ca8f;font-weight:bold}p{margin:10px 0}.meta{font-size:13px}summary{cursor:pointer;color:#bfd5bd}details img{margin-top:15px;background:#fff}a{color:#bbd6ba}footer{font-size:13px;color:#a2b2a4;margin-top:26px}@media(max-width:1000px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:650px){.grid{grid-template-columns:1fr}main{padding:16px}}</style><main><div class="sub">HAEDAM / GENERATED PROPS 01 / 2026.10.22</div><h1>가구 6종, 실제 3D 생성 결과</h1><p>아래 이미지는 Meshy가 생성한 GLB 모델의 렌더 미리보기입니다. 입력 시안은 각 카드의 ‘입력 시안과 비교’에서 따로 확인할 수 있습니다.</p><p><b>6건 × 30 = 180크레딧 사용 · 잔액320 · 재생성0회</b></p><div class="notice"><b>목표 치수와 원본 비율은 일치하지 않는 부분이 있습니다.</b><br>형상을 한 축으로 늘이거나 줄이지 않았고 게임에도 아직 적용하지 않았습니다. 치수 설명은 원본 외형을 균일 환산한 비교값이며, 모델 파일을 실제로 그 크기로 변경한 것은 아닙니다. 특히 의자·침구는 목표보다 넓습니다. 생성 원본은 약13만~85만 삼각형으로, 게임용 최적화와 싱크대 문 분리가 남아 있습니다.</div><div class="grid">CARDS</div><footer>모델 저장 폴더: Art/GeneratedProps/six-v1/각 영문 이름/model.glb<br><a href="../Art/GeneratedProps/six-v1/README.md">작업 ID·비용·검수 기록</a> · <a href="floor-plan.html">통합 설계도</a><br>추가 생성 비용 없이 원본 GLB 6개를 Blender에서 열어 메시 개수, 전체 바운딩 박스와 삼각형 수를 측정했습니다. 렌더 확인만으로 뒷면·토폴로지·충돌 품질을 보증하지 않습니다.</footer></main></html>'''.replace('CARDS',''.join(cards))
(R/'docs/generated-props-six-v1.html').write_text(html,encoding='utf-8')
md=['# 가구 6종 생성 결과','', '2026-10-22. Meshy standard textured image-to-3d, 4K PBR, GLB. 각 1회 생성.','',f'실사용 {total}크레딧. 시작500 → 종료320. 연결된 Tripo API 잔액은0으로 이번 생성에 사용하지 않음.','', '개별 입력 이미지는 built-in image_gen으로 승인된 priority-six.png에서 각 소품만 추출·재구성했다. 레퍼런스에 있던 샤워 배경벽은 제거했다. 사용자 승인 범위: 6종 신규 생성 및 결과 확인. 게임 적용·추가 유료 후처리·재생성 없음.','', '| 소품 | resource / task ID | 비용 | 삼각형 수 |','|---|---|---:|---:|']
for r in records:md.append(f"| {r['label']} | image-to-3d / {r['task_id']} | {r['consumed_credits']} | {r['triangles']:,} |")
md+=['','## 비율 검수','', '원본 GLB는 변경하지 않았다. 아래 수치는 Blender가 읽은 전체 외형 비율을 기준 축 하나에 맞춰 균일 환산한 참고치이며, 현재 파일의 물리 cm 단위가 아니다. 베개·이불·수도꼭지·호스 등 포함 여부에 유의한다.','']
for r in records:md.append(f"- {r['label']}: {r['review']}")
md+=['','## 파일','', '- 각 소품 폴더: model.glb / preview.png. references/: 생성 입력 이미지.','- delivery.json: 공개 가능한 task ID·비용·결과 파일 기록. geometry-audit.json: 원본 외형과 삼각형 수.','- meshy_output/ 및 원시 CLI 결과는 서명 URL을 포함할 수 있어 Git 제외.','- 일부 Meshy CLI 다운로드는 완료 JSON과 파일을 기록한 뒤 Windows libuv 종료 오류가 발생했다. 다운로드 완료 상태·실제 PNG와 GLB 헤더를 확인했으며 유료 작업을 재제출하지 않았다.']
(P/'README.md').write_text('\n'.join(md),encoding='utf-8')
print(f'Delivered {len(records)} valid GLB2 files and 6 previews; verified total={total}; review page written.')
