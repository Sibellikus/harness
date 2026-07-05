# Scout Protocol

Use scouts to gather evidence and counter-evidence. The orchestrator synthesizes; scouts do not write the final plan.

## Spawn Rules

- Spawn required shape scouts with `fork_context=false`.
- Pass explicit task-local inputs only: task brief, selected artifacts, code/doc targets, `PlanDecisionContext` when available, and neutral questions.
- Do not fork the whole planning thread into scouts or reviewers.

## Deep Roles

Run these roles for deep plans when available:

- `requirements_scout`
- `code_reality_scout`
- `business_semantics_scout`
- `ownership_persistence_scout`
- `lifecycle_entrypoint_scout`
- `failure_boundary_scout`
- `contract_surface_scout`
- `test_oracle_scout`
- `task_readiness_reviewer`
- `overengineering_reviewer`

If a required role is stale, invalid, branch-mismatched, or irrelevant, rerun that role sequentially and record recovery. If recovery is impossible, return `PROCESS_INVALID`.

## Scout Output

Every scout or fallback pass must produce:

```text
ScoutExecutionLog
- role:
- execution: subagent | sequential_main_agent | skipped
- evidence_collected:
- unknowns_or_blockers:
- skip_reason:
```

## Role Focus

- `requirements_scout`: user intent, accepted/rejected scope, non-goals, contradictions, missing decisions.
- `code_reality_scout`: current files, endpoints, handlers, jobs, storage, tests, sibling patterns, guardrails.
- `business_semantics_scout`: domain states, rules, invariants, access/money/data semantics.
- `ownership_persistence_scout`: source of truth, durable owner, storage lifecycle, migrations/backfill needs.
- `lifecycle_entrypoint_scout`: production triggers, jobs, callbacks, sync/backfill/repair paths, stop conditions.
- `failure_boundary_scout`: invalid/empty/unknown/partial/provider failure behavior, retries, idempotency.
- `contract_surface_scout`: API/module/frontend/public contract shape and compatibility risks.
- `test_oracle_scout`: current tests, missing regression or integration coverage, verification command.
- `task_readiness_reviewer`: whether candidate slices can be worker-ready under the accepted decisions.
- `overengineering_reviewer`: unnecessary abstraction, future scope, broad platforming, or layer churn.

## Orchestrator Synthesis

After scouts finish, synthesize:

- `PlanDecisionContext`;
- accepted invariants;
- `AcceptanceHandoff`;
- `ResearchGateCoverageTable` and `DecisionQuestionMatrix` for research, using [output-contracts.md](output-contracts.md);
- `DecisionPacket` and `HardenedTaskHandoff` for harden-task, using [output-contracts.md](output-contracts.md).

Do not promote scout guesses to accepted decisions without evidence or explicit user/spec authority.
