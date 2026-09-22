from __future__ import annotations
import csv, json
from pathlib import Path
from typing import Any, Iterable
def _first(r, *names):
    for n in names:
        if r.get(n) not in (None, ''): return r[n]
def _float(v):
    try: return None if v in (None, '') else float(v)
    except (TypeError, ValueError): return None
def normalize_record(record: dict[str, Any], source='injected'):
    r = dict(record); ident = _first(r, 'node_id','waterpoint_id','wpdx_id','id','waterpoint_name','name')
    r.update({'node_id': str(ident) if ident is not None else '', 'name': str(_first(r,'name','waterpoint_name','wpdx_name','node_id') or 'Unnamed water point'), 'latitude': _float(_first(r,'latitude','lat','decimal_latitude','gps_latitude')), 'longitude': _float(_first(r,'longitude','lon','lng','decimal_longitude','gps_longitude')), 'source': str(_first(r,'source','data_source') or source)})
    return r
def load_boreholes_csv(path: str | Path):
    with Path(path).open(newline='', encoding='utf-8') as f: return [normalize_record(x, 'malawi_boreholes.csv') for x in csv.DictReader(f)]
def load_community_profiles(path: str | Path):
    with Path(path).open(encoding='utf-8') as f: return json.load(f)
def records_from_optional_source(rows: Iterable[dict[str, Any]], source: str): return [normalize_record(x, source) for x in rows]
def load_default_records(root: str | Path = '.'):
    root = Path(root); rows = load_boreholes_csv(root/'data'/'malawi_boreholes.csv')
    profile_path = root/'data'/'community_profiles.json'
    profiles = load_community_profiles(profile_path) if profile_path.is_file() else []
    by_name = {str(n).casefold(): str(p['community']) for p in profiles for n in p.get('names', []) if p.get('community')}
    for row in rows:
        if row['name'].casefold() in by_name: row['community'] = by_name[row['name'].casefold()]
    return rows
