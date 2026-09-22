from __future__ import annotations
import math
from typing import Any
FIELD_SAMPLE_REQUIRED = 'FIELD SAMPLE REQUIRED'; SAFE = 'SAFE'; UNSAFE = 'UNSAFE'
def _num(v: Any):
    try:
        if v is None or str(v).strip() == '': return None
        x = float(v); return x if math.isfinite(x) else None
    except (TypeError, ValueError): return None
def assess_safety(record: dict[str, Any]):
    explicit = str(record.get('safety_state', record.get('safety_status', ''))).strip().upper()
    if explicit in {'UNSAFE','CONTAMINATED','POSITIVE','FAIL'}: return UNSAFE, 'explicit unsafe result'
    fecal = _num(record.get('faecal_coli_count', record.get('fecal_coli_count'))); turbidity = _num(record.get('turbidity_ntu'))
    if fecal is not None and fecal > 0: return UNSAFE, 'faecal_coli_count is above zero'
    if explicit in {'SAFE','VERIFIED SAFE','PASS'} and fecal is not None and turbidity is not None:
        if fecal == 0 and turbidity <= 5: return SAFE, 'explicit safe result supported by supplied lab fields'
        return UNSAFE, 'lab values do not support the safe claim'
    return FIELD_SAMPLE_REQUIRED, 'safety or complete laboratory evidence is missing'
def base_risk(state: str): return 1.0 if state == UNSAFE else 0.0 if state == SAFE else .5
def propagate_score(source_score: float, hops: int, decay: float = .75): return max(0., min(1., source_score * decay ** max(0, hops)))
def risk_label(score: float, state: str):
    if state == FIELD_SAMPLE_REQUIRED: return FIELD_SAMPLE_REQUIRED
    return 'HIGH' if score >= .67 else 'MEDIUM' if score >= .34 else 'LOW'
