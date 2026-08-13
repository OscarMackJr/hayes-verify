import argparse
import hashlib
import json
from pathlib import Path


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


ap = argparse.ArgumentParser()
ap.add_argument("--root", required=True)
ap.add_argument("--spec", required=True)
args = ap.parse_args()

root = Path(args.root).resolve()
spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))

regp = root / spec["baseline_registration"]
manp = root / spec["baseline_manifest"]
certp = root / spec["baseline_certification"]
errors = []

for path in (regp, manp, certp):
    if not path.exists():
        errors.append(f"missing {path}")

if not errors:
    reg = json.loads(regp.read_text(encoding="utf-8"))
    cert = json.loads(certp.read_text(encoding="utf-8"))
    if reg.get("status") != "PASS":
        errors.append("baseline registration not PASS")
    if reg.get("baseline_state") != "AUTHORITATIVE":
        errors.append("baseline registration not AUTHORITATIVE")
    if reg.get("manifest_sha256") != sha(manp):
        errors.append("manifest hash mismatch")
    if cert.get("baseline_registration_sha256") != sha(regp):
        errors.append("baseline registration hash mismatch")

out = {
    "status": "PASS" if not errors else "FAIL",
    "baseline_state": "AUTHORITATIVE" if not errors else "BLOCKED",
    "errors": errors,
}
print(json.dumps(out, indent=2))
raise SystemExit(0 if not errors else 1)
