---
name: deep-review
description: Run an invariant-first deep review by delegating to deep_review_orchestrator. Use only when the user explicitly invokes `$deep-review` or asks for deep orchestrated review. The launcher must keep findings out of chat until the orchestrator maps observations to business/runtime invariants, owning boundaries, adaptive participating-domain coverage, nearby same-invariant cases, and adversarial fixed-point checks, then relay an operator-facing STABLE_FIX_PLAN, GRADED_REVIEW, or BLOCKER in the resolved output language.
---

# Deep Review

Act as a launcher only. `$deep-review` authorizes delegation to `deep_review_orchestrator`.

## Skill Settings

- `output_language`: `auto` by default. Resolve from explicit user language request first, otherwise from the dominant conversation language.
- `presentation_style`: `operator_review` by default. User-facing output prioritizes actionable findings and fix plan before audit evidence.
- `nearby_cases_label`: localize the internal same-invariant saturation proof as `Checked Nearby Cases`; in Russian use `Что еще проверили`.
- `process_observability`: `compact` by default. Require process metrics and a patch simulation ledger, but record only stage counts, decisions, evidence references, and stop reasons. Do not record private chain-of-thought.
- `trace_file`: `optional_debug` by default. When practical, the orchestrator may create an append-only JSONL trace under `.codex/tmp/deep-review/<run-id>.jsonl`; the trace must contain only structured process events, not reasoning transcripts or intermediate findings intended for chat.
- `domain_inventory_mode`: `adaptive` by default. Require a compact inventory of domains that participate in each accepted invariant, but scale depth by invariant class: simple local render/test-oracle issues may name only the local page/component/test domains; lifecycle, state, payment, job, import, webhook, retry, storage, external-side-effect, authorization, or restart-affecting invariants must enumerate the cross-domain semantic paths that can create, mutate, store, read, poll, clean up, document, or test the same semantic entity.

## Launcher Job

Positive path is mandatory. A successful `$deep-review` turn must follow this exact shape:

1. Launch only `deep_review_orchestrator` for review content.
2. Receive terminal `ARTIFACT_READY ... artifact_path=...`.
3. Validate the referenced JSON artifact and metrics gate.
4. Render it through `scripts/render_review_manifest.py`.
5. Send that renderer stdout as the final answer, byte-for-byte except allowed multi-part splitting.

The launcher succeeds by relaying the renderer output, not by producing a better-looking manual review. When the terminal artifact path is missing, malformed, or absent, the launcher must repair the artifact contract or return a fixed `BLOCKER`; it must not switch into ordinary code-review mode.

1. Resolve the review base. Use the user-supplied base when present.
2. Capture compact scope:
   - repo path, branch, base;
   - `git status --short`;
   - `git diff --stat <base>...HEAD`;
   - `git diff --cached --stat`;
   - `git diff --stat`;
   - untracked files from `git status --short`.
3. Pass conversation constraints explicitly:
   - `implementation_intent`;
   - `accepted_decisions`;
   - `rejected_approaches`;
   - `scope_boundaries`;
   - `review_non_findings`;
   - `open_questions`.
4. Resolve `output_language` before delegation:
   - use an explicit user request when present, for example "по-русски", "in English", or "answer in <language>";
   - otherwise use the dominant language of the current conversation; for Russian-language threads, set `output_language=Russian` explicitly even when code symbols, paths, and sentinel tokens are English;
   - default to `English` only when the conversation language is ambiguous;
   - keep sentinel tokens (`STABLE_FIX_PLAN`, `GRADED_REVIEW`, `BLOCKER`) and code symbols unchanged, but localize section headings, prose, finding text, plan items, confidence boundaries, and residual risk explanations.
5. Read the reference contracts below and inline their contents into the orchestrator prompt. Do not pass only file paths; the orchestrator may not have loaded skill files.
6. Choose a runtime budget class and announce it before delegation:
   - `normal` by default: 45 minutes total;
   - `exhaustive` when the user explicitly accepts long-running quality review: 90 minutes total;
   - `quick` only when the user asks for a fast pass: 20 minutes total.
7. Delegate to `deep_review_orchestrator`; do not run a parallel local review.
8. Poll the orchestrator in bounded waits instead of one silent wait:
   - use a 5 minute poll interval for `normal` and `exhaustive`;
   - use a 3 minute poll interval for `quick`;
   - after each poll timeout, emit one progress heartbeat with elapsed time, budget class, and the fact that no terminal result exists yet;
   - do not emit intermediate findings, specialist notes, rejected candidates, file names, or partial summaries.
