import argparse,csv,json
from pathlib import Path
from datetime import datetime,timezone
ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--spec",required=True)
a=ap.parse_args()
root=Path(a.root).resolve()
spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))
controls=list(csv.DictReader((root/spec["control_decisions"]).open(encoding="utf-8-sig",newline="")))
targets=list(csv.DictReader((root/spec["target_decisions"]).open(encoding="utf-8-sig",newline="")))
valid={"INCLUDE","EXCLUDE","UNDECIDED"}
errors=[]
for r in controls:
    d=(r.get("decision") or "").strip().upper()
    if d not in valid: errors.append(f"control {r.get('control_id')}: invalid decision {d}")
    if d in {"INCLUDE","EXCLUDE"} and not (r.get("rationale") or "").strip(): errors.append(f"control {r.get('control_id')}: rationale required for {d}")
for r in targets:
    d=(r.get("decision") or "").strip().upper()
    if d not in valid: errors.append(f"target {r.get('target_id')}: invalid decision {d}")
    if d in {"INCLUDE","EXCLUDE"} and not (r.get("rationale") or "").strip(): errors.append(f"target {r.get('target_id')}: rationale required for {d}")
if errors:
    print(json.dumps({"status":"FAIL","errors":errors},indent=2));raise SystemExit(1)

ic=[r for r in controls if r["decision"].strip().upper()=="INCLUDE"]
ec=[r for r in controls if r["decision"].strip().upper()=="EXCLUDE"]
uc=[r for r in controls if r["decision"].strip().upper()=="UNDECIDED"]
it=[r for r in targets if r["decision"].strip().upper()=="INCLUDE"]
et=[r for r in targets if r["decision"].strip().upper()=="EXCLUDE"]
ut=[r for r in targets if r["decision"].strip().upper()=="UNDECIDED"]

scope={"wave":"2D","defined_at_utc":datetime.now(timezone.utc).isoformat(),"baseline_tag":spec["baseline_tag"],"scope_count":len(ic),"controls":[{"control_id":r["control_id"],"control_name":r["control_name"],"rationale":r["rationale"],"decision_owner":r["decision_owner"]} for r in ic],"excluded_control_count":len(ec),"undecided_control_count":len(uc),"implicit_carry_forward_performed":False,"status":"PASS" if not uc else "WARNING"}
(root/spec["scope_output"]).write_text(json.dumps(scope,indent=2),encoding="utf-8")

pop={"wave":"2D","defined_at_utc":datetime.now(timezone.utc).isoformat(),"population_count":len(it),"targets":[{"target_id":r["target_id"],"repository_name":r["repository_name"],"rationale":r["rationale"],"decision_owner":r["decision_owner"]} for r in it],"excluded_target_count":len(et),"undecided_target_count":len(ut),"implicit_carry_forward_performed":False,"evaluation_performed":False,"status":"PASS" if not ut else "WARNING"}
(root/spec["population_output"]).write_text(json.dumps(pop,indent=2),encoding="utf-8")

summary={"wave":"2D","generated_at_utc":datetime.now(timezone.utc).isoformat(),"status":"PASS" if not uc and not ut else "WARNING","candidate_control_count":len(controls),"candidate_target_count":len(targets),"included_control_count":len(ic),"excluded_control_count":len(ec),"undecided_control_count":len(uc),"included_target_count":len(it),"excluded_target_count":len(et),"undecided_target_count":len(ut),"evaluation_performed":False,"promotion_performed":False,"implicit_carry_forward_performed":False}
out=root/spec["summary_output"];out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(summary,indent=2),encoding="utf-8")
print(json.dumps(summary,indent=2))
