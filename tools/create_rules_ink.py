"""Write-on data for the red rule note (run after create_rules_display.py).

T_RulesInk.png       RGBA: red ink colour, alpha = ink coverage (Reply page minus plain page).
T_RulesInkOrder.png  L: when each ink pixel appears, 0..1, matching ANRGameMode::RuleInk.
The denial (dash first, then left to right) fills 0..0.53; the reply fills 0.55..0.98.
A small top-to-bottom term per column gives a pen-stroke edge instead of a straight wipe.
Also writes pen_scratch.wav (original synthesised sound, no external source).
"""
from pathlib import Path
import numpy as np, wave
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / 'Art/Generated'
REPLY_START = .55   # keep in sync with ANRGameMode::ReplyStart

page = np.asarray(Image.open(GEN / 'T_RulesPage.png').convert('RGB')).astype(int)
red = np.asarray(Image.open(GEN / 'T_RulesRed.png').convert('RGB')).astype(int)
reply = np.asarray(Image.open(GEN / 'T_RulesReply.png').convert('RGB')).astype(int)
ink = np.abs(reply - page).sum(2) > 24
denial = (np.abs(red - page).sum(2) > 24) & ink
answer = ink & ~denial

order = np.ones(ink.shape, np.float32)
rng = np.random.default_rng(2)
def fill(mask, lo, hi):
    ys, xs = np.nonzero(mask)
    if not len(xs): return
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    t = (xs - x0) / max(1, x1 - x0) + .02 * (ys - y0) / max(1, y1 - y0)
    # Per 18 px "character" jitter so the pen hesitates instead of sliding evenly.
    t += rng.uniform(-.008, .008, (x1 // 18 + 2))[xs // 18]
    t = (t - t.min()) / (t.max() - t.min())
    order[ys, xs] = lo + t * (hi - lo)
fill(denial, 0, REPLY_START - .02)
fill(answer, REPLY_START, .98)

coverage = np.clip((np.abs(reply - page).sum(2) - 24) / 120, 0, 1)
rgba = np.zeros(ink.shape + (4,), np.uint8)
rgba[..., :3] = reply.clip(0, 255)
rgba[..., 3] = (coverage * 255).astype(np.uint8)
Image.fromarray(rgba, 'RGBA').save(GEN / 'T_RulesInk.png')
Image.fromarray((order * 255).astype(np.uint8), 'L').save(GEN / 'T_RulesInkOrder.png')

# Pen on paper: short band-limited noise strokes with soft attacks.
rate = 44100; out = np.zeros(int(rate * 1.4), np.float32)
t = .05
for _ in range(9):
    n = int(rate * rng.uniform(.05, .14)); s = int(rate * t)
    noise = rng.normal(0, 1, n)
    spec = np.fft.rfft(noise); f = np.fft.rfftfreq(n, 1 / rate)
    spec *= np.exp(-((f - 3800) / 2200) ** 2)
    stroke = np.fft.irfft(spec, n) * np.sin(np.linspace(0, np.pi, n)) ** .6
    out[s:s + n] += stroke[: len(out) - s]
    t += rng.uniform(.09, .18)
out *= .5 / np.abs(out).max()
with wave.open(str(GEN / 'pen_scratch.wav'), 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
    w.writeframes((out * 32767).astype('<i2').tobytes())
print('RULES_INK_COMPLETE', int(denial.sum()), int(answer.sum()))
