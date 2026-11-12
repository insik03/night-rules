"""Original BGM and horror stingers, synthesized from scratch (numpy only, no samples).

Every loop is rendered on a circular buffer: oscillator frequencies are snapped to whole
cycles, and filtering/reverb use circular FFT convolution, so loop points are seamless.
"""
from pathlib import Path
import json, wave, hashlib
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Art' / 'Score'; OUT.mkdir(parents=True, exist_ok=True)
SR = 44100


def rng(seed): return np.random.default_rng(seed)


def t_axis(sec): return np.arange(int(SR * sec)) / SR


def snap(f, sec):  # whole cycles over the loop
    return max(1, round(f * sec)) / sec


def band(x, lo, hi, slope=4):
    """Circular smooth band-pass in the frequency domain."""
    F = np.fft.rfft(x, axis=-1); f = np.fft.rfftfreq(x.shape[-1], 1 / SR)
    m = np.ones_like(f)
    if lo: m *= 1 / (1 + (lo / np.maximum(f, 1e-3)) ** (2 * slope))
    if hi: m *= 1 / (1 + (f / hi) ** (2 * slope))
    return np.fft.irfft(F * m, n=x.shape[-1], axis=-1)


def formant(x, centers, q=8):
    F = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); m = np.zeros_like(f)
    for c, g in centers: m += g / (1 + ((f - c) / (c / q)) ** 2)
    return np.fft.irfft(F * m, n=len(x))


def reverb(x, sec, seed, damp=3.0, wet=.35, circular=True):
    """Stereo reverb from decaying filtered noise IRs. x is mono or (2,N)."""
    x = np.atleast_2d(x)
    if x.shape[0] == 1: x = np.vstack([x, x])
    n = x.shape[1]; ir_len = int(SR * sec); out = []
    for ch in range(2):
        r = rng(seed + ch); t = np.arange(ir_len) / SR
        ir = r.standard_normal(ir_len) * np.exp(-t * 6.9 / sec)
        # High frequencies die first.
        lp = np.fft.irfft(np.fft.rfft(ir) / (1 + (np.fft.rfftfreq(ir_len, 1 / SR) / 2500) ** 2), n=ir_len)
        ir = lp * np.exp(-t * damp) + ir * .15 * np.exp(-t * damp * 3)
        ir /= np.sqrt(np.sum(ir ** 2)) + 1e-9
        if circular:
            if ir_len > n: ir = ir[:n]
            irp = np.zeros(n); irp[:len(ir)] = ir
            y = np.fft.irfft(np.fft.rfft(x[ch]) * np.fft.rfft(irp), n=n)
        else:
            m = n + ir_len; y = np.fft.irfft(np.fft.rfft(x[ch], m) * np.fft.rfft(ir, m), n=m)[:n]
        out.append(y)
    return x * (1 - wet) + np.array(out) * wet * 1.8


def place(buf, ev, at, circular=True):
    """Add event ev (mono or stereo) into buf at sample offset, wrapping for loops."""
    ev = np.atleast_2d(ev)
    if ev.shape[0] == 1: ev = np.vstack([ev, ev])
    n = buf.shape[1]; idx = (np.arange(ev.shape[1]) + at)
    if circular: idx %= n
    else: keep = idx < n; idx = idx[keep]; ev = ev[:, keep]
    np.add.at(buf[0], idx, ev[0]); np.add.at(buf[1], idx, ev[1])


def pan(ev, p):  # p in [-1,1]
    return np.vstack([ev * np.sqrt((1 - p) / 2), ev * np.sqrt((1 + p) / 2)])


def env(n, a, d, shape=1.0):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) / d) ** shape


def bell(f0, sec, seed):
    t = t_axis(sec); r = rng(seed); y = np.zeros_like(t)
    for k, (ratio, g, dec) in enumerate([(1, 1, 2.6), (2.76, .5, 1.6), (5.4, .3, .9), (8.93, .18, .5), (13.3, .08, .3)]):
        y += g * np.sin(2 * np.pi * f0 * ratio * (1 + r.uniform(-.002, .002)) * t + r.uniform(0, 6)) * np.exp(-t / dec)
    return y * np.minimum(1, t / .004)


def thump(f0, f1, sec, dec):
    t = t_axis(sec); f = f1 + (f0 - f1) * np.exp(-t * 18)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / dec) * np.minimum(1, t / .002)


