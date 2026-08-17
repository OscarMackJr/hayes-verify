"""Fail-closed content audit for the explicit AR3F publication allowlist."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

PATH_PATTERN = re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/]|/(?:home|tmp)/")
SENSITIVE_PATTERN = re.compile(r"(?:password\s*[=:]|private key|api[_-]?key\s*[=:]|token\s*[=:])", re.IGNORECASE)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--allowlist", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    allowlist = json.loads(args.allowlist.read_text(encoding="utf-8"))["allowlist"]
    findings: list[dict[str, object]] = []
    for relative in allowlist:
        path = args.root / relative
        if not path.is_file():
            raise SystemExit(f"missing allowlisted file: {relative}")
        text = path.read_text(encoding="utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if PATH_PATTERN.search(line):
                findings.append({"kind": "LOCAL_ABSOLUTE_PATH", "path": relative, "line": line_number})
            if SENSITIVE_PATTERN.search(line) and not line.lstrip().startswith("SENSITIVE_PATTERN ="):
                findings.append({"kind": "SECRET_CREDENTIAL", "path": relative, "line": line_number})
    counts = {kind: sum(item["kind"] == kind for item in findings) for kind in {item["kind"] for item in findings}}
    result = {"status": "PASS" if not findings else "FAIL", "allowlist_count": len(allowlist), "findings": findings, "counts": counts}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if findings:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
