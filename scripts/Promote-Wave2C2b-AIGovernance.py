import argparse,csv,json,hashlib
from pathlib import Path
from datetime import datetime,timezone

ap=argparse.ArgumentParser()
ap.add_argument("--ems-root",required=True)
ap.add_argument("--spec",required=True)
ap.add_argument("--review",required=True)
ap.add_argument("--outdir",required=True)
a=ap.parse_args()

root=Path(a.ems_root).resolve()
spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))
review=json.loads(Path(a.review).read_text(encoding="utf-8"))
out=Path(a.outdir).resolve()
out.mkdir(parents=True,exist_ok=True)

expected={"EMS-CTRL-049","EMS-CTRL-050","EMS-CTRL-053"}
if review.get("promotion_authorized") is not True or review.get("promotion_performed") is not False:
    raise SystemExit("Promotion blocked: review record is not an unconsumed authorization.")
if set(review.get("controls",[]))!=expected:
    raise SystemExit("Promotion blocked: review control population mismatch.")

qpath=root/spec["qualification_source"]
queue_path=root/spec["queue"]
qualification=json.loads(qpath.read_text(encoding="utf-8"))

with queue_path.open(encoding="utf-8-sig",newline="") as f:
    rows=list(csv.DictReader(f))

open_before=[r for r in rows if r.get("remediation_state")=="OPEN"]
if len(open_before)!=spec["expected_pre_open_count"]:
    raise SystemExit(f"Promotion blocked: expected {spec['expected_pre_open_count']} open controls, found {len(open_before)}")

qmap={x["control_id"]:x for x in qualification["controls"]}
for cid in expected:
    x=qmap[cid]
    if not (x["status"]=="PASS" and x["sufficiency"]=="SUFFICIENT" and x["promotion_eligible"] is True and x["promotion_status"]=="QUALIFIED_NOT_PROMOTED"):
        raise SystemExit(f"Promotion blocked: stale/unqualified state for {cid}")

now=datetime.now(timezone.utc).isoformat()
evidence_root=root/spec["authoritative_evidence_root"]
evidence_root.mkdir(parents=True,exist_ok=True)

def sha256(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

evidence_files=[]
for cid in sorted(expected):
    x=qmap[cid]
    dest=evidence_root/f"{cid}.yaml"
    text=f"""control_id: {cid}
control_name: {x['control_name']}
scope: ORGANIZATION
status: PASS
evidence_class: OPERATING_EVIDENCE
sufficiency: SUFFICIENT
promotion_status: PROMOTED
remediation_state: CLOSED
promotion_wave: 2C.2b
promoted_at_utc: {now}
qualification_source: {str(qpath)}
assertion_source: {str(root/spec['assertion_source'])}
register_validation_source: {str(root/spec['register_validation_source'])}
promotion_performed: true
"""
    dest.write_text(text,encoding="utf-8")
    evidence_files.append({"control_id":cid,"path":str(dest),"sha256":sha256(dest)})

for r in rows:
    if r.get("control_id") in expected:
        r["current_status"]="PASS"
        r["evidence_sufficiency"]="SUFFICIENT"
        r["promotion_eligible"]="True"
        r["promotion_status"]="PROMOTED"
        r["remediation_state"]="CLOSED"
        r["next_action"]="NONE"

with queue_path.open("w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys()))
    w.writeheader();w.writerows(rows)

open_after=[r for r in rows if r.get("remediation_state")=="OPEN"]
remaining=sorted(r["control_id"] for r in open_after)
expected_remaining=sorted(spec["remaining_open_controls"])

if len(open_after)!=spec["expected_post_open_count"]:
    raise SystemExit(f"Post-promotion validation failed: expected {spec['expected_post_open_count']} open controls, found {len(open_after)}")
if remaining!=expected_remaining:
    raise SystemExit(f"Post-promotion population mismatch. expected={expected_remaining} actual={remaining}")

record={
    "wave":"2C.2b",
    "promotion_performed":True,
    "promoted_at_utc":now,
    "promoted_controls":sorted(expected),
    "pre_open_count":len(open_before),
    "post_open_count":len(open_after),
    "remaining_open_controls":remaining,
    "review_record":str(Path(a.review)),
    "evidence_files":evidence_files
}
(out/"promotion_record.json").write_text(json.dumps(record,indent=2),encoding="utf-8")
(out/"promotion_summary.json").write_text(json.dumps({
    "promoted_controls":sorted(expected),
    "pre_open_count":len(open_before),
    "post_open_count":len(open_after),
    "remaining_open_controls":remaining,
    "promotion_performed":True
},indent=2),encoding="utf-8")

print(json.dumps(record,indent=2))
