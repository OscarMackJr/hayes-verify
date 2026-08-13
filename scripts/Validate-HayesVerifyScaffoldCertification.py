import argparse,json,hashlib
from pathlib import Path
from datetime import datetime,timezone

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--spec",required=True)
a=ap.parse_args()

root=Path(a.root).resolve()
spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))
record=json.loads((root/spec["certification_output"]).read_text(encoding="utf-8"))

def sha256(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""):
            h.update(c)
    return h.hexdigest()

errors=[]
if record.get("status")!="PASS": errors.append("certification status not PASS")
if record.get("contract_validation_status")!="PASS": errors.append("contract validation not PASS")
if record.get("pytest_status")!="PASS": errors.append("pytest not PASS")
if record.get("ruff_status")!="PASS": errors.append("ruff not PASS")
if int(record.get("test_count",0))<spec["expected_test_count"]: errors.append("test count too low")
if int(record.get("contract_count",0))!=spec["expected_contract_count"]: errors.append("contract count mismatch")
if record.get("bootstrap_promotion_state")!=spec["required_promotion_state"]: errors.append("promotion invariant failed")

for meta in record.get("files",[]):
    p=root/meta["path"]
    if not p.exists():
        errors.append(f"missing certified file {meta['path']}")
    elif sha256(p)!=meta["sha256"]:
        errors.append(f"hash changed: {meta['path']}")

validation={
    "component":"Hayes Verify",
    "validated_at_utc":datetime.now(timezone.utc).isoformat(),
    "status":"PASS" if not errors else "FAIL",
    "errors":errors
}
(root/spec["validation_output"]).write_text(json.dumps(validation,indent=2),encoding="utf-8")
print(json.dumps(validation,indent=2))
raise SystemExit(0 if not errors else 1)
