import argparse,json,csv
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--ems-root",required=True)
ap.add_argument("--manifest",required=True)
ap.add_argument("--report",required=True)
ap.add_argument("--provenance",required=True)
a=ap.parse_args()

root=Path(a.ems_root).resolve()
m=json.loads(Path(a.manifest).read_text(encoding="utf-8"))
errors=[]
prov=[]

if m.get("source_count",0)<1:
    errors.append("No controlled sources in manifest.")
if m.get("record_count")!=m.get("source_count"):
    errors.append("Not every controlled source has a generation record.")

required_fields=["source_path","source_sha256","docx_path","docx_sha256","pdf_path","pdf_sha256","generator","generated_at_utc"]

for r in m.get("records",[]):
    missing=[f for f in required_fields if not r.get(f)]
    if missing:
        errors.append(f"{r.get('source_path')}: missing provenance fields {missing}")
    for key in ("docx_path","pdf_path"):
        p=root/r.get(key,"")
        if not p.exists():
            errors.append(f"{r.get('source_path')}: missing {key} output {p}")
        elif p.stat().st_size<=0:
            errors.append(f"{r.get('source_path')}: zero-byte output {p}")
    prov.append({k:r.get(k,"") for k in required_fields})

if m.get("status")!="PASS":
    errors.append("Generation manifest status is not PASS.")

with Path(a.provenance).open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=required_fields);w.writeheader();w.writerows(prov)

report={
    "status":"PASS" if not errors else "FAIL",
    "source_count":m.get("source_count",0),
    "record_count":m.get("record_count",0),
    "errors":errors,
    "promotion_performed":False
}
Path(a.report).write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps(report,indent=2))
raise SystemExit(0 if not errors else 1)
