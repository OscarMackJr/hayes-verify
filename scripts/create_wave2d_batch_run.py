"""Create a unique, immutable Wave 2D batch run identity."""
import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--root", required=True)
parser.add_argument("--spec", required=True)
args = parser.parse_args()
root = Path(args.root).resolve()
spec = json.loads(Path(args.spec).read_text(encoding="utf-8-sig"))
now = datetime.now(UTC)
batch_id = now.strftime("BATCH-%Y%m%dT%H%M%S.%fZ")
run_root = root / Path(spec["run_root"].replace("\\", "/")) / batch_id
run_root.mkdir(parents=True, exist_ok=False)
run = {"batch_id": batch_id, "wave": spec["wave"], "created_at_utc": now.isoformat(), "run_root": str(run_root), "request_path": str(run_root / spec["request_filename"]), "results_root": str(run_root / spec["results_dirname"]), "summary_path": str(run_root / spec["summary_filename"])}
latest = root / Path(spec["latest_pointer"].replace("\\", "/"))
latest.parent.mkdir(parents=True, exist_ok=True)
latest.write_text(json.dumps(run, indent=2), encoding="utf-8")
(run_root / "run_identity.json").write_text(json.dumps(run, indent=2), encoding="utf-8")
print(json.dumps(run, indent=2))