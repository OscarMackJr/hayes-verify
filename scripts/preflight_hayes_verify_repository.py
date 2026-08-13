import argparse
import json
import re
from pathlib import Path

SENSITIVE_PATTERNS = [
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)client_secret\s*[:=]\s*['\"][^'\"]+"),
    re.compile(r"(?i)api[_-]?key\s*[:=]\s*['\"][^'\"]+"),
]

IGNORE_DIRS = {
    ".git", ".venv", ".pytest-temp", ".pytest_cache",
    ".ruff_cache", "__pycache__", "generated", "evidence",
}

TEXT_EXTENSIONS = {
    ".py", ".ps1", ".json", ".yaml", ".yml", ".toml",
    ".md", ".txt", ".ini", ".cfg", ".env",
}

ap = argparse.ArgumentParser()
ap.add_argument("--root", required=True)
args = ap.parse_args()

root = Path(args.root).resolve()
errors = []

required = [
    root / "pyproject.toml",
    root / "README.md",
    root / "src",
    root / "tests",
    root / "contracts" / "contract_freeze.json",
    root / "scripts" / "validate_contract_bundle.py",
]
for path in required:
    if not path.exists():
        errors.append(f"missing required path: {path}")

for bad in [root / ".env", root / "evidence"]:
    if bad.exists():
        if bad.is_file():
            errors.append(f"sensitive/runtime artifact present: {bad}")
        elif any(bad.iterdir()):
            errors.append(f"sensitive/runtime directory is not empty: {bad}")

for path in root.rglob("*"):
    if not path.is_file():
        continue
    if any(part in IGNORE_DIRS for part in path.parts):
        continue
    if path.suffix.lower() not in TEXT_EXTENSIONS and path.name not in {".env", ".env.example"}:
        continue
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        continue
    for pattern in SENSITIVE_PATTERNS:
        if pattern.search(text):
            errors.append(f"potential secret pattern detected in {path}")
            break

out = {
    "component": "Hayes Verify",
    "phase": "Repository Bootstrap Preflight",
    "status": "PASS" if not errors else "FAIL",
    "errors": errors,
}
print(json.dumps(out, indent=2))
raise SystemExit(0 if not errors else 1)
