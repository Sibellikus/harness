# Closure Planner Contract

The final result must be one terminal artifact manifest whose referenced structured artifact has `result` = `STABLE_FIX_PLAN`, `GRADED_REVIEW`, or `BLOCKER`.

## Structured Artifact Contract

Write exactly one valid JSON object to `<repo_path>/.codex/tmp/deep-review/<run-id>/artifact.json`, then return exactly one short manifest line:

```text
ARTIFACT_READY result=<STABLE_FIX_PLAN|GRADED_REVIEW|BLOCKER> artifact_path=<absolute artifact.json path>
```

Do not return Markdown. Do not return raw JSON in the terminal message. Do not wrap the manifest in a fenced code block. The launcher validates and renders the artifact with `scripts/render_review_manifest.py`.

Keep machine sentinel values (`STABLE_FIX_PLAN`, `GRADED_REVIEW`, `BLOCKER`) in English. Localize prose values in the supplied `output_language`; keep code identifiers, enum values, API paths, file paths, commands, metric keys, trace event names, and status tokens unchanged.

`StructuredReviewArtifact` file shape:

```json
{
  "result": "STABLE_FIX_PLAN|GRADED_REVIEW|BLOCKER",
  "output_language": "Russian|English|...",
  "banner": {"level": "WARNING|NOTE|IMPORTANT|CAUTION", "text": "short localized status"},
  "summary": [{"field": "Scope", "value": "..."}],
  "findings": [
    {
      "id": "F1",
      "priority": "P0|P1|P2|P3",
      "title": "concise localized finding",
      "impact": "runtime/business consequence",
      "evidence": ["file:line or exact runtime path"],
      "invariant": "invariant id/class",
      "owning_boundary": "owning boundary"
    }
  ],
  "inline_comments": [
    {
      "finding_id": "F1",
      "file": "/absolute/path/to/file.ext",
      "start": 10,
      "end": 12,
      "title": "[P1] concise inline title",
      "body": "one-paragraph actionable explanation",
      "priority": 1
    }
  ],
  "fix_plan": ["action-oriented fix item"],
  "verification": [{"check": "...", "evidence": "...", "status": "planned|passed|not_run"}],
  "checked_nearby_cases": [{"case": "...", "result": "ok|problem_found|covered_by_plan|not_applicable", "evidence": "..."}],
  "review_health": [{"area": "Candidate accounting|Coverage|Fixed point|Verification", "status": "complete|partial|failed|reached|not_reached|clean|residuals", "meaning": "..."}],
  "participating_domain_inventory": ["compact domain/path coverage item"],
  "process_metrics": {
    "invariants_classified": 0,
    "candidate_observations": 0,
    "candidate_observations_accounted": 0,
    "candidate_observations_unaccounted": 0,
    "findings_accepted": 0,
    "fixed_point_iterations": 0,
    "nearby_cases_checked": 0,
    "same_invariant_cases_open": 0,
    "blocking_residuals": 0,
    "verification_residuals": 0,
    "production_wiring_paths_checked": 0,
    "restart_persistence_paths_checked": 0,
    "participating_domains_count": 0,
    "domains_with_expectation_source": 0,
    "domains_unaccounted": 0,
    "semantic_entity_paths_checked": 0,
    "semantic_entity_paths_unaccounted": 0,
    "expanded_domain_inventories": 0,
    "patch_simulation_rows": 0,
    "trace_file": "not_written"
  },
  "candidate_accounting_breakdown": {
    "accepted_findings": 0,
    "rejected": [{"reason": "decision_context|unclassified|duplicate_or_covered|low_confidence|out_of_scope|other", "count": 0, "sample_or_note": "..."}],
    "deferred_to_residual_risk": 0,
    "protected_input_non_findings": 0,
    "unaccounted": 0
  },
  "closure_evidence": ["concise audit evidence item"],
  "residual_risks": [{"risk": "...", "classification": "verification_residual|out_of_scope_residual|blocking_residual", "follow_up": "..."}],
  "launcher_gate_assessment": "only for GRADED_REVIEW when useful",
  "blocker": {"summary": "...", "details": "...", "evidence_needed": "...", "minimal_next_action": "..."}
}
```