def saw(freq, t, harmonics=14):
    y = np.zeros_like(t)
    for h in range(1, harmonics + 1): y += np.sin(2 * np.pi * freq * h * t) / h
    return y


def finish(x, rms_db, peak=.89):
    x = np.atleast_2d(x); x = x - x.mean(axis=1, keepdims=True)
    rms = np.sqrt(np.mean(x ** 2)); x = x * (10 ** (rms_db / 20) / max(rms, 1e-9))
    p = np.max(np.abs(x))
    if p > peak: x = np.tanh(x / p * 1.2) / np.tanh(1.2) * peak  # soft limit, not clip
    return x


def edge_fade(x, a=.004, r=.25):
    n = x.shape[1]; t = np.arange(n) / SR
    return x * np.minimum(1, np.minimum(t / a, (n / SR - t) / r))


# ---------------------------------------------------------------- tracks
def bgm_night():
    sec = 64; t = t_axis(sec); n = len(t); out = np.zeros((2, n)); r = rng(11)
    # Low drone on A with a rubbing minor second; slow swells in whole loop cycles.
    for f, g, ph in [(55, .5, 0), (55.4, .35, 1), (82.4, .22, 2), (58.3, .12, 3), (110, .16, 4), (116.6, .07, 5)]:
        fr = snap(f, sec); sw = .6 + .4 * np.sin(2 * np.pi * snap(1 / 21, sec) * t + ph)
        tone = saw(fr, t, 6) * sw * g
        out += pan(band(tone, 30, 900), np.sin(ph))
    # Building air: breathing band noise.
    air = band(r.standard_normal((2, n)), 180, 1400, 2)
    out += air * (.18 + .12 * np.sin(2 * np.pi * snap(1 / 32, sec) * t)) * .5
    # Faint high whistle that drifts in and out.
    wh = np.sin(2 * np.pi * snap(1760, sec) * t + 3 * np.sin(2 * np.pi * snap(.21, sec) * t))
    out += pan(wh * .018 * np.sin(np.pi * t / sec) ** 6, .4)
    # Distant metal (pipes, a dropped tray) and low building thuds.
    for at, f0, p in [(6.5, 233, -.6), (18.2, 311, .5), (31.0, 207, -.2), (43.7, 277, .7), (55.1, 185, -.8)]:
        place(out, pan(bell(f0, 5, int(at * 10)) * .16, p), int(at * SR))
    for at in [25.3, 50.6]:
        place(out, pan(band(thump(70, 40, 1.2, .25), 20, 300) * .55, r.uniform(-.5, .5)), int(at * SR))
    out = reverb(out, 4.5, 101, damp=1.2, wet=.45)
    return finish(out, -27), True


def bgm_blackout():
    sec = 48; t = t_axis(sec); n = len(t); out = np.zeros((2, n)); r = rng(23)
    for f, g, ph in [(36.7, .6, 0), (37.3, .5, 1.5), (55, .18, 3), (77.8, .12, 2)]:
        fr = snap(f, sec); out += pan(saw(fr, t, 4) * g * (.7 + .3 * np.sin(2 * np.pi * snap(1 / 16, sec) * t + ph)), np.sin(ph) * .5)
    out += band(r.standard_normal((2, n)), 25, 160, 2) * .9
    # Something moving in the walls: irregular low knocks.
    for at in [4.1, 4.5, 13.8, 22.0, 22.3, 22.6, 35.2, 41.9]:
        place(out, pan(band(thump(120, 55, .6, .07), 30, 900) * .7, r.uniform(-.9, .9)), int(at * SR))
    # A far-off moan: glide through a vowel filter.
    mt = t_axis(5.5); glide = 140 * (1 + .25 * np.sin(np.pi * mt / 5.5)) * (1 + .01 * np.sin(2 * np.pi * 5 * mt))
    src = np.sign(np.sin(2 * np.pi * np.cumsum(glide) / SR)) * .5 + r.standard_normal(len(mt)) * .2
    moan = formant(src, [(500, 1), (900, .5), (2400, .2)], 6) * np.sin(np.pi * mt / 5.5) ** 2
    place(out, pan(moan * .05, -.7), int(28 * SR))
    out = reverb(out, 5.5, 202, damp=.9, wet=.55)
    return finish(out, -25), True


