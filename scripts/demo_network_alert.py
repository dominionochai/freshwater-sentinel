from __future__ import annotations
import json
from app.network import analyze_records
records=[{'node_id':'upstream','name':'Upstream sample','latitude':-15.,'longitude':35.,'safety_status':'unsafe'},{'node_id':'downstream','name':'Downstream untested','latitude':-15.001,'longitude':35.001}]
print(json.dumps(analyze_records(records,alert_node_ids=['upstream']),indent=2))
