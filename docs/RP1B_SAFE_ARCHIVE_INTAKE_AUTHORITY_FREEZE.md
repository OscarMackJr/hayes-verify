# RP1B safe intake, authority freeze, and classification gate

RP1B performs safe ZIP validation/extraction, creates hash-bound source and extracted-content manifests, discovers current controlled Hayes/EMS roots, and freezes their identities into a workflow. It generates an attributable JSON classification request and pauses at `CLASSIFICATION`.

`resume <run-dir> --classification-response <response.json>` consumes exactly one schema-valid response and advances only to the `APPLICABILITY` boundary. UNKNOWN is preserved; it is never coerced to false. A resumed workflow reuses its frozen context.

ZIP limits are operational safety safeguards: 10,000 entries, 256 MiB expanded bytes, 64 MiB per file, 100:1 compression ratio, and 240-character paths. These are not EMS policy values. No evaluator, applicability compiler, frozen plan, or package builder executes in RP1B.
