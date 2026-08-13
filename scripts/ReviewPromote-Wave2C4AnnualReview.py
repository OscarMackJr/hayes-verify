import argparse,csv,json,hashlib
from pathlib import Path
from datetime import datetime,timezone

p=argparse.ArgumentParser()
p.add_argument("--root",required=True)
p.add_argument("--promote",action="store_true")
p.add_argument("--outdir",required=True)
a=p.parse_args()

root=Path(a.root)
out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True)
queue=root/"generated"/"wave2c"/"remediation_queue.csv"
qual_path=root/"generated"/"wave2c"/"annual-review"/"qualification.json"
assert_path=root/"generated"/"wave2c"/"annual-review"/"assertion_evidence.json"
val_path=root/"generated"/"wave2c"/"annual-review"/"register_validation.json"
reg=root/"registers"/"wave2c"/"ems-review"/"annual_ems_review_register.csv"

for pth in [queue,qual_path,assert_path,val_path,reg]:
    if not pth.exists(): raise SystemExit(f"Missing required artifact: {pth}")

q=json.loads(qual_path.read_text())
ae=json.loads(assert_path.read_text())
vr=json.loads(val_path.read_text())
ctrl=q["control"]

required={"status":"PASS","sufficiency":"SUFFICIENT","promotion_eligible":True,"promotion_status":"QUALIFIED_NOT_PROMOTED","remediation_state":"OPEN"}
for k,v in required.items():
    if ctrl.get(k)!=v: raise SystemExit(f"Review blocked: {k}={ctrl.get(k)!r}, expected {v!r}")
if q.get("promotion_performed") is not False: raise SystemExit("Review blocked: prior promotion detected.")
if vr.get("status")!="PASS" or vr.get("errors"): raise SystemExit("Review blocked: register validation failed.")
assertions=ae.get("assertions",[])
if len(assertions)!=7 or any(x.get("operating_evidence_sufficient") is not True for x in assertions):
    raise SystemExit("Review blocked: all 7 annual-review assertions must be sufficient.")

def sha256(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
    return h.hexdigest()

with queue.open(encoding="utf-8-sig",newline="") as f:
    rows=list(csv.DictReader(f))
open_before=[r for r in rows if r.get("remediation_state")=="OPEN"]
if len(open_before)!=1 or open_before[0].get("control_id")!="EMS-CTRL-080":
    raise SystemExit(f"Review blocked: CTRL-080 must be sole open remediation row. actual={[r.get('control_id') for r in open_before]}")

review={
 "wave":"2C.4",
 "reviewed_at_utc":datetime.now(timezone.utc).isoformat(),
 "control_id":"EMS-CTRL-080",
 "assertion_count":7,
 "sufficient_assertion_count":7,
 "register_sha256":sha256(reg),
 "register_record_count":vr.get("record_count"),
 "promotion_authorized":True,
 "promotion_performed":False
}
(out/"review_record.json").write_text(json.dumps(review,indent=2),encoding="utf-8")

if not a.promote:
    print(json.dumps(review,indent=2))
    raise SystemExit(0)

dest=root/"evidence"/"ems"/"EMS-CTRL-080.yaml"
dest.parent.mkdir(parents=True,exist_ok=True)
now=datetime.now(timezone.utc).isoformat()
dest.write_text(f"""control_id: EMS-CTRL-080
control_name: Annual EMS Review
scope: EMS
status: PASS
evidence_class: OPERATING_EVIDENCE
sufficiency: SUFFICIENT
promotion_status: PROMOTED
remediation_state: CLOSED
promotion_wave: 2C.4
promoted_at_utc: {now}
qualification_source: {qual_path}
assertion_source: {assert_path}
register_validation_source: {val_path}
register_source: {reg}
register_sha256: {review['register_sha256']}
promotion_performed: true
""",encoding="utf-8")

for r in rows:
    if r.get("control_id")=="EMS-CTRL-080":
        r["current_status"]="PASS"
        r["evidence_sufficiency"]="SUFFICIENT"
        r["promotion_eligible"]="True"
        r["promotion_status"]="PROMOTED"
        r["remediation_state"]="CLOSED"
        r["next_action"]="NONE"

with queue.open("w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)

open_after=[r for r in rows if r.get("remediation_state")=="OPEN"]
if open_after:
    raise SystemExit(f"Post-promotion validation failed: expected 0 open controls, actual={[r.get('control_id') for r in open_after]}")

record={
 "wave":"2C.4",
 "promotion_performed":True,
 "promoted_at_utc":now,
 "control_id":"EMS-CTRL-080",
 "pre_open_count":1,
 "post_open_count":0,
 "authoritative_evidence":str(dest),
 "authoritative_evidence_sha256":sha256(dest),
 "register_sha256":review["register_sha256"]
}
(out/"promotion_record.json").write_text(json.dumps(record,indent=2),encoding="utf-8")
print(json.dumps(record,indent=2))
