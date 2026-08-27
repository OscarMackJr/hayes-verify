from pathlib import Path

import pytest

from hayes_verify.aa4_run_orchestration import AA4RunAuthorizationError, persist_authorized_run


def authorization():
    return {"status": "ISSUED_ACTIVE_NOT_CONSUMED", "scope": {"run_id": "AA4-BLUTO-ONE-RUN-001"}, "window": {"expires_at_utc": "2099-01-01T00:00:00Z"}, "consumption": {"state": "NOT_CONSUMED"}}


def records(kind):
    return [{"control_id": f"EMS-CTRL-{n:03d}", kind: True} for n in range(1, 14)]


def test_persists_exactly_one_complete_run(tmp_path: Path):
    manifest = persist_authorized_run(authorization(), now_utc="2026-08-27T12:00:00Z", evidence=records("evidence"), results=records("result"), output_root=tmp_path)
    assert manifest["authorization_consumption_state"] == "CONSUMED"


def test_rejects_partial_run(tmp_path: Path):
    with pytest.raises(AA4RunAuthorizationError):
        persist_authorized_run(authorization(), now_utc="2026-08-27T12:00:00Z", evidence=[], results=[], output_root=tmp_path)
