from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

MANIFEST_PATTERNS = (
    "requirements.txt",
    "requirements/*.txt",
    "pyproject.toml",
    "Pipfile",
    "package.json",
    "*.csproj",
    "*.fsproj",
    "packages.config",
    "Cargo.toml",
    "go.mod",
)

LOCKFILE_PATTERNS = (
    "poetry.lock",
    "Pipfile.lock",
    "uv.lock",
    "package-lock.json",
    "npm-shrinkwrap.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "Cargo.lock",
    "packages.lock.json",
)

INTEGRITY_PATTERNS = (
    "package-lock.json",
    "npm-shrinkwrap.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "Cargo.lock",
    "packages.lock.json",
    "poetry.lock",
    "uv.lock",
    ".npmrc",
    "NuGet.Config",
    "nuget.config",
)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _matching_files(root: Path, patterns: tuple[str, ...]) -> list[str]:
    matches = set()
    for pattern in patterns:
        for path in root.glob(pattern):
            if path.is_file():
                matches.add(path.relative_to(root).as_posix())
    return sorted(matches)


def _manifest_present(root: Path) -> tuple[bool, dict[str, Any]]:
    matches = _matching_files(root, MANIFEST_PATTERNS)
    return bool(matches), {"matched_files": matches}


def _lockfile_present(root: Path) -> tuple[bool, dict[str, Any]]:
    matches = _matching_files(root, LOCKFILE_PATTERNS)
    return bool(matches), {"matched_files": matches}


def _integrity_present(root: Path) -> tuple[bool, dict[str, Any]]:
    matches = _matching_files(root, INTEGRITY_PATTERNS)
    return bool(matches), {"matched_files": matches}


def _workflow_regex(
    root: Path,
    regex: str,
) -> tuple[bool, dict[str, Any]]:
    compiled = re.compile(regex)
    matches = []
    examined = 0

    for pattern in (".github/workflows/*.yml", ".github/workflows/*.yaml"):
        for path in root.glob(pattern):
            if not path.is_file():
                continue
            examined += 1
            text = path.read_text(
                encoding="utf-8-sig",
                errors="ignore",
            )
            if compiled.search(text):
                matches.append(path.relative_to(root).as_posix())

    return bool(matches), {
        "matched_workflows": sorted(set(matches)),
        "workflow_files_examined": examined,
    }


def evaluate_rule(
    control_id: str,
    repository_path: Path,
    rule_registry_path: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    registry = json.loads(
        rule_registry_path.read_text(encoding="utf-8-sig")
    )
    rule = registry.get("rules", {}).get(control_id)

    if rule is None:
        raise ValueError(
            f"No dependency_supply_chain rule registered for {control_id}"
        )
    if not rule.get("supported"):
        raise ValueError(
            f"dependency_supply_chain rule not implemented for {control_id}"
        )

    assertions = []
    observations = {
        "repository_path": str(repository_path),
        "control_id": control_id,
        "family": "dependency_supply_chain",
        "checks": [],
    }

    for check in rule["checks"]:
        ctype = check["type"]

        if ctype == "repository_dependency_manifest_present":
            passed, detail = _manifest_present(repository_path)
        elif ctype == "repository_lockfile_present":
            passed, detail = _lockfile_present(repository_path)
        elif ctype == "repository_integrity_marker_present":
            passed, detail = _integrity_present(repository_path)
        elif ctype == "workflow_regex_any":
            passed, detail = _workflow_regex(
                repository_path,
                check["regex"],
            )
        else:
            raise ValueError(
                f"Unsupported dependency_supply_chain check type: {ctype}"
            )

        observations["checks"].append(
            {
                "assertion_id": check["assertion_id"],
                "type": ctype,
                "passed": passed,
                **detail,
            }
        )
        assertions.append(
            {
                "assertion_id": check["assertion_id"],
                "result": "PASS" if passed else "FAIL",
                "detail": json.dumps(detail, sort_keys=True),
            }
        )

    outcomes = [item["result"] == "PASS" for item in assertions]
    passed = (
        all(outcomes)
        if rule.get("pass_policy", "ALL") == "ALL"
        else any(outcomes)
    )

    now = datetime.now(UTC).isoformat()
    observation_text = json.dumps(observations, sort_keys=True)
    evidence_id = (
        f"SUPPLY-{control_id}-{_sha256_text(observation_text)[:16]}"
    )

    evidence = [
        {
            "contract_version": "1.0",
            "wave": "2D",
            "evidence_id": evidence_id,
            "control_id": control_id,
            "evidence_type": rule["evidence_type"],
            "source": f"repository:{repository_path}",
            "collected_at_utc": now,
            "sha256": _sha256_text(observation_text),
            "observation": observation_text,
            "provenance": {
                "collector": "hayes-verify",
                "collector_version": "0.1.0",
                "repository_path_or_url": str(repository_path),
                "collected_at_utc": now,
                "command_or_method": (
                    "dependency manifest, lockfile, integrity, and "
                    "workflow inspection"
                ),
                "tool_versions": {},
            },
            "sensitive": False,
        }
    ]

    result = {
        "contract_version": "1.0",
        "wave": "2D",
        "evaluation_state": "COMPLETE",
        "evidence_state": "SUFFICIENT",
        "result_state": "PASS" if passed else "FAIL",
        "evaluated_at_utc": now,
        "evidence_ids": [evidence_id],
        "rationale": (
            f"Dependency supply-chain rule {control_id} satisfied."
            if passed
            else f"Dependency supply-chain rule {control_id} not satisfied."
        ),
        "assertions": assertions,
        "promotion_state": "NOT_PROMOTED",
    }

    return evidence, result


def run(
    bundle,
    request: dict[str, Any],
    repository_path: Path,
    github_repo: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    del github_repo

    root = getattr(bundle, "root", None)
    if root is None:
        root = Path.cwd()

    rules = (
        Path(root)
        / "registry"
        / "dependency_supply_chain_rules.json"
    )

    evidence, result = evaluate_rule(
        request["control_id"],
        repository_path,
        rules,
    )

    for item in evidence:
        item["request_id"] = request["request_id"]
        item["target_id"] = request["target_id"]

    result["request_id"] = request["request_id"]
    result["control_id"] = request["control_id"]
    result["target_id"] = request["target_id"]

    bundle.validate_result(result)
    return evidence, result
