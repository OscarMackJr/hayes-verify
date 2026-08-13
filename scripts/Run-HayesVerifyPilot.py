import argparse
import json
from pathlib import Path

from hayes_verify.contracts import ContractBundle
from hayes_verify.pilots.orchestration import run_pilot

ap = argparse.ArgumentParser()
ap.add_argument("--root", required=True)
ap.add_argument("--request", required=True)
ap.add_argument("--repository-path", required=True)
ap.add_argument("--github-repo", required=True)
args = ap.parse_args()

root = Path(args.root).resolve()
bundle = ContractBundle(root)
request = json.loads(Path(args.request).read_text(encoding="utf-8-sig"))

evidence, result = run_pilot(
    bundle,
    request,
    Path(args.repository_path),
    args.github_repo,
)

out = root / "generated" / "pilot-evaluator" / request["control_id"] / request["target_id"]
out.mkdir(parents=True, exist_ok=True)

(out / "evidence.json").write_text(
    json.dumps(evidence, indent=2),
    encoding="utf-8",
)
(out / "result.json").write_text(
    json.dumps(result, indent=2),
    encoding="utf-8",
)

print(
    json.dumps(
        {
            "status": "PASS",
            "evidence_count": len(evidence),
            "result": result,
        },
        indent=2,
    )
)