def bgm_chase():
    bpm = 120; beat = 60 / bpm; sec = 48 * beat; t = t_axis(sec); n = len(t); out = np.zeros((2, n)); r = rng(37)
    # Heartbeat kick: lub-dub on every beat, extra push every 4th bar.
    for b in range(48):
        place(out, band(thump(95, 42, .45, .11), 20, 600) * .9, int(b * beat * SR))
        place(out, band(thump(80, 40, .35, .08), 20, 500) * .5, int((b * beat + .16) * SR))
    # Dissonant string cluster, 16th-note tremolo, filter opening over 4 bars.
    cluster = np.zeros(n)
    for f in [82.4, 87.3, 116.5, 123.5, 164.8, 174.6]:
        cluster += saw(snap(f, sec) * 1, t, 10) * (1 + .3 * np.sin(2 * np.pi * snap(5.3, sec) * t))
    trem = .55 + .45 * np.sign(np.sin(2 * np.pi * snap(1 / (beat / 4), sec) * t))
    swell = .35 + .65 * (np.sin(np.pi * ((t / (16 * beat)) % 1)) ** 2)
    lo_part = band(cluster, 60, 700); hi_part = band(cluster, 700, 3200)
    strings = (lo_part + hi_part * swell) * trem * .14
    out += np.vstack([strings, np.roll(strings, int(.011 * SR))])
    # Metallic hits on the off-beats of bar 2 and 4 of each phrase.
    for bar in range(12):
        if bar % 2 == 1:
            for k in [2.5, 3.5]:
                place(out, pan(bell(r.choice([466, 494, 523]), 1.2, bar * 7 + int(k)) * .2, r.uniform(-.8, .8)), int((bar * 4 + k) * beat * SR))
    # Screech: rising scraped tone every 4 bars.
    for ph in range(3):
        st = t_axis(3 * beat); fr = 1800 + 1400 * (st / st[-1]) ** 2
        scr = (np.sin(2 * np.pi * np.cumsum(fr) / SR) + .4 * r.standard_normal(len(st))) * np.sin(np.pi * st / st[-1]) ** 2
        place(out, pan(band(scr, 1200, 6000) * .05, (-1) ** ph * .6), int(((ph * 16) + 13) * beat * SR))
    # Ticking 16ths.
    hat = band(r.standard_normal(int(.03 * SR)), 5000, 12000) * env(int(.03 * SR), .001, .008)
    for s in range(48 * 4):
        if s % 4: place(out, pan(hat * (.08 if s % 2 else .05), .3 if s % 3 else -.3), int(s * beat / 4 * SR))
    out = reverb(out, 1.8, 303, damp=2.5, wet=.25)
    return finish(out, -17), True


def sting_chase():
    sec = 5; t = t_axis(sec); n = len(t); out = np.zeros((2, n)); r = rng(41)
    pre = .3; s0 = int(pre * SR)
    # Reverse swell into the hit.
    sw = band(r.standard_normal(s0), 800, 9000) * (np.arange(s0) / s0) ** 3 * .5
    place(out, sw, 0, False)
    hit = np.zeros(n - s0); ht = t_axis((n - s0) / SR)
    for f in [130.8, 138.6, 185.0, 196.0, 261.6, 277.2]:
        hit += saw(f, ht, 16) * np.exp(-ht / 1.4)
    hit = band(hit, 80, 5000) * .25 * np.minimum(1, ht / .006)
    hit += band(r.standard_normal(len(ht)), 200, 7000) * np.exp(-ht / .18) * .5
    hit += band(thump(90, 28, (n - s0) / SR, .9), 15, 300) * 1.2
    place(out, np.vstack([hit, np.roll(hit, 300)]), s0, False)
    out = reverb(out, 3.5, 404, damp=1.4, wet=.4, circular=False)
    return finish(edge_fade(out, .002, .8), -14, .95), False


def heartbeat():
    sec = 1.5; out = np.zeros((2, int(SR * sec)))  # two beats at 80 bpm
    for b in range(2):
        at = int(b * .75 * SR)
        place(out, band(thump(70, 38, .3, .07), 20, 200) * 1.0, at)
        place(out, band(thump(60, 35, .3, .06), 20, 180) * .6, at + int(.2 * SR))
    return finish(out, -16, .95), True


