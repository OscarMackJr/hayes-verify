import argparse,csv,json,re
from pathlib import Path

def classify(path):
    low=str(path).lower().replace("/","\\")
    name=Path(path).name.lower()

    if any(x in name for x in [
        "effective_compliance","repository_control_compliance","compliance_postpolicy",
        "inheritance_impact_report","qualification_summary","collector_report"
    ]):
        return "PRIOR_COMPLIANCE_RESULT","Derived compliance/result artifact cannot prove AI governance operation."

    if any(x in low for x in [
        "\\generated\\wave2\\higher-scope-collectors\\ai-governance\\",
        "\\generated\\wave2\\higher-scope-evidence\\"
    ]):
        return "GENERATED_PROPOSAL","Generated discovery/collector output is not primary operating evidence."

    if any(x in name for x in [
        "control_catalog","control_registry","control_scope_registry","taxonomy",
        "schema","policy","standard","guideline","requirements","architecture"
    ]):
        return "DEFINITIONAL","Defines requirements or expectations but does not prove execution."

    if any(x in name for x in [
        "approval","decision","adjudication","exception","waiver","review_queue","review-decision"
    ]):
        return "DECISIONAL","Decision evidence may support governance but does not independently prove operation."

    operating_tokens = [
        "inventory","assessment","review_record","review-record","security_review","security-review",
        "model_risk","model-risk","attestation","audit","register","log","finding","evidence",
        "approved_platforms","approved-platforms","attribution","trace","report","record"
    ]
    if any(tok in name for tok in operating_tokens):
        return "OPERATING_EVIDENCE","Artifact name indicates retained operating record/evidence."

    if any(x in low for x in ["\\evidence\\","\\reviews\\","\\assessments\\","\\registers\\"]):
        return "OPERATING_EVIDENCE","Artifact resides in controlled operating-evidence location."

    return "UNKNOWN","Source cannot be safely treated as operating evidence."

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--envelopes",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()

    rows=[]
    for line in Path(a.envelopes).read_text(encoding="utf-8").splitlines():
        if not line.strip(): continue
        e=json.loads(line)
        for assertion,detail in e.get("assertions",{}).items():
            for src in detail.get("evidence_paths",[]) or []:
                cls,reason=classify(src)
                rows.append({
                    "control_id":e["control_id"],
                    "control_name":e["control_name"],
                    "scope":e["scope"],
                    "assertion":assertion,
                    "source_path":src,
                    "source_class":cls,
                    "classification_reason":reason
                })

    fields=["control_id","control_name","scope","assertion","source_path","source_class","classification_reason"]
    with Path(a.out).open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=fields);w.writeheader();w.writerows(rows)

    counts={}
    for r in rows: counts[r["source_class"]]=counts.get(r["source_class"],0)+1
    print(json.dumps({"row_count":len(rows),"source_class_counts":counts},indent=2))

if __name__=="__main__":main()
