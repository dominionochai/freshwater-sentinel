from __future__ import annotations
import hashlib, math
from collections import defaultdict, deque
from typing import Any, Iterable
from app.network_models import NetworkNode, NetworkEdge, WaterNetwork, PropagationEvent, AlternativeWaterPoint, NetworkAnalysis
from app.network_scoring import FIELD_SAMPLE_REQUIRED, SAFE, UNSAFE, assess_safety, base_risk, propagate_score, risk_label
from app.network_sources import normalize_record
def haversine_km(a,b,c,d):
    r=6371.0088; p=math.radians(a); q=math.radians(b); dp=math.radians(c-a); dl=math.radians(d-b); z=math.sin(dp/2)**2+math.cos(p)*math.cos(math.radians(c))*math.sin(dl/2)**2
    return 2*r*math.asin(math.sqrt(z))
def _nid(nodes, edges):
    s='|'.join(f'{x.node_id}:{x.latitude:.6f}:{x.longitude:.6f}' for x in nodes)+'|'+'|'.join(f'{x.upstream}>{x.downstream}' for x in edges)
    return 'net-'+hashlib.sha256(s.encode()).hexdigest()[:16]
def build_water_network(records: Iterable[dict[str, Any]], max_distance_km=10.):
    rows=[normalize_record(x) for x in records]; nodes=[]; raw={}
    for r in rows:
        i=str(r.get('node_id','')).strip(); lat,lon=r.get('latitude'),r.get('longitude')
        if not i or lat is None or lon is None or i in raw: continue
        state,_=assess_safety(r); raw[i]=r; nodes.append(NetworkNode(i,str(r.get('name') or i),float(lat),float(lon),str(r.get('source','injected')),state,r.get('community'),r))
    nodes.sort(key=lambda x:x.node_id); ids={x.node_id for x in nodes}; edges=[]
    for n in nodes:
        for key in ('downstream','connected_to'):
            vals=raw[n.node_id].get(key,[]); vals=[vals] if isinstance(vals,str) else vals if isinstance(vals,list) else []
            for target in sorted(str(x) for x in vals if str(x) in ids and str(x)!=n.node_id):
                t=next(x for x in nodes if x.node_id==target); edges.append(NetworkEdge(n.node_id,target,haversine_km(n.latitude,n.longitude,t.latitude,t.longitude),key))
        up=raw[n.node_id].get('upstream')
        if up is not None and str(up) in ids and str(up)!=n.node_id:
            t=next(x for x in nodes if x.node_id==str(up)); edges.append(NetworkEdge(t.node_id,n.node_id,haversine_km(t.latitude,t.longitude,n.latitude,n.longitude),'upstream'))
    if not edges:
        for a in nodes:
            for b in nodes:
                if a.node_id < b.node_id:
                    d=haversine_km(a.latitude,a.longitude,b.latitude,b.longitude)
                    if d<=max_distance_km: edges.extend((NetworkEdge(a.node_id,b.node_id,d),NetworkEdge(b.node_id,a.node_id,d)))
    edges=sorted({(e.upstream,e.downstream,e.relation):e for e in edges}.values(), key=lambda e:(e.upstream,e.downstream,e.relation))
    return WaterNetwork(_nid(nodes,edges),tuple(nodes),tuple(edges),tuple({'source':n.source,'node_id':n.node_id} for n in nodes))
def analyze_water_network(network, alert_node_ids=(), max_hops=3, decay=.75, alternatives_limit=5):
    ns={n.node_id:n for n in network.nodes}; adj=defaultdict(list)
    for e in network.edges: adj[e.upstream].append(e)
    starts={x for x in alert_node_ids if x in ns} or {n.node_id for n in network.nodes if n.safety_state==UNSAFE}; best={}; q=deque((x,0,x,base_risk(ns[x].safety_state)) for x in sorted(starts))
    while q:
        cur,h,source,score=q.popleft()
        if cur in best and best[cur][0]>=score and best[cur][1]<=h: continue
        best[cur]=(score,h,source)
        if h<max_hops:
            for e in sorted(adj[cur],key=lambda x:x.downstream): q.append((e.downstream,h+1,source,propagate_score(score,1,decay)))
    uncertain=any(n.safety_state==FIELD_SAMPLE_REQUIRED for n in network.nodes); events=[]
    for n in sorted(network.nodes,key=lambda x:x.node_id):
        if n.node_id not in best: continue
        score,h,source=best[n.node_id]; state=n.safety_state if n.safety_state==UNSAFE else FIELD_SAMPLE_REQUIRED if score>=.34 else n.safety_state
        events.append(PropagationEvent(n.node_id,None if h==0 else source,h,round(score,6),risk_label(score,state),FIELD_SAMPLE_REQUIRED if state==FIELD_SAMPLE_REQUIRED or uncertain and h else 'NONE','direct unsafe source' if h==0 else f'risk propagated from {source} over {h} hop(s)'))
    alts=[]
    for n in sorted(network.nodes,key=lambda x:x.node_id):
        if n.safety_state==SAFE:
            ds=[e.distance_km for e in network.edges if e.upstream in starts and e.downstream==n.node_id]; alts.append(AlternativeWaterPoint(n.node_id,n.name,round(min(ds),6) if ds else None,SAFE,'explicit lab-supported safe result; verify locally before use'))
    alts=alts[:alternatives_limit]; dashboard={'network_id':network.network_id,'nodes':[{'node_id':n.node_id,'name':n.name,'latitude':n.latitude,'longitude':n.longitude,'safety_state':n.safety_state,'community':n.community} for n in network.nodes],'edges':[{'upstream':e.upstream,'downstream':e.downstream,'distance_km':round(e.distance_km,6),'relation':e.relation} for e in network.edges],'alerts':[e.__dict__ for e in events],'alternatives':[a.__dict__ for a in alts],'legend':{'SAFE':'supported evidence only','UNSAFE':'explicit or laboratory unsafe evidence',FIELD_SAMPLE_REQUIRED:'unknown or incomplete evidence; field sample required'}}
    return NetworkAnalysis(network.network_id,tuple(sorted(starts)),tuple(events),tuple(alts),FIELD_SAMPLE_REQUIRED if uncertain else 'NONE',dashboard)
def analyze_records(records, **kwargs): return analyze_water_network(build_water_network(records,kwargs.pop('max_distance_km',10)),**kwargs).to_dict()
