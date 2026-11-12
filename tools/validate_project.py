"""Offline integrity checks. These are not an Unreal compile/playtest substitute."""
import json, math, wave
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
project=ROOT/'NightRulesPrototype'
data=json.loads((project/'Content/Data/day1.json').read_text(encoding='utf-8'))
assert data['location']=='해담고시원'
for field in ['first_call_seconds','witness_window_seconds','second_call_seconds','uv_capacity_seconds']:
    assert math.isfinite(data[field]) and data[field]>0, field
assert data['witness_window_seconds']<data['second_call_seconds']
required={'rules','roster','note','physical','uv','minseo','chair','first_call','second_call','final_call'}
assert required<=data['documents'].keys()
assert all(data['documents'][k].strip() for k in required)
info=json.loads((project/'NightRulesPrototype.uproject').read_text(encoding='utf-8'))
assert info['Modules'][0]['Name']=='NightRulesPrototype'
for asset in ['SM_Phone','SM_Cartridge','SM_Chair','SM_Desk','SM_Flashlight','SM_Door']:
    f=ROOT/'Art/Generated'/(asset+'.fbx')
    assert f.is_file() and f.stat().st_size>1000, asset
for audio in ['phone_ring','knock','step']:
    with wave.open(str(ROOT/'Art/Generated'/(audio+'.wav')),'rb') as w:
        assert w.getnchannels()==1 and w.getsampwidth()==2 and w.getnframes()>0
source=(project/'Source/NightRulesPrototype/NRGame.cpp').read_text(encoding='utf-8')
assert 'ThreatTime>13' not in source, 'No arbitrary timed deaths'
assert 'NRMechanics::Drain' in source and 'NRMechanics::WitnessWindow' in source
assert 'Checkpoint.Pickups=Collected' in source and 'Collected=Checkpoint.Pickups' in source
print('PROJECT_DATA_OK: documents, timings, source links, six FBX files, three WAV files')
