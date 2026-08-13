from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import quote

from hayes_verify.provenance import build_provenance

_DEFAULT_BRANCH_CACHE: dict[str, tuple[bool, str, str]] = {}


def _run_gh(args: list[str]) -> tuple[int, str, str]:
    cp = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    return cp.returncode, cp.stdout, cp.stderr


def _parse_json(stdout: str) -> tuple[bool, dict[str, Any]]:
    if not stdout.strip():
        return False, {}
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return False, {}
    return isinstance(payload, dict), payload if isinstance(payload, dict) else {}


def _discover_default_branch(github_repo: str) -> tuple[bool, str, str]:
    if github_repo in _DEFAULT_BRANCH_CACHE:
        return _DEFAULT_BRANCH_CACHE[github_repo]

    rc, out, err = _run_gh(["api", f"repos/{github_repo}"])
    parsed, payload = _parse_json(out)

    branch = payload.get("default_branch") if parsed else None
    success = rc == 0 and parsed and isinstance(branch, str) and bool(branch.strip())

    result = (
        success,
        branch.strip() if success else "",
        "" if success else (err.strip() or "Default branch could not be discovered."),
    )
    _DEFAULT_BRANCH_CACHE[github_repo] = result
    return result


def _encode_branch(branch: str) -> str:
    return quote(branch, safe="")


def _evidence(
    request: dict,
    repository_path: Path,
    evidence_id: str,
    evidence_type: str,
    source: str,
    observation: dict[str, Any],
) -> dict:
    raw = json.dumps(observation, sort_keys=True).encode("utf-8")
    provenance = build_provenance(repository_path, "hayes-verify", "0.1.0")
    return {
        "contract_version": "1.0",
        "wave": "2D",
        "evidence_id": evidence_id,
        "request_id": request["request_id"],
        "control_id": request["control_id"],
        "target_id": request["target_id"],
        "evidence_type": evidence_type,
        "source": source,
        "collected_at_utc": provenance["collected_at_utc"],
        "sha256": hashlib.sha256(raw).hexdigest(),
        "observation": json.dumps(observation, sort_keys=True),
        "provenance": provenance,
        "sensitive": False,
    }


def collect_branch_protection(
    request: dict,
    repository_path: Path,
    github_repo: str,
) -> list[dict]:
    branch_ok, branch, branch_error = _discover_default_branch(github_repo)
    if not branch_ok:
        observation = {
            "api_success": False,
            "api_status": "ERROR",
            "default_branch_discovery_success": False,
            "default_branch": None,
            "evaluated_branch": None,
            "error": branch_error,
            "protected": False,
            "required_status_checks_present": False,
            "enforce_admins_present": False,
            "required_pull_request_reviews_present": False,
            "restrictions_present": False,
            "raw_summary": {"keys": []},
        }
        return [
            _evidence(
                request,
                repository_path,
                f"{request['request_id']}::branch-protection",
                "GITHUB_BRANCH_PROTECTION",
                f"github:{github_repo}",
                observation,
            )
        ]

    encoded = _encode_branch(branch)
    rc, out, err = _run_gh(
        ["api", f"repos/{github_repo}/branches/{encoded}/protection"],
    )
    parsed, payload = _parse_json(out)
    api_success = rc == 0 and parsed

    observation = {
        "api_success": api_success,
        "api_status": "SUCCESS" if api_success else "ERROR",
        "default_branch_discovery_success": True,
        "default_branch": branch,
        "evaluated_branch": branch,
        "encoded_branch": encoded,
        "exit_code": rc,
        "error": "" if api_success else err.strip(),
        "protected": api_success and bool(payload),
        "required_status_checks_present": (
            bool(payload.get("required_status_checks")) if api_success else False
        ),
        "enforce_admins_present": (
            bool(payload.get("enforce_admins")) if api_success else False
        ),
        "required_pull_request_reviews_present": (
            bool(payload.get("required_pull_request_reviews")) if api_success else False
        ),
        "restrictions_present": (
            bool(payload.get("restrictions")) if api_success else False
        ),
        "raw_summary": {
            "keys": sorted(payload.keys()) if api_success else [],
        },
    }

    return [
        _evidence(
            request,
            repository_path,
            f"{request['request_id']}::branch-protection",
            "GITHUB_BRANCH_PROTECTION",
            f"github:{github_repo}:{branch}",
            observation,
        )
    ]


