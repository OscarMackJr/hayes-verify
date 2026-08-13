import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--root", required=True)
args = ap.parse_args()
root = Path(args.root).resolve()


def run(cmd):
    cp = subprocess.run(
        cmd,
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return cp.returncode, cp.stdout, cp.stderr


rc_t, out_t, _err_t = run([sys.executable, "-m", "pytest", "-q"])
rc_r, out_r, _err_r = run([sys.executable, "-m", "ruff", "check", "src", "tests"])

status = "PASS" if rc_t == 0 and rc_r == 0 else "FAIL"
errors = []
if rc_t != 0:
    errors.append("pytest failed")
if rc_r != 0:
    errors.append("ruff failed")

summary = {
    "component": "Hayes Verify",
    "phase": "Pilot Evaluator Vertical Slice",
    "certified_at_utc": datetime.now(UTC).isoformat(),
    "status": status,
    "pilot_control_count": 3,
    "tests_status": "PASS" if rc_t == 0 else "FAIL",
    "ruff_status": "PASS" if rc_r == 0 else "FAIL",
    "promotion_state": "NOT_PROMOTED",
    "errors": errors,
}

out = root / "generated" / "pilot-evaluator" / "pilot_summary.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(summary, indent=2), encoding="utf-8")

print(json.dumps(summary, indent=2))
raise SystemExit(0 if status == "PASS" else 1)
