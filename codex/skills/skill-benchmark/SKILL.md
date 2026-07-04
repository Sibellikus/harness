---
name: skill-benchmark
description: Generic harness for Codex skill regression benchmarks with commit-pinned cases, automatically created worker threads, expected semantic findings, and deterministic scoring scripts. Currently implemented target support is deep-review only; use for deep-review quality benchmarks, deep-review old/new comparisons, deep-review gold case creation, parallel deep-review benchmark suites, and scorecards for deep-review skill changes. For other target skills, first add a suite and evaluator adapter.
---

# Skill Benchmark

## Overview

Use this skill to evaluate whether a Codex skill still produces the important behavior it is supposed to produce on known cases. Treat it as an external harness: the benchmark owns cases, worker threads, scoring, and run artifacts; the target skill owns the task behavior.

The harness is intentionally generic, but the only implemented target adapter today is `deep-review`. Do not claim support for other skills until a suite file and evaluator adapter exist for that target.

The operator must not create benchmark threads manually. When thread tools are available, this skill creates and coordinates the worker threads itself.

## Workflow

1. Identify the target skill and benchmark suite.
   - For deep-review, use a project-specific suite file that follows `references/case-schema.md`.
   - This public package does not bundle repository-specific benchmark cases; case commits and expected findings are project-owned data.
   - For first-time setup, read `references/onboarding.md` before creating the suite.
   - If the target is not `deep-review`, stop and add a target-specific suite plus evaluator adapter first.
   - For new deep-review suites, copy the existing case shape and keep case ids stable.
2. Create a run directory under `/tmp/skill-benchmark/<timestamp-or-run-id>`.
3. Create worker threads automatically.
   - Read `references/thread-orchestration.md` before running a suite.
   - Prefer one isolated worktree-backed thread per case.
   - Use a bounded concurrency window when the suite is large; for the current five-case deep-review suite, parallel execution is acceptable unless the user requests a smaller `--jobs`.
4. In each worker thread, run the target skill exactly as an operator would.
   - The worker must checkout the case commit in its own worktree.
   - The worker must run the target skill before reading or applying `expected_findings`.
   - The worker must save the raw target-skill output to the case run directory.
5. Score each output with `scripts/evaluate_deep_review_output.js`.
   - The evaluator checks semantic anchors: invariant class, required terms, evidence paths, severity floor, and forbidden claims.
   - Exact wording is not required.
6. Summarize the suite with `scripts/summarize_runs.js`.
   - Report per-case pass/fail, metric totals, worker thread ids, raw output paths, and score paths.
   - A failing benchmark is useful only if it names which expected observation or evidence anchor was missed.

## Case Contract

Read `references/case-schema.md` before adding or modifying cases. A good case has:

- a stable `id`;
- a `target_skill`;
- a repository `commit` and `base`;
- one or more expected findings with semantic anchors;
- forbidden claims that would indicate overfitting, hallucination, or wrong ownership.

Prefer compact semantic gold data over long golden transcripts. The benchmark should check whether the skill found the same class of bug, not whether it repeated the old prose.

## Scoring

Read `references/scoring.md` before changing evaluator behavior. Default scoring is deterministic:

- `critical_recall`: expected finding anchors are present.
- `boundary_accuracy`: owning boundary terms are present.
- `evidence_quality`: required file/symbol anchors are present.
- `false_positive_pressure`: forbidden claims are absent.
- `severity_floor`: output names at least the minimum expected severity.

Use an LLM judge only as a second pass for disputed semantic matches, never as the only scoring layer.

## Commands

Prepare or inspect a case:

```bash
"${CODEX_HOME:-$HOME/.codex}/skills/skill-benchmark/scripts/run_benchmark_case.sh" \
  --cases /path/to/deep-review.cases.json \
  --case-id example-case \
  --repo /path/to/repo \
  --run-dir /tmp/skill-benchmark/example
```

Score a saved target-skill output:

```bash
node "${CODEX_HOME:-$HOME/.codex}/skills/skill-benchmark/scripts/evaluate_deep_review_output.js" \
  --cases /path/to/deep-review.cases.json \
  --case-id example-case \
  --output /tmp/deep-review-output.md
```

Summarize a run directory:

```bash
node "${CODEX_HOME:-$HOME/.codex}/skills/skill-benchmark/scripts/summarize_runs.js" \
  --run-dir /tmp/skill-benchmark/example
```
