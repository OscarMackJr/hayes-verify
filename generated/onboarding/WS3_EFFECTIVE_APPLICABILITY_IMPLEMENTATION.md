# WS3 — Current Effective Applicability

Status: **COMPLETE**

WS3 adds a generic current-policy applicability compiler. It consumes WS1 identity and the exact WS2 classification snapshot hash, current controlled EMS policy, and explicit policy-condition evidence. It emits only `APPLICABLE`, `NOT_APPLICABLE`, or `APPLICABILITY_UNRESOLVED`; it emits no compliance result and no evaluator request.

- Current policy is authoritative; historical Wave 2D freezes are immutable reference evidence only.
- Unknown classification or insufficient condition evidence routes to `APPLICABILITY_UNRESOLVED`, never `NOT_APPLICABLE`.
- Service, organization, platform, and EMS scope cannot be fabricated from repository evidence.
- Hayes support state is recorded only as an optional projection and never changes applicability.
- Effective-applicability snapshots are immutable: changed policy, classification, or material condition evidence requires a new snapshot.

Validation: contract bundle PASS; Ruff PASS; WS1/WS2/WS3 targeted tests 38 passed; full pytest 124 passed. The historical freeze SHA-256 remained `79adb6c003e9a61e2fd36131b1a37d3387973f72d206102985a78a3271bc5b35`.

WS4 handoff requires the immutable effective-applicability snapshot plus its policy/classification/evidence provenance; WS3 does not implement WS4.
