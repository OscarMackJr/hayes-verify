from __future__ import annotations

import hashlib
from pathlib import Path

from hayes_verify.provenance import build_provenance


def collect_repository_evidence(request: dict) -> list[dict]:
    repo = Path(request["repository_name"])
    if not repo.exists():
        return []

    evidence = []
    for candidate in [repo / "README.md", repo / ".github" / "workflows"]:
        if not candidate.exists():
            continue

        if candidate.is_file():
            sha = hashlib.sha256(candidate.read_bytes()).hexdigest()
            evidence.append(
                {
                    "contract_version": "1.0",
                    "wave": "2D",
                    "evidence_id": f"{request['request_id']}::{candidate.name}",
                    "request_id": request["request_id"],
                    "control_id": request["control_id"],
                    "target_id": request["target_id"],
                    "evidence_type": "REPOSITORY_FILE",
                    "source": str(candidate),
                    "collected_at_utc": build_provenance(repo, "hayes-verify", "0.1.0")[
                        "collected_at_utc"
                    ],
                    "sha256": sha,
                    "observation": "Repository artifact discovered.",
                    "provenance": build_provenance(repo, "hayes-verify", "0.1.0"),
                    "sensitive": False,
                }
            )
    return evidence
