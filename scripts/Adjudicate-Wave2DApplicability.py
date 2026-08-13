import argparse,csv,json
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--spec",required=True)
a=ap.parse_args()

root=Path(a.root).resolve()
spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))
matrix=list(csv.DictReader((root/spec["matrix_file"]).open(encoding="utf-8-sig",newline="")))
rules=json.loads((root/spec["rules_output"]).read_text(encoding="utf-8"))
repo_attrs=rules.get("repository_attributes",{})

decision_path=root/spec["decisions_output"]
existing={}
if decision_path.exists():
    for r in csv.DictReader(decision_path.open(encoding="utf-8-sig",newline="")):
        key=(r["control_id"],r["target_id"])
        existing[key]=r

def truthy(v):
    if isinstance(v,bool): return v
    return str(v).strip().lower() in {"true","1","yes","y"}

def text_blob(attrs):
    vals=[]
    for k,v in attrs.items():
        if isinstance(v,(str,int,float,bool)):
            vals.append(f"{k}:{v}")
        elif isinstance(v,list):
            vals.extend(str(x) for x in v)
    return " ".join(vals).lower()

def classify(row):
    cid=row["control_id"]
    cname=(row.get("control_name") or "").lower()
    target=row["target_id"]
    repo=(row.get("repository_name") or "").lower()
    attrs=repo_attrs.get(target,{})
    blob=text_blob(attrs)

    # EMS repository: organization/EMS controls plus general engineering controls apply.
    if repo=="ems" or target=="REPO-EMS":
        return "APPLICABLE","EMS repository is the authoritative target for EMS/organization controls and its own engineering controls.","POLICY_EMS_TARGET"

    # Organization / governance / controlled-doc controls generally apply at EMS level, not per product repo.
    org_ids=set([f"EMS-CTRL-{i:03d}" for i in list(range(1,9))+list(range(49,61))+list(range(67,81))])
    if cid in org_ids:
        # Some in these ranges are actually product-facing AI/agent controls; handle AI first below.
        if cid in {f"EMS-CTRL-{i:03d}" for i in range(49,61)}:
            ai_enabled=truthy(attrs.get("ai_enabled"))
            if ai_enabled:
                return "APPLICABLE","AI control applies because repository classification indicates ai_enabled=true.","POLICY_AI_ENABLED"
            if "ai" in blob or "llm" in blob or "agent" in blob:
                return "APPLICABLE","AI control applies because repository metadata indicates AI/agent usage.","POLICY_AI_METADATA"
            return "NOT_APPLICABLE","AI-specific control is not applicable because repository classification does not indicate AI enablement.","POLICY_AI_DISABLED"
        return "NOT_APPLICABLE","Organization/EMS-level control is evaluated at REPO-EMS rather than separately for each product repository.","POLICY_ORG_ONLY"

    # Database-specific controls.
    if cid in {"EMS-CTRL-061","EMS-CTRL-062","EMS-CTRL-064"}:
        if any(x in blob for x in ["mssql","postgres","postgresql","database","sql","aurora","rds","snowflake"]):
            return "APPLICABLE","Database control applies because repository metadata indicates database technology or responsibility.","POLICY_DATABASE"
        return "REVIEW_REQUIRED","Database applicability cannot be proven from repository metadata.","POLICY_DATABASE_UNKNOWN"

    # IaC/cloud-specific controls.
    if cid in {"EMS-CTRL-041","EMS-CTRL-042","EMS-CTRL-043","EMS-CTRL-044","EMS-CTRL-045","EMS-CTRL-048"}:
        if any(x in blob for x in ["terraform","iac","aws","azure","cloud"]):
            return "APPLICABLE","Platform/IaC control applies because repository metadata indicates cloud or infrastructure-as-code responsibility.","POLICY_IAC"
        return "REVIEW_REQUIRED","IaC/cloud applicability cannot be proven from repository metadata.","POLICY_IAC_UNKNOWN"

    # Production / service / recovery controls.
    if cid in {"EMS-CTRL-029","EMS-CTRL-030","EMS-CTRL-040","EMS-CTRL-046","EMS-CTRL-047","EMS-CTRL-066"}:
        if truthy(attrs.get("production")):
            return "APPLICABLE","Service/production control applies because repository is classified as production.","POLICY_PRODUCTION"
        if str(attrs.get("production","")).strip()!="":
            return "NOT_APPLICABLE","Service/production control is not applicable because repository is classified non-production.","POLICY_NON_PRODUCTION"
        return "REVIEW_REQUIRED","Production classification is missing for this service/production control.","POLICY_PRODUCTION_UNKNOWN"

    # Data-specific controls.
    if cid in {"EMS-CTRL-063","EMS-CTRL-065"}:
        if truthy(attrs.get("contains_customer_data")) or "customer data" in blob or "confidential" in blob or "restricted" in blob:
            return "APPLICABLE","Data-governance control applies because repository metadata indicates customer/sensitive data.","POLICY_DATA"
        return "REVIEW_REQUIRED","Data-governance applicability cannot be proven from repository metadata.","POLICY_DATA_UNKNOWN"

    # General repository engineering controls.
    return "APPLICABLE","General engineering/repository control applies to registered Wave 2D product repository.","POLICY_DEFAULT_REPOSITORY"

rows=[]
for r in matrix:
    key=(r["control_id"],r["target_id"])
    prev=existing.get(key,{})
    prev_dec=(prev.get("decision") or "").strip().upper()

    if prev_dec in {"APPLICABLE","NOT_APPLICABLE"} and (prev.get("decision_source") or "").startswith("HUMAN_"):
        decision=prev_dec
        rationale=prev.get("rationale","")
        owner=prev.get("decision_owner","")
        source=prev.get("decision_source","HUMAN_OVERRIDE")
    else:
        decision,rationale,source=classify(r)
        owner="Engineering Management"

    rows.append({
        "wave":"2D",
        "control_id":r["control_id"],
        "control_name":r["control_name"],
        "target_id":r["target_id"],
        "repository_name":r["repository_name"],
        "decision":decision,
        "rationale":rationale,
        "decision_owner":owner,
        "decision_source":source
    })

with decision_path.open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=["wave","control_id","control_name","target_id","repository_name","decision","rationale","decision_owner","decision_source"])
    w.writeheader();w.writerows(rows)

print(json.dumps({
    "status":"PASS",
    "row_count":len(rows),
    "applicable_count":sum(1 for r in rows if r["decision"]=="APPLICABLE"),
    "not_applicable_count":sum(1 for r in rows if r["decision"]=="NOT_APPLICABLE"),
    "review_required_count":sum(1 for r in rows if r["decision"]=="REVIEW_REQUIRED")
},indent=2))
