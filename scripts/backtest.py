from __future__ import annotations
import argparse, json
from pathlib import Path
from app.verification import grade_alerts
p=argparse.ArgumentParser(description='Grade injected historical alerts against injected processed cases; no WHO downloads.')
p.add_argument('--alerts',required=True);p.add_argument('--cases',required=True);p.add_argument('--weeks',type=int,default=4);p.add_argument('--output')
a=p.parse_args(); result=grade_alerts(json.loads(Path(a.alerts).read_text()),json.loads(Path(a.cases).read_text()),a.weeks)
out=json.dumps(result,indent=2)+'\n'; Path(a.output).write_text(out) if a.output else print(out)
