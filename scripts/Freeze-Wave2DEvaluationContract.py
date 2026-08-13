import argparse,json,hashlib
from pathlib import Path
from datetime import datetime,timezone

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--spec",required=True)
a=ap.parse_args()

root=Path(a.root).resolve()
spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))

freeze_path=root/spec["applicability_freeze"]
if not freeze_path.exists():
    raise SystemExit(f"Contract freeze blocked: missing applicability freeze {freeze_path}")

app=json.loads(freeze_path.read_text(encoding="utf-8"))
errors=[]
if app.get("status")!="PASS": errors.append("applicability freeze is not PASS")
if int(app.get("matrix_row_count",-1))!=spec["expected_matrix_rows"]: errors.append("matrix row count mismatch")
if int(app.get("applicable_count",-1))!=spec["expected_applicable_count"]: errors.append("applicable count mismatch")
if int(app.get("not_applicable_count",-1))!=spec["expected_not_applicable_count"]: errors.append("not-applicable count mismatch")
if app.get("evaluation_performed") is not False: errors.append("evaluation already performed")
if app.get("promotion_performed") is not False: errors.append("promotion already performed")
if errors:
    print(json.dumps({"status":"FAIL","errors":errors},indent=2))
    raise SystemExit(1)

def sha256(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
    return h.hexdigest()

contracts={}
for k,rel in spec["contracts"].items():
    p=root/rel
    if not p.exists():
        raise SystemExit(f"Contract freeze blocked: missing {k}: {p}")
    contracts[k]={"path":rel,"sha256":sha256(p)}

record={
    "wave":"2D",
    "contract_version":"1.0",
    "frozen_at_utc":datetime.now(timezone.utc).isoformat(),
    "status":"PASS",
    "authority":spec["authority"],
    "applicability_freeze_sha256":sha256(freeze_path),
    "contracts":contracts,
    "evaluation_performed":False,
    "promotion_performed":False,
    "freeze_state":"CONTRACT_FROZEN"
}
out=root/spec["freeze_output"]
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(record,indent=2),encoding="utf-8")
print(json.dumps(record,indent=2))
