---
name: merger
description: Plan and execute high-risk PR/branch merges with business-logic preservation. Use when Codex needs to compare merge orders, choose a low-conflict order, analyze feature diffs against a target branch, resolve merge conflicts, or launch a merger/reviewer subagent for integration work.
---

# Merger

## Core Contract

Merge work is about preserving business semantics, not merely removing conflict markers. Use this skill for integration-branch assembly, risky PR ordering, or conflict resolution where multiple accepted features touch shared runtime paths.

The skill owns the merge methodology. A merger subagent, when explicitly requested by the user, owns only a concrete merge scope. The parent agent remains responsible for orchestration and final acceptance.

## Preflight

Before merging or resolving conflicts:

- Identify the target branch, source branches/PRs, requested base, and whether the target is protected.
- Fetch the relevant remotes before reasoning about ancestry or containment.
- Verify the worktree state. If it is dirty, separate user changes from merge output before continuing.
- Prefer a dedicated integration branch or worktree for risky merges; do not merge directly into a protected release branch unless the user explicitly requested that exact operation.
- Record the starting commit so the merge can be abandoned or compared without guessing.
- Check whether any source branch already contains another source branch to avoid duplicate/confusing merge order.

## Merge Order

Before merging, build a compact PR inventory:

```text
PR:
Base:
Head:
Touched files:
Business area:
Depends on:
Contains/contained by:
Risk:
```

Choose order using these rules:

- Verify the real base and ancestry first. Do not reason from stale local branches.
- Check commit containment with `git merge-base --is-ancestor`.
- Check patch overlap with `git diff --name-only` and direct file intersections.
- Merge independent low-risk PRs before shared semantic changes.
- Merge foundational config/DTO/persistence changes before their consumers.
- Merge domain-specific behavior before shared calculators when the calculator must preserve that behavior.
- Put disputed semantic changes last, so conflicts are resolved with full knowledge of accepted behavior.
- Explain the chosen order through concrete dependencies and file overlap.

## Business Inventory

For every risky PR or conflict area, write the business inventory before editing:

```text
PR / branch:
Business intent:
Runtime paths:
Changed invariants:
Fallback / validation changes:
Job or batch impact:
Tests that describe intent:
Compatibility risks against target:
```

Treat tests as evidence of intent, not just compile fixtures. If tests conflict with the agreed business behavior, call that out and adjust tests only after the behavior decision is explicit.

## Conflict Rules

- Compose accepted features deliberately. Do not pick `ours` or `theirs` just because it compiles.
- Preserve existing accepted behavior unless the merge target explicitly supersedes it.
- Localize disputed behavior. Do not turn a branch-specific validation rule into a global behavior change.
- Preserve trusted legacy fallbacks unless the task explicitly removes them.
- Do not hide bad or incomplete data with silent fallback, inferred substitution, or runtime auto-repair.
- Treat nullability, fallback, validation, and error-code changes as semantic changes.
- If a domain validation failure appears to come from impossible persisted data, inspect every write path and validator for that field before changing runtime validation. If all current system entrypoints reject the bad value, treat the root cause as stale/corrupt legacy data and ask for a migration/backfill/data-repair plan instead of weakening validation, adding fallback, or calculating with defaults.
- Conflict in a shared service means checking all meaningful callsites.
- Conflict in a calculator/loader means checking endpoint, report, batch, and job paths that reuse it.
- Conflict in tests means preserving the business assertion, not just updating fixtures until green.

Project-specific guardrails:

- Read the target repository's local instructions before resolving conflicts.
- Preserve provider/channel-specific semantics when merging into shared calculators or shared orchestration code.
- Do not globally remove legacy fallbacks unless the target task explicitly changes that invariant.
- Preserve job scheduling, persisted-slice recovery, upsert keys, event publishing, and retry semantics unless the merge task explicitly supersedes them.

## Verification

Testing is conditional, not default. The merger must not run broad suites by default. Broad build/test validation belongs to the repository's normal release gate unless the user explicitly asks to run it earlier.

During merge work, run only minimal focused checks when they directly validate a conflict decision:

- conflict marker search after manual resolution;
- `git diff --check` or equivalent whitespace/conflict sanity check when available;
- focused compile/test check when the conflict touched a fragile shared type or method signature;
- focused unit/job test when the conflict touched a calculator, loader, job path, or typed error contract;
- isolated failing group only after a failure is observed and needs classification.

Do not claim final green from local focused checks. Report:

```text
Merge-resolution confidence:
Focused checks run:
Release gate still required:
Known risks:
```

## Subagent Protocol

Use subagents only when the user explicitly authorizes them. Prefer one merger worker plus an optional read-only reviewer.

Spawn a merger worker when the task has a bounded write scope. Tell the worker it is not alone in the codebase and must not revert others' changes.

Merger prompt template:

```text
Use $merger.

Repo:
Target branch/worktree:
Source PRs/branches:
Requested base:
Write ownership:

Task:
- Analyze merge order and business semantics before editing.
- Resolve conflicts by preserving accepted behavior from all sources.
- Do not globalize disputed validation/fallback behavior.
- Check affected endpoint/use-case/calculator/report/job paths by reading code.
- Before changing validation/fallback behavior, prove whether bad persisted data can enter through current write paths. If current paths are strict, request migration/backfill/data repair instead.
- Run only focused checks if they directly validate a conflict decision.
- Do not commit unless explicitly asked.

Output:
- Order chosen and why.
- Business semantics preserved.
- Conflicts resolved and files changed.
- Focused checks run, if any.
- Release gate still required.
- Remaining risks.
```

Use a reviewer subagent only after a resolved diff exists or when the user asks for an independent challenge. Reviewer must be read-only and focus on business regressions, missing coverage for conflict decisions, accidental global behavior changes, job/batch breakage, and silent fallback.

Reviewer prompt template:

```text
Review the resolved merge diff read-only.
Focus on business regressions, conflict-resolution mistakes, accidental fallback/validation changes, job or batch path breakage, and missing focused coverage for merge decisions.
Do not comment on style unless it hides a correctness risk.
Return findings first with file/line references, then residual risk.
```

## Acceptance Report

End merge work with this compact report:

```text
Merge target:
Merged sources:
Order:
Business semantics preserved:
Conflict decisions:
Files changed:
Focused checks:
Release gate status:
Open risks:
Ready / not ready:
```
