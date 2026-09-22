from __future__ import annotations
import argparse, json
from pathlib import Path
from app.network import build_water_network
from app.network_sources import load_default_records
p=argparse.ArgumentParser(description='Build a deterministic local water network; no live source downloads.')
p.add_argument('--root',default='.');p.add_argument('--output',default='network.json');p.add_argument('--max-distance-km',type=float,default=10)
a=p.parse_args(); n=build_water_network(load_default_records(Path(a.root)),a.max_distance_km); Path(a.output).write_text(json.dumps(n.to_dict(),indent=2)+'\n',encoding='utf-8'); print(n.network_id)
