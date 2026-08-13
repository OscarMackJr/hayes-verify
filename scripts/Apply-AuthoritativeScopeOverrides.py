import argparse,csv,json
from pathlib import Path

ALLOWED_SCOPES={"REPOSITORY","SERVICE","APPLICATION","PLATFORM","ORGANIZATION","EMS"}
ALLOWED_DECISIONS={"APPROVED","RECLASSIFY"}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--queue",required=True)
    ap.add_argument("--overrides",required=True)
    ap.add_argument("--out",required=True)
    ap.add_argument("--report",required=True)
    a=ap.parse_args()

    with Path(a.queue).open(encoding="utf-8-sig",newline="") as fh:
        rows=list(csv.DictReader(fh))

    ov=json.loads(Path(a.overrides).read_text(encoding="utf-8"))
    decisions=ov["decisions"]
    qmap={r["control_id"]:r for r in rows}

    errors=[]
    applied=[]

    for cid,d in decisions.items():
        if cid not in qmap:
            errors.append(f"{cid}: not present in resolved adjudication queue")
            continue

        decision=d["decision"]
        scope=d["scope"]

        if decision not in ALLOWED_DECISIONS:
            errors.append(f"{cid}: invalid decision {decision}")
            continue
        if scope not in ALLOWED_SCOPES:
            errors.append(f"{cid}: invalid scope {scope}")
            continue

        r=qmap[cid]
        before_decision=r.get("reviewer_decision","")
        before_scope=r.get("proposed_scope","") or r.get("current_scope","")

        r["reviewer_decision"]=decision
        r["proposed_scope"]=scope
        r["reviewer_rationale"]=d["rationale"]
        r["reviewer"]=ov["reviewer"]
        r["review_date"]=ov["review_date"]

        applied.append({
            "control_id":cid,
            "before_decision":before_decision,
            "before_scope":before_scope,
            "after_decision":decision,
            "after_scope":scope
        })

    # Ensure no deferred/unreviewed rows remain.
    deferred=[r["control_id"] for r in rows if (r.get("reviewer_decision") or "").strip()=="DEFER"]
    blank=[r["control_id"] for r in rows if not (r.get("reviewer_decision") or "").strip()]

    if deferred:
        errors.append("DEFER remains for: "+", ".join(sorted(deferred)))
    if blank:
        errors.append("Blank reviewer_decision remains for: "+", ".join(sorted(blank)))

    report={
        "status":"PASS" if not errors else "FAIL",
        "override_count":len(decisions),
        "applied_count":len(applied),
        "applied":applied,
        "remaining_deferred_count":len(deferred),
        "remaining_blank_count":len(blank),
        "errors":errors
    }

    Path(a.report).parent.mkdir(parents=True,exist_ok=True)
    Path(a.report).write_text(json.dumps(report,indent=2),encoding="utf-8")

    if errors:
        print(json.dumps(report,indent=2))
        raise SystemExit(1)

    out=Path(a.out)
    with out.open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=list(rows[0].keys()))
        w.writeheader();w.writerows(rows)

    print(json.dumps(report,indent=2))

if __name__=="__main__":main()
