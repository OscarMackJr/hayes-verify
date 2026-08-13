import argparse,json,hashlib
from pathlib import Path
from datetime import datetime,timezone

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--spec",required=True)
a=ap.parse_args()
root=Path(a.root).resolve()
spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))
freeze=json.loads((root/spec["freeze_output"]).read_text(encoding="utf-8"))

def sha256(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
    return h.hexdigest()

errors=[]
if freeze.get("status")!="PASS": errors.append("freeze status not PASS")
if freeze.get("freeze_state")!="CONTRACT_FROZEN": errors.append("freeze_state invalid")
if freeze.get("evaluation_performed") is not False: errors.append("evaluation_performed must be false")
if freeze.get("promotion_performed") is not False: errors.append("promotion_performed must be false")

for k,meta in freeze.get("contracts",{}).items():
    p=root/meta["path"]
    if not p.exists():
        errors.append(f"missing contract {k}")
        continue
    if sha256(p)!=meta["sha256"]:
        errors.append(f"hash mismatch for {k}")

authority=freeze.get("authority",{})
if authority.get("applicability")!="EMS": errors.append("EMS must remain applicability authority")
if authority.get("evidence_promotion")!="EMS": errors.append("EMS must remain promotion authority")
if authority.get("evaluation_execution")!="Hayes Verify": errors.append("Hayes Verify must remain evaluation executor")

validation={
    "wave":"2D",
    "validated_at_utc":datetime.now(timezone.utc).isoformat(),
    "status":"PASS" if not errors else "FAIL",
    "contract_count":len(freeze.get("contracts",{})),
    "errors":errors,
    "evaluation_performed":False,
    "promotion_performed":False
}
(root/spec["freeze_validation"]).write_text(json.dumps(validation,indent=2),encoding="utf-8")
print(json.dumps(validation,indent=2))
raise SystemExit(0 if not errors else 1)
