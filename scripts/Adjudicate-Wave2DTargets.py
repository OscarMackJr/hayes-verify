import argparse,csv,json
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--spec",required=True)
a=ap.parse_args()

root=Path(a.root).resolve()
spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))
cand=list(csv.DictReader((root/spec["candidate_targets"]).open(encoding="utf-8-sig",newline="")))
dec_path=root/spec["target_decisions"]

existing={}
if dec_path.exists():
    for r in csv.DictReader(dec_path.open(encoding="utf-8-sig",newline="")):
        existing[r["target_id"]]=r

rows=[]
for r in cand:
    tid=r["target_id"]
    prev=existing.get(tid,{})
    prev_dec=(prev.get("decision") or "").strip().upper()

    if prev_dec in {"INCLUDE","EXCLUDE"}:
        decision=prev_dec
        rationale=prev.get("rationale","")
        owner=prev.get("decision_owner","")
        source="PRESERVED_EXPLICIT_DECISION"
    else:
        decision=spec["target_policy"]["default_decision"]
        rationale="Included because the repository is registered as a current EMS evaluation target."
        owner="Engineering Management"
        source="POLICY_REGISTERED_REPOSITORY"

    rows.append({
        "target_id":tid,
        "repository_name":r.get("repository_name",""),
        "decision":decision,
        "rationale":rationale,
        "decision_owner":owner,
        "adjudication_source":source
    })

with dec_path.open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=["target_id","repository_name","decision","rationale","decision_owner","adjudication_source"])
    w.writeheader();w.writerows(rows)

print(json.dumps({
    "status":"PASS",
    "target_count":len(rows),
    "include_count":sum(1 for r in rows if r["decision"]=="INCLUDE"),
    "exclude_count":sum(1 for r in rows if r["decision"]=="EXCLUDE"),
    "review_required_count":sum(1 for r in rows if r["decision"]=="REVIEW_REQUIRED"),
    "undecided_count":sum(1 for r in rows if r["decision"]=="UNDECIDED")
},indent=2))