For `BLOCKER`, `blocker` is required and the normal review arrays may be omitted. For `STABLE_FIX_PLAN` and `GRADED_REVIEW`, all non-blocker fields except `blocker` and optional `inline_comments` are required. The manifest `result` must equal the JSON artifact `result`.

Required semantic fields for non-blocker artifacts:

- summary: scope, result type, finding count by priority, confidence boundary;
- findings: priority, concise finding, runtime/business impact, concrete evidence with file links or exact code/runtime paths;
- inline_comments: optional exact line anchors for accepted findings; omit entries when a finding has no honest changed-line anchor;
- fix_plan: action-oriented remediation for every accepted finding;
- verification: checks to run or evidence already run, with status;
- checked_nearby_cases: same-invariant sibling/neighbor paths checked, result, evidence;
- participating_domain_inventory: adaptive domain coverage for each accepted invariant; keep the user-facing rendering compact and put full detail in closure evidence;
- review_health: operator-facing pass/fail/partial status for candidate accounting, coverage, fixed-point closure, and verification;
- process_metrics: required counters from this contract;
- closure_evidence: invariant, owning boundary, decision conformance, saturation, adversarial pass, fixed-point/ledger evidence;
- residual_risks: verification/out-of-scope residuals and follow-up.

Deterministic English renderer output:

```text
STABLE_FIX_PLAN

> **Warning**
>
> <one sentence if any P0/P1 finding exists; otherwise use Note with "No blocking findings.">

# Summary
| Field | Value |
| --- | --- |
| Scope | <branch/base/worktree summary> |
| Result | <stable_fix_plan|no_findings|blocker_prevented> |
| Findings | <count by priority> |
| Confidence | <high|medium|low and one reason> |

# Findings
| Priority | Finding | Impact | Evidence |
| --- | --- | --- | --- |
| P1 | <short finding> | <runtime/business consequence> | <file:line links> |

# Fix Plan
1. <action-oriented fix>
2. <action-oriented fix>

# Verification
| Check | Command or evidence | Status |
| --- | --- | --- |
| <test/review check> | `<command>` or <evidence> | <planned|passed|not run> |

:::github-details{summary="Audit details"}
# Checked Nearby Cases
| Case checked | Result | Evidence |
| --- | --- | --- |
| <neighbor scenario for the same invariant> | <ok|problem found|covered by plan|not applicable> | <file:line links or command evidence> |

# Review Health
| Area | Status | Meaning |
| --- | --- | --- |
| Candidate accounting | <complete|partial|failed> | <all candidate observations accounted, or what is missing> |
| Coverage | <complete|partial|failed> | <domain/path coverage status> |
| Fixed point | <reached|not reached> | <same-invariant closure status> |
| Verification | <clean|residuals> | <test/runtime verification residual status> |

# Process Metrics
| Metric | Value |
| --- | --- |
| invariants_classified | <number> |
| candidate_observations | <number> |
| candidate_observations_accounted | <number> |
| candidate_observations_unaccounted | <number> |
| findings_accepted | <number> |
| fixed_point_iterations | <number> |
| nearby_cases_checked | <number> |
| same_invariant_cases_open | <number> |
| blocking_residuals | <number> |
| verification_residuals | <number> |
| patch_simulation_rows | <number> |
| trace_file | <path|not_written> |

# Candidate Accounting
| Bucket | Count | Note |
| --- | --- | --- |
| accepted_findings | <number> |  |
| rejected:<reason> | <number> | <sample or note> |
| deferred_to_residual_risk | <number> |  |
| protected_input_non_findings | <number> |  |
| unaccounted | <number> |  |

# Closure Evidence
<structured evidence in concise bullets, preserving required fields>

# Residual Risks
| Risk | Classification | Follow-up |
| --- | --- | --- |
| <risk> | <verification_residual|out_of_scope_residual> | <next action> |
:::
```

For Russian launcher output, `scripts/render_review_manifest.py` loads the artifact and renders these section headings with localized table column labels/prose:

- `# Панель ревью`
- `# Резюме`
- `# Проблемы`
- `# План исправления`
- `# Проверка`
- collapsed `github-details` audit sections for `# Что еще проверили`, `# Состояние ревью`, `# Метрики процесса`, `# Доказательная часть`, and `# Остаточные риски`