def collect_pr_review(
    request: dict,
    repository_path: Path,
    github_repo: str,
) -> list[dict]:
    branch_ok, branch, branch_error = _discover_default_branch(github_repo)
    if not branch_ok:
        observation = {
            "api_success": False,
            "api_status": "ERROR",
            "default_branch_discovery_success": False,
            "default_branch": None,
            "evaluated_branch": None,
            "error": branch_error,
            "required_pull_request_reviews_present": False,
            "required_approving_review_count": None,
            "dismiss_stale_reviews": None,
            "require_code_owner_reviews": None,
            "raw_summary": {"keys": []},
        }
        return [
            _evidence(
                request,
                repository_path,
                f"{request['request_id']}::pr-review",
                "GITHUB_PR_REVIEW_REQUIREMENT",
                f"github:{github_repo}",
                observation,
            )
        ]

    encoded = _encode_branch(branch)
    endpoint = (
        f"repos/{github_repo}/branches/{encoded}/protection/"
        "required_pull_request_reviews"
    )
    rc, out, err = _run_gh(["api", endpoint])
    parsed, payload = _parse_json(out)
    api_success = rc == 0 and parsed

    observation = {
        "api_success": api_success,
        "api_status": "SUCCESS" if api_success else "ERROR",
        "default_branch_discovery_success": True,
        "default_branch": branch,
        "evaluated_branch": branch,
        "encoded_branch": encoded,
        "exit_code": rc,
        "error": "" if api_success else err.strip(),
        "required_pull_request_reviews_present": api_success and bool(payload),
        "required_approving_review_count": (
            payload.get("required_approving_review_count") if api_success else None
        ),
        "dismiss_stale_reviews": (
            payload.get("dismiss_stale_reviews") if api_success else None
        ),
        "require_code_owner_reviews": (
            payload.get("require_code_owner_reviews") if api_success else None
        ),
        "raw_summary": {
            "keys": sorted(payload.keys()) if api_success else [],
        },
    }

    return [
        _evidence(
            request,
            repository_path,
            f"{request['request_id']}::pr-review",
            "GITHUB_PR_REVIEW_REQUIREMENT",
            f"github:{github_repo}:{branch}",
            observation,
        )
    ]


def collect_secret_scanning(
    request: dict,
    repository_path: Path,
    github_repo: str,
) -> list[dict]:
    rc, out, err = _run_gh(["api", f"repos/{github_repo}"])
    parsed, payload = _parse_json(out)
    api_success = rc == 0 and parsed

    security = payload.get("security_and_analysis", {}) if api_success else {}
    if not isinstance(security, dict):
        security = {}

    secret = security.get("secret_scanning")
    push = security.get("secret_scanning_push_protection")

    secret_status = secret.get("status") if isinstance(secret, dict) else None
    push_status = push.get("status") if isinstance(push, dict) else None

    observation = {
        "api_success": api_success,
        "api_status": "SUCCESS" if api_success else "ERROR",
        "exit_code": rc,
        "error": "" if api_success else err.strip(),
        "secret_scanning_status": secret_status,
        "push_protection_status": push_status,
        "raw_summary": {
            "security_and_analysis_present": bool(security),
        },
    }

    return [
        _evidence(
            request,
            repository_path,
            f"{request['request_id']}::secret-scanning",
            "GITHUB_SECRET_SCANNING",
            f"github:{github_repo}",
            observation,
        )
    ]
