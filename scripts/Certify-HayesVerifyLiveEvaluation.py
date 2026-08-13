import argparse, hashlib, json
from datetime import UTC, datetime
from pathlib import Path
from jsonschema import Draft202012Validator

def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
    return h.hexdigest()

def parse_obs(evidence):
    if not evidence: return {}
    try:
        x=json.loads(evidence[0].get("observation",""))
    except Exception:
        return {}
    return x if isinstance(x,dict) else {}

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--spec",required=True)
a=ap.parse_args()
root=Path(a.root).resolve()
spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))
paths={
 "evidence":root/spec["live_evidence"],
 "result":root/spec["live_result"],
 "freeze":root/spec["contract_freeze"],
 "schema":root/spec["result_schema"],
}
errors=[]
for k,p in paths.items():
    if not p.exists(): errors.append(f"missing {k}: {p}")
if errors:
    print(json.dumps({"status":"FAIL","errors":errors},indent=2))
    raise SystemExit(1)

evidence=json.loads(paths["evidence"].read_text(encoding="utf-8-sig"))
result=json.loads(paths["result"].read_text(encoding="utf-8-sig"))
freeze=json.loads(paths["freeze"].read_text(encoding="utf-8-sig"))
schema=json.loads(paths["schema"].read_text(encoding="utf-8-sig"))

try:
    Draft202012Validator(schema).validate(result)
except Exception as exc:
    errors.append(f"result schema validation failed: {exc}")

checks=[
 ("control_id",result.get("control_id"),spec["control_id"]),
 ("target_id",result.get("target_id"),spec["target_id"]),
 ("evaluation_state",result.get("evaluation_state"),spec["expected_evaluation_state"]),
 ("evidence_state",result.get("evidence_state"),spec["expected_evidence_state"]),
 ("result_state",result.get("result_state"),spec["expected_result_state"]),
 ("promotion_state",result.get("promotion_state"),spec["expected_promotion_state"]),
]
for n,a1,e in checks:
    if a1!=e: errors.append(f"{n} mismatch: {a1!r} != {e!r}")

if not isinstance(evidence,list) or len(evidence)!=1:
    errors.append("expected exactly one evidence record")
obs=parse_obs(evidence)
if obs.get("evaluated_branch")!=spec["expected_evaluated_branch"]:
    errors.append("evaluated_branch mismatch")
if obs.get("api_success") is not True: errors.append("api_success is not true")
if obs.get("protected") is not True: errors.append("protected is not true")
evidence_id=evidence[0].get("evidence_id") if evidence else None
if evidence_id not in result.get("evidence_ids",[]): errors.append("result does not reference evidence_id")
if freeze.get("status")!="PASS": errors.append("contract freeze status not PASS")
if freeze.get("freeze_state")!="CONTRACT_FROZEN": errors.append("contract freeze state invalid")

cert={
 "component":"Hayes Verify",
 "phase":"Pilot Live Evaluation Certification",
 "certified_at_utc":datetime.now(UTC).isoformat(),
 "status":"PASS" if not errors else "FAIL",
 "wave":result.get("wave"),
 "control_id":result.get("control_id"),
 "target_id":result.get("target_id"),
 "request_id":result.get("request_id"),
 "evaluation_state":result.get("evaluation_state"),
 "evidence_state":result.get("evidence_state"),
 "result_state":result.get("result_state"),
 "promotion_state":result.get("promotion_state"),
 "acceptance_state":"PENDING_EMS_ACCEPTANCE",
 "evaluated_branch":obs.get("evaluated_branch"),
 "evidence_id":evidence_id,
 "evidence_sha256":sha256(paths["evidence"]),
 "result_sha256":sha256(paths["result"]),
 "contract_freeze_sha256":sha256(paths["freeze"]),
 "result_schema_sha256":sha256(paths["schema"]),
 "authority":{"result_acceptance":"EMS","evidence_promotion":"EMS"},
 "errors":errors
}
out=root/spec["certification_output"]
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(cert,indent=2),encoding="utf-8")
print(json.dumps(cert,indent=2))
raise SystemExit(0 if not errors else 1)