Rules:

- Use priorities `P0`, `P1`, `P2`, `P3`; do not invent other severity labels.
- Use `inline_comments` only for accepted findings with a precise file and line range. `finding_id` must match a finding id. `priority` is numeric `0`, `1`, `2`, or `3`, matching the `P0`-`P3` finding priority.
- Do not write `::code-comment{...}` directives inside artifact prose. The deterministic renderer owns directive emission, escaping, and placement.
- Keep inline comment bodies concise and actionable. They may summarize the finding, but the full review must remain in `findings`, `fix_plan`, and evidence fields.
- Keep each structured field short; put long proof in `closure_evidence`.
- `Findings` is the decision section; `Fix Plan` must appear before deep evidence so the operator can act without reading the appendix.
- The deterministic renderer presents the review panel and findings as renderer-neutral Markdown quote cards; do not hand-format cards in the artifact text.
- The deterministic renderer compacts the audit appendix into `github-details` blocks when the semantic fields above remain present and file/line evidence is not dropped.
- `Checked Nearby Cases` is the user-facing rendering of same-invariant saturation. It answers: "what adjacent paths for the same invariant were checked, and did they reveal another failure mode?" Do not title the user-facing section `Same-Invariant Saturation`.
- `Review Health` / `Состояние ревью` is the user-facing observability layer. It must answer how to interpret the review: whether candidate accounting is complete, coverage is complete, fixed point was reached, and verification has residuals.
- `Process Metrics` is the audit layer. Keep it to numeric counters and short statuses; do not include private chain-of-thought or specialist raw notes. Do not force the operator to infer review quality only from raw counters.
- `Closure Evidence` is an audit appendix. Keep it concise and structured; do not require an operator to read it to understand the finding or the fix.
- Do not use GitHub-style bracketed callout markers; the app may render them as raw text. Use ordinary quote cards with bold localized labels.
- Do not rely on color alone; every colored/callout signal must also have text.
- If there are no findings, return a `STABLE_FIX_PLAN` artifact with `findings=[]`, `process_metrics.findings_accepted=0`, and evidence explaining why.
- If findings are evidence-backed and decision-conformant but strict closure is incomplete, return a `GRADED_REVIEW` artifact with an explicit confidence boundary instead of forcing a fragile `STABLE_FIX_PLAN`.
- If returning `BLOCKER`, return a `BLOCKER` artifact with `blocker.summary`, `blocker.details`, `blocker.evidence_needed`, and `blocker.minimal_next_action`.

## Stable Fix Rule

A stable fix closes the classified invariant at the owning boundary. It does not only prevent the latest observed state.

Reject plans that:

- lack invariant classification;
- lack decision conformance evidence;
- report an observation as a finding;
- add downstream guards for data states already closed by a protected upstream writer boundary without proving an unprotected writer, legacy bad data, migration/backfill bypass, or explicit fail-closed corruption requirement;
- split related failure modes of one invariant;
- add only local guards;
- leave the owning boundary duplicated or unclear;
- leave split source of truth or duplicated decisions;
- lack architectural root assessment;
- lack same-invariant saturation evidence;
- lack adaptive participating-domain inventory for lifecycle/state/payment/job/import/webhook/retry/storage/external-side-effect/authorization/restart-affecting invariants;
- leave a relevant participating domain or semantic entity path unaccounted for when the invariant spans multiple domains;
- lack an adversarial second pass over the imagined patched state;
- leave runtime-critical production wiring untraced;
- perform commit-derived side effects before the owning commit succeeds unless they are part of the same atomic boundary;
- leave restart-affecting runtime facts only in memory without persistence, rehydration, and post-restart consumption evidence;
- fix only one creator/writer of a semantic entity while sibling creator/writer paths remain unreviewed;
- classify a residual risk as non-blocking when it can invalidate the stable fix;
- ignore accepted decisions or propose rejected approaches;
- report a declared review non-finding;
- cross scope boundaries without explicit user approval;
- would predictably require another review to find the next failure mode of the same invariant.

