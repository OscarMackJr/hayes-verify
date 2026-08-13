import argparse,csv,json
from pathlib import Path
ap=argparse.ArgumentParser()
ap.add_argument("--ems-root",required=True)
ap.add_argument("--review-queue",required=True)
a=ap.parse_args()
ems=Path(a.ems_root).resolve()
rows=list(csv.DictReader(Path(a.review_queue).open(encoding="utf-8-sig",newline="")))
parent=ems.parent
result={}
for name in sorted({r["repository_name"] for r in rows}):
    if name.lower()=="ems":
        result[name]=str(ems)
        continue
    found=""
    for c in (parent/name,parent/name.lower()):
        if c.exists() and c.is_dir():
            found=str(c.resolve());break
    result[name]=found
print(json.dumps(result,indent=2))