9. If the runtime budget is exhausted before terminal `ARTIFACT_READY` or `BLOCKER`, stop the orchestrator and return only:
   `BLOCKER: deep-review runtime budget exhausted before terminal ARTIFACT_READY/BLOCKER. Minimal next action: rerun with exhaustive budget or narrow review scope.`
10. If the user explicitly interrupts or asks to stop, stop the orchestrator and report that no terminal review result was produced.
11. Do not rely on `fork_context`; pass snapshot, decision context, and inlined contracts explicitly.
12. Do not emit intermediate findings, specialist notes, or partial summaries.
13. Treat `$deep-review` as review-only for the current turn. Historical requests such as "fix", "исправляй", or "давай" are not edit authorization after a terminal review artifact. After `METRICS_PASS`, the launcher may only relay the accepted artifact; it must not patch files, run fix commands, stage changes, or silently continue into implementation unless the user sends a new post-review instruction.
14. Load the structured artifact from the terminal manifest, then run a metrics reflection gate before accepting `STABLE_FIX_PLAN` or grading `GRADED_REVIEW`:
   - terminal orchestrator output must be one short line: `ARTIFACT_READY result=<STABLE_FIX_PLAN|GRADED_REVIEW|BLOCKER> artifact_path=<absolute path>`;
   - `artifact_path` must point under `<repo_path>/.codex/tmp/deep-review/<run-id>/artifact.json`;
   - do not accept raw JSON in the terminal agent message;
   - use a separate evaluator (`plan_contract_reviewer` when available, otherwise a launcher-owned checklist) to validate only process metrics, patch simulation ledger, fixed-point consistency, and optional trace schema;
   - the metrics evaluator must return only `METRICS_PASS` or a structured `METRICS_FAIL` with `blocking_gaps`, `downgrade_allowed`, `retry_allowed`, and `minimal_retry_instruction`;
   - it must not inspect for new code findings, change finding priorities, rewrite the plan, or relitigate decision context;
   - a bare `METRICS_FAIL` without gaps is invalid gate output; treat it as `blocking_gaps=[invalid_metrics_gate_output]`, retry the gate prompt once if budget allows, and otherwise downgrade only if the Minimum Evidence Gate passes;
   - if it returns structured `METRICS_FAIL`, treat the gaps as launcher-gate format/process gaps and prefer `GRADED_REVIEW` when the Minimum Evidence Gate passes; retry the orchestrator only when stable closure is explicitly required or the gaps make the findings unsafe to show.
15. Validate and render the accepted structured artifact with the deterministic renderer:
   - pass the terminal manifest to `scripts/render_review_manifest.py`;
   - renderer validation failure is a launcher-gate format gap, not a new code finding;
   - retry the orchestrator once with the renderer error when budget allows and the Minimum Evidence Gate is not yet satisfied;
   - the final user-facing response is the renderer output, not the manifest or raw JSON.
   - hard stop: any orchestrator terminal output that does not start with `ARTIFACT_READY ` or `BLOCKER:` is invalid terminal output, even when it contains plausible findings or starts with `STABLE_FIX_PLAN`/`GRADED_REVIEW`;
   - on invalid terminal output, do not inspect code, do not validate findings, do not call secondary reviewers on the findings, and do not manually format a review;
   - retry the orchestrator once with this exact repair instruction: `Your previous terminal output violated the deep-review relay contract. Write a valid artifact.json under <repo_path>/.codex/tmp/deep-review/<run-id>/artifact.json and return only ARTIFACT_READY result=<STABLE_FIX_PLAN|GRADED_REVIEW|BLOCKER> artifact_path=<absolute path>, or return BLOCKER: <reason>. Do not return Markdown findings.`;
   - when the retry again returns invalid terminal output, return exactly: `BLOCKER: deep-review orchestrator returned invalid terminal output instead of ARTIFACT_READY/BLOCKER after retry. Minimal next action: fix the orchestrator artifact contract before using this review result.`
16. Evaluate the loaded artifact with the graded launcher gate:
   - `STABLE_FIX_PLAN`: strict gate passed, metrics gate passed, renderer validation passed; relay the rendered artifact.
   - `GRADED_REVIEW`: strict gate failed only on closure/format completeness, but the artifact contains code-evidenced findings that satisfy the minimum evidence gate; preserve those findings and render the graded artifact.
   - `BLOCKER`: no terminal manifest/artifact, no usable findings, decision conflict, unclear owning boundary, missing invariant map, renderer-invalid artifact after retry, or other evidence gap that makes findings unsafe to show as review output.
