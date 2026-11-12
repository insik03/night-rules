"""Prepare louder source SFX without compounding gain on repeated runs."""
from pathlib import Path
import wave,json
import numpy as np
R=Path(__file__).resolve().parents[1];out=R/'Art/AudioBalanced';out.mkdir(exist_ok=True)
rows=[]
for source in [R/'Art/DemoAudio',R/'Art/Generated']:
 for p in source.glob('*.wav'):
  with wave.open(str(p)) as w:params=w.getparams();a=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)/32768
  target=.11 if p.stem in ['fluorescent_hum','room_tone','chase_pulse'] else .16
  before=float(np.sqrt(np.mean(a*a)));gain=min(target/max(before,1e-7),.85/max(float(np.max(np.abs(a))),1e-7),8)
  a*=gain
  with wave.open(str(out/p.name),'wb') as w:w.setparams(params);w.writeframes((a*32767).astype('<i2').tobytes())
  rows.append({'name':p.stem,'source':str(p.relative_to(R)),'gain':round(gain,3),'rms':round(float(np.sqrt(np.mean(a*a))),4),'loop':p.stem in ['fluorescent_hum','room_tone','chase_pulse']})
(out/'manifest.json').write_text(json.dumps(rows,indent=2))
print('AUDIO_BALANCED',len(rows))
