"""Single-use AA4 run persistence guard."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class AA4RunAuthorizationError(ValueError):
    pass


def persist_authorized_run(authorization: dict[str, Any], *, now_utc: str, evidence: list[dict[str, Any]], results: list[dict[str, Any]], output_root: Path) -> dict[str, Any]:
    """Persist exactly one complete run only while a published authorization is active."""
    if authorization.get("status") != "ISSUED_ACTIVE_NOT_CONSUMED" or authorization.get("consumption", {}).get("state") != "NOT_CONSUMED":
        raise AA4RunAuthorizationError("authorization is not available")
    now = datetime.fromisoformat(now_utc)
    expiry = datetime.fromisoformat(authorization["window"]["expires_at_utc"])
    if now.tzinfo is None or now > expiry or now > datetime.now(UTC):
        raise AA4RunAuthorizationError("authorization is expired or time is invalid")
    run_id = authorization["scope"]["run_id"]
    if len(evidence) != 13 or len(results) != 13:
        raise AA4RunAuthorizationError("the authorized run requires exactly thirteen evidence records and results")
    run_dir = output_root / run_id
    if run_dir.exists():
        raise AA4RunAuthorizationError("run output already exists; retry is prohibited")
    (run_dir / "evidence").mkdir(parents=True)
    (run_dir / "results").mkdir()
    for item in evidence:
        (run_dir / "evidence" / f"{item['control_id']}.json").write_text(json.dumps(item, sort_keys=True), encoding="utf-8")
    for item in results:
        (run_dir / "results" / f"{item['control_id']}.json").write_text(json.dumps(item, sort_keys=True), encoding="utf-8")
    manifest = {"run_id": run_id, "persisted_at_utc": now_utc, "evidence_count": len(evidence), "result_count": len(results), "authorization_consumption_state": "CONSUMED"}
    (run_dir / "manifest.json").write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
    return manifest
