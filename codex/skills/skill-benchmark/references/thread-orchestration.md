# Thread Orchestration

The benchmark runner must create and coordinate worker threads. Do not ask the user to create case threads manually.

## Preferred Flow

1. Create a run directory: `/tmp/skill-benchmark/<run-id>`.
2. For every selected case, build a worker prompt with `scripts/run_benchmark_case.sh`.
3. Create one isolated worker thread per case.
   - Prefer `fork_thread` with a new worktree from the current project when available.
   - Use `create_thread` with a project worktree only when the project id is known.
   - Do not run multiple cases in the same worktree.
4. Send each worker its case prompt.
5. Poll or read the worker threads until each case has produced:
   - `raw-output.md`
   - `score.json`
   - a short final status containing the same score JSON or the score path
6. Run `scripts/summarize_runs.js --run-dir <run-dir>` in the parent thread.
7. Report the scorecard and the worker thread ids.

## Worker Prompt Requirements

The worker must:

- checkout the case commit in its own worktree;
- run the target skill against the case base;
- save the target-skill output before running the evaluator;
- run the evaluator only after the raw output is saved;
- not read `expected_findings` before producing the raw review output;
- write `score.json` even when the case fails;
- return a compact final message with pass/fail and paths.

## Isolation Rules

- Never switch the parent thread worktree while running a suite.
- Never reuse one worker worktree for multiple cases in a parallel suite.
- Never rewrite branches for benchmark execution. Detached checkout inside the worker worktree is preferred.
- If a worker starts with a dirty worktree, it must stop and report the dirty state.

## Fallbacks

If thread tools are unavailable, use subagents only when the current user request explicitly permits automatic parallel workers. If neither thread tools nor permitted subagents are available, stop with a blocker. Do not turn the benchmark into a manual operator checklist.
