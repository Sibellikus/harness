# Plan Contract Reviewer Protocol

The reviewer validates a selected-mode draft against [output-contracts.md](output-contracts.md). It must not improve, complete, summarize, or rewrite the plan.

## Isolation

Spawn with `fork_context=false`. Pass only:
- selected mode;
- draft output;
- `output-contracts.md`;
- relevant mode reference;
- `PlanDecisionContext`;
- scout log;
- minimal task context.

The reviewer must not use inherited thread history as evidence.

## Validation Order

1. Extract and print `ObservedStructure` using the contract in `output-contracts.md`. `CONTRACT_PASS` without printed `ObservedStructure` is invalid.
2. Validate row blocks structurally.
3. Validate semantic gates against `PlanDecisionContext`.
4. Emit either `CONTRACT_PASS` or `PROCESS_INVALID`.

The orchestrator writes the accepted reviewer output and accepted draft into the main plan artifact after `CONTRACT_PASS`.

## Structural Rules

`ResearchGateCoverageTable` is present only if actual published rows exist and every row has these named fields. Multiline and compact inline syntax are both acceptable:
- `class`
- `status`
- `covered_subfields`
- `missing_subfields`
- `question_ids_or_decision_ids`
- `non_applicable_or_future_scope_reason`

`DecisionQuestionMatrix` is present only if actual published rows exist and every row has the required `DecisionQuestionRow` field names from `output-contracts.md`. Multiline and compact inline syntax are both acceptable.

Do not count prose summaries, comma-separated class lists, or claims like "11 rows with required labels" as rows. If the output says rows exist but they are not printed, return `PROCESS_INVALID`.

Checklist evidence may cite only structure that appears in `ObservedStructure`.

## Semantic Rules

Return `PROCESS_INVALID` when:
- rejected scope or open decisions appear as accepted behavior, target behavior, or `READY` worker scope;
- `accepted_scope` contains a material decision that is still listed as open, questioned, or blocked;
- material open decisions are represented only as loose questions;
- a `READY` slice lacks required `DecisionPacket` fields or worker surface;
- a row claims coverage but leaves the hardening worker to invent business/provider/lifecycle/contract semantics;
- any required scout is stale, invalid, skipped without reason, or unrecovered.

Do not require provider-specific operation names, endpoint names, statuses, or product names in the universal contract.
