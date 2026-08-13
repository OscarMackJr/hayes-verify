import argparse,csv,json,hashlib
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--ems-root",required=True)
ap.add_argument("--spec",required=True)
ap.add_argument("--out",required=True)
a=ap.parse_args()

root=Path(a.ems_root).resolve()
spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))
rows=[]

def sha256(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

for rel in spec["source_policy"]["allowed_roots"]:
    base=root/rel
    if not base.exists():
        continue
    for p in sorted(base.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() not in set(spec["source_policy"]["allowed_extensions"]):
            continue
        rows.append({
            "source_path":str(p.relative_to(root)).replace("\\","/"),
            "source_name":p.stem,
            "extension":p.suffix.lower(),
            "size_bytes":p.stat().st_size,
            "sha256":sha256(p)
        })

if spec["source_policy"].get("require_at_least_one_source") and not rows:
    raise SystemExit("No controlled document sources discovered.")

out=Path(a.out)
out.parent.mkdir(parents=True,exist_ok=True)
with out.open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys()))
    w.writeheader();w.writerows(rows)

print(json.dumps({"source_count":len(rows),"status":"PASS"},indent=2))
