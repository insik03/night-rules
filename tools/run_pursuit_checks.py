"""Run targeted packaged-game regressions, keeping helper consoles hidden."""
from pathlib import Path
import subprocess,json
R=Path(__file__).resolve().parents[1];E=R/'Builds/Windows/NightRulesPrototype/Binaries/Win64/NightRulesPrototype.exe'
report=[]
for flag,marker in [('NRPursuitTest','NR_PURSUIT_COMPLETE'),('NRFeedbackTest','NR_FEEDBACK_COMPLETE'),('NRFinaleTest','NR_FINALE_COMPLETE'),('NRChaseTest','NR_CHASE_COMPLETE')]:
    log=R/'tools/output'/(flag+'-chair.log')
    p=subprocess.run([str(E),'-'+flag,'-windowed','-ResX=1280','-ResY=720','-unattended','-nosplash','-abslog='+str(log)],cwd=E.parent,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW,timeout=75)
    text=log.read_text(encoding='utf-8',errors='replace') if log.exists() else ''
    rows=[s for s in text.splitlines() if marker in s]
    ok=p.returncode==0 and bool(rows) and 'failures=0' in rows[-1]
    print(flag,'PASS' if ok else 'FAIL',rows[-1:] if rows else 'no completion marker',flush=True)
    report.append({'test':flag,'passed':ok,'exit_code':p.returncode,'result':rows[-1:]})
    if not ok:break
(R/'tools/output/pursuit-regression.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
raise SystemExit(0 if all(x['passed'] for x in report) and len(report)==4 else 1)
