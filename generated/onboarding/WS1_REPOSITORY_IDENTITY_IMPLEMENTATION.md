# WS1 — Repository Identity Consumption

**Status: COMPLETE**

- Module: `src/hayes_verify/onboarding_identity.py`
- Snapshot schema: `schemas/repository_snapshot.schema.json`
- Identity source: EMS-controlled repository identity authority; Hayes consumes only.
- ID allocation: not implemented and prohibited in Hayes.
- Validation: targeted 12 passed; contract bundle PASS; Ruff PASS; full pytest 98 passed.

## Negative invariants

- `HAYES_ALLOCATES_REPO_ID` = `False`
- `REPOSITORY_NAME_EQUALS_CONTROLLED_ID` = `False`
- `LOCAL_PATH_EQUALS_CONTROLLED_IDENTITY` = `False`
- `RENAME_ALLOCATES_NEW_REPO_ID` = `False`
- `TRANSFER_ALLOCATES_NEW_REPO_ID` = `False`
- `ARCHIVE_DELETES_ID` = `False`
- `RETIREMENT_LOSES_HISTORICAL_ID` = `False`
- `DUPLICATE_REPO_ID_REJECTED` = `True`

## Limitations / WS2 handoff

- No EMS repository ID allocation in Hayes.
- No classification snapshot (WS2).
- No applicability, assessment plan, execution checkout verification, human review, outcome, bundle, or reassessment implementation.
- No real repository identity was consumed.
- Consume repository_snapshot.json by hash.
- Add only tri-state classification/provenance fields in a separate classification snapshot.
- Do not alter repository identity or add local path.
