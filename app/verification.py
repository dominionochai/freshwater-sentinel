from __future__ import annotations
from datetime import date, datetime, timedelta
def _date(v):
    if isinstance(v,datetime):return v.date()
    if isinstance(v,date):return v
    try:return date.fromisoformat(str(v)[:10]) if v is not None else None
    except ValueError:return None
def grade_alerts(alerts, cholera_cases, weeks=4, date_field='date'):
    cases=[x for x in cholera_cases if _date(x.get(date_field))]; out=[]
    for alert in alerts:
        start=_date(alert.get('alert_date',alert.get(date_field)))
        if start is None:out.append({**alert,'grade':'UNVERIFIABLE','reason':'missing or invalid alert date'});continue
        end=start+timedelta(weeks=weeks); node=str(alert.get('node_id',alert.get('waterpoint_id','')))
        matches=[x for x in cases if start<=_date(x.get(date_field))<=end and (not node or str(x.get('node_id',x.get('waterpoint_id','')))==node)]
        out.append({**alert,'grade':'SUPPORTED' if matches else 'NOT_SUPPORTED','follow_up_cases':len(matches),'follow_up_end':end.isoformat()})
    ver=sum(x['grade']!='UNVERIFIABLE' for x in out); sup=sum(x['grade']=='SUPPORTED' for x in out)
    return {'weeks':weeks,'total_alerts':len(out),'supported':sup,'verifiable':ver,'precision':sup/ver if ver else None,'alerts':out,'data_source':'injected cholera_cases'}
