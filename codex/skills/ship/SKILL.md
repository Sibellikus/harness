---
name: ship
description: Enforce a safe repository push workflow when the user asks to push, ship, publish, send changes upstream, create a PR/MR, or says an equivalent short push command. Use repository-owned checks and refuse raw pushes from dirty, unverified, protected, or ambiguous branch states.
---

# Ship

Treat every push-like request as a gated delivery operation. Do not run `git push`
directly just because the user said "push". First prove the repository state,
the intended target, and the release gate.

## Scope

Use this skill for ordinary current-branch delivery:

- push current branch;
- publish changes upstream;
- create or update a pull request / merge request;
- run the repository's pre-push or release gate before shipping.

Do not use this skill for multi-branch release promotion, hotfix bypasses, or
deployment automation unless the repository explicitly documents those flows.
If the current branch name or user request implies a special release branch,
bundle branch, hotfix branch, or deployment branch, stop and use the repo's
specific instructions instead of guessing.

## Preflight

1. Resolve the repository root and current branch.
2. Refuse to push from `main`, `master`, `dev`, `develop`, release branches, or
   any protected branch unless the user explicitly requested that exact branch
   operation and the repository instructions allow it.
3. Check worktree state:
   ```bash
   git status --short --branch
   ```
   - If there are uncommitted tracked or untracked files, stop before checks or
     push. Ask whether to include, ignore, or clean them.
   - Do not hide unrelated local changes inside a push.
4. Fetch the relevant remote refs before comparing branch state.
5. Identify the intended review target:
   - explicit user target wins;
   - otherwise use an existing PR/MR base if one exists for the branch;
   - otherwise use the repository's documented default branch or contribution
     branch;
   - if still ambiguous, ask one concise question before pushing.
6. Verify branch ancestry when the repository requires a fresh base. Do not use
   current `HEAD` as a replacement for an explicitly requested base.

## Gate Discovery

Prefer repository-owned gates over invented command lists.

Check in this order:

1. repo-local scripts such as `scripts/push_gate.sh`, `scripts/check`, `bin/check`,
   `make check`, `just check`, or `task check`;
2. package scripts such as `npm run check`, `pnpm check`, `yarn check`, `bun run check`;
3. documented commands in `README`, `CONTRIBUTING`, `AGENTS.md`, Makefile,
   Justfile, Taskfile, CI workflow names, or project scripts;
4. focused build/test/lint commands inferred from changed files only when the
   repository has no documented gate.

Do not weaken the gate to save time without saying so. If the repository has a
full pre-push gate, run that gate before push unless the user explicitly asks
for a narrower check and accepts the residual risk.

## Execution

1. If a repo-local push gate exists and supports a plan/dry-run mode, run that
   plan first and summarize target checks compactly.
2. Run the gate once for the clean `HEAD`.
3. Keep noisy command output out of chat:
   - capture long build/test logs to temporary files;
   - report compact failures, failed project/test names, and log paths;
   - do not paste full install, build, or test output.
4. If checks fail:
   - do not push;
   - report the failing gate step and the next fix action;
   - stop unless the user explicitly asks to continue diagnosing.
5. If checks pass, push the current branch:
   ```bash
   git push --set-upstream origin <current-branch>
   ```
   Use plain `git push` only when upstream is already correct.
6. Create or reuse the pull request / merge request when the repository workflow
   expects review before merge.
   - Prefer the platform CLI (`gh`, `glab`) when available.
   - If an open PR/MR already exists for the branch, report it instead of
     creating a duplicate.
   - Do not create a PR/MR against a guessed base.

## Reusing Prior Checks

You may reuse a prior gate result only when all are true:

- it was run for the same `HEAD`;
- the worktree is still clean;
- dependency lockfiles, generated files, and test inputs have not changed;
- the repository's own gate supports or accepts reuse.

If any condition is uncertain, rerun the gate.

## Failure Handling

If the gate script or PR tooling fails before producing a clear result:

- inspect the failure;
- do not fall back to a raw push or guessed PR base;
- report whether the blocker is local dirty state, missing dependency,
  failed check, authentication, remote rejection, branch protection, or unknown
  tool failure.

## Final Report

Return a compact delivery report:

```text
Branch:
Target:
Gate:
Gate result:
Push result:
Review request:
Commit:
Residual risk:
```

If nothing was pushed, say that explicitly and name the blocker.
