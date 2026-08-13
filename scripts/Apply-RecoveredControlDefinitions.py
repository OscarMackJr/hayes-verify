import argparse,csv,json,shutil
from pathlib import Path
import yaml

TARGETS={
"EMS-CTRL-001","EMS-CTRL-002","EMS-CTRL-003","EMS-CTRL-004","EMS-CTRL-005",
"EMS-CTRL-006","EMS-CTRL-007","EMS-CTRL-008","EMS-CTRL-016",
"EMS-CTRL-055","EMS-CTRL-056","EMS-CTRL-057","EMS-CTRL-058","EMS-CTRL-059","EMS-CTRL-060"
}

def meaningful(s):
    import re
    s=(s or "").strip()
    return bool(s and not re.fullmatch(r"Control\s+\d{3}",s,re.I))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--catalog",required=True)
    ap.add_argument("--recovered",required=True)
    ap.add_argument("--report",required=True)
    a=ap.parse_args()

    with Path(a.recovered).open(encoding="utf-8-sig",newline="") as fh:
        rec={r["control_id"]:r for r in csv.DictReader(fh) if r.get("auto_apply","").lower()=="true"}

    path=Path(a.catalog)
    data=yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    backup=path.with_suffix(path.suffix+".pre-definition-recovery.bak")
    shutil.copy2(path,backup)

    changed=[]
    def walk(x):
        if isinstance(x,dict):
            cid=x.get("control_id") or x.get("id")
            if cid in rec:
                r=rec[cid]
                old_name=x.get("control_name") or x.get("name") or x.get("title") or ""
                if meaningful(r["recovered_name"]):
                    if "control_name" in x:x["control_name"]=r["recovered_name"]
                    elif "name" in x:x["name"]=r["recovered_name"]
                    else:x["control_name"]=r["recovered_name"]
                if r["recovered_description"]:
                    if "description" in x:x["description"]=r["recovered_description"]
                    else:x["description"]=r["recovered_description"]
                x["definition_recovery_source"]=r["source_file"]
                x["definition_recovery_confidence"]=float(r["confidence"])
                changed.append({"control_id":cid,"before_name":old_name,"after_name":r["recovered_name"],"source":r["source_file"]})
            for v in x.values():walk(v)
        elif isinstance(x,list):
            for v in x:walk(v)
    walk(data)

    path.write_text(yaml.safe_dump(data,sort_keys=False),encoding="utf-8")
    report={"changed_count":len(changed),"changes":changed,"backup":str(backup)}
    Path(a.report).write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))

if __name__=="__main__":main()
