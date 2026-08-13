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

allowed={"INCLUDE","EXCLUDE","REVIEW_REQUIRED","UNDECIDED"}
errors=[]
for r in controls:
    d=(r.get("decision") or "").strip().upper()
    if d not in allowed: errors.append(f"control {r.get('control_id')}: invalid decision={d}")
    if d in {"INCLUDE","EXCLUDE"} and not (r.get("rationale") or "").strip():
        errors.append(f"control {r.get('control_id')}: rationale required")
for r in targets:
    d=(r.get("decision") or "").strip().upper()
    if d not in allowed: errors.append(f"target {r.get('target_id')}: invalid decision={d}")
    if d in {"INCLUDE","EXCLUDE"} and not (r.get("rationale") or "").strip():
        errors.append(f"target {r.get('target_id')}: rationale required")

review=[r for r in controls+targets if (r.get("decision") or "").strip().upper()=="REVIEW_REQUIRED"]
undec=[r for r in controls+targets if (r.get("decision") or "").strip().upper()=="UNDECIDED"]

if spec["finalization"]["require_zero_review_required"] and review:
    errors.append(f"{len(review)} REVIEW_REQUIRED row(s) remain")
if spec["finalization"]["require_zero_undecided"] and undec:
    errors.append(f"{len(undec)} UNDECIDED row(s) remain")

included_controls=[r for r in controls if r["decision"].strip().upper()=="INCLUDE"]
excluded_controls=[r for r in controls if r["decision"].strip().upper()=="EXCLUDE"]
included_targets=[r for r in targets if r["decision"].strip().upper()=="INCLUDE"]
excluded_targets=[r for r in targets if r["decision"].strip().upper()=="EXCLUDE"]

status="PASS" if not errors else "WARNING"

scope={
    "wave":"2D",
    "defined_at_utc":datetime.now(timezone.utc).isoformat(),
    "scope_count":len(included_controls),
    "controls":[{
        "control_id":r["control_id"],
        "control_name":r["control_name"],
        "decision":"INCLUDE",
        "rationale":r["rationale"],
        "decision_owner":r["decision_owner"]
    } for r in included_controls],
    "excluded_control_count":len(excluded_controls),
    "review_required_count":sum(1 for r in controls if r["decision"].strip().upper()=="REVIEW_REQUIRED"),
    "undecided_control_count":sum(1 for r in controls if r["decision"].strip().upper()=="UNDECIDED"),
    "implicit_carry_forward_performed":False,
    "status":status
}
(root/spec["scope_output"]).write_text(json.dumps(scope,indent=2),encoding="utf-8")

population={
    "wave":"2D",
    "defined_at_utc":datetime.now(timezone.utc).isoformat(),
    "population_count":len(included_targets),
    "targets":[{
        "target_id":r["target_id"],
        "repository_name":r["repository_name"],
        "decision":"INCLUDE",
        "rationale":r["rationale"],
        "decision_owner":r["decision_owner"]
    } for r in included_targets],
    "excluded_target_count":len(excluded_targets),
    "review_required_count":sum(1 for r in targets if r["decision"].strip().upper()=="REVIEW_REQUIRED"),
    "undecided_target_count":sum(1 for r in targets if r["decision"].strip().upper()=="UNDECIDED"),
    "evaluation_performed":False,
    "implicit_carry_forward_performed":False,
    "status":status
}
(root/spec["population_output"]).write_text(json.dumps(population,indent=2),encoding="utf-8")

report={
    "wave":"2D",
    "generated_at_utc":datetime.now(timezone.utc).isoformat(),
    "status":status,
    "control_decision_count":len(controls),
    "target_decision_count":len(targets),
    "included_control_count":len(included_controls),
    "excluded_control_count":len(excluded_controls),
    "included_target_count":len(included_targets),
    "excluded_target_count":len(excluded_targets),
    "review_required_count":len(review),
    "undecided_count":len(undec),
    "errors":errors,
    "evaluation_performed":False,
    "promotion_performed":False
}
out=root/spec["adjudication_report"]
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps(report,indent=2))

raise SystemExit(0 if not errors else 2)
