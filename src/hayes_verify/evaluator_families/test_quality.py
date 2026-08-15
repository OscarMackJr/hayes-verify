from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

TEST_FILE_PATTERNS = (
    "tests/**/*.py",
    "test/**/*.py",
    "**/*test*.py",
    "**/*.test.js",
    "**/*.test.ts",
    "**/*.spec.js",
    "**/*.spec.ts",
    "**/*Tests.cs",
    "**/*Test.cs",
    "**/*_test.go",
    "**/*_test.rs",
)

CONTRACT_MARKERS = (
    "openapi.yaml",
    "openapi.yml",
    "swagger.yaml",
    "swagger.yml",
    "contracts/**/*.json",
    "contracts/**/*.yaml",
    "contracts/**/*.yml",
    "tests/**/*contract*",
    "tests/**/*api*",
)

INTEGRATION_TEST_PATTERNS = (
    "tests/**/*integration*",
    "test/**/*integration*",
    "integration-tests/**/*",
    "integration_tests/**/*",
    "**/*integration*.py",
    "**/*Integration*.cs",
    "**/*integration*.ts",
    "**/*integration*.js",
)

TEST_ISOLATION_PATTERNS = (
    "docker-compose.test.yml",
    "docker-compose.test.yaml",
    "compose.test.yml",
    "compose.test.yaml",
    "tests/**/Dockerfile",
    "tests/**/*testcontainer*",
    "tests/**/*container*",
    "test/**/*testcontainer*",
    "test/**/*container*",
)

ZERO_TRUST_TEST_PATTERNS = (
    "tests/**/*zero*trust*",
    "test/**/*zero*trust*",
    "integration-tests/**/*zero*trust*",
    "integration_tests/**/*zero*trust*",
    "tests/**/*authz*",
    "tests/**/*authorization*",
    "tests/**/*identity*",
    "tests/**/*deny*",
)


PERFORMANCE_MARKERS = (
    "tests/**/*performance*",
    "tests/**/*load*",
    "tests/**/*benchmark*",
    "performance/**/*",
    "load-tests/**/*",
    "benchmarks/**/*",
    "k6/**/*",
    "jmeter/**/*",
)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _glob_matches(root: Path, patterns: tuple[str, ...]) -> list[str]:
    matches = set()
    for pattern in patterns:
        for path in root.glob(pattern):
            if path.is_file():
                matches.add(path.relative_to(root).as_posix())
    return sorted(matches)


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
        raise ValueError(f"No test_quality rule registered for {control_id}")
    if not rule.get("supported"):
        raise ValueError(f"test_quality rule not implemented for {control_id}")

    assertions = []
    observations = {
        "repository_path": str(repository_path),
        "control_id": control_id,
        "family": "test_quality",
        "checks": [],
    }

    for check in rule["checks"]:
        ctype = check["type"]

        if ctype == "repository_test_files_present":
            matches = _glob_matches(repository_path, TEST_FILE_PATTERNS)
            passed = bool(matches)
            detail = {"matched_files": matches}
        elif ctype == "repository_contract_test_marker_present":
            matches = _glob_matches(repository_path, CONTRACT_MARKERS)
            passed = bool(matches)
            detail = {"matched_files": matches}
        elif ctype == "repository_performance_test_marker_present":
            matches = _glob_matches(repository_path, PERFORMANCE_MARKERS)
            passed = bool(matches)
            detail = {"matched_files": matches}
        elif ctype == "repository_integration_test_marker_present":
            matches = _glob_matches(repository_path, INTEGRATION_TEST_PATTERNS)
            passed = bool(matches)
            detail = {"matched_files": matches}
        elif ctype == "test_environment_isolation_marker_present":
            matches = _glob_matches(repository_path, TEST_ISOLATION_PATTERNS)
            isolated = [
                item for item in matches
                if any(token in item.lower() for token in ("docker", "container", "compose", "testcontainer"))
            ]
            passed = bool(isolated)
            detail = {"matched_files": matches, "isolation_markers": isolated}
        elif ctype == "zero_trust_integration_test_marker_present":
            matches = _glob_matches(repository_path, ZERO_TRUST_TEST_PATTERNS)
            passed = bool(matches)
            detail = {"matched_files": matches}
        elif ctype == "workflow_regex_any":
            passed, detail = _workflow_regex(
                repository_path,
                check["regex"],
            )
        else:
            raise ValueError(
                f"Unsupported test_quality check type: {ctype}"
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
    evidence_id = f"TEST-{control_id}-{_sha256_text(observation_text)[:16]}"

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
                "command_or_method": "repository test-quality evidence inspection",
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
            f"Test quality rule {control_id} satisfied."
            if passed
            else f"Test quality rule {control_id} not satisfied."
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

    rules = Path(root) / "registry" / "test_quality_rules.json"

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