def ghost_breath():
    sec = 4.8; t = t_axis(sec); n = len(t); r = rng(53); out = np.zeros(n)
    noise = r.standard_normal(n)
    inhale = (t < 1.5) * np.sin(np.pi * np.clip(t / 1.5, 0, 1)) ** 1.5
    exhale = ((t > 1.9) & (t < 4.2)) * np.sin(np.pi * np.clip((t - 1.9) / 2.3, 0, 1)) ** .8
    out += formant(noise, [(1800, 1), (3200, .6), (700, .3)], 5) * inhale * .5
    out += formant(noise, [(600, 1), (1300, .7), (2600, .35)], 4) * exhale * .9
    # Vocal fry / rattle inside the exhale.
    fry_f = 48 + 10 * np.sin(2 * np.pi * 1.7 * t) + r.standard_normal(n).cumsum() * .002
    pulse = (np.sin(2 * np.pi * np.cumsum(fry_f) / SR) > .97).astype(float)
    out += formant(pulse, [(450, 1), (1100, .6), (2500, .3)], 6) * exhale * 2.2
    # Wet crackles.
    for _ in range(25):
        at = int(r.uniform(1.9, 4.0) * SR); c = band(r.standard_normal(200), 2000, 8000) * env(200, .0005, .002)
        out[at:at + 200] += c * .6
    st = band(np.vstack([out, np.roll(out, 90)]), 80, 4500, 2)  # throat, not hiss
    return finish(st, -18), True


def _rasp(n, r, f0, jitter):
    """Irregular glottal pulses: no smooth pitch line, so it never reads as a siren."""
    out = np.zeros(n); pos = 0
    while pos < n:
        out[pos] = 1 + r.uniform(-.4, .4)
        pos += max(8, int(SR / (f0 * (1 + r.uniform(-jitter, jitter)))))
    return out


def ghost_shriek():
    sec = 1.6; t = t_axis(sec); n = len(t); r = rng(61)
    voiced = formant(_rasp(n, r, 310, .35), [(850, 1), (1500, .7), (2900, .5)], 5) * 3
    breath = formant(r.standard_normal(n), [(1100, 1), (2400, .8), (3800, .4)], 3)
    v = voiced * .6 + breath
    shape = np.minimum(1, t / .015) * np.where(t < .95, 1, np.exp(-(t - .95) / .07))  # choked off
    v = np.tanh(v * 2.2) * shape
    st = reverb(band(np.vstack([v, np.roll(v, 180)]), 180, 6500, 2), 1.6, 606, damp=2.2, wet=.22, circular=False)
    return finish(edge_fade(st, .002, .2), -14, .95), False


def ghost_catch():
    """Right in your ear: a sharp inhale, then a wet guttural roar and a body hit."""
    sec = 2.2; t = t_axis(sec); n = len(t); r = rng(67)
    inhale = formant(r.standard_normal(n), [(1700, 1), (3000, .5)], 4) * ((t < .35) * np.sin(np.pi * np.clip(t / .35, 0, 1)) ** 2) * .5
    roar_t = np.clip(t - .38, 0, None)
    roar_env = (t > .38) * np.minimum(1, roar_t / .03) * np.exp(-roar_t / .55)
    fry = formant(_rasp(n, r, 46, .5), [(420, 1), (950, .8), (2200, .4)], 4) * 6
    growl = formant(r.standard_normal(n), [(500, 1), (1200, .6)], 3) * .7
    roar = np.tanh((fry + growl) * 2.5) * roar_env
    hit = np.concatenate([np.zeros(int(.38 * SR)), band(thump(85, 30, sec - .38, .35), 15, 250)[:n - int(.38 * SR)]]) * 1.4
    v = inhale + roar + hit
    st = reverb(np.vstack([v, np.roll(v, 60)]), 1.2, 707, damp=3, wet=.15, circular=False)
    return finish(edge_fade(st, .002, .3), -13, .95), False


