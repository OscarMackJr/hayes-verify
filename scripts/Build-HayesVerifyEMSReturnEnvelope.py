import argparse, hashlib, json
from datetime import UTC, datetime
from pathlib import Path
from jsonschema import Draft202012Validator

def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
    return h.hexdigest()

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--spec",required=True)
ap.add_argument("--schema",required=True)
a=ap.parse_args()
root=Path(a.root).resolve()
spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))
schema=json.loads(Path(a.schema).read_text(encoding="utf-8"))
certp=root/spec["certification_output"]
resultp=root/spec["live_result"]
evidencep=root/spec["live_evidence"]
cert=json.loads(certp.read_text(encoding="utf-8"))
result=json.loads(resultp.read_text(encoding="utf-8"))
if cert.get("status")!="PASS":
    raise SystemExit("Return envelope blocked: certification not PASS")
env={
 "envelope_version":"1.0",
 "created_at_utc":datetime.now(UTC).isoformat(),
 "source_system":"Hayes Verify",
 "destination_system":"EMS",
 "wave":result["wave"],
 "control_id":result["control_id"],
 "target_id":result["target_id"],
 "request_id":result["request_id"],
 "evaluation_state":result["evaluation_state"],
 "evidence_state":result["evidence_state"],
 "result_state":result["result_state"],
 "acceptance_state":"PENDING_EMS_ACCEPTANCE",
 "promotion_state":"NOT_PROMOTED",
 "evaluated_branch":cert["evaluated_branch"],
 "evidence_id":cert["evidence_id"],
 "evidence_sha256":sha256(evidencep),
 "result_sha256":sha256(resultp),
 "certification_sha256":sha256(certp),
 "contract_freeze_sha256":cert["contract_freeze_sha256"],
 "authority":{"result_acceptance":"EMS","evidence_promotion":"EMS"},
 "instructions_to_ems":[
   "Validate envelope and referenced hashes.",
   "Verify applicability remains EMS-authoritative.",
   "Accept or reject the Hayes Verify result.",
   "Do not infer promotion from Hayes Verify PASS.",
   "If accepted, use EMS-controlled promotion workflow."
 ]
}
Draft202012Validator(schema).validate(env)
out=root/spec["return_envelope_output"]
out.write_text(json.dumps(env,indent=2),encoding="utf-8")
print(json.dumps(env,indent=2))
