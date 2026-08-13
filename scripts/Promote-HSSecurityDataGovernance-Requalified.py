import argparse,csv,json,shutil
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--qualified",required=True)
ap.add_argument("--matrix",required=True)
ap.add_argument("--evidence-root",required=True)
ap.add_argument("--report",required=True)
a=ap.parse_args()

with Path(a.qualified).open(encoding="utf-8-sig",newline="") as f:
    q=list(csv.DictReader(f))
with Path(a.matrix).open(encoding="utf-8-sig",newline="") as f:
    matrix=list(csv.DictReader(f))

by={}
for r in matrix:
    by.setdefault(r["control_id"],[]).append(r)

folder=Path(a.evidence_root)/"organization"
folder.mkdir(parents=True,exist_ok=True)
promoted=[]; skipped=[]

for r in q:
    cid=r["control_id"]
    if str(r["promotion_eligible"]).lower()!="true":
        skipped.append({"control_id":cid,"reason":"Not promotion eligible after requalification"})
        continue
    refs=[]
    for x in by.get(cid,[]):
        refs.extend(s for s in x.get("operating_sources","").split(";") if s)
    dest=folder/f"{cid}.yaml"
    if dest.exists():
        shutil.copy2(dest,dest.with_suffix(dest.suffix+".pre-sdg-2B26a.bak"))
    payload={
        "control_id":cid,
        "scope":"ORGANIZATION",
        "status":"PASS",
        "authority_id":"SECURITY-DATA-GOVERNANCE",
        "evidence_class":"OPERATING_EVIDENCE",
        "evidence_references":sorted(set(refs)),
        "notes":"Promoted by Wave 2B.2.6a after register-backed requalification."
    }
    dest.write_text(json.dumps(payload,indent=2),encoding="utf-8")
    promoted.append({"control_id":cid,"destination":str(dest)})

result={"promoted_count":len(promoted),"skipped_count":len(skipped),"promoted":promoted,"skipped":skipped}
Path(a.report).write_text(json.dumps(result,indent=2),encoding="utf-8")
print(json.dumps(result,indent=2))
