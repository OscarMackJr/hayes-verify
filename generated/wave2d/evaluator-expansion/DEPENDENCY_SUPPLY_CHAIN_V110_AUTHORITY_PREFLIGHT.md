# Dependency Supply Chain v1.10 Authority Preflight

## Result

**DEPENDENCY_SUPPLY_CHAIN V1.10 AUTHORITY PREFLIGHT = PASS**
**IMPLEMENTATION AUTHORIZED = YES**

## Control

- EMS-CTRL-023 — Vulnerability Remediation Targets
- Current registry state: PLANNED_HYBRID / supported=false
- Evidence scope: ORGANIZATIONAL
- Future automation boundary: HYBRID
- Repository-only PASS: prohibited

## Reconstructed control contract

- Classification:
Use the severity rating issued by an approved vulnerability scanner as the remediation class.
- Targets:
Critical: 7 calendar days; High: 30 calendar days; Medium: 90 calendar days; Low: 180 calendar days or documented risk-managed disposition.
- Clock start:
Start aging at the first validated detection timestamp recorded by the authoritative vulnerability evidence system.
- Clock stop:
Stop the remediation clock only upon verified remediation, approved false-positive closure, or an active approved risk acceptance or compensating-control exception.
- Freshness:
Evidence is current when the authoritative system was refreshed within the preceding 24 hours for open Critical or High findings and within the preceding 7 calendar days for other findings.
- PASS:
PASS only when authoritative current evidence shows every applicable finding is within its remediation target or has a valid active approved closure, false-positive, or exception disposition.
- FAIL:
FAIL when current authoritative evidence proves an applicable finding is overdue without an active approved exception, lacks a required owner or target date, or has an expired exception.
- HUMAN_REVIEW:
Route to HUMAN_REVIEW when authoritative evidence is unavailable, inaccessible, incomplete, conflicting, stale, or insufficient to calculate a target or verify an exception.
- Exception:
Require Security Authority approval, business justification, compensating controls, accountable owner, approval timestamp, expiration/review date no later than 90 calendar days, renewal before expiry, and closure evidence; expired exceptions are noncompliant.
- Applicability:
Preserve FROZEN_APPLICABLE rows; evaluate EMS-CTRL-023 once per organization from authoritative organizational evidence, and expose repository rows only as projections with no repository-only PASS.
- Retention:
Retain remediation finding, status, closure, and exception history in the authoritative evidence system for three years after closure or expiration.

## Assertion classification

| Classification | Count |
| --- | ---: |
| AUTOMATABLE | 2 |
| HYBRID | 11 |
| HUMAN_EVIDENCE_REQUIRED | 0 |

The evaluator may consume contract-conforming organizational evidence when supplied. In the absence of qualifying authority, it must emit HUMAN_REVIEW rather than inventing a repository-only PASS or FAIL.

## Applicability runtime representation

Run one organization-level authoritative evaluation. Retain the seven historical repository targets as projections/supporting context only; they must not become seven independent repository-level PASS determinations.
