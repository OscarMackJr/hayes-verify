import argparse,csv,json,re
from pathlib import Path

def sufficiency(r):
    cls=r["source_class"]
    conf=float(r.get("confidence") or 0)
    status=r.get("candidate_status","")
    path=r["source_file"].lower()
    name=Path(r["source_file"]).name.lower()
    control=r["control_id"]

    if cls!="OPERATING_EVIDENCE":
        return "INSUFFICIENT",f"{cls} cannot serve as primary operating evidence."

    if conf < 0.90:
        return "INSUFFICIENT",f"Confidence {conf:.2f} is below 0.90."

    if status not in {"PASS","WARNING"}:
        return "INSUFFICIENT",f"Candidate status {status} is not affirmative."

    # Control-family sufficiency checks.
    cid=int(control.split("-")[-1])

    if cid in {67,68,69,70,71,72,75,76,80}:
        required_terms={
            67:["metadata","document"],
            68:["cross","reference"],
            69:["traceability","requirement"],
            70:["revision","history"],
            71:["executive","release"],
            72:["pdf","docx","validation"],
            75:["compliance","scan"],
            76:["corrective","action"],
            80:["annual","review"]
        }[cid]
        joined=(name+" "+path).lower()
        if not all(t in joined for t in required_terms):
            return "REVIEW_REQUIRED","Operating artifact found, but filename/path does not strongly demonstrate this control's specific obligation."

    if cid==16:
        joined=(name+" "+path).lower()
        if not any(t in joined for t in ["manifest","sha256","hash","retention","baseline","release"]):
            return "REVIEW_REQUIRED","CTRL-016 requires integrity/retention evidence such as manifests, hashes, retained releases, or equivalent."

    if cid in {73,74,78}:
        joined=(name+" "+path).lower()
        key={73:"kpi",74:"quarter",78:"lesson"}[cid]
        if key not in joined:
            return "REVIEW_REQUIRED","Review artifact exists but does not clearly correspond to the specific management-review obligation."

    return "SUFFICIENT","Operating evidence is direct, sufficiently specific, and above the confidence threshold."

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--classified",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()

    with Path(a.classified).open(encoding="utf-8-sig",newline="") as fh:
        rows=list(csv.DictReader(fh))

    for r in rows:
        s,reason=sufficiency(r)
        r["sufficiency"]=s
        r["sufficiency_reason"]=reason
        r["promotion_eligible"]=(
            r["source_class"]=="OPERATING_EVIDENCE"
            and float(r.get("confidence") or 0)>=0.90
            and s=="SUFFICIENT"
            and r.get("candidate_status") in {"PASS","WARNING"}
        )

    fields=list(rows[0].keys()) if rows else []
    with Path(a.out).open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=fields);w.writeheader();w.writerows(rows)

    summary={}
    for r in rows:
        summary[r["sufficiency"]]=summary.get(r["sufficiency"],0)+1
    print(json.dumps({"row_count":len(rows),"sufficiency_counts":summary,
                      "promotion_eligible_count":sum(str(r["promotion_eligible"]).lower()=="true" for r in rows)},indent=2))

if __name__=="__main__":main()
