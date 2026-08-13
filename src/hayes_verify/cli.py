from __future__ import annotations

import argparse
import json
from pathlib import Path

from hayes_verify.contracts import ContractBundle
from hayes_verify.orchestration import run_evaluation


def _cmd_validate_request(path: str) -> int:
    bundle = ContractBundle.discover()
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    bundle.validate_request(payload)
    print(json.dumps({"status": "PASS", "request_id": payload["request_id"]}, indent=2))
    return 0


def _cmd_evaluate(path: str) -> int:
    bundle = ContractBundle.discover()
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    result = run_evaluation(bundle, payload)
    print(json.dumps(result, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="hayes-verify")
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate-request")
    p_validate.add_argument("path")

    p_eval = sub.add_parser("evaluate")
    p_eval.add_argument("path")

    args = parser.parse_args()
    if args.command == "validate-request":
        return _cmd_validate_request(args.path)
    if args.command == "evaluate":
        return _cmd_evaluate(args.path)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
