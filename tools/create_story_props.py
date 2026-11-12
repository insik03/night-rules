"""Deterministic Korean document artwork, sourced from the existing DAY1 script."""
from pathlib import Path
import json, hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
FONTS=ROOT/'NightRulesPrototype/Content/Fonts'
OUT=ROOT/'Art/StoryProps';OUT.mkdir(parents=True,exist_ok=True)
GEN=ROOT/'Art/Generated'
DATA=json.loads((ROOT/'NightRulesPrototype/Content/Data/day1.json').read_text(encoding='utf-8'))
DOC=DATA['documents']
def font(size,kind='serif'):
 return ImageFont.truetype(str(FONTS/({'serif':'NanumMyeongjo-Regular.ttf','bold':'NanumMyeongjo-Bold.ttf','hand':'NanumBrushScript-Regular.ttf'}[kind])),size)
def paper(w,h):
 rng=np.random.default_rng(13); y,x=np.mgrid[:h,:w]
 edge=np.minimum.reduce([x/(w/2), (w-1-x)/(w/2),y/(h/2),(h-1-y)/(h/2)])
 grain=rng.normal(0,.9,(h,w))-7*np.exp(-edge*15)
 return Image.fromarray(np.clip(np.array([226,219,198])+grain[:,:,None],0,255).astype('uint8'))
def wrap(draw,text,f,width):
 rows=[]
 for raw in text.splitlines():
  line=''
  for ch in raw:
   if line and draw.textlength(line+ch,font=f)>width:rows.append(line);line=ch
   else:line+=ch
  rows.append(line)
 return rows
def body(im,text,at,size,width,kind='serif',leading=None):
 d=ImageDraw.Draw(im);x,y=at;f=font(size,kind)
 for line in wrap(d,text,f,width):
  d.text((x,y),line,font=f,fill=(38,34,28));y+=leading or round(size*1.35)
 assert y<im.height-28,(y,im.height,text)
 return y
def header(im,title,sub='해담고시원',size=64):
 d=ImageDraw.Draw(im);d.text((58,40),sub,font=font(25),fill=(92,80,61));d.text((55,86),title,font=font(size,'bold'),fill=(30,30,26));d.line((58,181,im.width-58,181),fill=(103,87,62),width=2)
def rules():
 base=paper(1024,1320);d=ImageDraw.Draw(base)
 d.rectangle((28,28,995,1291),outline=(99,86,64),width=2)
 header(base,'야 간 수 칙',size=73)
 d.text((750,48),'야간총무 숙지용',font=font(22),fill=(100,84,60))
 annotation=DATA['rule_annotation'];y=233;ink_y=0
 for i,line in enumerate(DOC['rules'].splitlines()[2:],1):
  d.text((65,y),str(i)+'.',font=font(43,'bold'),fill=(32,31,28))
  text=line.split('. ',1)[1];rows=wrap(d,text,font(36),810)
  for row in rows:d.text((128,y+3),row,font=font(36),fill=(33,31,26));y+=49
  if i==annotation['rule']:ink_y=y+3;y+=80
  y+=27
 assert y<1205,y
 d.line((65,1210,959,1210),fill=(134,120,92),width=1)
 d.text((65,1237),'근무 종료 전 관리실에 비치할 것.',font=font(25),fill=(90,78,60))
 # Both messages use precisely the same font, size, pigment and stroke treatment.
 for stage,name in enumerate(['T_RulesPage','T_RulesRed','T_RulesReply']):
  im=base.copy();p=ImageDraw.Draw(im)
  if stage:
   p.line((91,ink_y+19,120,ink_y+16),fill=(139,25,22),width=3)
   p.text((132,ink_y-5),annotation['denial'],font=font(53,'hand'),fill=(139,25,22))
  if stage==2:p.text((655,ink_y-5),annotation['reply'],font=font(53,'hand'),fill=(139,25,22))
  im.save(GEN/(name+'.png'));im.save(OUT/(name+'.png'))
 return ink_y
rules()
note=paper(1024,820);header(note,'다음 총무에게',size=55)
body(note,'\n'.join(DOC['note'].splitlines()[2:]),(58,213),40,905,'hand',43)
note.save(OUT/'T_PredecessorNote.png')
ledger=paper(1024,748);header(ledger,'전임 총무 장부',size=67)
body(ledger,'해담고시원 관리실\n\n기록 담당  :  도윤\n\n민원 · 공실 확인 · 열쇠 인수인계',(68,222),42,887,'serif',54)
ImageDraw.Draw(ledger).text((640,640),'버리지 마세요.',font=font(48,'hand'),fill=(44,41,34))
ledger.save(OUT/'T_ServiceLedgerCover.png')
guide=paper(768,1024);header(guide,'UV 점검등',size=58)
guide_text='\n'.join(DOC['uv_guide'].splitlines()[2:])
body(guide,guide_text,(58,215),33,655,'serif',47)
guide.save(OUT/'T_UVGuide.png')
# A single preview sheet is for reviewing the artwork before application.
sheet=Image.new('RGB',(1800,1400),(29,35,31));sheet.paste(Image.open(OUT/'T_RulesReply.png').resize((900,1160)),(30,120))
sheet.paste(note.resize((760,609)),(995,120));sheet.paste(ledger.resize((455,332)),(975,825));sheet.paste(guide.resize((330,440)),(1450,825))
d=ImageDraw.Draw(sheet);d.text((40,35),'야간수칙 · 필수 문서 에셋',font=font(48,'bold'),fill=(236,230,211));d.text((35,1300),'본문: 나눔명조   /   붉은 글씨·메모: 나눔손글씨 붓',font=font(34),fill=(211,211,195))
sheet.save(OUT/'preview.png')
manifest={'source':'NightRulesPrototype/Content/Data/day1.json','fonts':[],'writers_share_style':True,'ai_generated':False}
for p in FONTS.glob('*.ttf'):manifest['fonts'].append({'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(OUT/'provenance.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('STORY_ART_COMPLETE')
