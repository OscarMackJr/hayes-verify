import argparse
import hashlib
import json
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--root", required=True)
a = ap.parse_args()
root = Path(a.root).resolve()

freeze = json.loads((root / "contracts" / "contract_freeze.json").read_text(encoding="utf-8-sig"))
manifest = json.loads((root / "contracts" / "consumer_manifest.json").read_text(encoding="utf-8-sig"))

def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

mapping = {
    "evaluation_request": root / "contracts" / "schemas" / "wave2d_evaluation_request.schema.json",
    "evidence_record": root / "contracts" / "schemas" / "wave2d_evidence_record.schema.json",
    "evaluation_result": root / "contracts" / "schemas" / "wave2d_evaluation_result.schema.json",
    "provenance_envelope": root / "contracts" / "schemas" / "wave2d_provenance_envelope.schema.json",
    "status_vocabulary": root / "contracts" / "registry" / "evaluation_status_vocabulary.json",
}

errors = []
for name, path in mapping.items():
    expected = freeze["contracts"][name]["sha256"]
    if not path.exists():
        errors.append(f"missing {name}: {path}")
        continue
    actual = sha256(path)
    if actual != expected:
        errors.append(f"hash mismatch for {name}: {actual} != {expected}")

auth = manifest["authority"]
if auth["applicability"] != "EMS":
    errors.append("EMS must remain applicability authority")
if auth["evidence_promotion"] != "EMS":
    errors.append("EMS must remain evidence promotion authority")
if auth["evaluation_execution"] != "Hayes Verify":
    errors.append("Hayes Verify must remain evaluation executor")
if manifest.get("applicability_mutation_allowed") is not False:
    errors.append("applicability mutation must be forbidden")
if manifest.get("evidence_promotion_allowed") is not False:
    errors.append("evidence promotion must be forbidden")

print(json.dumps({
    "status": "PASS" if not errors else "FAIL",
    "contract_count": len(mapping),
    "errors": errors
}, indent=2))
raise SystemExit(0 if not errors else 1)
