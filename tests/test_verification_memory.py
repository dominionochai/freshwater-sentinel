from app.memory import AlertMemory
from app.verification import grade_alerts

def test_injected_follow_up_dates_are_reproducible():
    r=grade_alerts([{'alert_id':'a','node_id':'w','alert_date':'2024-01-01'}],[{'node_id':'w','date':'2024-01-08','cases':2}],4)
    assert r['precision']==1.0 and r['alerts'][0]['grade']=='SUPPORTED'
def test_memory_feedback(tmp_path):
    m=AlertMemory(tmp_path/'history.json');m.record_alert({'alert_id':'a'});assert m.add_feedback('a',{'useful':True});assert m.history()[0]['feedback'][0]['useful'] is True
