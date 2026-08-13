import argparse,csv,json,re
from pathlib import Path

def classify(path):
    p=path.lower().replace("/","\\")
    name=Path(path).name.lower()

    if "generated\\wave2\\higher-scope-evidence\\proposed_evidence_records" in p:
        return "GENERATED_PROPOSAL","Generated candidate evidence is never primary proof."

    if "effective_compliance" in name or "repository_control_compliance" in name or "compliance" in name:
        return "PRIOR_COMPLIANCE_RESULT","Prior compliance output is circular for higher-scope reevaluation."

    if any(x in name for x in [
        "control_catalog","control_registry","control_scope_registry","control_scope_taxonomy",
        "inheritance_policy","evidence_authority_registry","schema","mapping","policy_applicability"
    ]):
        return "DEFINITIONAL","Catalog/registry/schema/policy material defines expectations but does not prove control operation."

    if any(x in name for x in [
        "scope_adjudication","adjudication_queue","authoritative_scope_overrides",
        "policy_review_queue","policy_decisions","exception"
    ]):
        return "DECISIONAL","Decision/adjudication evidence supports governance but is not primary operating evidence."

    operating_terms = [
        "validation","validator","manifest","sha256","hash","review","minutes","kpi",
        "scan","audit","retention","release","baseline","evidence","corrective",
        "lessons","history","traceability","artifact","report","test"
    ]

    # Avoid over-promoting policy/docs merely because they contain 'review'.
    if any(x in p for x in ["\\releases\\","\\release\\","\\evidence\\"]):
        if any(t in name for t in operating_terms):
            return "OPERATING_EVIDENCE","Controlled release/evidence artifact with operating-evidence characteristics."

    if any(t in name for t in operating_terms):
        return "OPERATING_EVIDENCE","Artifact name indicates direct validation/review/audit/retention/test evidence."

    if "\\docs\\" in p and any(x in name for x in ["policy","standard","procedure","architecture","readme"]):
        return "DEFINITIONAL","Documentation defines process or policy but does not alone prove execution."

    return "UNKNOWN","Source could not be safely classified as operating evidence."

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--candidates",required=True)
    ap.add_argument("--policy",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()

    policy=json.loads(Path(a.policy).read_text(encoding="utf-8"))
    eligible_map={k:v["primary_evidence_eligible"] for k,v in policy["source_classes"].items()}

    with Path(a.candidates).open(encoding="utf-8-sig",newline="") as fh:
        rows=list(csv.DictReader(fh))

    for r in rows:
        cls,reason=classify(r["source_file"])
        r["source_class"]=cls
        r["primary_evidence_eligible"]=eligible_map.get(cls,False)
        r["source_class_reason"]=reason

    fields=list(rows[0].keys()) if rows else []
    with Path(a.out).open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=fields);w.writeheader();w.writerows(rows)

    counts={}
    for r in rows:
        counts[r["source_class"]]=counts.get(r["source_class"],0)+1
    print(json.dumps({"row_count":len(rows),"source_class_counts":counts},indent=2))

if __name__=="__main__":main()
