"""Author transparent repair-marker textures for the two DAY1 UV clues."""
from pathlib import Path
from PIL import Image,ImageDraw
out=Path(__file__).resolve().parents[1]/'Art/Investigation';out.mkdir(exist_ok=True)
im=Image.new('RGBA',(1024,384));d=ImageDraw.Draw(im)
# A repair worker's marks, not instructions or a translated answer. The same
# broken middle stroke appears on the fragment for the player to compare.
for x in (390,510,630):
 for start,end in ([(0,.425),(.575,1)] if x==510 else [(0,1)]):
  d.line([(x-45*start,70+210*start),(x-45*end,70+210*end)],fill=(150,220,184,220),width=14)
im.save(out/'T_UVDoor.png')
im=Image.new('RGBA',(512,256));d=ImageDraw.Draw(im)
for x in (140,250,360):
 for start,end in ([(0,.425),(.575,1)] if x==250 else [(0,1)]):
  d.line([(x-50*start,40+170*start),(x-50*end,40+170*end)],fill=(175,240,215,255),width=20)
im.save(out/'T_UVFragment.png')
