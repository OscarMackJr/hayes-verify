import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8-sig"))


def sha(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


manifest_path = "generated/wave2d/evaluator-expansion/priority2_completion_manifest.json"
cert_path = "generated/wave2d/evaluator-expansion/priority2_completion_certification.json"
spec_path = "registry/wave2d_evaluator_registry_v1_8_publication_spec.json"
manifest, cert, spec = load(manifest_path), load(cert_path), load(spec_path)
errors = []

expected = {
    "completion_state": "COMPLETE",
    "original_control_count": 21,
    "implemented_control_count": 21,
    "remaining_control_count": 0,
    "original_family_count": 4,
    "completed_family_count": 4,
    "remaining_family_count": 0,
}
for key, value in expected.items():
    if manifest.get(key) != value or cert.get(key) != value:
        errors.append(f"count/state mismatch: {key}")
if manifest.get("source_registry_version") != "1.8":
    errors.append("manifest source registry version")
if cert.get("status") != "PASS" or cert.get("registry_version") != "1.8":
    errors.append("certification state")
if cert.get("registry_state") != "CANDIDATE_FROZEN":
    errors.append("certification registry state")
if spec.get("registry_version") != "1.8" or spec.get("candidate_state") != "CANDIDATE_FROZEN":
    errors.append("publication specification state")

families = {item.get("family") for item in manifest.get("families", [])}
if families != {"dependency_supply_chain", "test_quality", "release_integrity", "documentation_governance"}:
    errors.append("family set")
for family in manifest.get("families", []):
    for key in ("verification_manifest_path", "family_certification_path"):
        relative = family.get(key)
        if not relative or not (ROOT / relative).is_file():
            errors.append(f"missing {family.get('family')} {key}")
    if family.get("verification_manifest_sha256") != sha(family["verification_manifest_path"]):
        errors.append(f"verification hash {family.get('family')}")

for path_key, hash_key in (("completion_manifest_path", "completion_manifest_sha256"), ("backlog_path", "backlog_sha256"), ("family_plan_path", "family_plan_sha256")):
    relative = cert.get(path_key)
    if not relative or not (ROOT / relative).is_file():
        errors.append(f"missing certification reference {path_key}")
    elif cert.get(hash_key) != sha(relative):
        errors.append(f"certification hash mismatch {hash_key}")

registry_hash = sha("registry/wave2d_evaluator_registry_v1_8.json")
if registry_hash != "49175ae4062541de8a2a9b4a5d74ede7f838f8b6f88385080da363885afd8ad8":
    errors.append("registry immutable hash")
if cert.get("registry_sha256") != registry_hash or spec.get("registry_sha256") != registry_hash:
    errors.append("registry reference hash")

print(json.dumps({"status": "PASS" if not errors else "FAIL", "errors": errors}, indent=2))
raise SystemExit(1 if errors else 0)
