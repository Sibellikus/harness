# Skill Benchmark Onboarding

Use this when a repository does not yet have a benchmark suite.

## Goal

Create a small project-owned case file that can catch regressions in a target skill without turning the benchmark into a transcript replay.

## First Suite Shape

Start with 2-3 cases:

- one high-confidence case where the target skill previously found a real issue;
- one no-finding or low-risk case, if the target supports no-finding outputs;
- one boundary case that used to produce a false positive, overreach, or wrong owner.

Keep cases pinned to commits. Do not use moving branch names as `commit` or `base`.

## Case File Location

Store the suite in the project that owns the benchmark data, for example:

```text
.codex/benchmarks/deep-review.cases.json
```

The public harness does not provide repository-specific cases.

## Creating A Case

1. Choose the reviewed `commit` and `base`.
2. Confirm both commits exist locally:

```bash
git cat-file -e <commit>^{commit}
git cat-file -e <base>^{commit}
```

3. Fill the case using `references/case-schema.md`.
4. Write semantic `expected_findings`:
   - use stable file names, symbols, endpoint paths, DTO names, or domain terms;
   - avoid full copied prose from old review output;
   - include `forbidden_claims` for common wrong explanations.
5. Keep private transcripts, chain-of-thought, credentials, customer data, and large logs out of the case file.

## First Smoke Run

Generate a worker prompt without running the full suite:

```bash
"${CODEX_HOME:-$HOME/.codex}/skills/skill-benchmark/scripts/run_benchmark_case.sh" \
  --cases .codex/benchmarks/deep-review.cases.json \
  --case-id <case-id> \
  --repo /path/to/repo \
  --run-dir /tmp/skill-benchmark/smoke
```

The output should be JSON containing `prompt`, `raw_output_path`, and `score_path`.

## Benchmark Integrity

- The worker must run the target skill before reading `expected_findings`.
- Score only after raw output is saved.
- A case should fail when the target misses the semantic issue, names the wrong owner, lacks required evidence, or makes a forbidden claim.
- Do not tune cases until they merely reward the old wording.

## When To Add More Cases

Add a case after:

- a production review miss;
- a false positive that wasted implementation time;
- a major prompt/agent change;
- adding support for a new target skill or review mode.
