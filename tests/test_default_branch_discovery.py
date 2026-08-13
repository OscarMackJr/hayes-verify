from __future__ import annotations

import json
from pathlib import Path

from hayes_verify.pilots import github_collectors


def _provenance(repository_path, collector, version):
    return {
        "collector": collector,
        "collector_version": version,
        "repository_path_or_url": str(repository_path),
        "repository_commit_sha": "abcdef0",
        "collected_at_utc": "2026-08-13T00:00:00+00:00",
        "command_or_method": "test",
        "tool_versions": {},
    }


def test_encode_branch_with_slash():
    assert github_collectors._encode_branch("implementation/bootstrap") == (
        "implementation%2Fbootstrap"
    )


def test_default_branch_discovered_and_cached(monkeypatch):
    calls = []

    def fake_run(args):
        calls.append(args)
        return 0, '{"default_branch":"implementation/bootstrap"}', ""

    github_collectors._DEFAULT_BRANCH_CACHE.clear()
    monkeypatch.setattr(github_collectors, "_run_gh", fake_run)

    first = github_collectors._discover_default_branch("OscarMackJr/bluto")
    second = github_collectors._discover_default_branch("OscarMackJr/bluto")

    assert first == (True, "implementation/bootstrap", "")
    assert second == first
    assert calls == [["api", "repos/OscarMackJr/bluto"]]


def test_branch_protection_targets_encoded_default_branch(monkeypatch, tmp_path):
    calls = []

    def fake_run(args):
        calls.append(args)
        if args == ["api", "repos/OscarMackJr/bluto"]:
            return 0, '{"default_branch":"implementation/bootstrap"}', ""
        if args == [
            "api",
            "repos/OscarMackJr/bluto/branches/implementation%2Fbootstrap/protection",
        ]:
            return (
                0,
                '{"required_pull_request_reviews":{"required_approving_review_count":1}}',
                "",
            )
        raise AssertionError(args)

    github_collectors._DEFAULT_BRANCH_CACHE.clear()
    monkeypatch.setattr(github_collectors, "_run_gh", fake_run)
    monkeypatch.setattr(github_collectors, "build_provenance", _provenance)

    request = {
        "request_id": "REQ-009",
        "control_id": "EMS-CTRL-009",
        "target_id": "REPO-001",
    }
    evidence = github_collectors.collect_branch_protection(
        request,
        tmp_path,
        "OscarMackJr/bluto",
    )

    obs = json.loads(evidence[0]["observation"])
    assert obs["default_branch"] == "implementation/bootstrap"
    assert obs["evaluated_branch"] == "implementation/bootstrap"
    assert obs["encoded_branch"] == "implementation%2Fbootstrap"
    assert obs["api_success"] is True
    assert calls[-1] == [
        "api",
        "repos/OscarMackJr/bluto/branches/implementation%2Fbootstrap/protection",
    ]


def test_pr_review_targets_encoded_default_branch(monkeypatch, tmp_path):
    calls = []
    expected_endpoint = (
        "repos/OscarMackJr/bluto/branches/implementation%2Fbootstrap/protection/"
        "required_pull_request_reviews"
    )

    def fake_run(args):
        calls.append(args)
        if args == ["api", "repos/OscarMackJr/bluto"]:
            return 0, '{"default_branch":"implementation/bootstrap"}', ""
        if args == ["api", expected_endpoint]:
            return 0, '{"required_approving_review_count":1}', ""
        raise AssertionError(args)

    github_collectors._DEFAULT_BRANCH_CACHE.clear()
    monkeypatch.setattr(github_collectors, "_run_gh", fake_run)
    monkeypatch.setattr(github_collectors, "build_provenance", _provenance)

    request = {
        "request_id": "REQ-010",
        "control_id": "EMS-CTRL-010",
        "target_id": "REPO-001",
    }
    evidence = github_collectors.collect_pr_review(
        request,
        tmp_path,
        "OscarMackJr/bluto",
    )

    obs = json.loads(evidence[0]["observation"])
    assert obs["default_branch"] == "implementation/bootstrap"
    assert obs["evaluated_branch"] == "implementation/bootstrap"
    assert obs["encoded_branch"] == "implementation%2Fbootstrap"
    assert calls[-1] == ["api", expected_endpoint]


def test_default_branch_discovery_failure_is_fail_closed(monkeypatch, tmp_path):
    def fake_run(args):
        assert args == ["api", "repos/OscarMackJr/bluto"]
        return 1, "", "gh: Not Found (HTTP 404)"

    github_collectors._DEFAULT_BRANCH_CACHE.clear()
    monkeypatch.setattr(github_collectors, "_run_gh", fake_run)
    monkeypatch.setattr(github_collectors, "build_provenance", _provenance)

    request = {
        "request_id": "REQ-009",
        "control_id": "EMS-CTRL-009",
        "target_id": "REPO-001",
    }
    evidence = github_collectors.collect_branch_protection(
        request,
        tmp_path,
        "OscarMackJr/bluto",
    )

    obs = json.loads(evidence[0]["observation"])
    assert obs["api_success"] is False
    assert obs["default_branch_discovery_success"] is False
    assert obs["protected"] is False


def test_no_hardcoded_main_branch_in_module():
    source = Path(github_collectors.__file__)
    text = source.read_text(encoding="utf-8")
    assert "/branches/main/" not in text