17. Do not hand-format, summarize, shorten, translate after the fact, reorder, omit, or "explain by meaning" any accepted terminal sections. Rendering is allowed only through `scripts/render_review_manifest.py` or the fixed launcher-generated budget/gate blocker strings.
18. If the rendered result is too long for one response, split it into consecutive parts labeled `STABLE_FIX_PLAN part N/M`, `GRADED_REVIEW part N/M`, or `BLOCKER part N/M`, preserving rendered order exactly. Do not replace omitted sections with a summary.
19. After relaying the rendered result, do not append commentary, acceptance notes, next-step suggestions, or separate summaries in the same final response.

## Progress Heartbeats

Progress heartbeats are operator visibility only. They must prove that the launcher is alive without leaking review content before the gate accepts it.

Allowed heartbeat content:

- elapsed time and total budget;
- budget class (`quick`, `normal`, `exhaustive`);
- current launcher state (`waiting for terminal result`, `retrying after launcher-gate rejection`, `budget exhausted`);
- confirmation that no intermediate observations/findings are being published.

Forbidden heartbeat content:

- candidate findings or observations;
- specialist output;
- suspected files, symbols, or failure modes;
- partial plans;
- rejected candidates.

Use concise heartbeat text, for example:

```text
deep-review still running: 15/45 min elapsed. No terminal ARTIFACT_READY/BLOCKER yet; not publishing intermediate observations.
```

If the user asks whether long runtime is acceptable, prefer continuing within the selected budget and keep heartbeats. A long review is acceptable only while the launcher remains observable and the budget has not expired.

## Terminal Relay Contract

The launcher is not the reviewer and not the editor of review content. Once the launcher gate accepts a terminal artifact manifest, the user-facing final answer must be the deterministic renderer output for that artifact.

Allowed final outputs:

- the rendered `STABLE_FIX_PLAN` produced by `scripts/render_review_manifest.py`;
- the rendered `BLOCKER` produced by `scripts/render_review_manifest.py`;
- the rendered `GRADED_REVIEW` produced by `scripts/render_review_manifest.py` when the strict closure gate fails but the minimum evidence gate passes;
- the fixed launcher-generated budget/gate blocker strings defined below.

Forbidden final outputs:

- raw JSON;
- raw artifact manifest as the final user answer;
- a manually formatted review that bypasses the renderer;
- a shortened plan;
- a prose recap of findings;
- a translated or normalized version of the result after the orchestrator returns; localization must happen inside the orchestrator artifact through `output_language`;
- a response that keeps only `Closure Evidence` or only the plan;
- dropping `Findings` because they look redundant with the plan;
- dropping file links or line references;
- dropping findings solely because closure evidence is incomplete;
- adding a postscript such as "key takeaway" or "next step".

Before sending the final answer, run this relay checklist:

- first non-empty line is exactly `STABLE_FIX_PLAN`, `GRADED_REVIEW`, or starts with `BLOCKER:`;
- final answer is the exact stdout produced by `scripts/render_review_manifest.py`, or one fixed launcher-generated budget/gate blocker string;
- raw orchestrator Markdown was never accepted as a terminal review result;
- no manual code inspection, finding validation, secondary reviewer call, or hand-formatted review happened after invalid terminal output;
- raw JSON is not exposed to the user;
- all findings, fix plan items, verification rows, nearby-case rows, review-health rows, process metrics, candidate accounting, closure evidence, and residual risks accepted by the launcher are present in the rendered output;
- no orchestrator-owned content was paraphrased by the launcher outside deterministic rendering.
- no file edits, formatting commands, tests, staging, commits, or implementation actions were run after the terminal manifest/artifact was accepted in a `$deep-review` turn.

If any relay checklist item fails, do not send the answer. Reconstruct the final answer from the stored terminal orchestrator result and repeat the checklist.

## Core Contract

Observations are not findings.

Conversation decisions are binding review constraints, not background.

The orchestrator must treat these launcher fields as normative:

- `accepted_decisions`;
- `rejected_approaches`;
- `review_non_findings`;
- `scope_boundaries`.

A candidate that relitigates an accepted decision, proposes a rejected approach, or reports a declared non-finding must be rejected before final planning. If code evidence proves an accepted decision makes the implementation impossible or contradicts `implementation_intent`, return `BLOCKER` naming that decision conflict. Do not convert the conflict into a normal finding.

The orchestrator must:

- build an `InvariantMap` before final findings;
- build an adaptive `ParticipatingDomainInventory` as part of the `InvariantMap` before final findings;
- ask specialists for observations only, not final findings;
- merge observations by invariant and owning boundary;
- reject unclassified observations;
- reject decision-conflicting observations;
- build same-invariant saturation before final `STABLE_FIX_PLAN`;
- run an adversarial second pass over the imagined patched state before final `STABLE_FIX_PLAN`;
- build `process_metrics` from actual pipeline counts and gate outcomes;
- build `patch_simulation_ledger` from fixed-point iterations without exposing private chain-of-thought;
- treat subagents as independent observation sources, not as ToT branches that decide final findings;
- trace production wiring for runtime-critical contracts and dependencies;
- trace commit-before-side-effect ordering when a side effect depends on a state/lifecycle commit;
- trace restart persistence for runtime facts that affect behavior after restart;
- enumerate sibling paths that create or mutate the same semantic entity;
- enumerate participating domains and semantic entity paths for lifecycle/stateful invariants before claiming same-invariant saturation;
- preserve valid narrower fixes as closed failure modes, not as bad work;
- return `BLOCKER` if the invariant or owning boundary cannot be classified.

Load and use these reference contracts:

- [Invariant Classifier](references/invariant-classifier.md): first pass, required before accepting findings.
- [Observation Specialists](references/observation-specialists.md): prompts for correctness/security/test/maintainability scouts.
- [Maintainability Cause](references/maintainability-cause.md): separate lens for solution-shape root causes.
- [Closure Planner](references/closure-planner.md): final `STABLE_FIX_PLAN` evidence and launcher gate.
- [Metrics Reflection Gate](references/metrics-reflection-gate.md): separate process-quality evaluator for metrics, ledger, fixed-point consistency, and optional trace schema.

Execution graph:

```text
0. DecisionContextGate -> binding accepted/rejected/non-finding constraints
1. InvariantClassifier -> InvariantMap + adaptive ParticipatingDomainInventory using DecisionContextGate
2. DomainCoverageGate -> participating domains and semantic paths marked covered, not_applicable, out_of_scope, or blocking_residual
3. ObservationSpecialists -> CandidateObservation[] using InvariantMap + ParticipatingDomainInventory + DecisionContextGate
4. MaintainabilityCause -> MaintainabilityCause[] using InvariantMap + CandidateObservation[] + DecisionContextGate
5. ClosurePlanner -> STABLE_FIX_PLAN, GRADED_REVIEW, or BLOCKER with decision_conformance_evidence
6. MetricsReflectionGate -> METRICS_PASS or structured METRICS_FAIL before launcher acceptance
```

The orchestrator must not spawn observation specialists before it has an `InvariantMap`. If it cannot build `InvariantMap`, it must return `BLOCKER`.

## Delegation Prompt

Use this shape:

