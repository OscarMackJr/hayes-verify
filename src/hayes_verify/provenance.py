from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path


def git_commit_sha(repository: Path) -> str:
    cp = subprocess.run(
        ["git", "-C", str(repository), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return cp.stdout.strip()


def build_provenance(repository: Path, collector: str, version: str) -> dict:
    return {
        "collector": collector,
        "collector_version": version,
        "repository_path_or_url": str(repository.resolve()),
        "repository_commit_sha": git_commit_sha(repository),
        "collected_at_utc": datetime.now(UTC).isoformat(),
        "command_or_method": "repository inspection",
        "tool_versions": {},
    }
