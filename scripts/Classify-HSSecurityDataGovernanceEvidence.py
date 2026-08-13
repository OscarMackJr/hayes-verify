import argparse,csv,json
from pathlib import Path

def classify(path):
    p=Path(path);name=p.name.lower();low=str(p).lower().replace("/","\\")
    if any(x in name for x in ["effective_compliance","repository_control_compliance","qualification_summary","collector_report","inheritance_impact_report"]):
        return "PRIOR_COMPLIANCE_RESULT","Derived compliance/result artifact."
    if "\\generated\\wave2\\higher-scope-collectors\\" in low:
        return "GENERATED_PROPOSAL","Generated collector output is not primary operating evidence."
    if any(x in name for x in ["control_catalog","control_registry","schema","policy","standard","guideline","requirements","architecture"]):
        return "DEFINITIONAL","Defines expectations; does not prove execution."
    if any(x in name for x in ["approval","decision","exception","waiver","adjudication"]):
        return "DECISIONAL","Decision evidence may support governance but does not independently prove operation."
    operating_tokens=["finding","vulnerability","scan","register","inventory","assessment","review","retention","disposition","classification","audit","validation","evidence","report","log"]
    if any(x in name for x in operating_tokens):
        return "OPERATING_EVIDENCE","Artifact name indicates retained operating evidence."
    if any(x in low for x in ["\\evidence\\","\\reviews\\","\\assessments\\","\\registers\\"]):
        return "OPERATING_EVIDENCE","Artifact resides in controlled operating-evidence location."
    return "UNKNOWN","Cannot safely classify as operating evidence."

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--envelopes",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    rows=[]
    for line in Path(a.envelopes).read_text(encoding="utf-8").splitlines():
        if not line.strip():continue
        e=json.loads(line)
        for assertion,d in e["assertions"].items():
            for src in d.get("evidence_paths",[]):
                cls,reason=classify(src)
                rows.append({
                    "control_id":e["control_id"],"control_name":e["control_name"],"scope":e["scope"],
                    "assertion":assertion,"source_path":src,"source_class":cls,"classification_reason":reason
                })
    fields=["control_id","control_name","scope","assertion","source_path","source_class","classification_reason"]
    with Path(a.out).open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    counts={}
    for r in rows:counts[r["source_class"]]=counts.get(r["source_class"],0)+1
    print(json.dumps({"row_count":len(rows),"source_class_counts":counts},indent=2))
if __name__=="__main__":main()
