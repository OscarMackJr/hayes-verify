# External Review — Hayes New Repository Onboarding Implementation

This guide maps the GitHub-reviewable Hayes onboarding implementation. It is source publication only; it is not an execution-evidence publication, EMS authority publication, repository compliance attestation, or production authorization.

## Workstream map

| Workstream | Capability | Source | Tests | Schema |
|---|---|---|---|---|
| WS1 | Repository identity | src/hayes_verify/onboarding_identity.py | tests/test_onboarding_identity.py | schemas/repository_snapshot.schema.json |
| WS2 | Classification snapshot | src/hayes_verify/onboarding_classification.py | tests/test_onboarding_classification.py | schemas/classification_snapshot.schema.json |
| WS3 | Effective applicability | src/hayes_verify/onboarding_applicability.py | tests/test_onboarding_applicability.py | schemas/effective_applicability_snapshot.schema.json |
| WS4 | Frozen assessment plan | src/hayes_verify/onboarding_plan.py | tests/test_onboarding_plan.py | schemas/assessment_plan.schema.json |
| WS5 | Evidence and request composition | src/hayes_verify/onboarding_execution.py | tests/test_onboarding_execution.py | schemas/evidence_resolution.schema.json; schemas/request_composition_manifest.schema.json |
| WS6 | Checkout identity verification | src/hayes_verify/onboarding_checkout.py | tests/test_onboarding_checkout.py | schemas/checkout_verification.schema.json; schemas/execution_readiness_manifest.schema.json |
| WS7 | Human review queue/history | src/hayes_verify/onboarding_review.py | tests/test_onboarding_review.py | No additional schema |
| WS8 | Assessment outcome/completeness | src/hayes_verify/onboarding_summary.py | tests/test_onboarding_summary.py | No additional schema |
| WS9 | Evidence bundle/certification | src/hayes_verify/onboarding_bundle.py | tests/test_onboarding_bundle.py | No additional schema |
| WS10 | Reassessment/change detection | src/hayes_verify/onboarding_reassessment.py | tests/test_onboarding_reassessment.py | No additional schema |

## Orchestration seam

`src/hayes_verify/onboarding_orchestrator.py` and `tests/test_onboarding_orchestrator.py` demonstrate the WS5 → evaluator → WS7 → WS8 → WS9 seam using the existing Hayes evaluator request/result contract. The orchestration module does not define EMS policy, allocate repository identities, define classification, or change evaluator business logic.

## Contract and authority boundary

The existing contract bundle remains unchanged and is validated by `scripts/validate_contract_bundle.py`. Controlled onboarding authority is published separately by EMS for review; it is not duplicated here.

## Deliberate exclusions

Synthetic execution run bundles, request/result payloads, local execution mappings, credentials, machine-specific paths, and external retention evidence are not included. Their P0 hash references remain external evidence, not GitHub source. The optional synthetic-run generator is also excluded from this source-only publication because it produces an excluded execution bundle.

## Pilot boundary

The hometown real-repository pilot remains execution-blocked. `PILOT_EXECUTION_AUTHORIZED = false` and `PRODUCTION_AUTHORIZED = false`.
