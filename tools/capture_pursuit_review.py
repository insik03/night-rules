"""Record only the game window after the dedicated presentation test starts."""
from pathlib import Path
import shutil,subprocess,time
R=Path(__file__).resolve().parents[1]
log=R/'Builds/Windows/NightRulesPrototype/Saved/Logs/PursuitPresentation.log'
out=R/'docs/showcase/media/source/pursuit-review-raw.mp4'
start=time.time()
for _ in range(240):
    if log.exists() and log.stat().st_mtime>=start and 'Engine is initialized' in log.read_text(encoding='utf-8',errors='replace'):break
    time.sleep(.25)
else:raise RuntimeError('Fresh pursuit test did not start')
graph='gfxcapture=window_exe=NightRulesPrototype.exe:capture_cursor=0:capture_border=0:max_framerate=30,hwdownload,format=bgra,scale=1600:900,format=yuv420p[v]'
p=subprocess.run([shutil.which('ffmpeg'),'-y','-hide_banner','-loglevel','warning','-filter_complex',graph,'-map','[v]','-t','6.6','-r','30','-c:v','libx264','-preset','fast','-crf','18',str(out)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=20)
print('PURSUIT_CAPTURE',p.returncode,out.stat().st_size if out.exists() else 0)
if p.returncode:print(p.stderr.decode(errors='replace'));raise SystemExit(p.returncode)
