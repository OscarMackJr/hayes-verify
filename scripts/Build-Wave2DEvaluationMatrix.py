import argparse,csv,json
from pathlib import Path
from datetime import datetime,timezone

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--spec",required=True)
a=ap.parse_args()
root=Path(a.root).resolve()
spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))

scope=json.loads((root/spec["scope_file"]).read_text(encoding="utf-8"))
population=json.loads((root/spec["population_file"]).read_text(encoding="utf-8"))

controls=scope.get("controls",[])
targets=population.get("targets",[])

if len(controls)!=spec["expected_control_count"]:
    raise SystemExit(f"Expected {spec['expected_control_count']} controls, got {len(controls)}")
if len(targets)!=spec["expected_target_count"]:
    raise SystemExit(f"Expected {spec['expected_target_count']} targets, got {len(targets)}")

rows=[]
for c in controls:
    for t in targets:
        rows.append({
            "wave":"2D",
            "control_id":c["control_id"],
            "control_name":c.get("control_name",""),
            "target_id":t["target_id"],
            "repository_name":t.get("repository_name",""),
            "applicability_state":spec["default_applicability_state"],
            "applicability_rationale":"",
            "applicability_owner":"",
            "evaluation_state":"NOT_STARTED",
            "evidence_state":"NOT_COLLECTED",
            "result_state":"NOT_EVALUATED",
            "promotion_state":"NOT_PROMOTED"
        })

out=root/spec["matrix_file"]
out.parent.mkdir(parents=True,exist_ok=True)
fields=["wave","control_id","control_name","target_id","repository_name",
        "applicability_state","applicability_rationale","applicability_owner",
        "evaluation_state","evidence_state","result_state","promotion_state"]
with out.open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=fields)
    w.writeheader();w.writerows(rows)

summary={
    "wave":"2D",
    "generated_at_utc":datetime.now(timezone.utc).isoformat(),
    "status":"PASS",
    "control_count":len(controls),
    "target_count":len(targets),
    "matrix_row_count":len(rows),
    "expected_matrix_row_count":spec["expected_matrix_rows"],
    "coverage_complete":len(rows)==spec["expected_matrix_rows"],
    "default_applicability_state":spec["default_applicability_state"],
    "pending_applicability_count":sum(1 for r in rows if r["applicability_state"]=="PENDING_APPLICABILITY"),
    "evaluation_performed":False,
    "promotion_performed":False
}
(root/spec["matrix_summary"]).write_text(json.dumps(summary,indent=2),encoding="utf-8")
print(json.dumps(summary,indent=2))
