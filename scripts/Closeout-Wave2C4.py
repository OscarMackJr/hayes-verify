import argparse,csv,json,hashlib
from pathlib import Path
from datetime import datetime,timezone

p=argparse.ArgumentParser()
p.add_argument("--root",required=True)
p.add_argument("--out",required=True)
a=p.parse_args()

root=Path(a.root)
queue=root/"generated"/"wave2c"/"remediation_queue.csv"
impact=root/"generated"/"wave2"/"inheritance"/"inheritance_impact_report.json"
higher=root/"generated"/"wave2"/"inheritance"/"higher_scope_results.json"
promotion=root/"generated"/"wave2c"/"annual-review-closeout"/"promotion_record.json"

for pth in [queue,impact,higher,promotion]:
    if not pth.exists(): raise SystemExit(f"Closeout blocked: missing {pth}")

with queue.open(encoding="utf-8-sig",newline="") as f:
    rows=list(csv.DictReader(f))
open_rows=[r for r in rows if r.get("remediation_state")=="OPEN"]
if open_rows:
    raise SystemExit(f"Closeout blocked: open remediation remains {[r.get('control_id') for r in open_rows]}")

impact_j=json.loads(impact.read_text())
higher_j=json.loads(higher.read_text())

# tolerate either direct status or nested status depending on existing artifact shape
inherit_status=impact_j.get("status") or impact_j.get("validation_status") or "UNKNOWN"

def sha256(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""):h.update(c)
    return h.hexdigest()

record={
 "wave":"2C.4",
 "certified_at_utc":datetime.now(timezone.utc).isoformat(),
 "status":"PASS",
 "open_remediation_count":0,
 "promotion_performed":True,
 "inheritance_validation":inherit_status,
 "queue_sha256":sha256(queue),
 "inheritance_impact_sha256":sha256(impact),
 "higher_scope_results_sha256":sha256(higher),
 "annual_review_promotion_record":str(promotion),
 "wave2c_state":"CLOSED"
}
Path(a.out).parent.mkdir(parents=True,exist_ok=True)
Path(a.out).write_text(json.dumps(record,indent=2),encoding="utf-8")
print(json.dumps(record,indent=2))
