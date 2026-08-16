# WS2 — Classification Snapshot

**Status: COMPLETE**

- Tri-state booleans: `KNOWN_TRUE`, `KNOWN_FALSE`, `UNKNOWN`.
- Non-boolean attributes: `KNOWN` or `UNKNOWN`.
- Discovery is not confirmation; material confirmation remains explicit.
- The snapshot binds WS1 by SHA-256 and does not calculate applicability.
- Validation: 24 targeted tests, Ruff PASS, contract bundle PASS, full pytest 110 passed.

## WS3 handoff

Consume the immutable classification snapshot and its completeness metadata as controlled applicability inputs; preserve UNKNOWN and do not mutate historical freezes.