```text
Review <repo_path> on branch <branch> against base <base>.

Snapshot:
<status, diff stats, untracked files>

Decision context:
implementation_intent=<...>
accepted_decisions=<...>
rejected_approaches=<...>
scope_boundaries=<...>
review_non_findings=<...>
open_questions=<...>

Output:
output_language=<resolved language, for example Russian or English>
localization_rule=Keep sentinel tokens, code identifiers, file paths, command names, enum values, and API paths unchanged; localize section headings, prose, finding text, plan text, confidence boundaries, and residual risk explanations.
presentation_rule=Write one valid JSON object matching StructuredReviewArtifact from ClosurePlannerContract to `<repo_path>/.codex/tmp/deep-review/<run-id>/artifact.json`, then return only `ARTIFACT_READY result=<STABLE_FIX_PLAN|GRADED_REVIEW|BLOCKER> artifact_path=<absolute path>`. Do not return Markdown. Do not return raw JSON in the terminal agent message. The launcher will validate and render Markdown using scripts/render_review_manifest.py.

Process observability:
process_observability=compact
domain_inventory_mode=adaptive
trace_file_policy=optional_debug_append_only_jsonl
trace_file_path=<repo_path>/.codex/tmp/deep-review/<run-id>.jsonl
trace_redaction_rule=Do not log private chain-of-thought, specialist raw notes, or intermediate findings meant to stay out of chat. Log only stage names, counts, invariant/finding ids, evidence references, rejection categories, patch simulation contracts, gate outcomes, and stop reasons.
trace_event_schema=Use only event names defined in ClosurePlannerContract: review_started, invariant_map_built, specialist_observations_collected, candidate_gate_applied, patch_simulated, launcher_gate_evaluated, review_finished.

Runtime budget:
budget_class=<quick|normal|exhaustive>
wall_clock_budget_minutes=<20|45|90>
max_specialist_rounds=1
max_launcher_retry=1
max_closure_iterations=3
budget_rule=If evidence is insufficient inside the budget, return BLOCKER instead of starting another exploratory loop.

Reference contracts are inlined below. Treat them as binding:

<InvariantClassifierContract>
<paste references/invariant-classifier.md>
</InvariantClassifierContract>

<ObservationSpecialistsContract>
<paste references/observation-specialists.md>
</ObservationSpecialistsContract>

<MaintainabilityCauseContract>
<paste references/maintainability-cause.md>
</MaintainabilityCauseContract>

<ClosurePlannerContract>
<paste references/closure-planner.md>
</ClosurePlannerContract>

<MetricsReflectionGateContract>
<paste references/metrics-reflection-gate.md>
</MetricsReflectionGateContract>

Hard rule: observations are not findings.
Hard rule: conversation decisions are binding constraints. Reject candidates that contradict accepted_decisions, rejected_approaches, review_non_findings, or scope_boundaries. If a real contradiction is proven, return BLOCKER instead of a finding.
Hard rule: runtime-critical contracts must include production wiring evidence through the composition root, hosted-service construction, or equivalent runtime entrypoint.
Hard rule: side effects derived from lifecycle/state commits must either be inside the same atomic boundary or occur only after the owning commit succeeds.
Hard rule: if a runtime fact affects restart behavior, closure must show where it is persisted, rehydrated, and consumed after restart.
Hard rule: if a fix touches one creator/writer of a semantic entity, sibling creator/writer paths for the same entity must be enumerated and either covered or ruled out with evidence.
Hard rule: for lifecycle, state, payment, job, import, webhook, retry, storage, external side-effect, authorization, or restart-affecting invariants, `STABLE_FIX_PLAN` requires an adaptive participating-domain inventory. The inventory must name every relevant domain for the semantic entity, the expectation source for that domain, and each create/mutate/read/store/poll/cleanup/docs/tests path as covered, not_applicable, out_of_scope, or blocking_residual. If any relevant domain is unaccounted, return GRADED_REVIEW or BLOCKER instead of STABLE_FIX_PLAN.
Hard rule: do not use a full domain matrix for simple local render/layout/test-oracle issues unless the invariant classification proves cross-domain lifecycle/state behavior. For simple local invariants, keep the inventory small and bounded.
Hard rule: STABLE_FIX_PLAN requires same-invariant saturation internally: enumerate same-invariant candidate failure modes with concrete search/file evidence across relevant writer, reader, job, API, client, persistence, projection, and manual rerun paths; each candidate must be covered_by_plan, not_applicable, or blocking_residual. In user-facing output, render this as "Checked Nearby Cases" or the localized equivalent, not as the jargon title "Same-Invariant Saturation".
Hard rule: STABLE_FIX_PLAN requires an adversarial second pass after the imagined patch: actively ask what code-backed same-invariant bug the next deep review would find. Any blocking same-invariant candidate means the plan must be revised or the result is not stable.
Hard rule: STABLE_FIX_PLAN requires process_metrics and patch_simulation_ledger. The ledger must describe the imagined patch as a behavior contract, not as a thought transcript. If the patch contract cannot name changed boundary, state transition, persistence effect, reader/writer behavior, and before/after test oracle or evidence, do not claim fixed_point_reached=true.
Hard rule: STABLE_FIX_PLAN requires complete candidate accounting. Every CandidateObservation must be accounted as accepted finding, rejected_by_decision_context, rejected_as_unclassified, rejected_as_duplicate_or_covered, rejected_as_low_confidence, rejected_as_out_of_scope, deferred_to_residual_risk, protected_input_non_finding, or explicitly unaccounted. `candidate_observations_unaccounted` must be 0 for STABLE_FIX_PLAN.
Hard rule: Do not invent process metric precision. Use non-negative integers when tracked, `unknown` when attempted but unreconstructable, and `not_tracked` when not tracked. Strict STABLE_FIX_PLAN requires numeric critical metrics listed in ClosurePlannerContract.
Hard rule: A separate MetricsReflectionGate will validate process_metrics, patch_simulation_ledger, fixed_point consistency, and optional trace schema before launcher acceptance. Make those fields internally consistent; do not rely on prose claims when counters or ledger rows contradict them.
Hard rule: GRADED_REVIEW can show evidence-backed findings when saturation is incomplete, but it must not claim the invariant is closed or that the plan is stable.
Hard rule: runtime budget is a quality boundary. Long work is allowed inside the budget; once evidence cannot be completed inside the budget, return BLOCKER rather than continuing exploration.
Hard rule: terminal output must be only `ARTIFACT_READY result=<...> artifact_path=<...>` after writing valid JSON matching the ClosurePlanner StructuredReviewArtifact contract to that path. The JSON artifact must contain `output_language`, findings, impact, evidence, fix plan, verification, nearby-case coverage, review health, process metrics, candidate accounting, and concise closure details. Do not return Markdown, raw JSON, or a prose wall in the terminal agent message.

Execution order is mandatory:
0. Build DecisionContextGate from accepted_decisions, rejected_approaches, review_non_findings, and scope_boundaries.
1. Build InvariantMap and adaptive ParticipatingDomainInventory using DecisionContextGate.
2. Run DomainCoverageGate: mark participating domains and semantic paths as covered, not_applicable, out_of_scope, unaccounted, or blocking_residual.
3. Only then ask specialists for CandidateObservation.
4. Run MaintainabilityCause after CandidateObservation.
5. Run ClosurePlanner last.

The orchestrator must merge candidates by invariant and owning boundary, reject unclassified observations, reject decision-conflicting observations, and return only STABLE_FIX_PLAN, GRADED_REVIEW, or BLOCKER.

Do not publish intermediate findings or specialist-by-specialist output.
The launcher will render your accepted JSON artifact deterministically from `artifact_path`, so include every user-visible finding, plan item, evidence block, residual risk, file link, and line reference as structured fields in the artifact file itself.
```

