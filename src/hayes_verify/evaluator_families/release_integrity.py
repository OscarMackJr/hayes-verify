from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

MANIFEST_FIELDS = (
    "release_id",
    "source_revision",
    "version",
    "artifact_inventory",
    "integrity_references",
    "approval_record",
    "timestamp",
)
SEMVER = re.compile(
    r"^v?(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-(?:0|[1-9][0-9]*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9][0-9]*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _release_manifests(root: Path) -> list[Path]:
    return sorted(path for path in root.glob("release/*/release_manifest.json") if path.is_file())


def _load_manifest(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON: {exc.msg}"
    if not isinstance(payload, dict):
        return None, "manifest root is not an object"
    return payload, None


def _inventory(manifest: dict[str, Any]) -> list[str] | None:
    inventory = manifest.get("artifact_inventory")
    if not isinstance(inventory, list):
        return None
    paths = []
    for item in inventory:
        if isinstance(item, str):
            paths.append(item)
        elif isinstance(item, dict) and isinstance(item.get("path"), str):
            paths.append(item["path"])
        else:
            return None
    return paths


def _warning(assertion_id: str, detail: dict[str, Any]) -> dict[str, Any]:
    return {
        "assertion_id": assertion_id,
        "result": "WARNING",
        "detail": json.dumps(detail, sort_keys=True),
    }


def _result(
    control_id: str,
    rule: dict[str, Any],
    repository_path: Path,
    assertions: list[dict[str, Any]],
    observations: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    has_fail = any(item["result"] == "FAIL" for item in assertions)
    has_warning = any(item["result"] == "WARNING" for item in assertions)
    result_state = "FAIL" if has_fail else "WARNING" if has_warning else "PASS"
    evidence_state = "INSUFFICIENT" if has_warning else "SUFFICIENT"
    now = datetime.now(UTC).isoformat()
    observation_text = json.dumps(observations, sort_keys=True)
    evidence_id = f"RELEASE-{control_id}-{_sha256_text(observation_text)[:16]}"
    evidence = [{
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
            "command_or_method": "repository release-integrity evidence inspection",
            "tool_versions": {},
        },
        "sensitive": False,
    }]
    rationale = (
        f"Release integrity rule {control_id} satisfied."
        if result_state == "PASS"
        else f"Release integrity rule {control_id} requires human review."
        if result_state == "WARNING"
        else f"Release integrity rule {control_id} not satisfied."
    )
    return evidence, {
        "contract_version": "1.0",
        "wave": "2D",
        "evaluation_state": "COMPLETE",
        "evidence_state": evidence_state,
        "result_state": result_state,
        "evaluated_at_utc": now,
        "evidence_ids": [evidence_id],
        "rationale": rationale,
        "assertions": assertions,
        "promotion_state": "NOT_PROMOTED",
    }


def _manifest_assertions(root: Path, control_id: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    paths = _release_manifests(root)
    observations: dict[str, Any] = {"release_manifests": [str(p.relative_to(root)) for p in paths]}
    if not paths:
        return [_warning("formal_release_applicability_unproven", observations)], observations
    assertions = []
    for path in paths:
        manifest, error = _load_manifest(path)
        detail: dict[str, Any] = {"manifest": str(path.relative_to(root))}
        if error:
            assertions.append({"assertion_id": "release_manifest_valid_json", "result": "FAIL", "detail": json.dumps({**detail, "error": error})})
            continue
        missing = [field for field in MANIFEST_FIELDS if field not in manifest]
        detail["missing_fields"] = missing
        assertions.append({"assertion_id": "release_manifest_required_fields", "result": "PASS" if not missing else "FAIL", "detail": json.dumps(detail, sort_keys=True)})
        if control_id == "EMS-CTRL-034":
            assertions.append(_warning("release_approval_and_immutable_binding_human_review", detail))
    observations["manifests_checked"] = len(paths)
    return assertions, observations


def _checksum_assertions(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    paths = _release_manifests(root)
    observations: dict[str, Any] = {"release_manifests": [str(p.relative_to(root)) for p in paths]}
    if not paths:
        return [_warning("formal_release_applicability_unproven", observations)], observations
    assertions = []
    for path in paths:
        manifest, error = _load_manifest(path)
        sums = path.parent / "SHA256SUMS"
        detail: dict[str, Any] = {"manifest": str(path.relative_to(root)), "checksum_file": str(sums.relative_to(root))}
        if error or manifest is None:
            assertions.append({"assertion_id": "manifest_for_checksum_inventory", "result": "FAIL", "detail": json.dumps({**detail, "error": error}, sort_keys=True)})
            continue
        inventory = _inventory(manifest)
        if inventory is None:
            assertions.append({"assertion_id": "manifest_artifact_inventory", "result": "FAIL", "detail": json.dumps(detail, sort_keys=True)})
            continue
        if not sums.is_file():
            assertions.append({"assertion_id": "sha256sums_present", "result": "FAIL", "detail": json.dumps(detail, sort_keys=True)})
            continue
        entries = {}
        for line in sums.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            match = re.fullmatch(r"([0-9a-f]{64})\s+\*?(.+)", line)
            if match:
                entries[match.group(2)] = match.group(1)
        missing = [item for item in inventory if item not in entries]
        invalid = len(entries) != len(sums.read_text(encoding="utf-8-sig", errors="replace").splitlines())
        assertions.append({"assertion_id": "sha256_inventory_coverage", "result": "PASS" if not missing and not invalid else "FAIL", "detail": json.dumps({**detail, "missing_artifacts": missing, "invalid_format": invalid}, sort_keys=True)})
        assertions.append(_warning("sha256_verification_record_and_release_gate_human_review", detail))
    return assertions, observations


def _version_assertions(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    paths = _release_manifests(root)
    observations: dict[str, Any] = {"release_manifests": [str(p.relative_to(root)) for p in paths]}
    if not paths:
        return [_warning("formal_release_applicability_unproven", observations)], observations
    assertions = []
    prefixes = set()
    for path in paths:
        manifest, error = _load_manifest(path)
        detail: dict[str, Any] = {"manifest": str(path.relative_to(root))}
        version = manifest.get("version") if manifest else None
        valid = isinstance(version, str) and bool(SEMVER.fullmatch(version))
        if isinstance(version, str) and valid:
            prefixes.add("v" if version.startswith("v") else "none")
        assertions.append({"assertion_id": "semver_release_version", "result": "PASS" if valid else "FAIL", "detail": json.dumps({**detail, "version": version, "error": error}, sort_keys=True)})
    assertions.append({"assertion_id": "consistent_release_tag_prefix", "result": "PASS" if len(prefixes) <= 1 else "FAIL", "detail": json.dumps({"prefixes": sorted(prefixes)}, sort_keys=True)})
    assertions.append(_warning("version_governance_effective_date_and_exception_human_review", {"manifest_count": len(paths)}))
    return assertions, observations


def evaluate_rule(control_id: str, repository_path: Path, rule_registry_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    registry = json.loads(rule_registry_path.read_text(encoding="utf-8-sig"))
    rule = registry.get("rules", {}).get(control_id)
    if rule is None or not rule.get("supported"):
        raise ValueError(f"release_integrity rule not implemented for {control_id}")
    if control_id == "EMS-CTRL-034":
        assertions, observations = _manifest_assertions(repository_path, control_id)
    elif control_id == "EMS-CTRL-035":
        assertions, observations = _checksum_assertions(repository_path)
    elif control_id == "EMS-CTRL-038":
        assertions, observations = _version_assertions(repository_path)
    else:
        observations = {"repository_path": str(repository_path), "evidence_authority": rule["evidence_authority"]}
        assertions = [_warning("authoritative_evidence_requires_human_review", observations)]
    observations.update({"control_id": control_id, "family": "release_integrity", "decision_ids": rule["decision_ids"]})
    return _result(control_id, rule, repository_path, assertions, observations)


def run(bundle, request: dict[str, Any], repository_path: Path, github_repo: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    del github_repo
    root = getattr(bundle, "root", None) or Path.cwd()
    evidence, result = evaluate_rule(request["control_id"], repository_path, Path(root) / "registry" / "release_integrity_rules.json")
    for item in evidence:
        item["request_id"] = request["request_id"]
        item["target_id"] = request["target_id"]
    result.update({"request_id": request["request_id"], "control_id": request["control_id"], "target_id": request["target_id"]})
    bundle.validate_result(result)
    return evidence, result
