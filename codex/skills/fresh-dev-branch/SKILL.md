---
name: fresh-dev-branch
description: create a new working branch from a fresh remote base when the user asks to create a branch, says "создай ветку", "создавай ветку", "new branch", or similar; fetch the requested base first, prefer the repository's configured remote base, never use stale local branches or current HEAD as a replacement base, and if an existing branch has wrong ancestry create a new clean branch instead
---

# Fresh Dev Branch

Use this skill when the user asks to create or switch to a fresh working branch.

Typical triggers:
- `создай ветку`
- `создавай ветку`
- `new branch`
- `branch off dev`
- `fresh branch from main`
- `fresh branch from release`

Default base:
- If the repo documents a feature-branch base, use that remote base.
- If the user explicitly names a base, apply the same freshness rules to that base, for example `origin/main`, `origin/dev`, or `origin/release-x`.
- If neither source identifies a base, inspect the remote default branch and repo conventions before choosing.

## Workflow

1. Resolve the requested base branch.
2. Fetch the remote base first:
   - `git fetch origin <base>`
3. Compare local and remote base tips:
   - inspect `git rev-parse <base>` and `git rev-parse origin/<base>`
4. Never branch from stale local `<base>` when it differs from `origin/<base>`.
5. Never use current `HEAD` as a substitute for the requested base just because `HEAD` happens to contain it.
6. Create the new branch from the fresh remote base:
   - `git switch --no-track -c <new-branch> origin/<base>`
   - verify the new branch does not track `origin/<base>` as its upstream
7. If the target branch name already exists:
   - verify it still descends from the requested base with `git merge-base`
   - if ancestry is correct, switch to it only if that matches the user request
   - if ancestry is wrong, stop using that branch name and create a new clean branch instead
8. After branch creation, report:
   - the new branch name
   - the exact remote base used, for example `origin/main`
   - the base commit sha used for creation

## Safety Rules

- Prefer the remote base over the local branch unless the user explicitly asked for local-only behavior.
- Do not silently skip `git fetch`.
- Do not rewrite or force-move an existing branch to fake correct ancestry.
- If the worktree is dirty and `git switch` cannot safely move to the fresh base, stop and explain the blocker.
- If `origin/<base>` does not exist, stop and report that exact fact instead of guessing another base.

## Examples

User:
`создавай ветку rewrite/products-pagination`

Expected behavior:
- resolve the repository's remote base
- fetch that base
- confirm whether the local base branch is stale
- create `rewrite/products-pagination` from the fetched remote base
- report the exact base sha

User:
`switch this thread to branch rewrite/foo`

Expected behavior:
- verify `rewrite/foo` still descends from the requested base
- if not, create a new clean branch from the fresh remote base instead of reusing `rewrite/foo`
