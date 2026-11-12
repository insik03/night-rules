from pathlib import Path
import json,math,html
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Arc,Circle
from matplotlib import font_manager
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Art/EnvironmentConcepts/furniture-review-v2'
r=json.loads((OUT/'audit.json').read_text(encoding='utf-8'))
font_manager.fontManager.addfont('C:/Windows/Fonts/malgun.ttf')
plt.rcParams['font.family']='Malgun Gothic';plt.rcParams['axes.unicode_minus']=False
fig,ax=plt.subplots(figsize=(10,10));fig.patch.set_facecolor('#f4f3ed');ax.set_facecolor('#f4f3ed')
ax.set_aspect('equal');ax.set_xlim(315,655);ax.set_ylim(-115,270);ax.axis('off')
def rect(x,y,w,h,c,ec='#52605d',lw=1.2):
 p=Rectangle((x,y),w,h,facecolor=c,edgecolor=ec,lw=lw);ax.add_patch(p);return p
rect(350,-70,230,300,'#e1e7df')
for x,y,w,h in [(345,-75,10,310),(575,-75,10,310),(345,225,240,10),(345,-75,16.5,10),(448.5,-75,136.5,10)]:rect(x,y,w,h,'#606966')
rect(355,169.5,106,55,'#b69c7a');ax.text(408,197,'책상\n106 × 55',ha='center',va='center',fontsize=11)
rect(404,163,42,44,'#819790');ax.text(425,185,'의자',ha='center',va='center',fontsize=9)
rect(484,22,90,200,'#a9c5bd');ax.text(529,125,'침대\n90 × 200',ha='center',va='center',fontsize=13)
rect(488,176,82,40,'#eaece3')
rect(452,25,20,20,'#b7beb4');ax.text(447,35,'휴지통',ha='right',va='center',fontsize=8)
rect(453,-44,24,28,'#6e817e')
for cx in [504.5,551.5]:
 rect(cx-22.5,-62.5,45,45,'#ccbba3')
 ax.text(cx,-40,'옷장\n45 × 45',ha='center',va='center',fontsize=10)
 for hx in [cx-21.75,cx+21.75]:
  rect(hx-1,-18.5,2,21.5,'#faf9ef',ec='#087f70',lw=1.7)
 ax.add_patch(Arc((cx-21.75,-18.5),43,43,theta1=0,theta2=90,color='#399f8d',lw=1,ls='--'))
 ax.add_patch(Arc((cx+21.75,-18.5),43,43,theta1=90,theta2=180,color='#399f8d',lw=1,ls='--'))
def dim(a,b,label,pos=None,color='#25564c'):
 ax.annotate('',xy=a,xytext=b,arrowprops={'arrowstyle':'<->','color':color,'lw':1.4})
 mid=pos or ((a[0]+b[0])/2,(a[1]+b[1])/2)
 ax.text(*mid,label,ha='center',va='center',fontsize=11,color=color,bbox=dict(facecolor='#f4f3ed',edgecolor='none',pad=2))
dim((350,247),(580,247),'벽 중심선 230cm')
dim((610,-70),(610,230),'300cm',(620,80))
dim((551.5,3),(551.5,22),'약 19cm',(624,12))
ax.plot([557,603],[12,12],color='#25564c',lw=1)
dim((355,70),(484,70),'침대 옆 129cm',(419,70))
dim((355,35),(452,35),'97cm',(400,35))
ax.text(400,13,'휴지통 옆 좁은 구간',ha='center',fontsize=9,color='#4d605b')
ax.add_patch(Circle((405,-30),28,fill=False,ec='#245d8a',lw=1.5,ls='--'))
ax.text(405,-30,'플레이어\nØ56cm',ha='center',va='center',fontsize=9,color='#245d8a')
ax.annotate('',xy=(395,110),xytext=(395,-6),arrowprops={'arrowstyle':'->','color':'#245d8a','lw':2})
ax.text(465,265,'치수는 유지 · 옷장 문만 양문으로 변경',ha='center',fontsize=16,weight='bold')
ax.text(465,-94,'각 문짝 폭 21.5cm / 90° 개방 · 옷장 사이 간격 2cm',ha='center',fontsize=11)
ax.text(465,-109,'블렌더 검토 도면 · 발치 틈은 통로가 아님 · 게임 충돌 검증 전',ha='center',fontsize=10,color='#6c6251')
fig.savefig(OUT/'room-clearance-plan.png',dpi=160,bbox_inches='tight',facecolor=fig.get_facecolor());plt.close(fig)

