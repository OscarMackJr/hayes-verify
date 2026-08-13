import argparse,csv,json
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--spec",required=True)
a=ap.parse_args()

root=Path(a.root).resolve()
spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))
cand=list(csv.DictReader((root/spec["candidate_controls"]).open(encoding="utf-8-sig",newline="")))
dec_path=root/spec["control_decisions"]

existing={}
if dec_path.exists():
    for r in csv.DictReader(dec_path.open(encoding="utf-8-sig",newline="")):
        existing[r["control_id"]]=r

org_scopes={x.upper() for x in spec["control_policy"]["organization_scopes"]}
repo_scopes={x.upper() for x in spec["control_policy"]["repository_scopes"]}

rows=[]
for r in cand:
    cid=r["control_id"]
    scope=(r.get("scope") or "").strip().upper()

    prev=existing.get(cid,{})
    prev_dec=(prev.get("decision") or "").strip().upper()

    # Preserve explicit human decisions.
    if prev_dec in {"INCLUDE","EXCLUDE"}:
        decision=prev_dec
        rationale=prev.get("rationale","")
        owner=prev.get("decision_owner","")
        source="PRESERVED_EXPLICIT_DECISION"
    else:
        if scope in org_scopes:
            decision=spec["control_policy"]["default_org_decision"]
            rationale=f"Included by Wave 2D policy for {scope or 'organization'}-scope control."
            owner="Engineering Management"
            source="POLICY_ORGANIZATION_SCOPE"
        elif scope in repo_scopes:
            decision=spec["control_policy"]["default_repository_decision"]
            rationale=f"Included by Wave 2D policy for repository-applicable {scope or 'repository'} control."
            owner="Engineering Management"
            source="POLICY_REPOSITORY_SCOPE"
        else:
            # Catalogs sometimes leave scope blank. Treat blank/unknown as review-required.
            decision="REVIEW_REQUIRED"
            rationale="Control scope is blank or not recognized by the Wave 2D adjudication policy."
            owner="Engineering Management"
            source="POLICY_UNKNOWN_SCOPE"

    rows.append({
        "control_id":cid,
        "control_name":r.get("control_name",""),
        "decision":decision,
        "rationale":rationale,
        "decision_owner":owner,
        "adjudication_source":source,
        "catalog_scope":scope
    })

with dec_path.open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=["control_id","control_name","decision","rationale","decision_owner","adjudication_source","catalog_scope"])
    w.writeheader();w.writerows(rows)

print(json.dumps({
    "status":"PASS",
    "control_count":len(rows),
    "include_count":sum(1 for r in rows if r["decision"]=="INCLUDE"),
    "exclude_count":sum(1 for r in rows if r["decision"]=="EXCLUDE"),
    "review_required_count":sum(1 for r in rows if r["decision"]=="REVIEW_REQUIRED"),
    "undecided_count":sum(1 for r in rows if r["decision"]=="UNDECIDED")
},indent=2))
