"""Add approaching breaths and stop the preview before execution; retain runtime death."""
from pathlib import Path
import json
import shutil
import subprocess
import zipfile
import numpy as np
from design_showcase_sound import asset, normalize, edges, write_wav, RATE

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'docs/showcase/media'
RAW = DEST / 'source'
FF = shutil.which('ffmpeg')
PROBE = shutil.which('ffprobe')
CUT = 2.6  # 78 frames; execution starts approximately 2.86s into the recording.


def run(args):
    return subprocess.run(args, check=True, capture_output=True,
                          creationflags=subprocess.CREATE_NO_WINDOW)


def decode(path):
    data = run([FF, '-v', 'error', '-i', str(path), '-vn', '-ac', '2',
                '-ar', str(RATE), '-f', 'f32le', '-']).stdout
    return np.frombuffer(data, dtype='<f4').reshape(-1, 2).astype(float)


def breathing():
    result = np.zeros((round(CUT * RATE), 2))
    # Separate gasps, retaining the source's throat texture and a short pause
    # between breaths. Pan stays close to centre as the creature approaches.
    for at, duration, speed, rms, pan in [
        (.10, .50, 1.30, .040, -.15),
        (.77, .64, .94, .065, .10),
        (1.53, .48, 1.20, .085, -.05),
        (2.09, .51, .86, .115, 0),
    ]:
        source = asset('breath_near', speed=speed, low=110, high=3600)
        count = round(duration * RATE)
        # Locate an audible portion, rather than stretching the asset's silence.
        energy = np.convolve(source * source, np.ones(2400) / 2400, mode='same')
        start = max(0, min(int(np.argmax(energy)) - count // 2, len(source) - count))
        sound = source[start:start + count]
        sound = edges(normalize(sound, rms), .055, .07)
        position = round(at * RATE)
        length = min(len(sound), len(result) - position)
        angle = (pan + 1) * np.pi / 4
        result[position:position + length] += sound[:length, None] * np.array([np.cos(angle), np.sin(angle)])
    return result


def finish_audio(path, mix):
    mix -= mix.mean(axis=0)
    peak = float(np.abs(mix).max())
    if peak > .75:
        mix *= .75 / peak
    write_wav(path, mix)


def validate(path, frames, seconds):
    metadata = json.loads(run([PROBE, '-v', 'error', '-show_streams',
                               '-show_format', '-of', 'json', str(path)]).stdout)
    video = next(s for s in metadata['streams'] if s['codec_type'] == 'video')
    assert int(video['nb_frames']) == frames, metadata
    assert abs(float(metadata['format']['duration']) - seconds) < .05
    decoded = decode(path)
    peak = float(np.abs(decoded).max())
    assert .01 < peak < .97, peak
    return {'file': path.name, 'frames': frames, 'duration': seconds,
            'encoded_sample_peak': peak, 'breathing': 'post-production project breath SFX',
            'execution_included': False}


def main():
    sync = json.loads((DEST / 'chair-preview-validation.json').read_text(encoding='utf-8'))
    assert CUT < sync['black_cut_seconds'] - 1.94
    audio = decode(ROOT / 'Builds/Windows/NightRulesPrototype/Saved/Verification/chair_chase_audio.wav')
    offset = round(sync['audio_trim_seconds'] * RATE)
    length = round(CUT * RATE)
    mix = audio[offset:offset + length].copy() + breathing()
    mix[-240:] *= np.linspace(1, 0, 240)[:, None]
    short_audio = RAW / 'chase-breath-v2.wav'
    finish_audio(short_audio, mix)
    short = DEST / '의자_추격_숨소리_v2.mp4'
    run([FF, '-y', '-v', 'error', '-i', str(RAW / 'ghost-live.mp4'),
         '-i', str(short_audio), '-map', '0:v:0', '-map', '1:a:0',
         '-t', str(CUT), '-c:v', 'libx264', '-crf', '18', '-preset', 'medium',
         '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '256k',
         '-movflags', '+faststart', str(short)])
    reports = [validate(short, 78, CUT)]

    # The existing showcase uses only 2.4s of chase footage, before execution.
    # Keep that edit and its full sound design; make the approaching breath clearer.
    old = DEST / '야간수칙_쇼케이스_사운드_v3.mp4'
    long_mix = decode(old)[:30 * RATE].copy()
    voice = breathing()[:round(2.4 * RATE)]
    voice[-480:] *= np.linspace(1, 0, 480)[:, None]
    long_mix[24 * RATE:24 * RATE + len(voice)] += voice * .9
    full_audio = RAW / 'showcase-breath-v4.wav'
    finish_audio(full_audio, long_mix)
    full = DEST / '야간수칙_쇼케이스_사운드_v4.mp4'
    run([FF, '-y', '-v', 'error', '-i', str(old), '-i', str(full_audio),
         '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'aac',
         '-b:a', '256k', '-t', '30', '-movflags', '+faststart', str(full)])
    reports.append(validate(full, 900, 30))
    (DEST / 'breath-cut-validation.json').write_text(
        json.dumps(reports, ensure_ascii=False, indent=2), encoding='utf-8')
    shutil.copy2(full, DEST / '야간수칙_쇼케이스_30초.mp4')
    with zipfile.ZipFile(DEST / '야간수칙_제출미디어.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in ('01_관리실_CCTV.png', '02_UV_손바닥흔적.png', '야간수칙_쇼케이스_30초.mp4'):
            archive.write(DEST / name, name)
    page = DEST / 'index.html'
    page.write_text(page.read_text(encoding='utf-8').replace(
        '야간수칙_쇼케이스_사운드_v3.mp4', full.name), encoding='utf-8')
    print(json.dumps(reports, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
