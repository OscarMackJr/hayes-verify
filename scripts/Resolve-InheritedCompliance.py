import argparse,csv,json
from pathlib import Path
import yaml

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--compliance",required=True)
    ap.add_argument("--scope-registry",required=True)
    ap.add_argument("--higher-scope-results",required=True)
    ap.add_argument("--out",required=True)
    ap.add_argument("--report",required=True)
    a=ap.parse_args()

    reg=yaml.safe_load(Path(a.scope_registry).read_text(encoding="utf-8"))
    scopes={c["control_id"]:c["scope"] for c in reg["controls"]}
    hs=json.loads(Path(a.higher_scope_results).read_text(encoding="utf-8"))
    hmap={x["control_id"]:x for x in hs}

    with Path(a.compliance).open(encoding="utf-8-sig",newline="") as fh:
        rows=list(csv.DictReader(fh))

    changed=[]
    for r in rows:
        cid=r["control_id"]
        scope=scopes.get(cid)
        if scope not in {"EMS","ORGANIZATION"}:
            r.setdefault("effective_status",r["compliance_status"])
            r.setdefault("inheritance_status","")
            r.setdefault("inherited_from_scope","")
            r.setdefault("inherited_control_status","")
            r.setdefault("inheritance_reason","")
            r.setdefault("inherited_evidence_id","")
            continue

        hsrow=hmap.get(cid)
        r["inherited_from_scope"]=scope

        if not hsrow or hsrow["status"]=="NOT_EVALUATED":
            r["effective_status"]="NOT_EVALUATED"
            r["inheritance_status"]="NOT_RESOLVED"
            r["inherited_control_status"]="NOT_EVALUATED"
            r["inheritance_reason"]="HIGHER_SCOPE_EVIDENCE_MISSING"
            r["inherited_evidence_id"]=hsrow.get("evidence_id","") if hsrow else ""
        elif hsrow["status"]=="PASS":
            r["effective_status"]="INHERITED"
            r["inheritance_status"]="INHERITED"
            r["inherited_control_status"]="PASS"
            r["inheritance_reason"]="HIGHER_SCOPE_PASS"
            r["inherited_evidence_id"]=hsrow.get("evidence_id","")
        elif hsrow["status"]=="WARNING":
            r["effective_status"]="WARNING"
            r["inheritance_status"]="INHERITED"
            r["inherited_control_status"]="WARNING"
            r["inheritance_reason"]="HIGHER_SCOPE_WARNING"
            r["inherited_evidence_id"]=hsrow.get("evidence_id","")
        elif hsrow["status"]=="FAIL":
            r["effective_status"]="FAIL"
            r["inheritance_status"]="INHERITED"
            r["inherited_control_status"]="FAIL"
            r["inheritance_reason"]="HIGHER_SCOPE_FAIL"
            r["inherited_evidence_id"]=hsrow.get("evidence_id","")

        if r["effective_status"] != r["compliance_status"]:
            changed.append({
                "repository_name":r["repository_name"],
                "control_id":cid,
                "before":r["compliance_status"],
                "after":r["effective_status"],
                "scope":scope,
                "reason":r["inheritance_reason"]
            })

    fields=[]
    for r in rows:
        for k in r.keys():
            if k not in fields: fields.append(k)

    with Path(a.out).open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=fields)
        w.writeheader();w.writerows(rows)

    report={
        "row_count":len(rows),
        "changed_count":len(changed),
        "inherited_count":sum(r.get("inheritance_status")=="INHERITED" for r in rows),
        "unresolved_higher_scope_count":sum(r.get("inheritance_reason")=="HIGHER_SCOPE_EVIDENCE_MISSING" for r in rows),
        "changes":changed
    }
    Path(a.report).write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))

if __name__=="__main__":main()
