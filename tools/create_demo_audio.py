"""Deterministic original atmospheric SFX; stdlib only, no recordings or voices."""
from pathlib import Path
import math, random, wave, array, json
OUT=Path(__file__).resolve().parents[1]/'Art'/'DemoAudio'; OUT.mkdir(parents=True,exist_ok=True)
RATE=44100
SPECS={'fluorescent_hum':(12,True),'room_tone':(16,True),'power_trip':(2,False),'power_return':(3,False),'chair_drag':(4,False),'pipe_knock':(3,False),'door_slam':(2,False),'distant_steps':(8,False),'breath_near':(5,False),'radio_static':(6,False),'metal_rattle':(4,False),'chase_pulse':(10,True)}
manifest=[]
for index,(name,(duration,loop)) in enumerate(SPECS.items()):
    rng=random.Random(413+index); samples=[]; low=0.; previous=0.
    for i in range(int(RATE*duration)):
        t=i/RATE; white=rng.uniform(-1,1); low+=.017*(white-low); high=white-previous; previous=white
        sine=lambda hz: math.sin(2*math.pi*hz*t)
        if name=='fluorescent_hum':v=.14*sine(100)+.07*sine(200)+.1*low
        elif name=='room_tone':v=.6*low+.012*sine(43)+.008*sine(71)
        elif name=='power_trip':v=(.36*white+.2*sine(72))*math.exp(-t*14)+.1*sine(100*math.exp(-t*2))*math.exp(-t*4)
        elif name=='power_return':v=.1*sine(100)*min(1,t)+sum(.18*white*math.exp(-(t-p)*35) if 0<t-p<.2 else 0 for p in [.1,.55,1.2])
        elif name=='chair_drag':v=(.27*low+.05*white+.05*sine(310+18*math.sin(t*8)))*(.4+.6*math.sin(t*3)**2)
        elif name=='pipe_knock':v=sum((.18*sine(185)+.12*sine(493)+.08*sine(811))*math.exp(-(t-p)*12) if 0<t-p<.45 else 0 for p in [.12,.63,1.5,1.75])
        elif name=='door_slam':v=(.35*low+.1*sine(58))*math.exp(-max(0,t-.15)*6) if t>.15 else .12*white*t
        elif name=='distant_steps':v=sum((.38*low+.03*white+.06*sine(87))*math.exp(-(t-p)*22) if 0<t-p<.32 else 0 for p in [.3,1.15,2.,2.9,3.8,4.8,5.9,7.])
        elif name=='breath_near':v=(.18*low+.015*high)*(math.sin(math.pi*t/duration)**2)*(.55+.45*math.sin(t*2))
        elif name=='radio_static':v=(.06*high+.12*low)*(.3+.7*math.sin(t*9)**8)
        elif name=='metal_rattle':v=sum((.06*sine(667)+.06*sine(971)+.08*sine(1331))*math.exp(-(t-p)*22) if 0<t-p<.35 else 0 for p in [.15,.4,.7,1.8,2.1,2.5,3.1])
        else:v=.1*sine(44)*(.1+.9*math.sin(math.pi*1.2*t)**12)+.15*low
        # Short fades also give seamless zero-crossing loop boundaries.
        edge=min(1,t/.06,(duration-t)/.12); samples.append(v*max(0,edge))
    mean=sum(samples)/len(samples); samples=[v-mean for v in samples]
    peak=max(abs(v) for v in samples); gain=min(1,.70/max(peak,1e-9))
    pcm=array.array('h',(round(v*gain*32767) for v in samples))
    with wave.open(str(OUT/(name+'.wav')),'wb') as w:
        w.setparams((1,2,RATE,0,'NONE','not compressed')); w.writeframes(pcm.tobytes())
    manifest.append({'name':name,'duration':duration,'loop':loop,'peak':peak*gain,'rms':math.sqrt(sum(v*v for v in samples)/len(samples))*gain,'source':'original deterministic synthesis'})
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('DEMO_AUDIO_COMPLETE',len(manifest))
