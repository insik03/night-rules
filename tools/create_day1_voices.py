"""Generate all DAY 1 narrative subtitles/voices from the same source text."""
from pathlib import Path
import sys,json,wave,hashlib,re,urllib.request
import numpy as np
ROOT=Path(__file__).resolve().parents[1]; MODEL=ROOT/'tools/output/tts'
for preset in ['M1','M2','F3','M3']:
 p=MODEL/'voice_styles'/(preset+'.json')
 if not p.exists():urllib.request.urlretrieve('https://huggingface.co/Supertone/supertonic-2/resolve/main/voice_styles/'+preset+'.json',p)
sys.path.insert(0,str(MODEL))
from helper import load_text_to_speech,load_voice_style
tts=load_text_to_speech(str(MODEL/'onnx')); styles={x:load_voice_style([str(MODEL/'voice_styles'/(x+'.json'))]) for x in ['F1','F2','F3','M1','M2','M3']}
out=ROOT/'Art/Voice/Day1';out.mkdir(parents=True,exist_ok=True)
docs=json.loads((ROOT/'NightRulesPrototype/Content/Data/day1.json').read_text(encoding='utf-8'))['documents']
rows=[]; sequences={}
DIALOGUE_KEYS={'resident_203_safe', 'final_call', 'resident_105', 'resident_203', 'resident_105_early', 'minseo', 'resident_104', 'first_call', 'manager_call', 'dream_voice', 'second_call', 'minseo_second_call', 'resident_203_second_call', 'resident_203_safe_second_call'}
# Only voices actually heard in the scene are dubbed. Written quotes and inspection prose are silent.
for key,body in docs.items():
 if key in ['rules','roster','note']:continue
 lines=[x.strip() for x in body.splitlines()[1:] if x.strip()]
 sequences[key]=[]
 for n,line in enumerate(lines):
  spoken=key in DIALOGUE_KEYS and line.startswith(('‘','“'))
  # Variants reuse their base scene's clips; only new lines are generated.
  base=key.removesuffix('_second_call').replace('resident_203_safe','resident_203')
  row=next((dict(x) for x in sequences.get(base,[]) if x['subtitle']==line and x['asset']),None) if spoken and base!=key else None
  if row:
   sequences[key].append(row);rows.append(row);continue
  if not spoken:
   row={'asset':'','subtitle':line,'spoken_text':'','voice':'','seconds':0}
   sequences[key].append(row);rows.append(row);continue
  voice='M1'
  if spoken:
   if key in ['first_call','second_call'] or key.startswith(('minseo','resident_203')):voice='F1'
   elif key.startswith('resident_105'):voice='F2'
   elif key=='manager_call':voice='M2'
   elif key=='resident_104':voice='M3'   # distinct from the manager
   elif key=='final_call':voice='F3'     # the 307 caller is not Jeongsuk's voice
  text=line.strip('‘’“”')
  text=re.sub(r'(\d{3})호',lambda m: {'104':'백사','105':'백오','202':'이백이','203':'이백삼','307':'삼백칠'}.get(m[1],m[1])+'호',text)
  text=text.replace('CCTV','씨씨티비').replace('PC','피씨').replace('UV','유브이').replace('J로','제이 키로')
  name=f'vo_{key}_{n+1:02}'; path=out/(name+'.wav')
  fingerprint=hashlib.sha256((text+voice+'v2').encode()).hexdigest()
  cache=MODEL/'voice-cache'/(name+'.json');cache.parent.mkdir(exist_ok=True)
  if not path.exists() or not cache.exists() or json.loads(cache.read_text())['fingerprint']!=fingerprint:
   np.random.seed(203+n); pcm,duration=tts(text,'ko',styles[voice],8,.98);pcm=pcm[0,:int(tts.sample_rate*duration[0])]
   if key in ['first_call','second_call','manager_call','final_call'] and spoken:
    freq=np.fft.rfftfreq(len(pcm),1/tts.sample_rate);mask=1/(1+(200/np.maximum(freq,1))**4)/(1+(freq/4200)**6)
    pcm=np.fft.irfft(np.fft.rfft(pcm)*mask,n=len(pcm)).astype(np.float32)
   rms=np.sqrt(np.mean(pcm*pcm));pcm=pcm*min(.13/max(float(rms),1e-6),.85/max(float(np.max(np.abs(pcm))),1e-6))
   with wave.open(str(path),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(tts.sample_rate);w.writeframes((pcm*32767).astype('<i2').tobytes())
   cache.write_text(json.dumps({'fingerprint':fingerprint}))
  with wave.open(str(path)) as w:seconds=w.getnframes()/w.getframerate()
  row={'asset':name,'subtitle':line,'spoken_text':text,'voice':voice,'seconds':round(seconds,3),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
  sequences[key].append(row); rows.append(row);print('VOICE',name,round(seconds,2),flush=True)
manifest={'model':'Supertone/supertonic-2','license_url':'https://huggingface.co/Supertone/supertonic-2/blob/main/LICENSE','generated_on':'2026-10-09','method':'local preset voices, no cloning; audible dialogue only; documents and narration remain subtitles','sequences':sequences}
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'NightRulesPrototype/Content/Data/voices.json').write_text(json.dumps(sequences,ensure_ascii=False,indent=2),encoding='utf-8')
print('DAY1_VOICES_COMPLETE',len(sequences),len(rows),sum(r['seconds'] for r in rows),flush=True)