## Launcher Gate

Before showing strict `STABLE_FIX_PLAN`, verify:

- MetricsReflectionGate returned `METRICS_PASS`;
- `Closure Evidence` includes `pipeline_order_evidence`;
- `pipeline_order_evidence` proves InvariantMap existed before CandidateObservation;
- `Closure Evidence` includes `counterfactual_sweep`;
- `counterfactual_sweep` mentally applies the proposed fix and explains why the next review should not find another failure mode of the same invariant;
- `Closure Evidence` includes `fixed_point_status`;
- `fixed_point_status.fixed_point_reached=true`, with at most 3 iterations and only same-invariant failure modes backed by code evidence;
- loaded artifact includes `review_health` or a localized equivalent that directly states candidate accounting, coverage, fixed-point, and verification health;
- loaded artifact includes `process_metrics`;
- `process_metrics` includes at least `invariants_classified`, `candidate_observations`, `candidate_observations_accounted`, `candidate_observations_unaccounted`, `findings_accepted`, `fixed_point_iterations`, `nearby_cases_checked`, `same_invariant_cases_open`, `blocking_residuals`, `verification_residuals`, `participating_domains_count`, `domains_with_expectation_source`, `domains_unaccounted`, `semantic_entity_paths_checked`, `semantic_entity_paths_unaccounted`;
- loaded artifact includes canonical `candidate_accounting_breakdown` with `accepted_findings`, `rejected[]`, `deferred_to_residual_risk`, `protected_input_non_findings`, and `unaccounted`;
- `process_metrics` uses only non-negative integers, `unknown`, or `not_tracked`;
- strict `STABLE_FIX_PLAN` requires numeric `invariants_classified`, `candidate_observations`, `candidate_observations_accounted`, `candidate_observations_unaccounted`, `findings_accepted`, `fixed_point_iterations`, `nearby_cases_checked`, `same_invariant_cases_open`, `blocking_residuals`, `participating_domains_count`, `domains_with_expectation_source`, `domains_unaccounted`, `semantic_entity_paths_checked`, `semantic_entity_paths_unaccounted`, and `patch_simulation_rows`;
- candidate accounting must balance: `candidate_observations = candidate_observations_accounted + candidate_observations_unaccounted`;
- `candidate_accounting_breakdown` must sum to `candidate_observations`. It may group rejected/deferred reasons into a bounded structured list instead of exposing every reason as a separate critical metric.
- `candidate_observations_accounted = candidate_observations - candidate_observations_unaccounted`;
- `process_metrics.candidate_observations_unaccounted=0`, `process_metrics.same_invariant_cases_open=0`, `process_metrics.blocking_residuals=0`, `process_metrics.domains_unaccounted=0`, and `process_metrics.semantic_entity_paths_unaccounted=0` for strict `STABLE_FIX_PLAN`;
- `review_health` must not claim complete candidate accounting, complete coverage, or reached fixed point when corresponding metrics show unaccounted observations, unaccounted domains/paths, open same-invariant cases, blocking residuals, or fixed-point contradiction;
- expanded lifecycle/state/payment/job/import/webhook/retry/storage/external-side-effect/authorization/restart-affecting invariants include `participating_domain_inventory`;
- `participating_domain_inventory` marks every relevant participating domain and semantic entity path as covered, not_applicable, or out_of_scope; no unaccounted or blocking_residual domain/path remains for strict `STABLE_FIX_PLAN`;
- `participating_domain_inventory` is consumed by `same_invariant_saturation` and `counterfactual_sweep`;
- no domain with `expectation_source=missing` is marked covered;
- `Closure Evidence` includes `patch_simulation_ledger`;
- every accepted finding has a `patch_simulation_ledger` row with `finding_id`, `imagined_patch_contract`, `re_review_checks`, `new_same_invariant_candidates`, `result`, and `stop_reason`;
- `patch_simulation_ledger` has at least 1 and at most 3 rows per accepted finding;
- every `imagined_patch_contract` names changed boundary, state transition, persistence effect, reader/writer behavior after patch, and before/after test oracle or evidence;
- `Closure Evidence` includes `same_invariant_saturation`;
- `same_invariant_saturation` enumerates discovered same-invariant candidate failure modes with concrete search/file evidence for relevant writer, reader, job, API, client, persistence, projection, and manual rerun paths;
- every same-invariant saturation candidate is marked `covered_by_plan` or `not_applicable`; no `blocking_residual` is present;
- `Closure Evidence` includes `adversarial_second_pass`;
- `adversarial_second_pass` mentally applies the proposed fix and actively searches for the next code-backed same-invariant bug the next review would find;
- `adversarial_second_pass` is clean or plan-revised; no code-backed same-invariant `blocking_residual` remains;
- `Closure Evidence` includes `architectural_root_assessment`;
- `architectural_root_assessment` classifies each stable fix as `local_boundary_root`, `symptom_of_larger_architecture`, or `unclear`;
- no fix with `symptom_of_larger_architecture` or `unclear` is shown as stable unless the plan revises the owning boundary and reaches `local_boundary_root`;
- `Closure Evidence` includes `decision_conformance_evidence`;
- `decision_conformance_evidence` explicitly maps every reported issue and stable fix to `accepted_decisions`, `rejected_approaches`, `review_non_findings`, and `scope_boundaries`;
- runtime-critical new or changed contracts include `production_wiring_evidence`;
- commit-derived side effects include `commit_side_effect_order_evidence`;
- restart-affecting runtime facts include `restart_persistence_evidence`;
- fixes that touch semantic entity creation or mutation include `sibling_semantic_paths`;
- `residual_risk_classification` exists and contains no `blocking_residual`;
- every reported issue has `Invariant classification`;
- no reported issue is only an observed bad state;
- no reported issue relitigates an accepted decision, proposes a rejected approach, or reports a declared non-finding;
- related failure modes are grouped by invariant and owning boundary;
- valid earlier narrower fixes are preserved as closed failure modes;
- `Closure Evidence` proves the owning boundary closes all known failure modes;
- accepted decisions and rejected approaches are respected.

