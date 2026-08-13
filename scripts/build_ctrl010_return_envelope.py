import argparse, hashlib, json
from datetime import UTC, datetime
from pathlib import Path
from jsonschema import Draft202012Validator

def load(p): return json.loads(p.read_text(encoding="utf-8-sig"))
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
    return h.hexdigest()
def rp(root,rel): return root/Path(rel.replace("\\","/"))

ap=argparse.ArgumentParser();ap.add_argument("--root",required=True);ap.add_argument("--spec",required=True);ap.add_argument("--schema",required=True)
a=ap.parse_args();root=Path(a.root).resolve();spec=load(Path(a.spec));schema=load(Path(a.schema))
certp=rp(root,spec["certification_output"]);res=load(rp(root,spec["live_result"]));cert=load(certp)
if cert.get("status")!="PASS": raise SystemExit("certification not PASS")
env={
 "envelope_version":"1.0","created_at_utc":datetime.now(UTC).isoformat(),
 "source_system":"Hayes Verify","destination_system":"EMS","wave":"2D",
 "control_id":"EMS-CTRL-010","target_id":"REPO-001","request_id":res["request_id"],
 "evaluation_state":res["evaluation_state"],"evidence_state":res["evidence_state"],"result_state":res["result_state"],
 "acceptance_state":"PENDING_EMS_ACCEPTANCE","promotion_state":"NOT_PROMOTED",
 "evaluated_branch":cert.get("evaluated_branch"),"evidence_id":cert["evidence_id"],
 "evidence_sha256":cert["evidence_sha256"],"result_sha256":cert["result_sha256"],
 "certification_sha256":sha(certp),"contract_freeze_sha256":cert["contract_freeze_sha256"],
 "authority":{"result_acceptance":"EMS","evidence_promotion":"EMS"}
}
Draft202012Validator(schema).validate(env)
out=rp(root,spec["return_envelope_output"]);out.write_text(json.dumps(env,indent=2),encoding="utf-8");print(json.dumps(env,indent=2))
