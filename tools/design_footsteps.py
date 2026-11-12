"""Deterministic, licensed shoe foley for gameplay and the showcase mix."""
from pathlib import Path
import hashlib, json, shutil, subprocess, wave, zipfile
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'Art/Footsteps'; SRC=BASE/'Source'; OUT=BASE/'Processed'
OUT.mkdir(parents=True,exist_ok=True)
RATE=48000
with zipfile.ZipFile(SRC/'kenney_impact-sounds.zip') as z:
    for name in z.namelist():
        if name=='License.txt' or (name.startswith('Audio/') and any(k in name for k in ('footstep_concrete_','footstep_wood_','impactSoft_heavy_','impactWood_heavy_'))):
            (SRC/Path(name).name).write_bytes(z.read(name))

def source(name,speed=1):
    result=subprocess.run([shutil.which('ffmpeg'),'-v','error','-i',str(SRC/(name+'.ogg')),'-f','f32le','-ac','1','-ar',str(RATE),'-'],capture_output=True,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
    x=np.frombuffer(result.stdout,dtype='<f4').astype(float)
    hits=np.flatnonzero(np.abs(x)>.004)
    if len(hits):x=x[max(0,hits[0]-120):min(len(x),hits[-1]+1200)]
    return np.interp(np.arange(0,len(x),speed),np.arange(len(x)),x)

def eq(x,low=45,high=5000):
    f=np.fft.rfftfreq(len(x),1/RATE)
    return np.fft.irfft(np.fft.rfft(x)*(1-np.exp(-(f/low)**2))/(1+(f/high)**4),n=len(x))

def overlay(layers):
    x=np.zeros(max(int(at*RATE)+len(y) for y,at,gain in layers))
    for y,at,gain in layers:
        start=int(at*RATE);x[start:start+len(y)]+=y*gain
    return x

def write(name,x,peak=.78):
    x=eq(x,38,6000); x[:120]*=np.linspace(0,1,120);x[-960:]*=np.linspace(1,0,960)
    x*=min(peak/max(np.max(np.abs(x)),1e-9),.115/max(np.sqrt(np.mean(x*x)),1e-9))
    with wave.open(str(OUT/(name+'.wav')),'wb') as w:
        w.setparams((1,2,RATE,0,'NONE',''));w.writeframes((x*32767).astype('<i2').tobytes())
    return x

clips={}
for i in range(5):
    concrete=source(f'footstep_concrete_{i:03d}',.96+i*.012)
    wood=eq(source(f'footstep_wood_{i:03d}',.87),45,850)
    clips[f'step_player_{i:02d}']=write(f'step_player_{i:02d}',overlay([(eq(concrete,65,4200),0,.85),(wood,.012,.23)]),.65)
    heavy=eq(source(f'impactSoft_heavy_{i:03d}',.8),40,1600)
    shoe=eq(source(f'footstep_concrete_{i:03d}',.76+i*.018),45,3400)
    heel=eq(source(f'impactWood_heavy_{i:03d}',.88),50,1100)
    clips[f'step_ghost_{i:02d}']=write(f'step_ghost_{i:02d}',overlay([(shoe,0,.82),(heavy,.008,.32),(heel,.025,.16)]))

# A short solid chair strike: no scream, gore, or synthesized click.
strike=overlay([(source('impactWood_heavy_002',.78),0,.75),(source('impactSoft_heavy_003',.7),.012,.55)])
clips['chair_strike']=write('chair_strike',strike,.85)
preview=np.zeros(RATE*12)
for start,prefix,interval,gain in [(0,'step_player_',.55,.7),(4,'step_player_',.35,1),(8,'step_ghost_',.27,1.2)]:
    for i,at in enumerate(np.arange(start,start+3.3,interval)):
        x=clips[prefix+f'{i%5:02d}']*gain; j=int(at*RATE);n=min(len(x),len(preview)-j);preview[j:j+n]+=x[:n]
with wave.open(str(BASE/'footsteps-preview.wav'),'wb') as w:
    w.setparams((1,2,RATE,0,'NONE',''));w.writeframes((np.clip(preview,-.95,.95)*32767).astype('<i2').tobytes())
report={'source':'https://kenney.nl/assets/impact-sounds','license':'CC0 1.0; Source/License.txt','processing':'EQ, pitch variation, layered shoe/heel foley. Original source retained.','clips':{name:{'seconds':round(len(x)/RATE,3),'peak':round(float(np.max(np.abs(x))),4),'sha256':hashlib.sha256((OUT/(name+'.wav')).read_bytes()).hexdigest()} for name,x in clips.items()}}
(BASE/'manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('FOOTSTEP_DESIGN_COMPLETE',len(clips))
