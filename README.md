# Hayes Verify

Hayes Verify is the evidence-collection and control-evaluation execution engine for the EMS.

## Authority boundary

Hayes Verify **may**:
- consume EMS evaluation requests;
- collect repository/system evidence;
- produce provenance envelopes;
- execute control assertions;
- emit evaluation results.

Hayes Verify **may not**:
- modify the EMS control catalog;
- change EMS applicability;
- accept results on behalf of EMS;
- promote evidence.

EMS remains authoritative for control definitions, applicability, result acceptance, and promotion.

## First vertical slice

```text
EMS evaluation request
        ↓
Hayes Verify request validator
        ↓
collector
        ↓
evidence record + provenance
        ↓
evaluator
        ↓
evaluation result
        ↓
promotion_state = NOT_PROMOTED
        ↓
returned to EMS
```

## Local setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest
```

Validate the frozen contract bundle:

```powershell
python .\scripts\validate_contract_bundle.py --root .
```

Validate an evaluation request:

```powershell
hayes-verify validate-request .\examples\evaluation_request.json
```
