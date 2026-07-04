# Scoring Rules

The default evaluator is deterministic and conservative.

## Metrics

- `critical_recall`: every expected finding has its required `must_mention` anchors.
- `boundary_accuracy`: every expected finding has its `owning_boundary_terms`.
- `evidence_quality`: every expected finding has all required `evidence_paths`.
- `severity_floor`: output contains severity at or above `severity_min`.
- `false_positive_pressure`: no `forbidden_claims` patterns appear.

## Pass Rule

A case passes only when all metrics pass for every expected finding and no forbidden claim appears.

This is intentionally strict. A benchmark should catch regressions in recall, ownership, and evidence discipline.

## LLM Judge Policy

Use an LLM judge only for disputed semantic matches, not as the primary evaluator. The judge may answer whether an output semantically matches a finding, but it must not invent new gold findings or change case expectations.

## Output Comparison Policy

Do not compare target-skill output to old text verbatim. Exact-text matching encourages overfitting and punishes better phrasing. Compare invariant class, owning boundary, evidence, and severity.
