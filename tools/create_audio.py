"""Original synthetic placeholder audio. No recordings or third-party licenses."""
from pathlib import Path
import math, random, struct, wave

OUT=Path(__file__).resolve().parent.parent/'Art'/'Generated'
OUT.mkdir(parents=True, exist_ok=True)
RATE=22050
random.seed(71)
def save(name,seconds,fn):
    with wave.open(str(OUT/(name+'.wav')),'wb') as w:
        w.setparams((1,2,RATE,0,'NONE','not compressed'))
        w.writeframes(b''.join(struct.pack('<h',int(max(-1,min(1,fn(i/RATE)))*14000)) for i in range(int(seconds*RATE))))
save('phone_ring',2.2,lambda t: (math.sin(t*2*math.pi*660)+math.sin(t*2*math.pi*880))*.3 if t%1.1<.7 else 0)
save('knock',1.2,lambda t: sum(math.exp(-max(0,t-s)*45)*math.sin((t-s)*2*math.pi*110)*.8 if 0<=t-s<.16 else 0 for s in [.05,.4,.75]))
save('step',.22,lambda t: random.uniform(-1,1)*math.exp(-t*32)*.5)
print('AUDIO_OK',OUT)
