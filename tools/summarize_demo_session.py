"""Read real session timing; never infer play length from scripted event-clock tests."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument('log',type=Path); args=p.parse_args()
sessions=[]; current=[]
for line in args.log.read_text(encoding='utf-8-sig').splitlines():
    try:row=json.loads(line)
    except ValueError:continue
    if row.get('event')=='session' and row.get('detail')=='start':
        if current:sessions.append(current)
        current=[]
    current.append(row)
if current:sessions.append(current)
for index,rows in enumerate(sessions):
    start=rows[0].get('real_seconds'); finish=next((r for r in reversed(rows) if r.get('event')=='demo_end'),None)
    seconds=None if start is None or finish is None or 'real_seconds' not in finish else finish['real_seconds']-start
    known_route=any(r.get('event')=='test' and r.get('detail')=='known_route_walk_start' for r in rows)
    print(json.dumps({'session':index,'run_type':'automated_known_route' if known_route else 'unclassified','finished':finish is not None,'real_minutes':None if seconds is None else round(seconds/60,2),'deaths':sum(r.get('event')=='death' for r in rows),'scares':sorted({r['detail'] for r in rows if r.get('event')=='scare'}),'milestones':[r['detail'] for r in rows if r.get('event')=='demo'],'note':'Known-route automation is not blind first-play timing. Unclassified sessions may include automated state tests.'},ensure_ascii=False))
