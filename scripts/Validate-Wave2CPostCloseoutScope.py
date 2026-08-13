import argparse,json,subprocess
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--spec",required=True)
ap.add_argument("--report",required=True)
a=ap.parse_args()

root=Path(a.root).resolve()
spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))
allowed=spec["allowed_roots"]

cp=subprocess.run(["git","status","--porcelain"],cwd=root,capture_output=True,text=True)
if cp.returncode!=0:
    raise SystemExit(cp.stderr)

rows=[]
errors=[]
for line in cp.stdout.splitlines():
    if not line.strip(): continue
    path=line[3:].replace("\\","/")
    if " -> " in path:
        path=path.split(" -> ",1)[1]
    ok=any(path.startswith(prefix) for prefix in allowed)
    rows.append({"path":path,"allowed":ok})
    if not ok:
        errors.append(f"OUT_OF_SCOPE:{path}")

report={"status":"PASS" if not errors else "FAIL","changed_paths":rows,"errors":errors}
Path(a.report).write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps(report,indent=2))
raise SystemExit(0 if not errors else 1)
