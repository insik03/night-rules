"""Synchronize captured game video and the game's own master mix at the chair impact."""
from pathlib import Path
import json,re,shutil,subprocess,wave
import numpy as np
R=Path(__file__).resolve().parents[1]; D=R/'docs/showcase/media';S=D/'source';F=shutil.which('ffmpeg')
def run(args):return subprocess.run([F,'-hide_banner',*args],check=True,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
video=S/'ghost-live.mp4';audio=R/'Builds/Windows/NightRulesPrototype/Saved/Verification/chair_chase_audio.wav'
pixels=run(['-i',str(video),'-vf','crop=iw:ih-160:0:100,fps=30,scale=32:18,format=gray','-f','rawvideo','-']).stdout
luma=np.frombuffer(pixels,dtype=np.uint8).reshape(-1,18,32).mean(axis=(1,2))
black=None
for i in range(80,len(luma)-15):
    if max(luma[i:i+15])<1.5:black=i/30;break
if black is None:raise RuntimeError('No sustained impact blackout in game footage')
def wav(p):
    with wave.open(str(p)) as w:
        rate=w.getframerate(); x=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)/32768
        return x.reshape(-1,w.getnchannels()).mean(axis=1),rate
x,rate=wav(audio);y,yr=wav(R/'Art/Footsteps/Processed/chair_strike.wav')
assert np.sqrt(np.mean(x*x))>.005 and np.max(np.abs(x))<.995,'Recorded game mix is silent or clipped'
if yr!=rate:y=np.interp(np.arange(round(len(y)*rate/yr))*yr/rate,np.arange(len(y)),y)
log=(S/'capture-ghost.log').read_text(encoding='utf-8',errors='replace')
start=float(re.search(r'NR_CAPTURE_AUDIO_START world_time=([\d.]+)',log)[1]);hit=float(re.search(r'NR_EXECUTION_HIT world_time=([\d.]+)',log)[1])
expected=hit-start
n=1<<(len(x)+len(y)-1).bit_length();corr=np.fft.irfft(np.fft.rfft(x,n)*np.conj(np.fft.rfft(y,n)),n=n)
lo=max(0,int((expected-.3)*rate));hi=min(len(x),int((expected+.3)*rate))
at=(lo+int(np.argmax(corr[lo:hi])))/rate;offset=at-black
length=min(len(luma)/30,black+1.2)
assert offset>=0 and offset<2,(at,black,offset)
dest=D/'의자_추격과_사망연출_v1.mp4'
run(['-y','-i',str(video),'-ss',str(offset),'-i',str(audio),'-map','0:v:0','-map','1:a:0','-c:v','copy','-af','alimiter=limit=0.95:level=false','-c:a','aac','-b:a','256k','-t',str(length),'-movflags','+faststart',str(dest)])
(D/'chair-preview-validation.json').write_text(json.dumps({'video':dest.name,'audio_source':'actual game master output; no microphone/desktop loopback','black_cut_seconds':black,'recorded_strike_seconds':at,'audio_trim_seconds':offset,'duration_seconds':length,'sample_peak':float(np.max(np.abs(x))),'rms':float(np.sqrt(np.mean(x*x)))},indent=2),encoding='utf-8')
print('CHAIR_PREVIEW_READY',dest.name,'duration',length,'offset',offset)
