# Invariant Classifier Contract

This is the first pass. It runs before any finding is accepted.

## Rule

An observation is not a finding.

Bad states, failing lines, broken tests, duplicate rows, missing rows, null values, partial writes, stale values, and bad responses are only observations until they are mapped to an invariant.

Conversation decisions are binding constraints.

Before accepting an invariant, check it against:

- `accepted_decisions`;
- `rejected_approaches`;
- `review_non_findings`;
- `scope_boundaries`.

## Protected Input Boundary Rule

If an upstream owning writer is the only production path that can create or mutate the reviewed data, and that writer validates the invariant before commit, downstream readers should treat the persisted data as valid for the same invariant.

Do not accept a finding that only guards against bad persisted data after a protected writer boundary unless code evidence proves at least one of:

- another production writer, job, import, backfill, migration, manual repair path, or external sync can write the same data without the invariant check;
- the current diff creates or preserves a bypass around the protected writer;
- existing legacy data is known to violate the invariant and the task scope includes runtime recovery for that data;
- the business contract explicitly requires fail-closed behavior for corrupted database state independent of writer correctness.

If none of the above is proven, classify the candidate as `rejected_by_decision_context` or `protected_input_non_finding`. Do not turn hypothetical database corruption into a stable finding.

Do not create an invariant whose closure requires relitigating an accepted decision, using a rejected approach, or reporting a declared non-finding. If an observation appears to contradict a decision, classify it as one of:

- `rejected_by_decision_context`: the observation is outside review scope or names a declared non-finding;
- `decision_conflict_blocker`: code evidence proves the accepted decision makes the implementation impossible or contradicts the implementation intent.

Return `BLOCKER` for `decision_conflict_blocker`. Do not turn it into a finding.

## Runtime Boundary Rules

For runtime-state, execution, scheduling, recovery, or hosted-service changes, classify the whole operational boundary, not only the noisy method.

- If a new or changed contract/dependency is runtime-critical, the owning boundary includes production DI/composition-root wiring and the real hosted-service or runtime entrypoint that constructs it. Test-only construction is not enough evidence.
- If a side effect is derived from a lifecycle/state/persistence commit, the owning boundary includes commit ordering. The side effect must be inside the same atomic boundary or happen only after the owning commit succeeds.
- If a runtime fact affects behavior after restart, the owning boundary includes the persistence -> rehydration -> post-restart consumer chain. An in-memory-only fact is not restart-safe unless the invariant explicitly says it is ephemeral.
- If one code path creates or mutates a semantic entity, the owning boundary includes sibling paths that create or mutate the same entity. A fix that only covers one sibling is incomplete unless the other siblings are ruled out with code evidence.

## Adaptive Participating Domain Inventory

Every invariant must include a participating-domain inventory, but the inventory depth is adaptive.

Use `inventory_depth=local` when the invariant is a simple local render/layout/test-oracle issue and code evidence shows no lifecycle, persisted state, external side effect, authorization, restart, retry, job, import, webhook, or cross-contract behavior. Keep this inventory small, for example page/component props/test oracle.

Use `inventory_depth=expanded` when the invariant touches lifecycle/state/payment/job/import/webhook/retry/storage/external side effects/authorization/restart behavior, or when the same semantic entity has more than one writer, reader, state transition, persistence location, or documented/tested contract. Expanded inventory must name all domains that can affect the invariant inside the approved scope.

For each participating domain, include:

- `domain`: a bounded area such as backend contract, API client, frontend click path, rehydration path, persistence/storage path, polling/reader path, terminal cleanup path, job/import/webhook path, docs, tests, permissions, runtime wiring, or restart recovery;
- `expectation_source`: code, DTO, endpoint, docs, tests, runtime config, conversation decision, or `missing`;
- `semantic_entity_paths`: create, mutate, reactivate/retry, direct action, rehydrate, restore, persist, read/poll, terminal cleanup, refetch/replacement, docs oracle, test oracle, or another concrete path name;
- `coverage_status`: `covered`, `not_applicable`, `out_of_scope`, `blocking_residual`, or `unaccounted`;
- `evidence`: concrete files/functions/commands or a short reason when not applicable/out of scope.

Rules:

- Do not require a large matrix for a local invariant. The goal is to prevent missing participating domains, not to create paperwork.
- For expanded inventory, `STABLE_FIX_PLAN` is impossible while any relevant domain or semantic entity path is `unaccounted` or `blocking_residual`.
- A domain with `expectation_source=missing` cannot be silently treated as covered. Mark it as an open question, `GRADED_REVIEW` confidence boundary, or `BLOCKER` depending on whether it can invalidate the fix.
- Same-invariant saturation must consume this inventory. Do not claim saturation from the accepted finding alone.

## Output

Return only this structure:

```text
InvariantMap
- invariant_id:
  invariant_statement:
  invariant_class:
  owning_boundary:
  operation_scope:
  inventory_depth: local|expanded
  participating_domains:
    - domain:
      expectation_source:
      semantic_entity_paths:
        - path:
          coverage_status: covered|not_applicable|out_of_scope|blocking_residual|unaccounted
          evidence:
      domain_status: covered|not_applicable|out_of_scope|blocking_residual|unaccounted
  decision_conformance:
  failure_modes:
  previously_closed_failure_modes:
  still_open_failure_modes:
  evidence:
  production_wiring_scope:
  commit_side_effect_scope:
  restart_persistence_scope:
  sibling_semantic_paths:
  domains_unaccounted:
  open_questions:
```

Use concrete invariant classes:

- `cardinality`
- `atomicity`
- `unit-of-work`
- `idempotency`
- `source-of-truth`
- `scope conservation`
- `identity resolution`
- `failure/data boundary`
- `temporal ordering`
- `production wiring`
- `restart persistence`
- `semantic lifecycle`
- `authorization/ownership`
- `read-model exposure`

## Merge Rule

Merge observations into one invariant when they share the same business/runtime rule and owning boundary.

Example:

```text
invariant_statement: active snapshot replacement for a fileKind is atomic; old active remains visible unless the new snapshot commits completely.
invariant_class: atomicity, unit-of-work, cardinality
owning_boundary: ImportAsync transaction boundary
failure_modes: two active versions; zero active versions; partially written replacement snapshot
previously_closed_failure_modes: filtered unique index closed two active versions
still_open_failure_modes: non-atomic swap can leave zero active or partial import
```

Do not call a valid narrower fix bad work. Say which failure mode it closed and which broader invariant remains open.

If the invariant statement or owning boundary cannot be named, return `BLOCKER` instead of findings.

If the invariant conflicts with accepted decisions, rejected approaches, review non-findings, or scope boundaries, reject it before specialist review unless the conflict is a proven blocker.
