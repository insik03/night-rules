"""Generate Stable Audio 3 candidates for the game's score/SFX through the local audio-studio MCP server.

Run with that server's Python (it ships the MCP client):
  %USERPROFILE%\\Tools\\audio-studio-mcp\\.venv\\Scripts\\python.exe tools/generate_score_sa3.py
Writes Art/ScoreSA3/<name>_<a|b>.wav (+ .json sidecars with prompt and seed). Existing
synthesized tracks in Art/Score are untouched; nothing is imported into Unreal.
Model: Stable Audio 3 medium, Stability AI Community License.
"""
import asyncio, json, os, sys
from pathlib import Path
from mcp import Client, StdioServerParameters

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Art' / 'ScoreSA3'; RAW = OUT / 'raw'; RAW.mkdir(parents=True, exist_ok=True)
SERVER = Path(os.environ['USERPROFILE']) / 'Tools/audio-studio-mcp/.venv/Scripts/audio-studio-mcp.exe'
NO_MUSIC = 'music, melody, singing, speech, words'

# name: (generate args, process args). Loops get a crossfade; one-shots get trimmed.
TRACKS = {
    'bgm_night': (dict(audio_type='music', duration_seconds=64, prompt='Dark ambient horror drone for quietly exploring an old run-down Korean boarding house at night. Low sustained cello and synth pad cluster, distant metallic pipe resonances, faint fluorescent hum, subtle tape hiss. No drums, no melody, slow and unsettling, sparse.'),
                  dict(loop=True, loop_crossfade_ms=2000, normalize='loudness', target_lufs=-24)),
    'bgm_blackout': (dict(audio_type='music', duration_seconds=48, prompt='Oppressive dark ambient for a building power outage. Deep sub-bass rumble, low droning, faint knocks and creaks inside the walls, a distant muffled moan. No drums, no melody, claustrophobic and very dark.'),
                     dict(loop=True, loop_crossfade_ms=2000, normalize='loudness', target_lufs=-22)),
    'bgm_chase': (dict(audio_type='music', duration_seconds=32, bpm=120, prompt='Intense psychological horror chase cue. Pounding low taiko and kick like a racing heartbeat, dissonant tremolo strings, metallic scrapes, rising panic. Cinematic, no vocals.'),
                  dict(loop=True, loop_crossfade_ms=120, normalize='loudness', target_lufs=-16)),
    # Round 2 (user: round-1 sting too grand). Close and dry, a jolt rather than a trailer hit.
    'sting_chase': (dict(audio_type='sfx', duration_seconds=3, cfg=3, letters='cdef', sound_source='sudden horror jolt in a narrow hallway', sound_action='one sharp violent screech of a metal chair leg scraped hard across tile, with a single short dissonant violin stab, then quick silence', sound_material='harsh metal on ceramic, thin scratchy strings, no brass, no drums, no boom', sound_space='small dry corridor, close, not cinematic, not epic'),
                    dict(trim_silence=True, normalize='peak')),    'heartbeat': (dict(audio_type='sfx', duration_seconds=6, sound_source='human heartbeat', sound_action='steady lub-dub at about 80 beats per minute', sound_material='muffled deep thumps, felt more than heard', sound_space='inside the chest, close, dry'),
                  dict(loop=True, loop_crossfade_ms=60, normalize='peak', mono=True)),
    'ghost_breath': (dict(audio_type='sfx', duration_seconds=6, sound_source='monstrous emaciated man breathing', sound_action='slow sharp inhale then long wet rattling exhale, repeating', sound_material='raspy throat, wet crackle', sound_space='very close, dry indoor'),
                     dict(loop=True, loop_crossfade_ms=300, normalize='peak', mono=True)),
    'ghost_shriek': (dict(audio_type='sfx', duration_seconds=2.5, sound_source='inhuman ghost', sound_action='sudden harsh raspy shriek, choked off abruptly', sound_material='distorted torn voice, no clear pitch', sound_space='indoor corridor, short reverb'),
                     dict(trim_silence=True, normalize='peak', mono=True)),
    'ghost_catch': (dict(audio_type='sfx', duration_seconds=2.5, sound_source='monster grabbing its victim', sound_action='sharp inhale right next to the ear, then a guttural roar and a heavy body impact', sound_material='wet throat, low growl, thud', sound_space='extremely close, intimate'),
                    dict(trim_silence=True, normalize='peak')),
    # Round 3 (user: rounds 1-2 too ordinary, voice must match the caretaker: 215 cm, burned skin,
    # empty eye sockets, an ear-to-ear grin frozen in place).
    'ghost_laugh': (dict(audio_type='sfx', duration_seconds=4, cfg=4, letters='gh', sound_source='a burned emaciated man with a frozen ear-to-ear grin', sound_action='laughing without moving his mouth: rapid high hissing giggle forced through clenched small teeth, breath catching and crackling in a scorched throat, goes on far too long then stops abruptly', sound_material='dry crackling burned throat, teeth clicking, wheezing, uncanny and wrong, not cartoonish', sound_space='right behind the listener in a narrow dark corridor'),
                    dict(trim_silence=True, normalize='peak', mono=True)),
    'ghost_chuckle': (dict(audio_type='sfx', duration_seconds=4, cfg=4, letters='gh', sound_source='a very tall hollow-chested man laughing from deep in a long throat', sound_action='slow low wet laugh that stutters and repeats like a skipping record, then a long crackling inhale', sound_material='scorched raspy voice, hollow chest resonance, uncanny', sound_space='a few metres away in a dark corridor, faint echo'),
                      dict(trim_silence=True, normalize='peak', mono=True)),    'tinnitus': (dict(audio_type='sfx', duration_seconds=6, sound_source='aftermath of a blow to the head', sound_action='muffled low rumble and soft ear ringing slowly fading out', sound_material='dull, muted, no siren, no alarm', sound_space='inside the head'),
                 dict(normalize='peak', peak_ceiling_db=-6, fade_out_ms=1500)),
}


