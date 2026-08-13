import argparse
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from jsonschema import Draft202012Validator


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git(root: Path, *args: str) -> str:
    cp = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if cp.returncode != 0:
        raise RuntimeError(cp.stderr.strip() or cp.stdout.strip())
    return cp.stdout.strip()


ap = argparse.ArgumentParser()
ap.add_argument("--root", required=True)
ap.add_argument("--spec", required=True)
ap.add_argument("--schema", required=True)
args = ap.parse_args()

root = Path(args.root).resolve()
spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
schema = json.loads(Path(args.schema).read_text(encoding="utf-8"))

tracked = git(root, "ls-files").splitlines()
manifest_items = []

for rel in tracked:
    path = root / rel
    if path.is_file():
        manifest_items.append({
            "path": rel.replace("\\", "/"),
            "sha256": sha256(path),
        })

manifest = {
    "component": "Hayes Verify",
    "created_at_utc": datetime.now(UTC).isoformat(),
    "file_count": len(manifest_items),
    "files": manifest_items,
}
manifest_path = root / spec["baseline_manifest"]
manifest_path.parent.mkdir(parents=True, exist_ok=True)
manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

commit_sha = git(root, "rev-parse", "HEAD")
registration = {
    "baseline_version": "1.0",
    "component": "Hayes Verify",
    "registered_at_utc": datetime.now(UTC).isoformat(),
    "status": "PASS",
    "baseline_state": "AUTHORITATIVE",
    "repository_name": spec["repository_name"],
    "default_branch": spec["default_branch"],
    "commit_sha": commit_sha,
    "manifest_sha256": sha256(manifest_path),
    "authority": spec["authority"],
}
Draft202012Validator(schema).validate(registration)

reg_path = root / spec["baseline_registration"]
reg_path.parent.mkdir(parents=True, exist_ok=True)
reg_path.write_text(json.dumps(registration, indent=2), encoding="utf-8")

cert = {
    "component": "Hayes Verify",
    "phase": "Initial Controlled Baseline Certification",
    "certified_at_utc": datetime.now(UTC).isoformat(),
    "status": "PASS",
    "baseline_state": "AUTHORITATIVE",
    "baseline_registration": spec["baseline_registration"],
    "baseline_registration_sha256": sha256(reg_path),
    "manifest_path": spec["baseline_manifest"],
    "manifest_sha256": sha256(manifest_path),
    "commit_sha": commit_sha,
}
cert_path = root / spec["baseline_certification"]
cert_path.parent.mkdir(parents=True, exist_ok=True)
cert_path.write_text(json.dumps(cert, indent=2), encoding="utf-8")
print(json.dumps(cert, indent=2))
