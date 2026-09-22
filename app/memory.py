from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
class AlertMemory:
    def __init__(self,path='data/alerts_history.json'):self.path=Path(path)
    def history(self):
        try:
            x=json.loads(self.path.read_text(encoding='utf-8')); return x if isinstance(x,list) else []
        except (OSError,json.JSONDecodeError):return []
    def _write(self,x):
        self.path.parent.mkdir(parents=True,exist_ok=True); self.path.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    def record_alert(self,alert):
        e={'recorded_at':datetime.now(timezone.utc).isoformat(),'alert':alert,'feedback':[]}; x=self.history(); x.append(e); self._write(x); return e
    def add_feedback(self,alert_id,feedback):
        x=self.history()
        for e in x:
            a=e.get('alert',{})
            if str(a.get('alert_id',a.get('node_id','')))==str(alert_id):e.setdefault('feedback',[]).append({'recorded_at':datetime.now(timezone.utc).isoformat(),**feedback}); self._write(x); return True
        return False