asset_rel='../Art/EnvironmentConcepts/furniture-review-v2/'
rows=''.join(f"<tr><td>{html.escape(d['asset'])}</td><td>{' × '.join(map(str,d['expected_cm']))}</td><td>{' × '.join(map(str,d['measured_cm']))}</td><td>{'치수 일치' if d['passed'] else '재검토'}</td></tr>" for d in r['after'])
page='''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>해담고시원 | 가구·개폐 검토 v2</title><style>
*{box-sizing:border-box}body{margin:0;background:#17211f;color:#edf1e9;font:16px/1.65 'Malgun Gothic',sans-serif}main{max-width:1450px;margin:auto;padding:42px 28px}h1{font-size:34px;line-height:1.35}h2{margin-top:48px}p{max-width:960px;color:#c6d0c8}.tag{color:#8bd0b3;letter-spacing:2px;font-size:13px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}figure{margin:0;background:#26332e;border:1px solid #435047;border-radius:8px;overflow:hidden}img{display:block;width:100%;height:auto}figcaption{padding:16px 20px}.wide{margin-top:18px}.facts{display:flex;gap:16px;flex-wrap:wrap}.facts span{padding:16px 22px;background:#263a32;border:1px solid #41634f;border-radius:6px}table{border-collapse:collapse;width:100%;font-size:14px}td,th{text-align:left;border-bottom:1px solid #435047;padding:9px}a{color:#9ed2bd}.note{border-left:3px solid #d2b57a;padding-left:18px}button{font:inherit;color:#eaf2e8;background:#304b3f;border:1px solid #618371;padding:9px 18px;cursor:pointer}button[aria-pressed=true]{background:#91c9aa;color:#17211f}.plan{max-width:930px;margin:auto}@media(max-width:800px){.grid{grid-template-columns:1fr}main{padding:22px 14px}h1{font-size:26px}}
</style><main><div class="tag">HAEDAM / FURNITURE REVIEW 02</div><h1>가구 치수는 그대로.<br>옷장은 침대에 닿지 않게.</h1><p>기존 통합 설계도와 블렌더 검토본을 대조했습니다. 각 옷장 45 × 45 × 175cm, 두 개를 발치에 나란히 둔 배치는 유지하고 문을 폭 21.5cm의 양문으로 분리했습니다.</p><div class="facts"><span>31종 외형 치수 확인</span><span>225개 배치 위치 대조</span><span>옷장 30개 반영</span><span>문–침대 여유 ≥18.97cm</span><span>크레딧 0</span></div><h2>같은 카메라에서 닫힘 / 열림</h2><div class="grid">
'''
for file,label in [('room-closed','닫힌 상태 · 외형과 위치 유지'),('room-open','문 90° 개방 · 내부 선반과 분리 문짝')]:page+=f'<figure><img src="{asset_rel}{file}.png"><figcaption>{label}</figcaption></figure>'
page+=f'''</div><h2>통로와 문 끝의 여유</h2><div class="grid"><figure><img src="{asset_rel}room-open-top.png"><figcaption>동일 모델의 실제 상부 렌더</figcaption></figure><figure><img src="{asset_rel}room-clearance-plan.png"><figcaption>명세 좌표에 따른 치수 도면 / cm</figcaption></figure></div><p class="note">발치의 39.5cm 틈은 플레이어가 지나가는 통로가 아닙니다. 왼쪽 통로로 접근합니다. 휴지통 옆 가구 기준 유효 폭은 97cm, 현재 코드의 플레이어 캡슐 지름은 56cm입니다. 이 수치 비교는 게임 엔진의 실제 이동·문 개폐 테스트를 대신하지 않습니다.</p><h2>1–3층과 옥상 배치</h2><p>구조와 기존 가구 위치를 보존한 검토용 렌더입니다. 벽은 내부가 보이도록 일부 높이에서 잘랐고, 위생기구 등 일부 소품은 외형 치수만 표현한 임시 형태입니다.</p><nav>'''
for f in range(1,5):page+=f'<button onclick="floor({f})" id="b{f}" aria-pressed="{str(f==1).lower()}">{str(f)+"층" if f<4 else "옥상"}</button> '
page+=f'''</nav><figure class="wide"><img id="floor" src="{asset_rel}floor-1.png"><figcaption id="floorlabel">1층 전체 가구 배치</figcaption></figure><h2>실측 결과</h2><p>평가 메시의 실제 경계로 외형을 측정했습니다. 목표 대비 0.1cm 이내이며, 기존 게임에 들어간 모든 에셋의 치수가 같다는 의미는 아닙니다. 배치 가구끼리의 부품 경계상자 교차 후보는 0건입니다. 전체 벽체·계단·런타임 충돌까지 통과했다는 뜻은 아닙니다.</p><details><summary>31종 치수 표 열기</summary><table><tr><th>모델</th><th>목표 cm</th><th>실측 cm</th><th>결과</th></tr>{rows}</table></details><h2>파일과 검증 범위</h2><p><a href="{asset_rel}haedam-furniture-reviewed.blend">수정 블렌더 원본</a> · <a href="{asset_rel}audit.json">치수·개폐 검사 JSON</a> · <a href="floor-plan.html">통합 설계도</a></p><p>원본 검토본을 보존하고 별도 버전으로 저장했습니다. Blender 타임라인 1=닫힘, 91=열림. 91개 상태의 실측과 문 회전 반경의 보수적 계산을 함께 확인했습니다. Unreal 에셋·게임 실행파일은 이번 검토에서 변경하지 않았습니다.</p><script>function floor(n){{document.getElementById('floor').src='{asset_rel}floor-'+n+'.png';document.getElementById('floorlabel').textContent=(n===4?'옥상':n+'층')+' 전체 가구 배치';for(let i=1;i<=4;i++)document.getElementById('b'+i).setAttribute('aria-pressed',i===n);}}</script></main></html>'''
(ROOT/'docs/furniture-review-v2.html').write_text(page,encoding='utf-8')
(OUT/'BUILD_NOTES.md').write_text('''# 가구 검토 v2
2026-11-01. 기존 45×45×175cm 옷장 2개/거주실의 외형과 위치를 유지하고 각 21.5cm 양문으로 변경.
31종 실제 평가 메시 치수와 225개 배치 대조. 옷장 30개 업데이트. 부품 AABB 가구 교차 후보 0건.
닫힘/열림과 모든 층 이미지는 같은 수정 .blend에서 렌더. 프레임 1 닫힘, 91 열림.
문-침대 연속 회전 여유 하한 약18.97cm. 발치 틈은 통행용이 아니며 왼쪽 통로 접근.
실측 보고서 audit.json. Unreal 임포트/게임 충돌 미검증. 일부 소품은 치수 검토용 placeholder.
기존 검토 .blend는 보존. 유료 생성 없음.
''',encoding='utf-8')
print('PUBLISHED furniture-review-v2.html and clearance plan')
