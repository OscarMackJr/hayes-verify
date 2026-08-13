import argparse,csv,json
from pathlib import Path
from datetime import datetime,timezone
ap=argparse.ArgumentParser()
ap.add_argument("--ems-root",required=True);ap.add_argument("--spec",required=True);ap.add_argument("--outdir",required=True)
a=ap.parse_args()
root=Path(a.ems_root); spec=json.loads(Path(a.spec).read_text(encoding="utf-8")); out=Path(a.outdir); out.mkdir(parents=True,exist_ok=True)
cert_path=root/"generated"/"wave2"/"closeout-certification"/"wave2b_certification.json"
if not cert_path.exists(): raise SystemExit(f"Wave 2B certification not found: {cert_path}")
cert=json.loads(cert_path.read_text(encoding="utf-8"))
if cert.get("status")!="PASS": raise SystemExit("Wave 2B certification is not PASS.")
expected={c["control_id"] for c in spec["controls"]}; actual=set(cert.get("open_remediation_controls",[]))
if expected!=actual: raise SystemExit(f"Wave 2C intake set does not match Wave 2B remediation set. missing={sorted(expected-actual)} extra={sorted(actual-expected)}")
queue=[]; req=[]
for c in spec["controls"]:
    queue.append({"control_id":c["control_id"],"control_name":c["control_name"],"scope":c["scope"],"intake_classification":c["intake_classification"],
                  "owner_role":c["default_owner_role"],"wave2b_gap":c["wave2b_gap"],"current_status":"WARNING","disposition":"REMEDIATE",
                  "remediation_state":"OPEN","promotion_eligible":"False","promotion_status":"NOT_PROMOTED","evidence_record_count":"0",
                  "evidence_sufficiency":"INSUFFICIENT","next_action":"CAPTURE_OPERATING_EVIDENCE"})
    req.append({"control_id":c["control_id"],"control_name":c["control_name"],"scope":c["scope"],"intake_classification":c["intake_classification"],
                "required_evidence":c["required_evidence"],"minimum_evidence_class":"OPERATING_EVIDENCE","empty_template_sufficient":"False",
                "policy_or_definition_sufficient":"False","prior_compliance_result_sufficient":"False","promotion_mode":"FAIL_CLOSED"})
for name,rows in [("remediation_queue.csv",queue),("evidence_requirements.csv",req)]:
    with (out/name).open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
counts={}
for r in queue: counts[r["intake_classification"]]=counts.get(r["intake_classification"],0)+1
summary={"wave":"2C","initialized_at":datetime.now(timezone.utc).isoformat(),"source_wave2b_certification_state":cert.get("certification_state"),
         "control_count":len(queue),"classification_counts":counts,"open_count":len(queue),"promotion_eligible_count":0,"status":"PASS"}
(out/"remediation_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
init={"wave":"2C","source_release":spec["source_release"],"branch":spec["branch"],"source_certification":str(cert_path),
      "control_ids":sorted(expected),"promotion_policy":"FAIL_CLOSED","promotion_performed":False,"status":"PASS"}
(out/"wave2c_initialization.json").write_text(json.dumps(init,indent=2),encoding="utf-8")
print(json.dumps(summary,indent=2))
