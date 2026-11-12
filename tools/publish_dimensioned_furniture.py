"""Review presentation and geometric clearance checks for locally authored models."""
from pathlib import Path
import json,html,math
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'Art/EnvironmentConcepts/dimensioned-furniture-v1'
audit=json.loads((OUT/'dimensions.json').read_text(encoding='utf-8'))
data=json.loads((OUT/'placement.json').read_text(encoding='utf-8'));items=data['items']
checks=[]
def rect(it,dy=0):
    w,d=it['width'],it['depth']
    return (it['x']-w/2,it['y']+dy-d/2,it['x']+w/2,it['y']+dy+d/2)
def overlap(a,b):return min(a[2],b[2])>max(a[0],b[0]) and min(a[3],b[3])>max(a[1],b[1])
for ch in [i for i in items if i['name']=='객실 의자']:
    closets=[i for i in items if i['floor']==ch['floor'] and i['name']=='옷장']
    ok=all(not overlap(rect(ch,-30),rect(c)) for c in closets)
    checks.append(dict(check='객실 의자 30cm 인출과 옷장 비중첩',floor=ch['floor'],x=ch['x'],pass_check=ok))
# Door leaves are conservative 87cm quarter-disc footprints. Check furniture that rises from the floor.
def door_intersects(it,hx,hy,r):
    a=rect(it);xmin=max(a[0],hx);xmax=min(a[2],hx+r);ymin=max(a[1],hy);ymax=min(a[3],hy+r)
    if xmin>=xmax or ymin>=ymax:return False
    return (xmin-hx)**2+(ymin-hy)**2<r*r
for f in [1,2,3]:
    for n in range(12):
        left=350+n*230
        local=[i for i in items if i['floor']==f and left<i['x']<left+230 and i['y']>=-70 and i['z']==0]
        blocked=[i['name'] for i in local if door_intersects(i,left+11.5,-70,87)]
        checks.append(dict(check='객실 문 87cm 회전 구역',room=f*100+n+1,blocked_by=blocked,pass_check=not blocked))
for w in [i for i in items if i['name']=='옷장']:
    beds=[i for i in items if i['name']=='싱글 침대 프레임' and i['floor']==w['floor'] and abs(i['x']-w['x'])<80]
    for bed in beds:
        checks.append(dict(check='발치 옷장과 침대 비중첩',floor=w['floor'],x=w['x'],clearance_cm=rect(bed)[1]-rect(w)[3],pass_check=not overlap(rect(bed),rect(w))))