Accepted decisions, rejected approaches, review non-findings, and scope boundaries are hard gates. If a candidate finding conflicts with them, remove it from the plan. If the conflict proves the accepted decision is impossible to satisfy, return `BLOCKER` and name the conflicting decision.

## Closure Evidence

For every failure class:

```text
Closure Evidence
- pipeline_order_evidence:
- review_health:
- invariant_id:
- invariant_statement:
- invariant_class:
- owning_boundary:
- operation_scope:
- failure_modes_covered:
- previously_closed_failure_modes:
- still_open_failure_modes_after_plan:
- boundary_trace:
- production_wiring_evidence:
- commit_side_effect_order_evidence:
- restart_persistence_evidence:
- sibling_semantic_paths:
- stable_fix:
- why_this_closes_the_invariant:
- architectural_root_assessment:
- same_invariant_saturation:
- participating_domain_inventory:
- adversarial_second_pass:
- patch_simulation_ledger:
- counterfactual_sweep:
- fixed_point_status:
- process_metrics:
- maintainability_cause_pass:
- decision_conformance_evidence:
- residual_risk_classification:
- scope_preserved:
- regression_coverage:
```

`boundary_trace` must use concrete files/functions for relevant layers:

- source/provider/persisted input;
- importer/job/API client;
- mapper/input builder/canonical request;
- owning use case, transaction, resolver, storage boundary, or domain contract;
- production DI/composition root and hosted-service/runtime construction when a runtime-critical contract or dependency is involved;
- commit boundary plus any derived side effects when lifecycle/state/persistence commits drive follow-up writes or markers;
- durable persistence, rehydration, and post-restart consumer when the runtime fact affects behavior after restart;
- destructive writer/reconciler/index;
- read projection/endpoint/module route/job/manual rerun/tests.

If a layer is not applicable, say why.

Before accepting any read-side or downstream fix, `boundary_trace` must explicitly identify all known production writers for the data being guarded. If the only writer is protected by the proposed or existing invariant check, the downstream guard is not a stable fix unless the plan proves a separate corrupted-data recovery requirement.

Before accepting a fix that changes one semantic entity creator/writer, `sibling_semantic_paths` must name all discovered sibling creators/writers for that same semantic entity and mark each as `covered`, `not_applicable`, or `blocking_residual`.

`same_invariant_saturation` is required before `STABLE_FIX_PLAN`. It must enumerate all discovered same-invariant candidate failure modes, not only the first accepted finding. In the user-facing report, render its useful content as `Checked Nearby Cases` or the localized equivalent. In `Closure Evidence`, preserve the internal field name `same_invariant_saturation` and use this shape:

```text
SameInvariantSaturation
- invariant_id:
  invariant_statement:
  owning_boundary:
  inventory_depth: local|expanded
  search_evidence:
    - command_or_method:
      paths_checked:
      why_complete_enough_for_scope:
  candidates:
    - candidate_failure_mode:
      evidence:
      owning_path:
      disposition: covered_by_plan|not_applicable|blocking_residual
      disposition_reason:
```

`search_evidence` must include concrete `rg`/file evidence or equivalent code-navigation evidence for relevant writer, reader, job, API, client, persistence, projection, and manual rerun paths that can violate the same invariant. If a path class is not relevant, say why. Do not claim saturation from intuition or from the accepted finding alone.

For expanded inventories, `same_invariant_saturation` must consume `participating_domain_inventory`. Every relevant domain and semantic entity path must be represented in a candidate, search evidence entry, or explicit `not_applicable`/`out_of_scope` disposition. If a domain or path remains `unaccounted`, return `GRADED_REVIEW` with that confidence boundary or `BLOCKER` when it can invalidate the plan.

`participating_domain_inventory` must use this compact shape in `Closure Evidence`:

```text
ParticipatingDomainInventory
- invariant_id:
  inventory_depth: local|expanded
  coverage_budget:
    max_invariants:
    max_semantic_paths_per_invariant:
    budget_result: within_budget|exceeded_budget|not_applicable
  domains:
    - domain:
      expectation_source:
      paths:
        - semantic_entity_path:
          status: covered|not_applicable|out_of_scope|blocking_residual|unaccounted
          evidence:
      domain_status: covered|not_applicable|out_of_scope|blocking_residual|unaccounted
  unaccounted_domains:
  blocking_domain_residuals:
```