async def call(c, name, args):
    r = await c.call_tool(name, args)
    text = ''.join(getattr(x, 'text', '') for x in r.content)
    if r.is_error: sys.exit(f'FAILED {name}: {text}')
    return json.loads(text)


async def main(only):
    params = StdioServerParameters(command=str(SERVER), args=[], env={**os.environ, 'AUDIO_STUDIO_OUTPUT_DIR': str(RAW)})
    manifest = []
    async with Client(params, read_timeout_seconds=1800) as c:
        for name, (gen, proc) in TRACKS.items():
            if only and name not in only: continue
            gen = dict(gen); letters = gen.pop('letters', 'ab')  # later rounds keep earlier files
            res = await call(c, 'generate_audio', {'variations': len(letters), **gen, 'title': name})
            for k, f in zip(letters, res['candidates']):
                path = f['path']
                done = await call(c, 'process_audio', {'input_audio': path, 'format': 'wav', 'sample_rate': 44100, **proc})
                out_path = Path(done['path'])
                final = OUT / f'{name}_{k}.wav'; final.write_bytes(out_path.read_bytes())
                manifest.append({'name': name, 'candidate': k, 'file': final.name, 'raw': Path(path).name,
                                 'seed': f.get('seed'), 'loop': bool(proc.get('loop')), **gen})
                print('SA3', final.name, flush=True)
        await call(c, 'unload_models', {})
    old = json.loads((OUT / 'manifest.json').read_text(encoding='utf-8')) if (OUT / 'manifest.json').exists() else []
    keep = [m for m in old if m['name'] not in {x['name'] for x in manifest}]
    (OUT / 'manifest.json').write_text(json.dumps(keep + manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    print('SA3_COMPLETE', len(manifest))


if __name__ == '__main__':
    asyncio.run(main(set(sys.argv[1:])))