def _laugh(sec, syllables, f0s, seed, double):
    """Voiced 'heh' bursts with a breathy onset; each syllable holds one jittered pitch."""
    t = t_axis(sec); n = len(t); r = rng(seed); out = np.zeros(n)
    for (at, dur), f0 in zip(syllables, f0s):
        m = int(dur * SR); s = int(at * SR); tt = np.arange(m) / SR
        e = np.minimum(1, tt / .012) * np.exp(-tt / (dur * .45))
        voice = formant(_rasp(m, r, f0, .12), [(620, 1), (1750, .7), (2700, .4)], 6) * 3
        if double:  # a second, lower throat a beat behind: one mouth, two voices
            voice += np.roll(formant(_rasp(m, r, f0 * .5, .2), [(480, 1), (1200, .5)], 5) * 2.4, int(.018 * SR))
        h = formant(r.standard_normal(m), [(1500, 1), (2900, .6)], 3) * np.exp(-tt / .03) * .6
        seg = np.tanh((voice + h) * 1.6) * e
        out[s:s + m] += seg[:max(0, min(m, n - s))]
    # Wheezing in-breath after the laugh.
    w0 = syllables[-1][0] + syllables[-1][1] + .08; wt = t - w0
    wheeze = formant(r.standard_normal(n), [(2300, 1), (3600, .5)], 8) * ((wt > 0) & (wt < .7)) * np.sin(np.pi * np.clip(wt / .7, 0, 1)) * .35
    st = reverb(np.vstack([out + wheeze, np.roll(out + wheeze, 140)]), 1.4, seed + 900, damp=2.4, wet=.2, circular=False)
    return finish(edge_fade(st, .002, .25), -17, .95), False


def ghost_laugh():
    syl = [(.0, .15), (.2, .13), (.37, .14), (.55, .12), (.72, .16), (.97, .2)]
    return _laugh(2.0, syl, [232, 228, 236, 221, 214, 190], 81, False)


def ghost_chuckle():
    syl = [(.0, .2), (.34, .18), (.66, .22), (1.05, .28)]
    return _laugh(2.3, syl, [128, 124, 131, 112], 83, True)

def tinnitus():
    """Muffled aftermath of the blow: low ringing in the skull, no alarm-like tone."""
    sec = 6; t = t_axis(sec); r = rng(71)
    ring = (np.sin(2 * np.pi * 2900 * t) + .4 * np.sin(2 * np.pi * 3900 * t)) * np.minimum(1, t / .4) * np.exp(-t / 2.2) * .05
    rumble = band(r.standard_normal(len(t)), 20, 120) * np.exp(-t / 2.0) * 2
    st = np.vstack([ring + rumble, ring * .9 + np.roll(rumble, 400)])
    return finish(edge_fade(st, .002, 1.0), -24, .9), False

TRACKS = {'bgm_night': bgm_night, 'bgm_blackout': bgm_blackout, 'bgm_chase': bgm_chase,
          'sting_chase': sting_chase, 'heartbeat': heartbeat, 'ghost_breath': ghost_breath,
          'ghost_shriek': ghost_shriek, 'ghost_catch': ghost_catch, 'ghost_laugh': ghost_laugh, 'ghost_chuckle': ghost_chuckle, 'tinnitus': tinnitus}

if __name__ == '__main__':
    manifest = []
    for name, fn in TRACKS.items():
        x, loop = fn()
        pcm = (np.clip(x, -1, 1) * 32767).astype('<i2').T.copy()
        with wave.open(str(OUT / (name + '.wav')), 'wb') as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
        seam = float(np.max(np.abs(x[:, 0] - x[:, -1]))) if loop else None
        manifest.append({'name': name, 'loop': loop, 'seconds': round(x.shape[1] / SR, 3),
                         'peak': round(float(np.max(np.abs(x))), 3), 'rms_dbfs': round(float(20 * np.log10(np.sqrt(np.mean(x ** 2)))), 1),
                         'loop_seam_jump': None if seam is None else round(seam, 4),
                         'sha256': hashlib.sha256((OUT / (name + '.wav')).read_bytes()).hexdigest(),
                         'source': 'original synthesis, tools/create_score.py; no samples or recordings'})
        print('SCORE', name, manifest[-1]['seconds'], manifest[-1]['rms_dbfs'], manifest[-1]['loop_seam_jump'], flush=True)
    # Loops must not click: the wrap-around step should look like any neighbouring step.
    for row in manifest:
        assert row['peak'] <= .96, row
        if row['loop']: assert row['loop_seam_jump'] < .05, row
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print('SCORE_COMPLETE', len(manifest))