Rules:

- Use `inventory_depth=local` for simple local render/layout/test-oracle invariants; keep domains short and do not inflate the review.
- Use `inventory_depth=expanded` for lifecycle, state, payment, job, import, webhook, retry, storage, external-side-effect, authorization, or restart-affecting invariants.
- For strict `STABLE_FIX_PLAN`, expanded inventory requires `unaccounted_domains=[]`, `blocking_domain_residuals=[]`, and no path with `status=unaccounted` or `status=blocking_residual`.
- `expectation_source=missing` is not covered. Classify it as unaccounted, a graded confidence boundary, or a blocker.
- If the expanded inventory would exceed the budget, return `GRADED_REVIEW` or `BLOCKER` instead of producing a sprawling unstable plan.

For `Checked Nearby Cases`, convert each candidate into operator language:

- `Case checked`: the adjacent scenario or sibling path, not the invariant jargon.
- `Result`: `ok`, `problem found`, `covered by plan`, or `not applicable` localized to `output_language`.
- `Evidence`: short file/command evidence.

Keep this section short enough to scan. Put full fixed-point and search proof in `Closure Evidence`.

Every `blocking_residual` in `same_invariant_saturation` means the result cannot be `STABLE_FIX_PLAN`; revise the plan or return `BLOCKER`. The launcher may downgrade an evidence-backed but incomplete artifact to `GRADED_REVIEW`; if closure is incomplete, the artifact must explicitly state that same-invariant closure is not proven and must not present the plan as stable.

`adversarial_second_pass` is required before `STABLE_FIX_PLAN`. After mentally applying the proposed fix, run a hostile second pass asking: "what code-backed bug in this same invariant would the next deep review find?" Return this shape:

```text
AdversarialSecondPass
- imagined_patch:
- attack_question:
- same_invariant_candidates_after_patch:
  - candidate:
    evidence:
    disposition: closed_by_plan|blocking_residual|not_applicable
- result: clean|plan_revised|blocker
- why_next_review_should_not_find_same_invariant_bug:
```

If the hostile pass finds any code-backed same-invariant candidate with `blocking_residual`, the plan is not stable. Revise the plan at the owning boundary and rerun the pass, or return `BLOCKER` when revision crosses scope or needs a business decision.

`patch_simulation_ledger` is required before `STABLE_FIX_PLAN`. It is not a chain-of-thought transcript. It is a compact audit trail that proves the fixed-point loop had concrete checkpoints. Use this shape:

```text
PatchSimulationLedger
- finding_id:
  iteration:
  imagined_patch_contract:
    changed_boundary:
    state_transition_change:
    persistence_effect:
    reader_writer_behavior_after_patch:
    before_after_test_oracle_or_evidence:
  re_review_checks:
    - check:
      evidence:
      result: clean|new_candidate_found|not_applicable
  previous_failure_mode_status: closed|still_open|not_applicable
  new_same_invariant_candidates:
    - candidate:
      evidence:
      disposition: closed_by_plan|blocking_residual|not_applicable
  result: clean|plan_revised|blocker
  stop_reason:
```

Rules:

- Every accepted finding must have at least one ledger row.
- Keep the ledger bounded: maximum 3 rows per accepted finding. If more iterations would be needed, return `BLOCKER` or downgrade for launcher grading instead of expanding the ledger.
- `imagined_patch_contract` must name changed boundary, state transition, persistence effect, reader/writer behavior after patch, and before/after test oracle or evidence.
- If the patch is purely read-side or persistence is not applicable, say why in `persistence_effect`; do not leave it blank.
- If the ledger cannot define the behavior contract, do not claim `fixed_point_reached=true`.
- If `new_same_invariant_candidates` contains any `blocking_residual`, revise the plan or return `BLOCKER`.
- Keep ledger rows compact; full reasoning belongs nowhere in the artifact.

`process_metrics` is required for `STABLE_FIX_PLAN` and `GRADED_REVIEW`. It must use numeric counters from the actual review pipeline, not invented precision. Use this shape:

