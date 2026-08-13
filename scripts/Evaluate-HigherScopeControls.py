import argparse,json,yaml
from pathlib import Path
from datetime import date

def load_records(root):
    out=[]
    for p in list(Path(root).rglob("*.yaml"))+list(Path(root).rglob("*.yml"))+list(Path(root).rglob("*.json")):
        if p.name.lower()=="readme.md": continue
        try:
            if p.suffix.lower()==".json":
                d=json.loads(p.read_text(encoding="utf-8"))
            else:
                d=yaml.safe_load(p.read_text(encoding="utf-8"))
            if isinstance(d,dict) and d.get("control_id"):
                d["_source_file"]=str(p)
                out.append(d)
        except Exception:
            pass
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--scope-registry",required=True)
    ap.add_argument("--evidence-root",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()

    reg=yaml.safe_load(Path(a.scope_registry).read_text(encoding="utf-8"))
    controls={c["control_id"]:c for c in reg["controls"] if c["scope"] in {"EMS","ORGANIZATION"}}
    records=load_records(a.evidence_root)

    by={}
    for r in records:
        cid=r.get("control_id")
        if cid not in controls:
            continue
        by.setdefault(cid,[]).append(r)

    results=[]
    today=date.today().isoformat()

    for cid,c in controls.items():
        candidates=by.get(cid,[])
        candidates.sort(key=lambda x:x.get("evidence_date",""),reverse=True)
        rec=candidates[0] if candidates else None

        if not rec:
            results.append({
                "control_id":cid,
                "control_name":c["control_name"],
                "scope":c["scope"],
                "status":"NOT_EVALUATED",
                "reason":"HIGHER_SCOPE_EVIDENCE_MISSING",
                "evidence_id":"",
                "evidence_source":""
            })
            continue

        status=rec.get("status","NOT_EVALUATED")
        reason="EVIDENCE_PRESENT" if status!="NOT_EVALUATED" else "HIGHER_SCOPE_EVIDENCE_MISSING"
        results.append({
            "control_id":cid,
            "control_name":c["control_name"],
            "scope":c["scope"],
            "status":status,
            "reason":reason,
            "evidence_id":rec.get("evidence_id",""),
            "evidence_source":rec.get("_source_file",""),
            "authority_id":rec.get("authority_id",""),
            "evidence_date":rec.get("evidence_date",""),
            "evidence_summary":rec.get("evidence_summary","")
        })

    Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    Path(a.out).write_text(json.dumps(results,indent=2),encoding="utf-8")
    print(json.dumps({
        "control_count":len(results),
        "pass":sum(x["status"]=="PASS" for x in results),
        "warning":sum(x["status"]=="WARNING" for x in results),
        "fail":sum(x["status"]=="FAIL" for x in results),
        "not_evaluated":sum(x["status"]=="NOT_EVALUATED" for x in results)
    },indent=2))

if __name__=="__main__":main()
