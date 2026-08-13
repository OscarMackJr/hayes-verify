from __future__ import annotations

import subprocess

from hayes_verify.pilots import github_collectors


class DummyCompleted:
    def __init__(self):
        self.returncode = 0
        self.stdout = "{}"
        self.stderr = ""


def test_run_gh_never_appends_repo(monkeypatch):
    captured = {}

    def fake_run(cmd, capture_output, text, check):
        captured["cmd"] = cmd
        captured["capture_output"] = capture_output
        captured["text"] = text
        captured["check"] = check
        return DummyCompleted()

    monkeypatch.setattr(subprocess, "run", fake_run)

    rc, out, err = github_collectors._run_gh(
        ["api", "repos/OscarMackJr/bluto"]
    )

    assert rc == 0
    assert out == "{}"
    assert err == ""
    assert captured["cmd"] == [
        "gh",
        "api",
        "repos/OscarMackJr/bluto",
    ]
    assert "--repo" not in captured["cmd"]
    assert captured["check"] is False


def test_repository_metadata_endpoint_does_not_use_repo_flag(monkeypatch):
    captured = {}

    def fake_run(cmd, capture_output, text, check):
        captured["cmd"] = cmd
        return DummyCompleted()

    monkeypatch.setattr(subprocess, "run", fake_run)

    github_collectors._run_gh(
        ["api", "repos/OscarMackJr/bluto"]
    )

    assert captured["cmd"] == [
        "gh",
        "api",
        "repos/OscarMackJr/bluto",
    ]
    assert "--repo" not in captured["cmd"]