checks += [dict(check='옷장 문 90도 개방 시 통로',clearance_cm=39.5,pass_check=False,note='발치와 옷장 사이39.5cm. 폭44cm 문은 90도 열면 침대와 겹침. 개방각 약60도 제한 또는 문 방식 변경을 게임 반영 시 검토.'),dict(check='관리실 출입구와 책상 측면',clearance_cm=59.5,pass_check=True,note='문 오른쪽 끝 X78.5, 책상 왼쪽 X138; 복도 유효폭을 뜻하지 않음.')]
(OUT/'clearance-checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
assert all(x['within_0_1cm'] for x in audit)
assert all(x['pass_check'] for x in checks if x['check']!='옷장 문 90도 개방 시 통로')
font='C:/Windows/Fonts/malgun.ttf'
ft=lambda n:ImageFont.truetype(font,n)
titles=['의자','침구','싱크대·하부장','샤워 수전','슬리퍼 한 쌍','책·문제집']
sizes=['42 × 44 × 80 cm','88 × 195 × 18 cm','120 × 60 × 85 cm','25 × 15 × 110 cm','24 × 28 × 10 cm','30 × 22 × 25 cm']
board=Image.new('RGB',(1800,1490),'#172421');d=ImageDraw.Draw(board)
d.text((35,24),'설계 치수로 직접 만든 6종 기본 모델',font=ft(36),fill='#ede9db')
d.text((35,80),'Blender 실측 일치 · 추가 크레딧 0 · 재질/생활감 작업 전',font=ft(23),fill='#b8c8be')
for i,(title,sz) in enumerate(zip(titles,sizes)):
    x=(i%3)*600;y=140+(i//3)*670
    # Preserve square image aspect; pad rather than stretching the rendered model.
    im=Image.open(OUT/f'asset-{i+1}.png').convert('RGB');im.thumbnail((580,540))
    board.paste(im,(x+(600-im.width)//2,y))
    d.text((x+30,y+552),title,font=ft(29),fill='#ede9db');d.text((x+30,y+597),sz,font=ft(24),fill='#a6cfbb')
board.save(OUT/'six-models.png')
link='../Art/EnvironmentConcepts/dimensioned-furniture-v1/'
def fig(file,title,caption):return f'<figure><a href="{link}{file}.png"><img loading="lazy" src="{link}{file}.png" alt="{html.escape(title)}"></a><figcaption><b>{title}</b><br>{caption}</figcaption></figure>'
figures=''.join(fig(f'floor-{i}',f'{i}층'+(' · 옥상' if i==4 else ''),'전체와 확대는 같은 Blender 장면입니다. 구조 확인을 위해 벽체 상부와 유리는 생략했습니다.') for i in range(1,5))
detail=fig('office','관리실·창고','관리실 책상 264×55×75cm. 중앙 벽 유지, CCTV 아래 3대·위 2대. 책상을 늘린 메시가 아니라 해당 치수로 직접 구성한 상판·서랍입니다.')+fig('room','거주 객실','침대 발치에 옷장 45×45×175cm 두 개를 나란히 배치, 사이 간격 2cm. 침대 프레임 90×200×45cm, 침구 88×195×18cm, 책상 106×55×75cm. 의자는 기존 도면보다 +X 41cm 옮겼습니다.')+fig('kitchen','1층 주방','지름200cm·높이75cm 원형 식탁 두 개. 싱크대 상판 높이85cm. 기존 조리대88cm와는 3cm 높이 차이가 남아 있습니다.')+fig('wet-area','2층 샤워 구역','수전 전체110cm, 바닥에서90cm에 설치해 상단200cm. 주위 변기·세면대 등은 부피만 표시한 자리표시 모델입니다.')
rows=''.join(f'<tr><td>{html.escape(a["asset"])}</td><td>{" × ".join(f"{v:g}" for v in a["expected_cm"])}</td><td>{" × ".join(f"{v:g}" for v in a["measured_cm"])}</td><td>{"부피 표시" if a["kind"]=="placeholder" else "형태 제작"}</td></tr>' for a in audit)
page=f'''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>가구 실치수 Blender 배치 검토</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#14221f;color:#eae8dd;font:16px/1.7 'Malgun Gothic',sans-serif}}main{{max-width:1600px;margin:auto;padding:36px}}h1{{font-size:34px;margin:4px 0}}p{{color:#b9c8bf}}a{{color:#b3ddc3}}nav{{display:flex;gap:24px;flex-wrap:wrap;margin:20px 0}}figure{{margin:24px 0;background:#20322b;border:1px solid #496052}}img{{display:block;width:100%;height:auto}}figcaption{{padding:18px 24px}}.details{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}.details figure{{margin:0}}.note{{background:#343427;padding:20px;border-left:3px solid #c8b789}}table{{width:100%;border-collapse:collapse}}td,th{{padding:10px;text-align:left;border-bottom:1px solid #415449}}small{{color:#9bb8a4}}@media(max-width:900px){{.details{{display:block}}main{{padding:16px}}}}
</style><main><small>HAEDAM / DIMENSIONED BLENDER REVIEW · 2026.10.22</small><h1>치수부터 만든 가구, 같은 장면에서 본 배치.</h1><p>추가 크레딧 <b>0</b> · AI 재생성 없음 · 게임 적용 전 검토용 기본 모델</p><nav><a href="#six">6종 모델</a><a href="#details">구역 확대</a><a href="#floors">전체 층</a><a href="#sizes">실측 치수표</a><a href="floor-plan.html">통합 설계도</a><a href="{link}haedam-dimensioned-furniture.blend">Blender 원본</a></nav>
<div class="note">가구는 원래 치수로 메시를 직접 구성했습니다. 원본 AI 메시를 늘려서 맞추지 않았습니다. 벽은 배치를 보도록 낮게 절단한 검토용이며, 실제 게임의 천장·벽 마감·계단 상세 모델을 교체한 결과가 아닙니다. 변기·세면대·전화기 등은 아직 기본 부피만 표시했습니다.</div>
<section id="six">{fig('six-models','먼저 확인할 6종','단위 cm, 가로×깊이×높이. 싱크대85cm는 하부장·상판 기준이며 수도꼭지는 별도입니다. 샤워 수전은 설치 높이와 모델 자체 높이를 구분합니다.')}</section>
<h2 id="details">같은 모델의 구역 확대</h2><div class="details">{detail}</div>
<h2>배치 점검에서 확인한 여유</h2><ul><li>객실 의자는 책상 아래 위치를 유지했습니다. 옷장 두 개를 침대 발치로 옮겨 의자를 뒤로 30cm 뺄 때 옷장과 겹치지 않습니다.</li><li>객실 문: 도면의 87cm 회전 영역과 바닥 가구의 평면 중첩 없음. 실제 문 손잡이·캐릭터 충돌 검증은 별도입니다.</li><li>옷장과 침대 발치 사이39.5cm. 옷장 문은 침대를 향하며, 90도 열면 침대에 닿습니다. 게임 반영 시 약60도 개방 제한 또는 문 방식 변경이 필요합니다. 현재는 닫힌 상태의 배치 검토입니다.</li><li>관리실 책상 왼쪽과 출입구 오른쪽 끝 사이59.5cm. 책상은 방 전체 폭465cm가 아니라 확정된264cm 규격이며, 관리실 창324cm 안쪽에 배치했습니다.</li><li>실내 크기는 벽 중심선 기준입니다. 객실230×300cm, 관리실·창고 각465×420cm. 이번에 방을 임의로 축소하지 않았습니다.</li></ul>
<h2 id="floors">1~3층과 옥상</h2>{figures}<h2 id="sizes">모델 외곽 치수 실측</h2><p>Blender 메시 외곽으로 측정, 허용 오차0.1cm. 배치용 인스턴스의 스케일은 모두1입니다. 부피 표시는 최종 소품 형태가 아닙니다.</p><table><thead><tr><th>모델</th><th>설계 cm</th><th>실측 cm</th><th>상태</th></tr></thead><tbody>{rows}</tbody></table><p><a href="{link}dimensions.json">치수 검증 결과</a> · <a href="{link}clearance-checks.json">배치 점검 결과</a> · <a href="{link}placement.json">배치 좌표</a></p></main></html>'''
(ROOT/'docs/dimensioned-furniture-v1.html').write_text(page,encoding='utf-8')
(OUT/'README.md').write_text('''# 치수 기반 Blender 가구 검토

- 추가 크레딧 0. Meshy/Tripo/API 호출 없음.
- 원본: haedam-dimensioned-furniture.blend. 각 층은 별도 Scene이며 MODEL 컬렉션을 실제 cm 치수로 제작하고 인스턴스로 배치.
- tools/build_dimensioned_furniture.py 재현 가능. tools/publish_dimensioned_furniture.py 검증·검토 페이지 생성.
- 전체 장면과 확대 모두 같은 모델. 평면 도면은 unified-v15/furniture-layout.json.
- 형태·치수 검토용. Unreal 반영, 게임 충돌 검증, 재질 제작은 하지 않음.
- 옷장 두 개를 침대 발치로 이전하고 통합 도면과 동기화. 의자와 벽 구조 유지.
- 기존 AI 생성 GLB와 rejected preparation은 이 모델에 사용하지 않음.
''',encoding='utf-8')
print(json.dumps(dict(models=len(audit),dimension_checks_passed=True,placement_checks=len(checks),wardrobe_foot_gap_cm=39.5,credits_spent=0)))
