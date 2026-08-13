import argparse,csv,json,hashlib
from pathlib import Path
from datetime import datetime,timezone

ap=argparse.ArgumentParser()
ap.add_argument("--ems-root",required=True)
ap.add_argument("--spec",required=True)
ap.add_argument("--outdir",required=True)
a=ap.parse_args()

root=Path(a.ems_root).resolve()
spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))
outdir=Path(a.outdir).resolve()
outdir.mkdir(parents=True,exist_ok=True)

evidence_path=root/spec["qualification_source"]
qualified_queue_path=root/spec["qualified_queue_source"]
queue_path=root/spec["updated_queue"]
dest=root/spec["authoritative_evidence_destination"]

for p in (evidence_path,qualified_queue_path,queue_path):
    if not p.exists():
        raise SystemExit(f"Required promotion input missing: {p}")

e=json.loads(evidence_path.read_text(encoding="utf-8"))

required = {
    "status":"PASS",
    "sufficiency":"SUFFICIENT",
    "promotion_eligible":True,
    "promotion_status":"QUALIFIED_NOT_PROMOTED",
    "remediation_state":"OPEN",
    "promotion_performed":False
}
for k,v in required.items():
    if e.get(k)!=v:
        raise SystemExit(f"Promotion blocked: evidence {k}={e.get(k)!r}; expected {v!r}")

# Verify all current DOCX/PDF hashes again before promotion.
manifest_path=Path(e["evidence_summary"]["generation_manifest"])
manifest=json.loads(manifest_path.read_text(encoding="utf-8"))

def sha256(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

for r in manifest.get("records",[]):
    for path_key,hash_key in (("docx_path","docx_sha256"),("pdf_path","pdf_sha256")):
        p=root/r[path_key]
        if not p.exists() or p.stat().st_size<=0:
            raise SystemExit(f"Promotion blocked: output missing/empty: {p}")
        actual=sha256(p).lower()
        expected=r[hash_key].lower()
        if actual!=expected:
            raise SystemExit(f"Promotion blocked: hash mismatch for {p}")

# Load authoritative Wave 2C queue and confirm exactly 8 open controls before transition.
with queue_path.open(encoding="utf-8-sig",newline="") as f:
    rows=list(csv.DictReader(f))

open_before=[r for r in rows if r.get("remediation_state")=="OPEN"]
if len(open_before)!=spec["expected_pre_promotion_open_count"]:
    raise SystemExit(f"Promotion blocked: expected {spec['expected_pre_promotion_open_count']} OPEN controls, found {len(open_before)}")

target=[r for r in rows if r.get("control_id")=="EMS-CTRL-072"]
if len(target)!=1:
    raise SystemExit("Promotion blocked: EMS-CTRL-072 row missing or duplicated in Wave 2C queue.")
t=target[0]

# Ensure authoritative queue has not already been promoted.
if t.get("remediation_state")!="OPEN":
    raise SystemExit(f"Promotion blocked: CTRL-072 remediation_state={t.get('remediation_state')}")
if t.get("promotion_status")=="PROMOTED":
    raise SystemExit("Promotion blocked: CTRL-072 is already promoted.")

# Load qualified row to prevent stale queue manipulation.
with qualified_queue_path.open(encoding="utf-8-sig",newline="") as f:
    qrows=list(csv.DictReader(f))
q=[r for r in qrows if r.get("control_id")=="EMS-CTRL-072"]
if len(q)!=1:
    raise SystemExit("Promotion blocked: qualified CTRL-072 row missing or duplicated.")
q=q[0]
if q.get("current_status")!="PASS" or q.get("evidence_sufficiency")!="SUFFICIENT" or q.get("promotion_eligible")!="True":
    raise SystemExit("Promotion blocked: qualified queue row is not PASS/SUFFICIENT/eligible.")

# Create authoritative evidence YAML without requiring PyYAML.
dest.parent.mkdir(parents=True,exist_ok=True)
yaml_text = f"""control_id: EMS-CTRL-072
control_name: PDF/DOCX Generation Validation
scope: EMS
status: PASS
evidence_class: OPERATING_EVIDENCE
sufficiency: SUFFICIENT
promotion_status: PROMOTED
remediation_state: CLOSED
promotion_wave: 2C.1c
promoted_at_utc: {datetime.now(timezone.utc).isoformat()}
source_evidence: {str(evidence_path)}
generation_manifest: {e['evidence_summary']['generation_manifest']}
output_validation: {e['evidence_summary']['output_validation']}
provenance: {e['evidence_summary']['provenance']}
source_count: {e['evidence_summary']['source_count']}
docx_count: {e['evidence_summary']['docx_count']}
pdf_count: {e['evidence_summary']['pdf_count']}
promotion_performed: true
"""
dest.write_text(yaml_text,encoding="utf-8")

# Transition only CTRL-072.
for r in rows:
    if r.get("control_id")=="EMS-CTRL-072":
        r["current_status"]="PASS"
        r["evidence_sufficiency"]="SUFFICIENT"
        r["promotion_eligible"]="True"
        r["promotion_status"]="PROMOTED"
        r["remediation_state"]="CLOSED"
        r["evidence_record_count"]=str(e["evidence_summary"]["record_count"])
        r["next_action"]="NONE"

with queue_path.open("w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys()))
    w.writeheader();w.writerows(rows)

open_after=[r for r in rows if r.get("remediation_state")=="OPEN"]
remaining=sorted(r["control_id"] for r in open_after)
expected=sorted(spec["remaining_open_controls"])
if len(open_after)!=spec["expected_post_promotion_open_count"]:
    raise SystemExit(f"Post-promotion validation failed: expected {spec['expected_post_promotion_open_count']} OPEN controls, found {len(open_after)}")
if remaining!=expected:
    raise SystemExit(f"Post-promotion population mismatch. expected={expected} actual={remaining}")

record={
    "wave":"2C.1c",
    "control_id":"EMS-CTRL-072",
    "control_name":"PDF/DOCX Generation Validation",
    "promotion_performed":True,
    "promoted_at_utc":datetime.now(timezone.utc).isoformat(),
    "source_status":e["status"],
    "source_sufficiency":e["sufficiency"],
    "source_promotion_eligible":e["promotion_eligible"],
    "pre_open_count":len(open_before),
    "post_open_count":len(open_after),
    "remaining_open_controls":remaining,
    "authoritative_evidence":str(dest),
    "authoritative_evidence_sha256":sha256(dest),
    "qualification_evidence":str(evidence_path)
}
(outdir/"promotion_record.json").write_text(json.dumps(record,indent=2),encoding="utf-8")

summary={
    "control_id":"EMS-CTRL-072",
    "status":"PASS",
    "promotion_status":"PROMOTED",
    "remediation_state":"CLOSED",
    "pre_open_count":len(open_before),
    "post_open_count":len(open_after),
    "remaining_open_controls":remaining,
    "promotion_performed":True
}
(outdir/"promotion_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
print(json.dumps(summary,indent=2))
