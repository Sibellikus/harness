# Observation Specialists Contract

Specialists gather evidence. They do not decide final findings.

## Shared Prompt

Every specialist must receive:

```text
Raw observations are not findings.
Use the provided InvariantMap.
Use the provided ParticipatingDomainInventory. For expanded inventories, gather evidence against the named participating domains and semantic entity paths instead of stopping at the first failing line.
Use the provided decision context as binding constraints.
Return CandidateObservation items only.
If an observation cannot be mapped to an invariant_id, mark it unclassified and explain what evidence or business decision is missing.
If an observation contradicts accepted_decisions, requires rejected_approaches, reports review_non_findings, or crosses scope_boundaries, mark it rejected_by_decision_context and explain which decision rejected it.
If code evidence proves a decision makes the implementation impossible, mark it decision_conflict_blocker instead of proposing a finding.
If an observation only requires a downstream guard against data that all known production writers already validate, mark it protected_input_non_finding unless you can name the unprotected writer, legacy data source, migration/backfill path, or explicit fail-closed business requirement.
For runtime-critical contracts/dependencies, trace production wiring through DI/composition root and real hosted-service/runtime construction.
For side effects derived from state/lifecycle/persistence commits, trace whether the side effect happens after the owning commit or inside the same atomic boundary.
For restart-affecting facts, trace persistence, rehydration, and post-restart consumption.
For semantic entities with multiple creators/writers, enumerate sibling paths and say whether each is covered or ruled out.
For lifecycle/state/payment/job/import/webhook/retry/storage/external-side-effect/authorization/restart invariants, report any participating domain or semantic entity path that remains unaccounted, has a missing expectation source, or has evidence of the same invariant failing in a sibling path.
Do not propose a final finding.
```

## Candidate Shape

```text
CandidateObservation
- observed_state:
- invariant_id:
- suspected_invariant:
- possible_owning_boundary:
- related_failure_modes:
- evidence:
- counter_evidence:
- decision_conformance:
- production_wiring_evidence:
- commit_side_effect_order_evidence:
- restart_persistence_evidence:
- sibling_semantic_paths:
- participating_domain_evidence:
- semantic_entity_path_evidence:
- unaccounted_domains_or_paths:
- suggested_risk_level:
```

## Lenses

- `correctness`: runtime behavior, contracts, data integrity, concurrency, lifecycle, downstream effects.
- `security`: auth, permissions, tenant/organization boundaries, sensitive data.
- `test`: missing proof for invariant and failure modes, false-green fixtures, flaky or blind tests.
- `maintainability`: duplicated decisions, split source of truth, hidden fallback paths, scattered guards, difficult ownership.
- `runtime-recovery`: production wiring, hosted-service lifecycle, commit/side-effect ordering, persistence, rehydration, restart consumers.

Specialists should prefer concrete file/function evidence over broad opinions.

Specialists must not smuggle rejected approaches through alternate wording. For example, if the decision context says not to validate individual items/cards/rows, then a candidate that gates readiness by selected item/card/row completeness is rejected even if phrased as scope conservation or read-model exposure.
