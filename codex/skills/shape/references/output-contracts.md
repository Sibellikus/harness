# Shape Output Contracts

This file is the single source of truth for output shapes. Other shape files may refer to these contracts, but must not restate or fork them.

## Shared Enums

Readiness verdicts: `READY`, `BLOCKED`, `TOO_BROAD`, `OVERENGINEERED`, `UNDER_SPECIFIED`.

Research gate status: `resolved`, `questioned`, `future_scope`, `non_applicable`, `missing`.

Question answer type: `choose_one`, `choose_many`, `boolean`, `value`, `policy_text`.

## File-Backed Result

The plan body is written to the artifact files defined in [file-backed-artifacts.md](file-backed-artifacts.md). The chat response must only return this pointer contract:

```text
ShapeChatResult
- mode: research | harden-task
- verdict: READY_FOR_HARDEN_TASK | READY | BLOCKED | TOO_BROAD | OVERENGINEERED | UNDER_SPECIFIED | PROCESS_INVALID
- plan_artifact:
- questions_artifact:
- open_question_ids:
- accepted_decision_ids:
- next_action:
```

Rules:
- Do not paste `ResearchPlanDossier`, `HardenedTaskHandoff`, reviewer output, or full question cards into chat by default.
- If a deep reviewer validates a draft, store the reviewer output and accepted draft verbatim in `plan_artifact`.
- If validation fails, store `PROCESS_INVALID` in `plan_artifact` and keep the chat response compact.

## ResearchPlanDossier

Research artifact content must use this compact dossier, not a 20-section report:

```text
ResearchPlanDossier
1. PlanDecisionContext
2. EvidenceSummary
3. AcceptedInvariants
4. AcceptanceHandoff
5. ResearchGateCoverageTable
6. DecisionQuestionMatrix
7. CandidateSlices
8. ResearchVerdict
```

### 1. PlanDecisionContext

```text
PlanDecisionContext
- user_intent:
- accepted_scope:
- rejected_scope:
- open_decisions:
- non_goals:
- source_authority:
- constraints_from_user_or_artifacts:
```

`accepted_scope` may contain only already accepted behavior. If an item is also listed in `open_decisions`, it must move to `open_decisions`, `candidate_scope`, or `future_or_out_of_scope`; otherwise the plan is internally contradictory.

### 2. EvidenceSummary

Keep this concise. Include only evidence needed to justify invariants, questions, and slice readiness.

```text
EvidenceSummary
- current_behavior:
- external_or_artifact_facts:
- guardrails_or_project_rules:
- gaps:
```

### 3. AcceptedInvariants

```text
AcceptedInvariant
- id:
- invariant:
- evidence:
- must_not_violate:
```

### 4. AcceptanceHandoff

```text
AcceptanceScenario
- id:
- behavior:
- status: accepted | questioned | future_scope | non_applicable
- evidence:
- open_decision_ids:
- proof_type:
```

### 5. ResearchGateCoverageTable

This block must publish actual rows. A prose summary is invalid. Rows may be multiline or compact inline rows, but each row must expose the required field names clearly.

```text
ResearchGateCoverageRow
- class:
- status: resolved | questioned | future_scope | non_applicable | missing
- covered_subfields:
- missing_subfields:
- question_ids_or_decision_ids:
- non_applicable_or_future_scope_reason:
```

Rules:
- Every applicable class must have a row.
- A row is valid only if all required field names above are present in that row. Multiline and compact inline syntax are both acceptable.
- `covered_subfields` must list concrete generic subfields; a broad question id alone is not enough.
- `missing_subfields` must be explicit. Use `[]` only when all material subfields are covered or the class has a concrete non-applicable/future-scope reason.
- If `missing_subfields` is non-empty, every missing item must map to a `DecisionQuestionRow` or an explicit future/non-applicable decision.
- Universal contracts must not require provider-specific operations, endpoint names, statuses, or product names. Provider-specific details belong in evidence and decision questions only when the task evidence makes them relevant.

### 6. DecisionQuestionMatrix

This block must publish actual rows. A numbered FAQ is invalid. Rows may be multiline or compact inline rows, but each row must expose the required field names clearly.

```text
DecisionQuestionRow
- id:
- decision_needed:
- decision_packet_field:
- research_gate_classes:
- covered_subfields_by_class:
- risk_class:
- affected_scenarios:
- affected_slices:
- current_evidence:
- why_code_or_docs_cannot_decide:
- answer_type: choose_one | choose_many | boolean | value | policy_text
- options_or_policy_shape:
- recommended_default_with_evidence:
- implementation_effect:
- tests_unlocked:
```