```text
ProcessMetrics
- invariants_classified:
- candidate_observations:
- candidate_observations_accounted:
- candidate_observations_unaccounted:
- findings_accepted:
- fixed_point_iterations:
- nearby_cases_checked:
- same_invariant_cases_open:
- blocking_residuals:
- verification_residuals:
- production_wiring_paths_checked:
- restart_persistence_paths_checked:
- participating_domains_count:
- domains_with_expectation_source:
- domains_unaccounted:
- semantic_entity_paths_checked:
- semantic_entity_paths_unaccounted:
- expanded_domain_inventories:
- patch_simulation_rows:
- trace_file:
```

`candidate_accounting_breakdown` is required for `STABLE_FIX_PLAN` and `GRADED_REVIEW`. It is the human/audit explanation for `candidate_observations_accounted`, not a long mandatory counter list. Use a bounded structured list:

```text
CandidateAccountingBreakdown
- accepted_findings:
- rejected:
  - reason: decision_context|unclassified|duplicate_or_covered|low_confidence|out_of_scope|other
    count:
    sample_or_note:
- deferred_to_residual_risk:
- protected_input_non_findings:
- unaccounted:
```

Rules:

- Allowed metric values are non-negative integers, `unknown`, or `not_tracked`.
- Do not invent exact counts. If a value was not tracked, use `not_tracked`; if it was attempted but cannot be reconstructed, use `unknown`.
- For strict `STABLE_FIX_PLAN`, these metrics must be numeric: `invariants_classified`, `candidate_observations`, `candidate_observations_accounted`, `candidate_observations_unaccounted`, `findings_accepted`, `fixed_point_iterations`, `nearby_cases_checked`, `same_invariant_cases_open`, `blocking_residuals`, `participating_domains_count`, `domains_with_expectation_source`, `domains_unaccounted`, `semantic_entity_paths_checked`, `semantic_entity_paths_unaccounted`, and `patch_simulation_rows`.
- Candidate accounting equation: `candidate_observations` must equal `candidate_observations_accounted + candidate_observations_unaccounted`.
- `candidate_observations_accounted` must equal `candidate_observations - candidate_observations_unaccounted`.
- `candidate_accounting_breakdown` must sum to `candidate_observations`. Accepted findings must match `findings_accepted`; unaccounted must match `candidate_observations_unaccounted`. Rejection/deferred/protected reasons may be grouped in the breakdown and are not critical process metrics by themselves.
- For strict `STABLE_FIX_PLAN`, `candidate_observations_unaccounted`, `same_invariant_cases_open`, `blocking_residuals`, `domains_unaccounted`, and `semantic_entity_paths_unaccounted` must be numeric `0`.
- For strict `STABLE_FIX_PLAN`, `review_health.candidate_accounting` must be `complete`, `review_health.coverage` must be `complete`, and `review_health.fixed_point` must be `reached`.
- `domains_with_expectation_source` must equal `participating_domains_count` for strict `STABLE_FIX_PLAN` unless all missing-source domains are explicitly `not_applicable` or `out_of_scope` in `participating_domain_inventory`.
- `fixed_point_iterations` must match `fixed_point_status.iterations_run`.
- `patch_simulation_rows` must match the number of ledger rows.
- If a trace file was not written, set `trace_file=not_written` and explain in `Closure Evidence`; absence of a trace file is not a blocker when `process_metrics` and `patch_simulation_ledger` are present.
- If a trace file is written, it must be append-only JSONL under `.codex/tmp/deep-review/<run-id>.jsonl` and must contain only structured process events: stage names, counts, invariant/finding ids, evidence references, rejection categories, patch simulation contracts, gate outcomes, and stop reasons. Do not log private chain-of-thought, specialist raw notes, or intermediate findings intended to stay out of chat.

Trace JSONL events must use this schema family when written:

```json
{"event":"review_started","run_id":"<id>","base":"<base>","branch":"<branch>","output_language":"<language>","budget_class":"<quick|normal|exhaustive>"}
{"event":"invariant_map_built","run_id":"<id>","invariants_classified":0,"invariant_ids":[],"evidence_refs":[]}
{"event":"specialist_observations_collected","run_id":"<id>","specialists":[],"candidate_observations":0}
{"event":"candidate_gate_applied","run_id":"<id>","accepted":0,"accounted":0,"unaccounted":0,"breakdown":[{"reason":"decision_context|unclassified|duplicate_or_covered|low_confidence|out_of_scope|other","count":0}]}
{"event":"patch_simulated","run_id":"<id>","finding_id":"<id>","iteration":1,"changed_boundary":"<boundary>","re_review_checks":[],"new_same_invariant_candidates":0,"result":"clean|plan_revised|blocker"}
{"event":"launcher_gate_evaluated","run_id":"<id>","strict_pass":true,"format_gaps":[],"blocking_residuals":0}
{"event":"review_finished","run_id":"<id>","result":"STABLE_FIX_PLAN|GRADED_REVIEW|BLOCKER","findings_accepted":0,"fixed_point_iterations":0,"stop_reason":"<reason>"}
```

Rules:

- Use only the event names above unless a future contract revision adds another name.
- Omit unknown optional fields rather than filling them with prose.
- For arrays, use compact ids or evidence references, not raw specialist notes.
- `patch_simulated` must not include the full ledger if it would duplicate long text; include ids, boundary, counts, and results.

`production_wiring_evidence` is required when the plan adds or changes a runtime-critical contract/dependency. It must name the production registration or construction path, not only tests or ad hoc constructors.

`commit_side_effect_order_evidence` is required when a side effect is derived from a state/lifecycle/persistence commit. It must prove the side effect is after successful commit or inside the same atomic boundary.

`restart_persistence_evidence` is required when a runtime fact affects post-restart behavior. It must name where the fact is persisted, how it is rehydrated, and which post-restart consumer uses it.

`residual_risk_classification` must classify each residual as:

- `blocking_residual`: can invalidate the stable fix or same invariant closure;
- `verification_residual`: needs extra proof but does not change the fix shape;
- `out_of_scope_residual`: real follow-up outside the user-approved scope.

Any `blocking_residual` requires plan revision or `BLOCKER`.

`architectural_root_assessment` must classify the plan as:

- `local_boundary_root`: the owning boundary named by `InvariantMap` is sufficient to close all known same-invariant failure modes;
- `symptom_of_larger_architecture`: the plan only patches the observed state while the real source of truth, ownership boundary, or architectural shape remains wrong;
- `unclear`: evidence is insufficient.

For `local_boundary_root`, state why the fix is not merely a local guard and why a larger redesign is not required. For `symptom_of_larger_architecture`, revise the stable fix to the larger owning boundary or return `BLOCKER` if that larger boundary needs a business decision or crosses scope. For `unclear`, return `BLOCKER`.

## Counterfactual Sweep

Before returning `STABLE_FIX_PLAN`, run a bounded fixed-point loop over the classified invariant. The loop mentally applies the proposed fix and reviews the imagined patched state.

Return these blocks:

```text
CounterfactualSweep
- iteration:
  imagined_patch:
  next_review_would_check:
  likely_next_failure_modes:
  participating_domains_rechecked:
  sibling_paths_rechecked:
  production_wiring_rechecked:
  commit_side_effect_order_rechecked:
  restart_persistence_rechecked:
  local_guard_or_boundary_fix:
  plan_revision_if_needed:
  why_next_review_should_be_clean:
  blocker_if_not_clean:

FixedPointStatus
- fixed_point_reached: true|false
- iterations_run:
- remaining_same_invariant_failure_modes:
- evidence_limit:
- blocker_if_false:
```

Rules:

- Run at most 3 iterations.
- Each iteration must consume `same_invariant_saturation`; do not build the loop only around the first accepted finding.
- Each iteration must consume `participating_domain_inventory` for expanded inventories; do not build the loop only around the first accepted finding or one operation path.
- Each iteration must include an `adversarial_second_pass` that actively searches for the next code-backed same-invariant bug after the imagined patch.
- Each iteration must have a corresponding `patch_simulation_ledger` row for each accepted finding affected by that iteration.
- Only same-invariant failure modes with code evidence are allowed. Do not invent speculative future-proofing work.
- `likely_next_failure_modes` must include every plausible next failure mode of the same invariant discovered from current code evidence.
- `sibling_paths_rechecked` must name concrete files/functions or say why no siblings exist.
- `participating_domains_rechecked` must name each relevant participating domain/path for expanded inventories, or say why the inventory is local.
- `production_wiring_rechecked` must name the runtime wiring path when a runtime-critical dependency is involved, or say why none is involved.
- `commit_side_effect_order_rechecked` must name the commit and side effect order when relevant, or say why none is involved.
- `restart_persistence_rechecked` must name persistence, rehydration, and post-restart consumer when restart behavior is involved, or say why none is involved.
- `local_guard_or_boundary_fix` must state whether the plan fixes the owning boundary. If it is only a local guard, reject the plan.
- `why_next_review_should_be_clean` must also explain why the imagined patch is a root fix within the selected boundary rather than a symptom patch that shifts the same invariant failure elsewhere.
- If `why_next_review_should_be_clean` cannot be defended with code evidence, revise the plan and rerun the loop.
- If the imagined patched state leaves a same-invariant failure mode open, revise the plan at the owning boundary and rerun the loop.
- Stop only when `fixed_point_reached=true`, `remaining_same_invariant_failure_modes=[]`, `local_guard_or_boundary_fix=boundary_fix`, `process_metrics.same_invariant_cases_open=0`, `process_metrics.blocking_residuals=0`, `process_metrics.domains_unaccounted=0`, and `process_metrics.semantic_entity_paths_unaccounted=0`.
- If closure requires a business decision, or the loop reaches 3 iterations without a fixed point, return `BLOCKER`.

`pipeline_order_evidence` must state:

- when DecisionContextGate was produced;
- when `InvariantMap` was produced;
- which specialists received that `InvariantMap`;
- whether any CandidateObservation was rejected as unclassified;
- whether any CandidateObservation was rejected by decision context;
- when `MaintainabilityCause` ran;
- that ClosurePlanner ran last.

`decision_conformance_evidence` must state for each reported issue:

- which accepted decisions it preserves;
- which rejected approaches it avoids;
- which review non-findings it does not relitigate;
- which scope boundaries it stays inside;
- whether protected upstream writer coverage was checked, and if a downstream guard is proposed, which unprotected writer or explicit corruption requirement justifies it;
- whether any candidates were rejected because they conflicted with decision context.

If `still_open_failure_modes_after_plan` is not empty, return `BLOCKER` or make the plan close them.

If `same_invariant_saturation` is missing, lacks search evidence for relevant sibling paths, or contains `blocking_residual`, do not return `STABLE_FIX_PLAN`. Make the closure gap explicit for launcher grading when findings are still code-evidenced and safe to show; otherwise return `BLOCKER`.

If `participating_domain_inventory` is missing for an expanded invariant, contains unaccounted relevant domains/paths, reports missing expectation sources as covered, or is not consumed by same-invariant saturation, do not return `STABLE_FIX_PLAN`. Make the coverage gap explicit for launcher grading when findings are still code-evidenced and safe to show; otherwise return `BLOCKER`.

If `adversarial_second_pass` is missing or finds a code-backed same-invariant candidate not closed by the plan, do not return `STABLE_FIX_PLAN`. Revise the plan, make the incomplete closure explicit for launcher grading when findings are still safe to show, or return `BLOCKER`.

If `process_metrics` or `patch_simulation_ledger` is missing, do not return `STABLE_FIX_PLAN`. If findings are still evidence-backed and decision-conformant, make the process observability gap explicit for launcher grading; otherwise return `BLOCKER`.

If `patch_simulation_ledger` lacks behavior contracts for every accepted finding, or `process_metrics.same_invariant_cases_open` / `process_metrics.blocking_residuals` / `process_metrics.domains_unaccounted` / `process_metrics.semantic_entity_paths_unaccounted` is nonzero, do not return `STABLE_FIX_PLAN`. Revise the plan or return `BLOCKER`.

If `architectural_root_assessment` is missing, `unclear`, or says `symptom_of_larger_architecture` without revising the owning boundary, return `BLOCKER`.

If `production_wiring_evidence`, `commit_side_effect_order_evidence`, `restart_persistence_evidence`, or `sibling_semantic_paths` is applicable but missing, return `BLOCKER` or retry closure with that evidence.

If `residual_risk_classification` contains any `blocking_residual`, return `BLOCKER` or revise the plan until no blocking residual remains.
