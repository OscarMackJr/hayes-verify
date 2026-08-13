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
out=Path(a.outdir).resolve()
out.mkdir(parents=True,exist_ok=True)

qpath=root/spec["qualification_source"]
apath=root/spec["assertion_source"]
vpath=root/spec["register_validation_source"]
regroot=root/spec["register_root"]

for p in (qpath,apath,vpath):
    if not p.exists():
        raise SystemExit(f"Review blocked: missing evidence artifact {p}")

qualification=json.loads(qpath.read_text(encoding="utf-8"))
assertions=json.loads(apath.read_text(encoding="utf-8"))
validation=json.loads(vpath.read_text(encoding="utf-8"))

expected={"EMS-CTRL-063","EMS-CTRL-065","EMS-CTRL-066"}
qcontrols={x["control_id"]:x for x in qualification.get("controls",[])}

if set(qcontrols)!=expected:
    raise SystemExit(f"Review blocked: qualification population mismatch {sorted(qcontrols)}")

for cid in expected:
    x=qcontrols[cid]
    required={
        "status":"PASS",
        "sufficiency":"SUFFICIENT",
        "promotion_eligible":True,
        "promotion_status":"QUALIFIED_NOT_PROMOTED",
        "remediation_state":"OPEN"
    }
    for k,v in required.items():
        if x.get(k)!=v:
            raise SystemExit(f"Review blocked: {cid} {k}={x.get(k)!r}; expected {v!r}")

if qualification.get("promotion_performed") is not False:
    raise SystemExit("Review blocked: qualification indicates prior promotion.")
if validation.get("status")!="PASS" or validation.get("errors"):
    raise SystemExit("Review blocked: register validation is not clean.")
if validation.get("promotion_performed") is not False:
    raise SystemExit("Review blocked: register validation indicates promotion.")

rows=assertions.get("assertions",[])
if len(rows)!=spec["expected_assertion_count"]:
    raise SystemExit(f"Review blocked: expected {spec['expected_assertion_count']} assertions, found {len(rows)}")
for r in rows:
    if r.get("control_id") not in expected:
        raise SystemExit(f"Review blocked: unexpected assertion control {r.get('control_id')}")
    if r.get("operating_evidence_sufficient") is not True:
        raise SystemExit(f"Review blocked: insufficient assertion {r.get('control_id')} / {r.get('assertion')}")
    if int(r.get("qualifying_record_count",0))<1:
        raise SystemExit(f"Review blocked: no qualifying record {r.get('control_id')} / {r.get('assertion')}")

def sha256(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

registers=[]
for name in [
    "data_classification_register.csv",
    "data_retention_register.csv",
    "production_data_protection_register.csv"
]:
    p=regroot/name
    if not p.exists():
        raise SystemExit(f"Review blocked: missing register {p}")
    with p.open(encoding="utf-8-sig",newline="") as f:
        rr=list(csv.DictReader(f))
    if len(rr)<1:
        raise SystemExit(f"Review blocked: empty register {name}")
    registers.append({
        "register":str(p),
        "record_count":len(rr),
        "sha256":sha256(p)
    })

review={
    "wave":"2C.3a",
    "reviewed_at_utc":datetime.now(timezone.utc).isoformat(),
    "controls":sorted(expected),
    "qualification_status":"PASS",
    "assertion_count":len(rows),
    "sufficient_assertion_count":sum(1 for r in rows if r.get("operating_evidence_sufficient") is True),
    "register_validation_status":validation.get("status"),
    "registers":registers,
    "promotion_authorized":True,
    "promotion_performed":False
}
(out/"review_record.json").write_text(json.dumps(review,indent=2),encoding="utf-8")
print(json.dumps(review,indent=2))
