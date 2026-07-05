---
name: shape
description: "Use before risky implementation work to choose research or harden-task mode, gather evidence, ask/record open decisions in file-backed artifacts, and validate a compact plan contract without dumping the full plan into chat context. Trigger for ambiguous briefs/transcripts/tables, endpoint/use-case behavior, persistence, calculations, state transitions, cross-module flows, side effects/jobs/sync/backfill, failure semantics, or repeated review/symptom-fix risk."
---

# Shape

Use this skill when a task can fail because the plan is shallower than the real complexity. It writes either a research decision dossier, a worker-ready task plan, or `PROCESS_INVALID` into file-backed artifacts and returns only a compact chat summary with paths.

Do not use it for trivial renames, one-field mappings, obvious null guards, isolated UI tweaks, or mechanical refactors with a clear local test oracle.

## Progressive Disclosure

Keep `SKILL.md` as the orchestrator. Load details only when needed:

- Always read [references/output-contracts.md](references/output-contracts.md). It is the single source of truth for output formats.
- Always read [references/file-backed-artifacts.md](references/file-backed-artifacts.md). It controls where the plan, questions, and final result are written.
- For research mode, read [references/research-mode.md](references/research-mode.md).
- For harden-task mode, read [references/harden-task-mode.md](references/harden-task-mode.md).
- For deep runs, read [references/scout-protocol.md](references/scout-protocol.md) and [references/reviewer-contract.md](references/reviewer-contract.md).

Do not copy or restate format schemas from references. Use the exact contracts from `output-contracts.md`.

## Mode Selection

Choose one mode before drafting:

- `research`: determine what is true, what is in scope, and what decisions block implementation. Use when business semantics, provider behavior, ownership, lifecycle, storage, public contracts, or failure behavior are still being discovered.
- `harden-task`: produce worker-ready implementation tasks. Use only when accepted decisions are already present in the request, artifacts, previous accepted research, or current code.

Default to `research` when material decisions remain open. Default to `harden-task` only when a coding worker could implement without inventing business/provider/lifecycle/contract semantics.

## Core Rules

- Evidence is not a decision. Synthesize decisions into `PlanDecisionContext`, accepted invariants, acceptance scenarios, gate coverage, and decision rows.
- If evidence cannot resolve business, ownership, lifecycle, compliance, access, money, data-loss, public contract, retry/idempotency, reversal, or externally visible behavior, keep it open.
- Research questions must be `DecisionQuestionRow` entries, not a loose FAQ.
- Put detailed clarification questions in `questions.md`; keep only question IDs and compact status in the main plan artifact.
- The user answers questions in chat. The orchestrator normalizes the answer, updates `questions.md`, and converts accepted answers into `DecisionPacket` entries or accepted plan sections.
- Hardening must use `DecisionPacket` entries, not assumptions.
- Optional provider/framework capabilities are evidence, not requirements. Classify them as in scope, blocked decision, future scope, or non-applicable.
- Use enum verdicts only: `READY`, `BLOCKED`, `TOO_BROAD`, `OVERENGINEERED`, `UNDER_SPECIFIED`.
- Never use ad hoc verdicts such as `DEFERRED`, `FUTURE`, or `OUT_OF_SCOPE`. If a slice is future work and not selected for the current plan, keep the verdict in the allowed enum, usually `UNDER_SPECIFIED` when the future contract is intentionally not detailed or `BLOCKED` when a named decision is missing. Put the future-scope reason in `stop_conditions`, `evidence`, or `OpenDecisionsMappedToSlices`.

## Risk Scan

Start with a short risk scan. Score `0-3` and cite evidence for nonzero scores:

```text
RiskScan
- public_contract
- business_logic
- scope_source_of_truth
- authorization_or_ownership
- data_completeness
- failure_boundary
- calculation_or_algorithm
- rule_interaction
- state_transition
- side_effects_or_persistence
- lifecycle_or_entrypoint
- cross_module_dependency
- sibling_flow_consistency
- legacy_behavior_ambiguity
- raw_requirement_ambiguity
- test_oracle_gap
- architecture_pressure
- repeated_review_or_history_signal
```

Depth:

- `lightweight`: total <= 3 and no category is 3.
- `standard`: total 4-7 or one strong localized risk.
- `deep`: total >= 8, any source-of-truth/failure/business/lifecycle score is 3, or several categories interact.
- `stop-and-ask`: multiple valid business outcomes remain after discovery and cannot be narrowed by local evidence.

## Evidence Collection

For non-lightweight runs, record:

```text
ScoutExecutionLog
- role:
- execution: subagent | sequential_main_agent | skipped
- evidence_collected:
- unknowns_or_blockers:
- skip_reason:
```

For `deep`, subagents are required when available and not forbidden. Explicit `$shape` invocation authorizes this skill's required scouts. If subagents are unavailable, run roles sequentially and record fallback.

Use subagents as scouts/reviewers, not mini planners. Spawn with `fork_context=false` and pass explicit task-local inputs only.

## Draft And Review

Draft exactly one selected-mode artifact in the main plan file:

- `ResearchPlanDossier` for research;
- `HardenedTaskHandoff` or `BLOCKER` for harden-task.

When converting an existing research artifact into `harden-task`, update the artifact so the current mode, final verdict, open-question index, accepted scenario statuses, candidate-slice verdicts, and reviewer label cannot be mistaken for stale research state. If previous reviewer output remains in the file, mark it as historical for the mode it validated. Do not present a prior research `CONTRACT_PASS` as validation of a later harden-task draft.

Before finalizing a file-backed artifact, scan every `CandidateSlice` and `TaskReadinessReport` verdict. If any verdict is outside the shared enum from `output-contracts.md`, fix it before writing the result. If you cannot safely map it without changing meaning, write `PROCESS_INVALID` instead of leaving the invalid verdict in the artifact.

For `deep`, do not publish the draft until an isolated `plan_contract_reviewer` validates it. The reviewer gets only the draft, selected mode, relevant contracts, `PlanDecisionContext`, scout log, and minimal task context.

If reviewer returns `CONTRACT_PASS`, update the main plan file with:

1. the reviewer output verbatim;
2. the accepted draft verbatim.

Do not add, remove, compress, reorder, rename, summarize, translate, or reformat any reviewed row, section, checklist, or `ObservedStructure` after validation. If you cannot write the validated artifacts verbatim to the plan file, write `PROCESS_INVALID` as the result.

If reviewer returns `PROCESS_INVALID` or no isolated reviewer ran, write `PROCESS_INVALID` to the plan file and return a compact chat response with the path and reason.

The final chat response must not include the full plan. Return only `ShapeChatResult` from [references/output-contracts.md](references/output-contracts.md): artifact paths, selected mode, verdict, open question IDs, and next action.

## Quality Rejects

Reject plans that:

- invent business semantics, hidden fallbacks, speculative frameworks, or future-proofing without evidence;
- include optional provider/framework capabilities in target behavior, storage, BDD, or `READY` slices without scope authority;
- collapse unknown into zero/empty/default without a trusted source;
- create side effects without production entrypoints;
- create persisted, mirrored, imported, cached, or derived state without lifecycle operations;
- mark ordinary naming/shape choices as blockers when conventions can harden them safely;
- mark provider/external lifecycle, retry/idempotency, reversal/refund/cancel, access/entitlement, reconciliation mode, attempt cardinality, or state reuse `READY` from an unevidenced safe default.
