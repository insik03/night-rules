"""Generate a local Korean audition; model/runtime stay out of the game build."""
from pathlib import Path
import sys,json,wave,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1];MODEL=ROOT/'tools/output/tts'
sys.path.insert(0,str(MODEL))
from helper import load_text_to_speech,load_voice_style
out=ROOT/'Art/Voice';out.mkdir(parents=True,exist_ok=True)
tts=load_text_to_speech(str(MODEL/'onnx'))
style=load_voice_style([str(MODEL/'voice_styles/F1.json')])
lines=['옆방에서 계속 의자를 끌어요.','근데… 제가 전화하는 소리가 그 방에서도 나요.','이백이호요. 공실이라면서요?']
clips=[];items=[];np.random.seed(203)
for i,text in enumerate(lines):
 pcm,duration=tts(text,'ko',style,8,.92);pcm=pcm[0,:int(tts.sample_rate*duration[0])]
 # Gentle telephone band limiting, retaining a quiet noise floor without clipping.
 freq=np.fft.rfftfreq(len(pcm),1/tts.sample_rate);mask=1/(1+(240/np.maximum(freq,1))**4)/(1+(freq/3800)**6)
 pcm=np.fft.irfft(np.fft.rfft(pcm)*mask,n=len(pcm)).astype(np.float32)
 pcm=pcm/max(float(np.max(np.abs(pcm))),.001)*.65
 name=f'minseo_first_{i+1:02}.wav';path=out/name
 with wave.open(str(path),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(tts.sample_rate);w.writeframes((pcm*32767).astype('<i2').tobytes())
 clips.extend([pcm,np.zeros(int(tts.sample_rate*.45),np.float32)])
 items.append({'file':name,'text':text,'seconds':round(len(pcm)/tts.sample_rate,3),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
 print('VOICE',name,items[-1]['seconds'],flush=True)
with wave.open(str(out/'minseo_first_sample.wav'),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(tts.sample_rate);w.writeframes((np.concatenate(clips)*32767).astype('<i2').tobytes())
(out/'manifest.json').write_text(json.dumps({'model':'Supertone/supertonic-2','voice':'F1 preset (no voice cloning)','language':'ko','license':'OpenRAIL-M','license_url':'https://huggingface.co/Supertone/supertonic-2/blob/main/LICENSE','use':'pre-generated first-phone-call audition','processing':'240Hz highpass, 3800Hz lowpass, peak 0.65','clips':items},ensure_ascii=False,indent=2),encoding='utf-8')
(out/'MODEL_LICENSE.txt').write_bytes((MODEL/'LICENSE').read_bytes())
