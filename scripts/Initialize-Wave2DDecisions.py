import argparse,csv,json
from pathlib import Path
ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--spec",required=True)
a=ap.parse_args()
root=Path(a.root).resolve()
spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))
controls=list(csv.DictReader((root/spec["candidate_controls"]).open(encoding="utf-8-sig",newline="")))
targets=list(csv.DictReader((root/spec["candidate_targets"]).open(encoding="utf-8-sig",newline="")))
control_dec=root/spec["control_decisions"]
target_dec=root/spec["target_decisions"]
control_dec.parent.mkdir(parents=True,exist_ok=True)
if not control_dec.exists():
    with control_dec.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["control_id","control_name","decision","rationale","decision_owner"])
        w.writeheader()
        for r in controls:w.writerow({"control_id":r["control_id"],"control_name":r["control_name"],"decision":"UNDECIDED","rationale":"","decision_owner":""})
if not target_dec.exists():
    with target_dec.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["target_id","repository_name","decision","rationale","decision_owner"])
        w.writeheader()
        for r in targets:w.writerow({"target_id":r["target_id"],"repository_name":r["repository_name"],"decision":"UNDECIDED","rationale":"","decision_owner":""})
print(json.dumps({"status":"PASS","control_decision_rows":len(controls),"target_decision_rows":len(targets),"automatic_inclusion":False},indent=2))