If the strict gate fails, evaluate the minimum evidence gate before deciding whether to hide the result.

## Minimum Evidence Gate

Use `GRADED_REVIEW` as a normal downgraded review result, not as a failed review, when all of these are true:

- The loaded artifact has a `Findings` section or equivalent clearly separated findings.
- Each shown finding has concrete code evidence with file links, line references, symbol names, or exact runtime paths.
- Each shown finding is tied to an invariant, owning boundary, or failure mode either in the finding text or closure evidence.
- The artifact includes a stable plan or remediation section for the shown findings.
- If `participating_domain_inventory`, `same_invariant_saturation`, `adversarial_second_pass`, `fixed_point_status`, `review_health`, `process_metrics`, candidate accounting, or `patch_simulation_ledger` is missing/incomplete, the launcher-owned `confidence_boundary` must state that invariant closure is not proven and the plan must not be treated as stable.
- If MetricsReflectionGate returns structured `METRICS_FAIL`, the launcher-owned `confidence_boundary` must include its blocking gaps unless the launcher retry repairs them. If the gate returns bare `METRICS_FAIL`, include `invalid_metrics_gate_output` as the gap after one failed gate retry.
- No shown finding relitigates an accepted decision, proposes a rejected approach, reports a declared non-finding, or crosses scope boundaries.
- No shown finding depends on an explicitly unclear owning boundary.
- No terminal `BLOCKER` says the accepted decision is impossible or the invariant map could not be built.

