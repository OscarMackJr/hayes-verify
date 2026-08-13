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
def observation(evidence):
    try: x=json.loads(evidence[0]["observation"])
    except Exception: return {}
    return x if isinstance(x,dict) else {}

ap=argparse.ArgumentParser();ap.add_argument("--root",required=True);ap.add_argument("--spec",required=True)
a=ap.parse_args();root=Path(a.root).resolve();spec=load(Path(a.spec))
p={k:rp(root,spec[k]) for k in ("live_evidence","live_result","contract_freeze","result_schema")}
errors=[f"missing {k}: {v}" for k,v in p.items() if not v.exists()]
if errors: print(json.dumps({"status":"FAIL","errors":errors},indent=2));raise SystemExit(1)
ev=load(p["live_evidence"]);res=load(p["live_result"]);freeze=load(p["contract_freeze"]);rs=load(p["result_schema"])
try: Draft202012Validator(rs).validate(res)
except Exception as exc: errors.append(f"result schema validation failed: {exc}")
for f,e in (("control_id","EMS-CTRL-010"),("target_id","REPO-001"),("evaluation_state","COMPLETE"),("evidence_state","SUFFICIENT"),("promotion_state","NOT_PROMOTED")):
    if res.get(f)!=e: errors.append(f"{f} mismatch")
if not isinstance(ev,list) or len(ev)!=1: errors.append("expected one evidence record")
obs=observation(ev)
if obs.get("api_success") is not True: errors.append("GitHub API evidence unsuccessful")
eid=ev[0].get("evidence_id") if ev else None
if eid not in res.get("evidence_ids",[]): errors.append("result/evidence linkage invalid")
if freeze.get("status")!="PASS" or freeze.get("freeze_state")!="CONTRACT_FROZEN": errors.append("contract freeze invalid")
cert={
 "component":"Hayes Verify","phase":"CTRL-010 Pilot Live Evaluation Certification",
 "certified_at_utc":datetime.now(UTC).isoformat(),"status":"PASS" if not errors else "FAIL",
 "wave":"2D","control_id":"EMS-CTRL-010","target_id":"REPO-001","request_id":res.get("request_id"),
 "evaluation_state":res.get("evaluation_state"),"evidence_state":res.get("evidence_state"),
 "result_state":res.get("result_state"),"promotion_state":res.get("promotion_state"),
 "acceptance_state":"PENDING_EMS_ACCEPTANCE","evaluated_branch":obs.get("evaluated_branch"),
 "evidence_id":eid,"evidence_sha256":sha(p["live_evidence"]),"result_sha256":sha(p["live_result"]),
 "contract_freeze_sha256":sha(p["contract_freeze"]),"errors":errors
}
out=rp(root,spec["certification_output"]);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(cert,indent=2),encoding="utf-8")
print(json.dumps(cert,indent=2));raise SystemExit(0 if not errors else 1)
