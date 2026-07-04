# Metrics Reflection Gate Contract

Run this after the orchestrator returns a terminal artifact manifest, the launcher loads the referenced artifact, and before the launcher accepts `STABLE_FIX_PLAN` or grades `GRADED_REVIEW`.

This evaluator is a process-quality checker, not a reviewer. It must not add findings, remove findings, rewrite the fix plan, or relitigate decision context. It validates whether the reported process metrics, patch simulation ledger, fixed-point claims, and optional trace file are internally consistent and honest enough to support the loaded artifact.

## Input

The evaluator receives:

- terminal `ARTIFACT_READY ... artifact_path=...` manifest from the orchestrator;
- loaded `StructuredReviewArtifact` JSON object from `artifact_path`;
- resolved `output_language`;
- launcher gate requirements;
- ClosurePlannerContract process metrics and patch simulation rules;
- deterministic renderer validation result from `scripts/render_review_manifest.py` when available;
- optional trace file path if the artifact reports one.

## Output

Return only one of these. A bare `METRICS_FAIL` without the required fields is invalid evaluator output.

```text
METRICS_PASS
- checked:
  - process_metrics_present:
  - critical_metrics_numeric:
  - candidate_accounting_complete:
  - candidate_accounting_breakdown_present:
  - no_fabricated_precision_detected:
  - review_health_present:
  - review_health_consistent:
  - renderer_validation_passed:
  - ledger_present:
  - ledger_row_bounds:
  - ledger_contract_fields_present:
  - participating_domain_inventory_present:
  - domain_coverage_metrics_present:
  - domain_coverage_consistency:
  - fixed_point_consistency:
  - trace_file_consistency:
- notes:
```

```text
METRICS_FAIL
- blocking_gaps:
  - <gap>
- downgrade_allowed: true|false
- retry_allowed: true|false
- minimal_retry_instruction:
```

## Rules

- Do not inspect the codebase for new bugs.
- Do not create candidate findings.
- Do not change finding priorities.
- Do not judge whether the proposed fix is correct beyond process evidence consistency.
- Treat missing or inconsistent process evidence, invalid manifest, invalid JSON, schema mismatch, or renderer validation failure as a gate issue, not as a code finding.
- Never return a bare `METRICS_FAIL`. If the evaluator cannot determine the exact process gap, return `METRICS_FAIL` with `blocking_gaps=[unclassified_metrics_gap]`, `downgrade_allowed=false`, `retry_allowed=true`, and a minimal retry instruction asking for the missing process evidence.
- Use stable gap identifiers so the launcher can act without guessing. Prefer: `invalid_artifact_manifest`, `invalid_json_artifact`, `renderer_validation_failed`, `process_metrics_missing`, `critical_metric_non_numeric`, `candidate_accounting_metrics_missing`, `candidate_accounting_breakdown_missing`, `candidate_accounting_mismatch`, `candidate_observations_unaccounted_nonzero`, `review_health_missing`, `review_health_contradicted`, `same_invariant_cases_open_nonzero`, `blocking_residuals_nonzero`, `participating_domain_inventory_missing`, `domain_coverage_metrics_missing`, `domains_unaccounted_nonzero`, `semantic_entity_paths_unaccounted_nonzero`, `expectation_source_missing_marked_covered`, `expanded_inventory_not_consumed_by_saturation`, `patch_simulation_rows_mismatch`, `ledger_missing`, `ledger_row_missing_for_finding`, `ledger_row_bounds_invalid`, `ledger_contract_field_missing`, `fixed_point_iterations_mismatch`, `fixed_point_claim_contradicted`, `trace_schema_invalid`, `invalid_metrics_gate_output`, `unclassified_metrics_gap`.
- If a trace file is reported as `not_written`, that is acceptable when `process_metrics` and `patch_simulation_ledger` satisfy the contract.
- If a trace file path is reported, validate only that the artifact claims allowed event names and schema consistency. Do not require reading the file unless the launcher explicitly has it available and doing so is cheap.
- Reject fabricated precision: a metric that cannot be reconciled with the artifact should be `unknown` or `not_tracked`, not a precise-looking integer.
- Fail when the terminal manifest is invalid, the artifact is not valid JSON, or `scripts/render_review_manifest.py` rejects it.
- For strict `STABLE_FIX_PLAN`, fail when any critical metric is non-numeric, `candidate_observations_unaccounted != 0`, `same_invariant_cases_open != 0`, `blocking_residuals != 0`, `domains_unaccounted != 0`, `semantic_entity_paths_unaccounted != 0`, or `patch_simulation_rows` does not match ledger rows.
- Fail when candidate accounting metrics are missing: `candidate_observations_accounted` or `candidate_observations_unaccounted`.
- Fail when strict `STABLE_FIX_PLAN` lacks `candidate_accounting_breakdown` or equivalent structured list.
- Fail when `candidate_observations` does not equal `candidate_observations_accounted + candidate_observations_unaccounted`.
- Fail when `candidate_observations_accounted` does not equal `candidate_observations - candidate_observations_unaccounted`.
- Fail when `candidate_accounting_breakdown` does not sum to `candidate_observations`, its accepted finding count does not match `findings_accepted`, or its unaccounted count does not match `candidate_observations_unaccounted`.
- Fail when strict `STABLE_FIX_PLAN` lacks a `review_health` or equivalent operator-facing health section.
- Fail when `review_health` says candidate accounting, coverage, or fixed point is complete/reached while the matching metrics say there are unaccounted candidates, unaccounted domains/paths, open same-invariant cases, blocking residuals, or fixed-point contradiction.
- For strict `STABLE_FIX_PLAN`, fail when an expanded lifecycle/state/payment/job/import/webhook/retry/storage/external-side-effect/authorization/restart-affecting invariant has no `participating_domain_inventory`.
- Fail when `participating_domain_inventory` reports an expanded inventory but `ProcessMetrics` lacks `participating_domains_count`, `domains_with_expectation_source`, `domains_unaccounted`, `semantic_entity_paths_checked`, or `semantic_entity_paths_unaccounted`.
- Fail when a domain has `expectation_source=missing` but is marked `covered`.
- Fail when expanded inventory has unaccounted domains/paths that are not reflected in `domains_unaccounted` or `semantic_entity_paths_unaccounted`.
- Fail when `same_invariant_saturation` does not reference or otherwise consume an expanded `participating_domain_inventory`.
- Fail when any accepted finding has no ledger row.
- Fail when any accepted finding has more than 3 ledger rows.
- Fail when any ledger row lacks changed boundary, state transition, persistence effect, reader/writer behavior after patch, or before/after oracle/evidence.
- Fail when `fixed_point_iterations` disagrees with `fixed_point_status.iterations_run`.
- Fail when `fixed_point_reached=true` but process metrics or ledger imply open same-invariant candidates.

## Downgrade Guidance

Set `downgrade_allowed=true` only when:

- findings are still evidence-backed and decision-conformant in the artifact;
- the failure is limited to process observability, trace, or closure-format evidence;
- no metric/ledger inconsistency proves the fix plan itself is impossible.

Set `retry_allowed=true` when the artifact likely needs only formatting or process-evidence repair. Set `retry_allowed=false` when the artifact contains contradictory metrics that make the process state unreliable.
