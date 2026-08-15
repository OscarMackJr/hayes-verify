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


def _base_run(
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

_base_evaluate_rule = evaluate_rule


def _v110_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _v110_outcome(authority: dict[str, Any] | None) -> tuple[str, dict[str, Any]]:
    required = ("authority_type", "source_identity", "evidence_timestamp", "reference_timestamp", "findings")
    if not isinstance(authority, dict) or not all(authority.get(key) not in (None, "") for key in required):
        return "WARNING", {"reason": "authoritative organizational vulnerability evidence unavailable or incomplete"}
    if authority.get("authority_type") != "vulnerability_management" or authority.get("accessible") is False or authority.get("ambiguous") is True or authority.get("conflicting") is True:
        return "WARNING", {"reason": "authoritative organizational evidence inaccessible, ambiguous, or conflicting"}
    evidence_at = _v110_time(authority["evidence_timestamp"])
    reference_at = _v110_time(authority["reference_timestamp"])
    if evidence_at is None or reference_at is None or not isinstance(authority["findings"], list):
        return "WARNING", {"reason": "authoritative evidence contract invalid"}
    failures: list[dict[str, Any]] = []
    for finding in authority["findings"]:
        if not isinstance(finding, dict):
            return "WARNING", {"reason": "authoritative finding record invalid"}
        severity = finding.get("severity")
        detected = _v110_time(finding.get("first_validated_detection_timestamp"))
        if severity not in {"Critical", "High", "Medium", "Low"} or detected is None or not finding.get("finding_id"):
            return "WARNING", {"reason": "finding classification/detection evidence incomplete"}
        freshness = 24 if severity in {"Critical", "High"} and finding.get("status") == "OPEN" else 24 * 7
        if (reference_at - evidence_at).total_seconds() > freshness * 3600:
            return "WARNING", {"reason": "authoritative evidence stale", "severity": severity}
        status = finding.get("status")
        if status == "VERIFIED_REMEDIATED":
            if _v110_time(finding.get("closure_timestamp")) is None:
                return "WARNING", {"reason": "remediation closure evidence incomplete"}
            continue
        if status == "APPROVED_FALSE_POSITIVE":
            if finding.get("false_positive_approved") is not True:
                return "WARNING", {"reason": "false-positive authority incomplete"}
            continue
        if not finding.get("owner"):
            failures.append({"finding_id": finding["finding_id"], "reason": "missing required owner"})
            continue
        target = _v110_time(finding.get("remediation_target_date"))
        if target is None:
            failures.append({"finding_id": finding["finding_id"], "reason": "missing remediation target"})
            continue
        exception = finding.get("exception")
        if isinstance(exception, dict):
            approval = _v110_time(exception.get("approval_timestamp"))
            expiry = _v110_time(exception.get("expiration_timestamp"))
            valid = (exception.get("approving_authority") == "Security Authority" and bool(exception.get("justification")) and bool(exception.get("compensating_controls")) and bool(exception.get("owner")) and approval is not None and expiry is not None and expiry > reference_at and (expiry - approval).total_seconds() <= 90 * 86400)
            if valid:
                continue
            if expiry is not None and expiry <= reference_at:
                failures.append({"finding_id": finding["finding_id"], "reason": "expired exception"})
                continue
            return "WARNING", {"reason": "exception evidence incomplete or ambiguous"}
        if severity == "Low" and finding.get("risk_managed_disposition") is True:
            continue
        if target < reference_at:
            failures.append({"finding_id": finding["finding_id"], "reason": "overdue finding"})
    if failures:
        return "FAIL", {"noncompliant_findings": failures}
    return "PASS", {"finding_count": len(authority["findings"]), "source_identity": authority["source_identity"]}


def evaluate_rule(control_id: str, repository_path: Path, rule_registry_path: Path, authoritative_evidence: dict[str, Any] | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if control_id != "EMS-CTRL-023":
        return _base_evaluate_rule(control_id, repository_path, rule_registry_path)
    registry = json.loads(rule_registry_path.read_text(encoding="utf-8-sig"))
    rule = registry.get("rules", {}).get(control_id)
    if rule is None or not rule.get("supported"):
        raise ValueError("dependency_supply_chain rule not implemented for EMS-CTRL-023")
    outcome, detail = _v110_outcome(authoritative_evidence)
    now = datetime.now(UTC).isoformat()
    observation = {"control_id": control_id, "organization_level": True, "repository_projection": str(repository_path), "outcome": outcome, "detail": detail}
    text = json.dumps(observation, sort_keys=True)
    evidence_id = f"SUPPLY-{control_id}-{_sha256_text(text)[:16]}"
    evidence = [{"contract_version": "1.0", "wave": "2D", "evidence_id": evidence_id, "control_id": control_id, "evidence_type": rule["evidence_type"], "source": "organizational:vulnerability_management" if authoritative_evidence else f"repository:{repository_path}", "collected_at_utc": now, "sha256": _sha256_text(text), "observation": text, "provenance": {"collector": "hayes-verify", "collector_version": "0.1.0", "repository_path_or_url": str(repository_path), "collected_at_utc": now, "command_or_method": "organizational vulnerability evidence contract evaluation", "tool_versions": {}}, "sensitive": False}]
    result = {"contract_version": "1.0", "wave": "2D", "evaluation_state": "COMPLETE", "evidence_state": "INSUFFICIENT" if outcome == "WARNING" else "SUFFICIENT", "result_state": outcome, "evaluated_at_utc": now, "evidence_ids": [evidence_id], "rationale": detail.get("reason", "Authoritative organizational vulnerability evidence evaluated."), "assertions": [{"assertion_id": item["assertion_id"], "result": outcome, "detail": json.dumps(detail, sort_keys=True)} for item in rule["assertions"]], "promotion_state": "NOT_PROMOTED", "organization_level": True, "repository_projection_only": False}
    return evidence, result


def run(bundle, request: dict[str, Any], repository_path: Path, github_repo: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    del github_repo
    root = getattr(bundle, "root", None) or Path.cwd()
    evidence, result = evaluate_rule(request["control_id"], repository_path, Path(root) / "registry" / "dependency_supply_chain_rules.json", request.get("evidence_payload") or request.get("authoritative_evidence"))
    if request["control_id"] == "EMS-CTRL-023" and str(request.get("target_id", "")).startswith("REPO-") and result["result_state"] == "PASS":
        result["result_state"] = "WARNING"
        result["evidence_state"] = "INSUFFICIENT"
        result["rationale"] = "HUMAN_REVIEW: repository target is an organizational-evidence projection and cannot independently establish PASS."
    for item in evidence:
        item["request_id"] = request["request_id"]
        item["target_id"] = request["target_id"]
    result.update({"request_id": request["request_id"], "control_id": request["control_id"], "target_id": request["target_id"], "repository_projection_only": request.get("evaluation_role") == "PROJECTION"})
    bundle.validate_result(result)
    return evidence, result