"""Create a Korean roster monitor image from the project's own story data."""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Art/Generated/T_ResidentScreen.png'
data=json.loads((ROOT/'NightRulesPrototype/Content/Data/day1.json').read_text(encoding='utf-8'))
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',28)
small=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',20)
image=Image.new('RGB',(700,500),(9,24,22));draw=ImageDraw.Draw(image)
draw.rectangle((12,12,687,487),outline=(45,88,75),width=2)
draw.text((34,26),'해담고시원  |  입주자 관리',font=font,fill=(160,211,181))
draw.line((34,78,665,78),fill=(65,105,88),width=2)
lines=[line for line in data['documents']['roster'].splitlines() if '호 ' in line]
assert len(lines)==17, '15 residents plus vacant 202 and 307 must fit on the monitor'
for floor in (1,2,3):
 x=36+(floor-1)*210
 draw.text((x,100),f'{floor}층',font=small,fill=(180,206,162))
 rows=[line for line in lines if line.startswith(str(floor))]
 for i,line in enumerate(rows):
  # The monitor shows identity and occupancy; E opens full role/inspection notes.
  label=line.split(' / ',1)[0]
  assert draw.textlength(label,font=small)<200 and 145+i*39+26<420
  draw.text((x,145+i*39),label,font=small,fill=(134,182,156))
draw.text((36,440),'거주 15명  |  [E] 전체 명단 열기',font=small,fill=(180,206,162))
image.save(OUT)
print(OUT)
