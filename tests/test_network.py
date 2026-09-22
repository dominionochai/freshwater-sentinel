from app.network import analyze_water_network, build_water_network
from app.network_scoring import FIELD_SAMPLE_REQUIRED, SAFE, UNSAFE, assess_safety

def test_graph_is_deterministic_and_propagates():
    rows=[{'node_id':'b','latitude':0,'longitude':0.001},{'node_id':'a','latitude':0,'longitude':0,'safety_status':'unsafe'}]
    n=build_water_network(rows,1); x=analyze_water_network(n,['a']); assert n.network_id==build_water_network(rows,1).network_id
    assert any(e.node_id=='b' and e.state==FIELD_SAMPLE_REQUIRED for e in x.propagation)
def test_lab_safety_fails_closed():
    assert assess_safety({'turbidity_ntu':1})[0]==FIELD_SAMPLE_REQUIRED
    assert assess_safety({'turbidity_ntu':1,'faecal_coli_count':0,'safety_status':'safe'})[0]==SAFE
    assert assess_safety({'turbidity_ntu':1,'faecal_coli_count':2})[0]==UNSAFE
def test_alternatives_require_supported_safe_evidence():
    n=build_water_network([{'node_id':'a','latitude':0,'longitude':0,'safety_status':'unsafe'},{'node_id':'b','latitude':0,'longitude':.001,'safety_status':'safe','turbidity_ntu':1,'faecal_coli_count':0}],1)
    assert [a.node_id for a in analyze_water_network(n,['a']).alternatives]==['b']
