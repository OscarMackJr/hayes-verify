"""Consume, validate, and snapshot EMS-controlled repository identities.

This module deliberately contains no repository-ID allocation logic.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

REPOSITORY_ID_RE = re.compile(r"^REPO-(?:[1-9][0-9]*|EMS)$")
LIFECYCLE_STATES = frozenset({"ACTIVE", "RENAMED", "TRANSFERRED", "ARCHIVED", "RETIRED", "DELETED", "REPLACED"})
LOCAL_PATH_FIELDS = frozenset({"local_path", "repository_path", "execution_path", "filesystem_path"})
IDENTITY_FIELDS = frozenset({"repository_id", "repository_name", "repository_owner_or_org", "repository_host", "repository_url", "lifecycle_state", "default_branch"})


class IdentityValidationError(ValueError):
    """Raised when an EMS-controlled identity cannot be safely consumed."""


@dataclass(frozen=True)
class RepositoryIdentity:
    repository_id: str
    repository_name: str
    repository_owner_or_org: str
    repository_host: str
    repository_url: str
    lifecycle_state: str
    default_branch: str | None = None


def _parse_github(value: str) -> tuple[str, str, str, str]:
    owner, sep, name = value.strip().strip("/").partition("/")
    if not sep or not owner or not name:
        raise IdentityValidationError("github identity must be owner/name")
    return "github.com", owner, name, f"https://github.com/{owner}/{name}"


def _identity_from_record(record: dict[str, Any]) -> RepositoryIdentity:
    prohibited = LOCAL_PATH_FIELDS.intersection(record)
    if prohibited:
        raise IdentityValidationError(f"local execution path is not controlled identity: {sorted(prohibited)}")
    repository_id = str(record.get("repository_id", record.get("id", "")))
    if not REPOSITORY_ID_RE.fullmatch(repository_id):
        raise IdentityValidationError(f"malformed controlled repository_id: {repository_id!r}")
    if "github" in record and not record.get("repository_host"):
        host, owner, name, url = _parse_github(str(record["github"]))
    else:
        host = str(record.get("repository_host", ""))
        owner = str(record.get("repository_owner_or_org", record.get("owner", "")))
        name = str(record.get("repository_name", record.get("name", "")))
        url = str(record.get("repository_url", ""))
    state = str(record.get("lifecycle_state", "ACTIVE")).upper()
    if state not in LIFECYCLE_STATES:
        raise IdentityValidationError(f"unsupported lifecycle_state: {state!r}")
    if not all((host, owner, name, url)):
        raise IdentityValidationError("controlled identity requires host, owner, name, and URL")
    return RepositoryIdentity(repository_id, name, owner, host, url, state, record.get("default_branch"))


def consume_controlled_identities(authority: dict[str, Any]) -> dict[str, RepositoryIdentity]:
    """Consume a controlled identity authority; never allocate or derive IDs."""
    rows = authority.get("repositories", authority.get("identities"))
    if not isinstance(rows, list):
        raise IdentityValidationError("identity authority must contain repositories or identities list")
    identities: dict[str, RepositoryIdentity] = {}
    coordinates: set[tuple[str, str, str]] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise IdentityValidationError("identity record must be an object")
        identity = _identity_from_record(row)
        if identity.repository_id in identities:
            raise IdentityValidationError(f"duplicate controlled repository_id: {identity.repository_id}")
        coordinate = (identity.repository_host.lower(), identity.repository_owner_or_org.lower(), identity.repository_name.lower())
        if coordinate in coordinates:
            raise IdentityValidationError("duplicate canonical repository host/owner/name")
        identities[identity.repository_id] = identity
        coordinates.add(coordinate)
    return identities


def repository_snapshot(identity: RepositoryIdentity, *, captured_at: str, authority_reference: str, authority_sha256: str) -> dict[str, Any]:
    """Build the WS1 immutable input snapshot; no local path or classification data is admitted."""
    if not authority_reference or not authority_sha256:
        raise IdentityValidationError("authority reference and SHA-256 are required")
    try:
        datetime.fromisoformat(captured_at)
    except ValueError as exc:
        raise IdentityValidationError("captured_at must be ISO-8601") from exc
    return {"repository_id": identity.repository_id, "repository_name": identity.repository_name, "repository_owner_or_org": identity.repository_owner_or_org, "repository_host": identity.repository_host, "repository_url": identity.repository_url, "lifecycle_state": identity.lifecycle_state, "default_branch": identity.default_branch, "captured_at": captured_at, "authority_reference": authority_reference, "authority_sha256": authority_sha256}


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
