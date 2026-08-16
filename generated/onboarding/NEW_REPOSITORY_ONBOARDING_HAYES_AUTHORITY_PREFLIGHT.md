# New Repository Onboarding MVP — Hayes Authority Preflight

**Result: BLOCKED — implementation authorization is NO.**

EMS authority is valid: 24/24 published, all hashes match, and the historical freeze is unchanged. Hayes has reusable batch execution, target, registry, evidence-boundary, and contract foundations.

## Architecture blockers

- **H-ARCH-01:** Generic new-target effective-applicability snapshot producer — EMS defines required inputs/outcomes, but Hayes has only frozen/scoped applicability consumers; choosing a generalized engine versus a thin onboarding adapter changes public architecture.
- **H-ARCH-02:** Onboarding assessment-plan/bundle contract boundary — Existing evaluator request/result contract should remain stable; EMS requires additional immutable plan and bundle artifacts, but their standalone versus additive contract placement is not determined.
- **H-ARCH-03:** Unified human-review derived-artifact persistence — EMS requires non-mutating review resolution, but current Hayes has applicability-only review artifacts and no canonical onboarding storage contract.

## Reusable foundations

- repository identities: EXISTS_NEEDS_EXTENSION (`registry/wave2d_repository_map.json; src/hayes_verify/wave2d_targets.py`)
- classification metadata: EXISTS_NEEDS_EXTENSION (`registry/wave2d_repository_map.json; registry/wave2d_repository_path_overrides.example.json`)
- repository/organization targets: EXISTS_REUSABLE (`src/hayes_verify/wave2d_targets.py; scripts/build_wave2d_batch_requests_scoped.py`)
- local path overrides: EXISTS_NEEDS_EXTENSION (`registry/wave2d_repository_path_overrides.example.json; scripts/build_wave2d_batch_requests_scoped.py`)
- checkout identity validation: EXISTS_NEEDS_EXTENSION (`src/hayes_verify/provenance.py; scripts/Bootstrap-HayesVerifyGitHubRepository.ps1`)
- effective applicability: EXISTS_NEEDS_EXTENSION (`scripts/build_wave2d_batch_requests_scoped.py; contracts/schemas/wave2d_evaluation_request.schema.json`)
- immutable batch identity/requests: EXISTS_REUSABLE (`scripts/create_wave2d_batch_run.py; scripts/build_wave2d_batch_requests_scoped.py`)
- registry/support states: EXISTS_NEEDS_EXTENSION (`registry/wave2d_evaluator_registry_v1_10.json; src/hayes_verify/evaluator_registry.py`)
- evidence providers: EXISTS_NEEDS_EXTENSION (`src/hayes_verify/wave2d_targets.py; evaluator family modules`)
- service/organization evidence boundaries: EXISTS_REUSABLE (`src/hayes_verify/evaluator_families/test_quality.py; dependency_supply_chain.py`)
- human review: EXISTS_NEEDS_EXTENSION (`scripts/Build-Wave2DApplicabilityReviewQueue.py; generated review artifacts`)
- request/result contracts: EXISTS_REUSABLE (`contracts/schemas/wave2d_evaluation_request.schema.json; wave2d_evaluation_result.schema.json`)
- batch/verification manifests: EXISTS_REUSABLE (`scripts/run_wave2d_batch_registry_scoped.py; generated/wave2d/evaluator-expansion`)
- auditor reports/certification: EXISTS_NEEDS_EXTENSION (`generated/wave2d/evaluator-expansion/*certification*.json`)

No onboarding runtime, allocator, applicability engine, plan, review queue, registry v1.11, or assessment was created.
