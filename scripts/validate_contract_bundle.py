import argparse
import json
from pathlib import Path

from hayes_verify.contract_hashing import (
    CANONICAL_CONTRACT_HASH_ALGORITHM,
    sha256_canonical_contract_file,
)

ap = argparse.ArgumentParser()
ap.add_argument("--root", required=True)
a = ap.parse_args()
root = Path(a.root).resolve()

freeze = json.loads((root / "contracts" / "contract_freeze.json").read_text(encoding="utf-8-sig"))
manifest = json.loads((root / "contracts" / "consumer_manifest.json").read_text(encoding="utf-8-sig"))

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
    actual = sha256_canonical_contract_file(path)
    if actual != expected:
        errors.append(f"canonical hash mismatch for {name}: path={path} expected={expected} actual={actual} algorithm={CANONICAL_CONTRACT_HASH_ALGORITHM}")

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
    "hash_algorithm": CANONICAL_CONTRACT_HASH_ALGORITHM,
    "errors": errors
}, indent=2))
raise SystemExit(0 if not errors else 1)