Rules:
- Each material open decision must fill a future `DecisionPacket` field or explicitly downgrade scope to future/out-of-scope.
- A row is valid only if it names at least these fields: `id`, `decision_needed`, `decision_packet_field`, `research_gate_classes`, `risk_class`, `affected_scenarios` or `affected_slices`, `answer_type`, `options_or_policy_shape`, `implementation_effect`, and `tests_unlocked`. Multiline and compact inline syntax are both acceptable.
- If one question covers multiple research-gate classes, list covered subfields per class.
- If a question only partially covers a class, add another row; do not mark the whole class covered.

### 7. CandidateSlices

```text
CandidateSlice
- id:
- name:
- verdict: READY | BLOCKED | TOO_BROAD | OVERENGINEERED | UNDER_SPECIFIED
- covered_scenarios:
- blocking_decision_ids:
- worker_surface_if_ready:
- stop_conditions:
- evidence:
```

Research normally has no `READY` slices while material decisions remain open.

### 8. ResearchVerdict

```text
ResearchVerdict
- verdict: READY_FOR_HARDEN_TASK | UNDER_SPECIFIED | BLOCKED
- reason:
- minimal_next_action:
- decision_packet_fields_needed_next:
```

## DecisionPacket

Use after user/spec answers are accepted. A `harden-task` output must not make a slice `READY` without the packet fields it needs.

```text
DecisionPacket
- decision_id:
- field:
- accepted_value:
- source: user_answer | accepted_spec | current_code | authoritative_artifact
- affected_scenarios:
- affected_slices:
- implementation_effect:
- tests_unlocked:
- remaining_followup: none | future_scope | blocker
```

## HardenedTaskHandoff

```text
HardenedTaskHandoff
- PlanDecisionContext
- DecisionPacket
- AcceptanceHandoff
- SelectedSliceOrSlices
- TaskReadinessReportPerSlice
- WorkerSurfaceForReadySlices
- OpenDecisionsMappedToSlices
- ImplementationOrder
- TestsRequired
- StopConditions
```

```text
TaskReadinessReport
- verdict: READY | BLOCKED | TOO_BROAD | OVERENGINEERED | UNDER_SPECIFIED
- task_scope:
- decision_packet_fields_used:
- bdd_scenarios_covered:
- ownership:
- scope_vocabulary:
- rule_interactions:
- lifecycle_entrypoints:
- execution_scope:
- credentials_context:
- blocker_classification:
- risk_class_completeness:
- project_guardrails:
- contract_surface:
- storage_impact:
- failure_boundary:
- worker_surface:
- dependencies:
- non_goals:
- tests_required:
- worker_stop_conditions:
- done_criteria:
- required_task_file_edits:
- evidence:
```

## Reviewer Output

The reviewer must validate structure before meaning and must print the extracted structure before the checklist. `CONTRACT_PASS` without a printed `ObservedStructure` is invalid. If any required structure is absent, summary-only, or ambiguous, use `PROCESS_INVALID`.

The reviewer emits only reviewer output. It must not repeat, rewrite, or append the draft dossier/handoff. The orchestrator writes the accepted reviewer output and accepted draft into `plan_artifact` after `CONTRACT_PASS`.

Artifact relay is part of the contract: after `CONTRACT_PASS`, the orchestrator must write the reviewer output verbatim and then the accepted draft verbatim into `plan_artifact`. Any post-review summary, compression, row shortening, section renaming, or replacement of `ObservedStructure` invalidates the result; write `PROCESS_INVALID` instead. The chat response remains `ShapeChatResult`.

### Invalid

```text
PROCESS_INVALID
ObservedStructure
- selected_mode:
- sections:
- checklist_anchors:
- scenario_ids:
- question_ids:
- decision_packet_fields:
- research_gate_rows_observed:
- decision_question_rows_observed:
- missing_required_row_fields:
- required_blocks_present:
- required_blocks_missing:

InvalidReasons
- failed_anchor:
- why_invalid:
- minimal_next_action:
```

### Pass

```text
CONTRACT_PASS
ObservedStructure
- selected_mode:
- sections:
- checklist_anchors:
- scenario_ids:
- question_ids:
- decision_packet_fields:
- research_gate_rows_observed:
- decision_question_rows_observed:
- missing_required_row_fields:
- required_blocks_present:
- required_blocks_missing:

FinalContractChecklist
- SelectedMode: PASS - evidence:
- StructurePresence: PASS - evidence:
- ScoutExecutionLog: PASS - evidence:
- PlanDecisionContext: PASS - evidence:
- AcceptanceHandoff: PASS - evidence:
- ScopeAuthorityAndVocabulary: PASS - evidence:
- BlockerAndRiskDiscipline: PASS - evidence:
- ResearchGateCoverageTable: PASS - evidence:
- DecisionQuestionMatrixOrDecisionPacket: PASS - evidence:
- NoFalseReadiness: PASS - evidence:
- MandatoryScoutRecovery: PASS - evidence:
```
