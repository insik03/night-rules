"""Measure the game's captured master output, not just source WAVs."""
from pathlib import Path
import wave,json
import numpy as np
r=Path(__file__).resolve().parents[1]
p=r/'Builds/Windows/NightRulesPrototype/Saved/Verification/polish_audio_output.wav'
with wave.open(str(p)) as w:
 channels=w.getnchannels();rate=w.getframerate();a=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)/32768
result={'recorded_game_mix':str(p),'seconds':len(a)/(rate*channels),'rms':float(np.sqrt(np.mean(a*a))),'peak':float(np.max(np.abs(a))),'channels':channels,'sample_rate':rate}
assert result['seconds']>4 and result['rms']>.01 and result['peak']<.995,result
(r/'tools/output/polish-audio-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('GAME_AUDIO_OUTPUT_PASS',result['rms'],result['peak'])
