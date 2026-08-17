"""RP1A durable, evaluator-free archive-assessment workflow foundation."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import uuid
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from jsonschema import Draft202012Validator, FormatChecker

WORKFLOW_FORMAT_VERSION = "1.0"
STAGES = ("INTAKE", "CLASSIFICATION", "APPLICABILITY", "PLAN", "AUTHORITY_PREFLIGHT", "EXECUTION", "REVIEW", "PACKAGE")
STATUSES = ("CREATED", "RUNNING", "AWAITING_HUMAN_INPUT", "BLOCKED", "FAILED", "PARTIAL", "COMPLETE")


class ArchiveWorkflowError(RuntimeError):
    """Fail-closed workflow integrity or lifecycle error."""


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def archive_target_id(source_zip_sha256: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{64}", source_zip_sha256):
        raise ArchiveWorkflowError("source ZIP SHA-256 must be lowercase 64-character hex")
    return f"ARCHIVE-{source_zip_sha256[:24].upper()}"


def workflow_id(target_id: str, now: str | None = None) -> str:
    if not re.fullmatch(r"ARCHIVE-[0-9A-F]{24}", target_id):
        raise ArchiveWorkflowError("invalid archive target ID")
    stamp = (now or _utc_now()).replace("-", "").replace(":", "").replace("Z", "").replace("+", "")
    return f"ARCHIVE-ASSESS-{target_id.removeprefix('ARCHIVE-')[:16]}-{stamp}-{uuid.uuid4().hex[:8].upper()}"


def _write_json_new(path: Path, value: Any) -> None:
    if path.exists():
        raise ArchiveWorkflowError(f"refusing to overwrite immutable artifact: {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_canonical_bytes(value) + b"\n")


def _write_json_pointer(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(_canonical_bytes(value) + b"\n")
    temporary.replace(path)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ArchiveWorkflowError(f"invalid JSON artifact: {path}") from exc
    if not isinstance(value, dict):
        raise ArchiveWorkflowError(f"JSON artifact must be an object: {path}")
    return value


def _run_root(output_root: Path, target_id: str, run_id: str) -> Path:
    root = output_root.resolve()
    candidate = (root / "archive-assessment" / "runs" / target_id / run_id).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ArchiveWorkflowError("run directory escapes output root") from exc
    return candidate


def preflight_archive(path: Path, *, non_production: bool) -> dict[str, Any]:
    if not non_production:
        raise ArchiveWorkflowError("explicit non-production acknowledgement is required")
    if not path.is_file() or not path.stat().st_size:
        raise ArchiveWorkflowError("archive input must be a non-empty readable file")
    if not zipfile.is_zipfile(path):
        raise ArchiveWorkflowError("archive input is not a supported ZIP")
    source_sha = sha256_file(path)
    return {"source_zip_sha256": source_sha, "archive_target_id": archive_target_id(source_sha), "archive_size_bytes": path.stat().st_size}


def _state_path(run_dir: Path) -> Path:
    return run_dir / "workflow" / "archive_assessment_workflow_state.json"


def _manifest_path(run_dir: Path) -> Path:
    return run_dir / "workflow" / "archive_assessment_workflow_manifest.json"


def _input_path(run_dir: Path) -> Path:
    return run_dir / "workflow" / "archive_assessment_input_manifest.json"


def _events_path(run_dir: Path) -> Path:
    return run_dir / "logs" / "workflow_events.jsonl"


def _checkpoint_dir(run_dir: Path) -> Path:
    return run_dir / "checkpoints"


def _validate_state(state: dict[str, Any]) -> None:
    required = {"schema_version", "workflow_id", "archive_target_id", "source_zip_sha256", "assessment_run_id", "workflow_status", "current_stage", "created_at", "updated_at", "non_production", "output_root_identity", "authority_context", "completed_stages", "predecessor_state_sha256", "state_revision"}
    missing = required - state.keys()
    if missing or state.get("schema_version") != WORKFLOW_FORMAT_VERSION:
        raise ArchiveWorkflowError(f"unsupported or incomplete workflow state: missing={sorted(missing)}")
    if state["current_stage"] not in STAGES or state["workflow_status"] not in STATUSES:
        raise ArchiveWorkflowError("unsupported workflow stage or status")
    if state["assessment_run_id"] != state["workflow_id"]:
        raise ArchiveWorkflowError("workflow and assessment run identity mismatch")
    if state["archive_target_id"] != archive_target_id(state["source_zip_sha256"]):
        raise ArchiveWorkflowError("archive target does not match source ZIP identity")
    completed = state["completed_stages"]
    if completed != [stage for stage in STAGES if STAGES.index(stage) < STAGES.index(state["current_stage"])]:
        raise ArchiveWorkflowError("completed stages are not a valid immutable prefix")


def _event(run_dir: Path, event_type: str, state: dict[str, Any]) -> None:
    record = {"event_type": event_type, "at_utc": state["updated_at"], "workflow_id": state["workflow_id"], "stage": state["current_stage"], "workflow_status": state["workflow_status"], "state_revision": state["state_revision"]}
    _events_path(run_dir).parent.mkdir(parents=True, exist_ok=True)
    with _events_path(run_dir).open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")


def _write_checkpoint(run_dir: Path, state: dict[str, Any], *, event_type: str) -> str:
    prior = state.get("last_checkpoint_sha256")
    checkpoint = {"schema_version": WORKFLOW_FORMAT_VERSION, "workflow_id": state["workflow_id"], "revision": state["state_revision"], "stage": state["current_stage"], "workflow_status": state["workflow_status"], "timestamp": state["updated_at"], "input_hashes": {"input_manifest_sha256": state["input_manifest_sha256"]}, "output_hashes": {}, "authority_hashes": state["authority_context"], "predecessor_checkpoint_sha256": prior, "next_allowed_stages": list(_next_stages(state)), "resume_allowed": state["workflow_status"] in {"AWAITING_HUMAN_INPUT", "BLOCKED", "RUNNING"}, "resume_requirements": state.get("resume_requirements", []), "event_type": event_type, "state_sha256": sha256_json({k:v for k,v in state.items() if k != "last_checkpoint_sha256"})}
    path = _checkpoint_dir(run_dir) / f"{state['state_revision']:04d}-{state['current_stage']}-{event_type}.json"
    _write_json_new(path, checkpoint)
    return sha256_file(path)


def _next_stages(state: dict[str, Any]) -> tuple[str, ...]:
    if state["workflow_status"] in {"BLOCKED", "FAILED", "PARTIAL", "COMPLETE"}:
        return ()
    index = STAGES.index(state["current_stage"])
    return (STAGES[index + 1],) if index < len(STAGES) - 1 else ()


def _persist_transition(run_dir: Path, state: dict[str, Any], event_type: str) -> dict[str, Any]:
    _validate_state(state)
    state["updated_at"] = _utc_now()
    state["state_revision"] += 1
    state["predecessor_state_sha256"] = sha256_json(_read_json(_state_path(run_dir)))
    checkpoint_sha = _write_checkpoint(run_dir, state, event_type=event_type)
    state["last_checkpoint_sha256"] = checkpoint_sha
    _write_json_pointer(_state_path(run_dir), state)
    _event(run_dir, event_type, state)
    return state


def create_workflow(archive_path: Path, output_root: Path, *, non_production: bool, authority_context: dict[str, Any] | None = None, now: str | None = None) -> Path:
    preflight = preflight_archive(archive_path, non_production=non_production)
    created = now or _utc_now()
    run_id = workflow_id(preflight["archive_target_id"], created)
    run_dir = _run_root(output_root, preflight["archive_target_id"], run_id)
    if run_dir.exists():
        raise ArchiveWorkflowError("workflow run already exists")
    for name in ("workflow", "inputs", "checkpoints", "logs", "generated"):
        (run_dir / name).mkdir(parents=True, exist_ok=False)
    input_manifest = {"schema_version": WORKFLOW_FORMAT_VERSION, "workflow_id": run_id, "archive_target_id": preflight["archive_target_id"], "source_archive_filename": archive_path.name, "source_zip_sha256": preflight["source_zip_sha256"], "archive_size_bytes": preflight["archive_size_bytes"], "non_production": True, "created_at": created, "workflow_format_version": WORKFLOW_FORMAT_VERSION}
    _write_json_new(_input_path(run_dir), input_manifest)
    state = {"schema_version": WORKFLOW_FORMAT_VERSION, "workflow_id": run_id, "archive_target_id": preflight["archive_target_id"], "source_zip_sha256": preflight["source_zip_sha256"], "assessment_run_id": run_id, "workflow_status": "CREATED", "current_stage": "INTAKE", "created_at": created, "updated_at": created, "non_production": True, "output_root_identity": hashlib.sha256(str(output_root.resolve()).encode()).hexdigest(), "authority_context": authority_context or {}, "completed_stages": [], "blocked_reason": None, "failure_reason": None, "awaiting_input_type": None, "predecessor_state_sha256": None, "state_revision": 0, "input_manifest_sha256": sha256_file(_input_path(run_dir)), "last_checkpoint_sha256": None, "resume_requirements": []}
    _validate_state(state)
    _write_json_new(_state_path(run_dir), state)
    checkpoint_sha = _write_checkpoint(run_dir, state, event_type="WORKFLOW_CREATED")
    state["last_checkpoint_sha256"] = checkpoint_sha
    _write_json_pointer(_state_path(run_dir), state)
    manifest = {"schema_version": WORKFLOW_FORMAT_VERSION, "workflow_id": run_id, "archive_target_id": state["archive_target_id"], "source_zip_sha256": state["source_zip_sha256"], "initial_state_sha256": sha256_json({k:v for k,v in state.items() if k != "last_checkpoint_sha256"}), "input_manifest_sha256": state["input_manifest_sha256"], "checkpoint_root": "checkpoints/0000-INTAKE-WORKFLOW_CREATED.json", "software_version": "unknown", "workflow_format_version": WORKFLOW_FORMAT_VERSION, "output_structure_version": "1.0"}
    _write_json_new(_manifest_path(run_dir), manifest)
    _event(run_dir, "WORKFLOW_CREATED", state)
    return run_dir


def load_workflow(run_dir: Path) -> dict[str, Any]:
    state = _read_json(_state_path(run_dir))
    _validate_state(state)
    input_manifest = _read_json(_input_path(run_dir))
    if sha256_file(_input_path(run_dir)) != state.get("input_manifest_sha256") or input_manifest.get("source_zip_sha256") != state["source_zip_sha256"]:
        raise ArchiveWorkflowError("input manifest integrity failure")
    validate_checkpoint_chain(run_dir)
    return state


def validate_checkpoint_chain(run_dir: Path) -> bool:
    state = _read_json(_state_path(run_dir))
    records=[]
    for path in sorted(_checkpoint_dir(run_dir).glob("*.json")):
        record=_read_json(path); records.append((path,record,sha256_file(path)))
    if not records:
        raise ArchiveWorkflowError("checkpoint chain missing")
    prior=None
    for path, record, digest in records:
        if record.get("predecessor_checkpoint_sha256") != prior:
            raise ArchiveWorkflowError(f"checkpoint chain integrity failure: {path.name}")
        prior=digest
    if state.get("last_checkpoint_sha256") != prior:
        raise ArchiveWorkflowError("current state does not bind the final checkpoint")
    return True


def advance_workflow(run_dir: Path, next_stage: str) -> dict[str, Any]:
    state=load_workflow(run_dir)
    if state["workflow_status"] not in {"CREATED","RUNNING"} or next_stage not in _next_stages(state):
        raise ArchiveWorkflowError(f"illegal transition {state['current_stage']} -> {next_stage}")
    state["completed_stages"] = [stage for stage in STAGES if STAGES.index(stage) < STAGES.index(next_stage)]
    state["current_stage"] = next_stage
    state["workflow_status"] = "RUNNING"
    state["awaiting_input_type"] = None; state["blocked_reason"] = None; state["failure_reason"] = None; state["resume_requirements"] = []
    return _persist_transition(run_dir,state,"STAGE_ENTERED")


def pause_workflow(run_dir: Path, *, input_type: str, resume_requirements: list[str]) -> dict[str, Any]:
    state=load_workflow(run_dir)
    if state["workflow_status"] not in {"CREATED","RUNNING"} or not input_type:
        raise ArchiveWorkflowError("cannot pause workflow in current status")
    state["workflow_status"]="AWAITING_HUMAN_INPUT"; state["awaiting_input_type"]=input_type; state["resume_requirements"]=list(resume_requirements)
    return _persist_transition(run_dir,state,"WORKFLOW_PAUSED")


def block_workflow(run_dir: Path, reason: str) -> dict[str, Any]:
    state=load_workflow(run_dir)
    if not reason: raise ArchiveWorkflowError("blocked reason is required")
    state["workflow_status"]="BLOCKED"; state["blocked_reason"]=reason
    return _persist_transition(run_dir,state,"WORKFLOW_BLOCKED")


def fail_workflow(run_dir: Path, reason: str) -> dict[str, Any]:
    state=load_workflow(run_dir)
    if not reason: raise ArchiveWorkflowError("failure reason is required")
    state["workflow_status"]="FAILED"; state["failure_reason"]=reason
    return _persist_transition(run_dir,state,"WORKFLOW_FAILED")


def resume_workflow(run_dir: Path) -> dict[str, Any]:
    state=load_workflow(run_dir)
    if state["workflow_status"] not in {"AWAITING_HUMAN_INPUT","BLOCKED"}:
        raise ArchiveWorkflowError("workflow is not resumable in current status")
    state["workflow_status"]="RUNNING"; state["awaiting_input_type"]=None; state["blocked_reason"]=None; state["resume_requirements"]=[]
    return _persist_transition(run_dir,state,"WORKFLOW_RESUMED")


def get_status(run_dir: Path) -> dict[str, Any]:
    state=load_workflow(run_dir)
    return {"workflow_id":state["workflow_id"],"archive_target_id":state["archive_target_id"],"source_zip_sha256":state["source_zip_sha256"],"workflow_status":state["workflow_status"],"current_stage":state["current_stage"],"completed_stages":state["completed_stages"],"awaiting_input_type":state["awaiting_input_type"],"blocked_reason":state["blocked_reason"],"last_checkpoint_sha256":state["last_checkpoint_sha256"],"resume_allowed":state["workflow_status"] in {"AWAITING_HUMAN_INPUT","BLOCKED","RUNNING"},"authority_context":state["authority_context"]}


class StageHandler(Protocol):
    def __call__(self, state: dict[str, Any]) -> str: ...


def run_stage_handler(run_dir: Path, handler: StageHandler) -> dict[str, Any]:
    state=load_workflow(run_dir); outcome=handler(state)
    if outcome == "STAGE_COMPLETE": return state
    if outcome == "AWAITING_HUMAN_INPUT": return pause_workflow(run_dir,input_type="UNSPECIFIED",resume_requirements=[])
    if outcome == "BLOCKED": return block_workflow(run_dir,"stage handler reported BLOCKED")
    if outcome == "FAILED": return fail_workflow(run_dir,"stage handler reported FAILED")
    raise ArchiveWorkflowError("unsupported stage handler outcome")


def _immutable(run_dir: Path, relative: str, value: Any) -> tuple[Path, str]:
    path = run_dir / relative
    _write_json_new(path, value)
    return path, sha256_file(path)


def _authority_path(run_dir: Path) -> Path:
    return run_dir / "workflow" / "archive_assessment_authority_context.json"


def initialize_intake_authority_and_classification(
    run_dir: Path, *, hayes_authority_root: Path, ems_authority_root: Path
) -> dict[str, Any]:
    """Perform RP1B work only: safe intake, authority freeze, request, and pause."""
    from .archive_assessment_authority import discover_authority
    from .archive_assessment_intake import safe_intake

    state = load_workflow(run_dir)
    if state["current_stage"] != "INTAKE" or state["workflow_status"] != "CREATED":
        raise ArchiveWorkflowError("RP1B initialization requires a newly created INTAKE workflow")
    source_name = _read_json(_input_path(run_dir))["source_archive_filename"]
    # The archive path is supplied only for local operation; it is never persisted as identity.
    archive_path = Path(_read_json(run_dir / "logs" / "local_execution.json").get("archive_path", ""))
    if not archive_path.is_file() or archive_path.name != source_name:
        raise ArchiveWorkflowError("local archive execution input unavailable")
    _event(run_dir, "ARCHIVE_INTAKE_STARTED", state)
    try:
        intake = safe_intake(
            archive_path,
            run_dir / "execution" / "archive-content",
            workflow_id=state["workflow_id"],
            archive_target_id=state["archive_target_id"],
            source_zip_sha256=state["source_zip_sha256"],
        )
    except ArchiveWorkflowError:
        state["workflow_status"] = "FAILED"; state["failure_reason"] = "ARCHIVE_INTAKE_FAILED"
        _persist_transition(run_dir, state, "ARCHIVE_INTAKE_FAILED")
        raise
    _, source_sha = _immutable(run_dir, "inputs/archive_source_manifest.json", intake["source_manifest"])
    _, content_sha = _immutable(run_dir, "inputs/archive_extracted_content_manifest.json", intake["content_manifest"])
    state["intake"] = {"source_manifest_sha256": source_sha, "content_manifest_sha256": content_sha, "extraction_integrity_state": "PASS"}
    _persist_transition(run_dir, state, "ARCHIVE_INTAKE_COMPLETE")
    _event(run_dir, "AUTHORITY_DISCOVERY_STARTED", state)
    try:
        context = discover_authority(hayes_authority_root, ems_authority_root)
    except ArchiveWorkflowError as exc:
        state = load_workflow(run_dir); state["workflow_status"] = "BLOCKED"; state["blocked_reason"] = str(exc)
        _persist_transition(run_dir, state, "AUTHORITY_BLOCKED")
        raise
    _, context_sha = _immutable(run_dir, "workflow/archive_assessment_authority_context.json", context)
    state = load_workflow(run_dir); state["authority_context"] = context; state["authority_context_sha256"] = context_sha
    _persist_transition(run_dir, state, "AUTHORITY_FROZEN")
    _event(run_dir, "AUTHORITY_FROZEN", state)
    advance_workflow(run_dir, "CLASSIFICATION")
    state = load_workflow(run_dir)
    request = {"schema_version": WORKFLOW_FORMAT_VERSION, "workflow_id": state["workflow_id"], "archive_target_id": state["archive_target_id"], "source_zip_sha256": state["source_zip_sha256"], "authority_context_sha256": context_sha, "request_version": "1.0", "created_at": _utc_now(), "required_fields": ["production", "internet_exposed", "contains_customer_data", "ai_enabled", "owner", "tier", "service_criticality", "data_classification"]}
    _, request_sha = _immutable(run_dir, "classification/archive_classification_request.json", request)
    markdown = "# Archive Classification Request\n\n" + "\n".join([f"- {field}: provide KNOWN value or UNKNOWN with confirmed_by, confirmed_at, and basis." for field in request["required_fields"]]) + f"\n\nWorkflow: `{state['workflow_id']}`\nArchive: `{state['archive_target_id']}`\nSource SHA: `{state['source_zip_sha256']}`\n"
    text_path = run_dir / "classification" / "ARCHIVE_CLASSIFICATION_REQUEST.md"; text_path.parent.mkdir(parents=True, exist_ok=True); text_path.write_text(markdown, encoding="utf-8")
    state = load_workflow(run_dir); state["classification_request_sha256"] = request_sha
    pause_workflow(run_dir, input_type="ARCHIVE_CLASSIFICATION_RESPONSE", resume_requirements=["schema-valid attributable classification response bound to workflow and authority context"])
    _event(run_dir, "CLASSIFICATION_REQUEST_CREATED", load_workflow(run_dir))
    return get_status(run_dir)


def _validate_response(response: dict[str, Any], state: dict[str, Any]) -> None:
    schema_path = Path(__file__).resolve().parents[2] / "schemas" / "archive_assessment_classification_response.schema.json"
    schema = _read_json(schema_path)
    errors = sorted(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(response), key=str)
    if errors:
        raise ArchiveWorkflowError("invalid classification response schema")
    for key in ("workflow_id", "archive_target_id", "source_zip_sha256", "authority_context_sha256"):
        expected = state["authority_context_sha256"] if key == "authority_context_sha256" else state[key]
        if response[key] != expected:
            raise ArchiveWorkflowError(f"classification response binding mismatch: {key}")
    for field in response["fields"].values():
        if field["state"] == "UNKNOWN" and field["value"] not in (None, "UNKNOWN"):
            raise ArchiveWorkflowError("UNKNOWN classification must not carry a known value")


def consume_classification_response(run_dir: Path, response_path: Path) -> dict[str, Any]:
    state = load_workflow(run_dir)
    if state["current_stage"] == "APPLICABILITY":
        existing = run_dir / "classification" / "archive_classification_response.json"
        if existing.is_file() and sha256_file(existing) == sha256_file(response_path):
            return get_status(run_dir)
        raise ArchiveWorkflowError("classification already consumed; successor workflow required for a conflicting response")
    if state["current_stage"] != "CLASSIFICATION" or state["workflow_status"] != "AWAITING_HUMAN_INPUT":
        raise ArchiveWorkflowError("workflow is not awaiting classification")
    response = _read_json(response_path); _validate_response(response, state)
    raw = response_path.read_bytes(); destination = run_dir / "classification" / "archive_classification_response.json"
    if destination.exists():
        if destination.read_bytes() == raw: return get_status(run_dir)
        raise ArchiveWorkflowError("classification response overwrite refused")
    destination.parent.mkdir(parents=True, exist_ok=True); destination.write_bytes(raw)
    raw_sha = sha256_file(destination)
    unknown_count = sum(item["state"] == "UNKNOWN" for item in response["fields"].values())
    snapshot = {"schema_version": "1.0", "workflow_id": state["workflow_id"], "archive_target_id": state["archive_target_id"], "source_zip_sha256": state["source_zip_sha256"], "authority_context_sha256": state["authority_context_sha256"], "raw_response_sha256": raw_sha, "fields": response["fields"], "remaining_unknown_count": unknown_count, "created_at": _utc_now()}
    _, snapshot_sha = _immutable(run_dir, "classification/archive_classification_snapshot.json", snapshot)
    resume_workflow(run_dir)
    state = load_workflow(run_dir); state["classification_response_sha256"] = raw_sha; state["classification_snapshot_sha256"] = snapshot_sha
    _persist_transition(run_dir, state, "CLASSIFICATION_RESPONSE_ACCEPTED")
    advance_workflow(run_dir, "APPLICABILITY")
    _event(run_dir, "WORKFLOW_ADVANCED_TO_APPLICABILITY", load_workflow(run_dir))
    return get_status(run_dir)


def _print(value: Any, as_json: bool) -> None:
    if as_json:
        print(json.dumps(value, sort_keys=True))
    else:
        for key, item in value.items():
            print(f"{key}: {item}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m hayes_verify.archive_assessment")
    commands = parser.add_subparsers(dest="command", required=True)
    assess = commands.add_parser("assess"); assess.add_argument("archive", type=Path); assess.add_argument("--output-root", type=Path, required=True); assess.add_argument("--hayes-authority-root", type=Path, required=True); assess.add_argument("--ems-authority-root", type=Path, required=True); assess.add_argument("--non-production", action="store_true"); assess.add_argument("--json", action="store_true")
    status = commands.add_parser("status"); status.add_argument("run_dir", type=Path); status.add_argument("--json", action="store_true")
    resume = commands.add_parser("resume"); resume.add_argument("run_dir", type=Path); resume.add_argument("--classification-response", type=Path); resume.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "assess":
            run = create_workflow(args.archive, args.output_root, non_production=args.non_production)
            _write_json_pointer(run / "logs" / "local_execution.json", {"archive_path": str(args.archive.resolve()), "classification": "EXECUTION_LOCAL"})
            result = initialize_intake_authority_and_classification(run, hayes_authority_root=args.hayes_authority_root, ems_authority_root=args.ems_authority_root)
            result["run_dir"] = str(run)
            _print(result, args.json); return 0
        if args.command == "status": _print(get_status(args.run_dir), args.json); return 0
        if args.command == "resume":
            result = consume_classification_response(args.run_dir, args.classification_response) if args.classification_response else get_status(args.run_dir)
            _print(result, args.json); return 0
    except ArchiveWorkflowError as exc:
        print(f"archive-assessment error: {exc}", file=sys.stderr); return 3
    return 64

if __name__ == "__main__":
    raise SystemExit(main())