For `GRADED_REVIEW`, prepend a launcher gate assessment in `output_language`. Keep the first line exactly `GRADED_REVIEW`; localize the heading labels and prose after that line. For Russian, use:

```text
GRADED_REVIEW

# Оценка launcher gate
- acceptance: graded
- strict_gate: failed
- format_gaps:
  - <missing strict evidence fields or MetricsReflectionGate gaps, for example participating_domain_inventory, review_health, candidate_accounting, process_metrics, patch_simulation_ledger, same_invariant_saturation, adversarial_second_pass, decision_conformance_evidence, or fixed_point_status>
- confidence_boundary: Findings показаны, потому что прошли минимальный evidence gate; неполные participating domain coverage, process metrics, patch simulation ledger, MetricsReflectionGate gaps, проверка соседних сценариев, adversarial second pass, fixed-point или другие format gaps означают, что закрытие инварианта не доказано и план нельзя считать stable.
```

Then include the orchestrator artifact sections in original order, without paraphrasing. Do not retry only to perfect presentation if the findings satisfy this gate and no blocking safety gap remains.

If the strict gate fails and the minimum evidence gate also fails, send one retry:

```text
Rejected by launcher gate. Observations are not findings.
Re-run the decision context gate first, then invariant classifier, then observation specialists, then maintainability cause, then closure planner.
Respect the remaining runtime budget. Do not start a second broad exploratory sweep; use the retry only to repair missing closure evidence for already classified invariant candidates, or return BLOCKER.
Reject unclassified observations and decision-conflicting observations, merge by invariant and owning boundary, then return only STABLE_FIX_PLAN, GRADED_REVIEW, or BLOCKER with Closure Evidence.
Include pipeline_order_evidence proving InvariantMap existed before CandidateObservation.
Include decision_conformance_evidence proving every finding respects accepted_decisions, rejected_approaches, review_non_findings, and scope_boundaries. If a candidate contradicts them, reject it; if the accepted decision is impossible, return BLOCKER instead of a finding.
Include counterfactual_sweep and fixed_point_status proving the imagined patched state closes same-invariant failure modes and is not just a local guard. Use at most 3 iterations; if fixed point is not reached, return BLOCKER.
Include process_metrics and patch_simulation_ledger. The ledger must describe imagined patches as behavior contracts with changed boundary, state transition, persistence effect, reader/writer behavior, before/after test oracle or evidence, re-review checks, new same-invariant candidates, result, and stop reason. Do not include private chain-of-thought.
Repair any MetricsReflectionGate blocking gaps. Ensure the metrics evaluator could return METRICS_PASS without inventing precision or weakening the ledger.
Include same_invariant_saturation with concrete search/file evidence across relevant writer, reader, job, API, client, persistence, projection, and manual rerun paths. Every candidate must be covered_by_plan, not_applicable, or blocking_residual; any blocking_residual means the plan is not stable.
Include adversarial_second_pass after the imagined patch, asking what code-backed same-invariant bug the next deep review would find. If it finds any open same-invariant candidate, revise the plan or make closure incompleteness explicit so the launcher can grade evidence-backed findings; otherwise return BLOCKER instead of STABLE_FIX_PLAN.
Include architectural_root_assessment proving whether the plan is a root fix inside the owning boundary or only a symptom of a larger architecture problem. If it is a symptom or unclear, revise the owning boundary or return BLOCKER.
Include production_wiring_evidence for runtime-critical contracts, commit_side_effect_order_evidence for commit-derived side effects, restart_persistence_evidence for restart-affecting facts, sibling_semantic_paths for semantic entity creators/writers, and residual_risk_classification. If any residual can invalidate the stable fix, return BLOCKER.
```

If the second result fails strict gate, run the minimum evidence gate again.

- If it passes, return `GRADED_REVIEW`.
- If it fails, return:

```text
BLOCKER: deep-review did not satisfy minimum invariant and decision-conformance gates before findings. Minimal next action: rerun with narrower scope or fix the orchestrator/reference contracts before using this review result.
```

If no terminal result arrives before the runtime budget expires, stop the orchestrator and return:

```text
BLOCKER: deep-review runtime budget exhausted before terminal ARTIFACT_READY/BLOCKER. Minimal next action: rerun with exhaustive budget or narrow review scope.
```
