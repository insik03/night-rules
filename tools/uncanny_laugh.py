"""Make a laugh sound wrong: under it, the same laugh an octave lower and slower, slightly late,
plus faint crackle on the loud parts. Art/ScoreSA3/<name>_<g|h>.wav -> <name>_<i|j>.wav (numpy only)."""
import sys, wave
from pathlib import Path
import numpy as np

D = Path(__file__).resolve().parents[1] / 'Art' / 'ScoreSA3'


def read(p):
    with wave.open(str(p)) as w:
        sr, ch, sw, n = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes(); raw = w.readframes(n)
    if sw == 3:  # 24-bit PCM
        b = np.frombuffer(raw, np.uint8).reshape(-1, 3); x = (b[:, 0].astype(np.int32) | b[:, 1].astype(np.int32) << 8 | b[:, 2].astype(np.int8).astype(np.int32) << 16) / 2 ** 23
    else: x = np.frombuffer(raw, '<i2') / 32768
    return x.reshape(-1, ch).mean(axis=1), sr


def uncanny(x, sr, seed):
    r = np.random.default_rng(seed)
    low = np.interp(np.arange(0, len(x), .5), np.arange(len(x)), x)  # octave down, twice as slow
    lag = int(.07 * sr); out = np.zeros(max(len(x), len(low) + lag))
    out[:len(x)] += x; out[lag:lag + len(low)] += .55 * low
    envl = np.convolve(np.abs(out), np.ones(400) / 400, 'same')
    out += (r.random(len(out)) < .004) * r.uniform(-1, 1, len(out)) * envl * 3  # crackle where it is loud
    fade = np.minimum(1, (len(out) - np.arange(len(out))) / (.3 * sr)); out *= fade
    return out / max(1e-6, np.abs(out).max()) * .89


if __name__ == '__main__':
    for name in ('ghost_laugh', 'ghost_chuckle'):
        for src, dst in (('g', 'i'), ('h', 'j')):
            x, sr = read(D / f'{name}_{src}.wav'); y = uncanny(x, sr, len(name) * 10 + ord(src))
            with wave.open(str(D / f'{name}_{dst}.wav'), 'wb') as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((y * 32767).astype('<i2').tobytes())
            assert np.abs(y).max() <= .9
            print('UNCANNY', f'{name}_{dst}.wav', round(len(y) / sr, 2))
