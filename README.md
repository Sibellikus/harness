# My Harness

Curated Codex skills and agents intended for public sharing.

This repository is a distributable Codex harness, not a live Codex home. Keep
private runtime state, local configuration, repository-specific delivery
workflows, session logs, and customer/project-specific examples outside this
package.

## Layout

```text
codex/
  skills/
  agents/
  manifests/
```

`codex/` is the package namespace for Codex-specific assets. It intentionally is
not named `.codex`, because this repository should not look like a live
`$CODEX_HOME` with runtime state.

## Install

Copy or symlink the contents into your Codex home:

```bash
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
cp -R codex/skills/* "$CODEX_HOME/skills/"
cp -R codex/agents/* "$CODEX_HOME/agents/"
cp -R codex/manifests/* "$CODEX_HOME/manifests/"
```

## Core Delivery Flow

The main skills are designed as a Codex delivery harness: turn a raw request
into a bounded implementation task, apply it, verify it, review it, and only
then push.

1. `plan-pipeline` hardens raw requirements into an implementation-ready plan
   with file-level tasks and BDD-style acceptance criteria.
2. `apply-handoff` applies one READY slice from that plan without inventing
   missing decisions. If the plan is incomplete, it stops with a plan gap.
3. `post-implementation-test-pipeline` plans the verification pass after code
   changes, including the test surface and acceptance evidence to collect.
4. `deep-review`, `review-changes`, `frontend-ux-review`, and
   `idempotency-audit` cover review gates for code correctness, current diffs,
   rendered UI, and retry/idempotency risks.
5. `push-gate` runs the final repository-owned delivery gate before pushing or
   opening a PR.

Supporting flow skills:

- `fresh-dev-branch` starts work from a fresh remote base instead of stale local
  state.
- `route-to-correct-project` keeps multi-repo work in the correct Codex project
  or thread.
- `issue-research` investigates production/API/DB discrepancies before a fix is
  planned.
- `thread-reflection` captures reusable delivery lessons after the work is
  done.
- `skill-benchmark` gives project owners a way to regression-test skill quality
  with their own benchmark cases.

## Included

- `codex/skills/deep-review` - structured code-review workflow.
- `codex/skills/plan-pipeline` - planning and task-hardening workflow.
- `codex/skills/apply-handoff` - bounded applier for READY plan-pipeline handoffs.
- `codex/skills/frontend-ux-review` - rendered frontend UX review workflow.
- `codex/skills/idempotency-audit` - retry/idempotency audit workflow.
- `codex/skills/review-changes` - current-diff review workflow.
- `codex/skills/issue-research` - evidence-first discrepancy investigation workflow.
- `codex/skills/merger` - high-risk merge planning and conflict-resolution workflow.
- `codex/skills/fresh-dev-branch` - fresh remote-base branch creation guardrail.
- `codex/skills/push-gate` - repository-owned check/push/PR guardrail.
- `codex/skills/route-to-correct-project` - multi-project/thread routing guardrail.
- `codex/skills/thread-reflection` - post-delivery reflection workflow.
- `codex/skills/utp-requirements` - evidence-based positioning requirements workflow.
- `codex/skills/postgres-db-search` - read-only PostgreSQL search helpers.
- `codex/skills/codex-component-commit` - component manifest/version commit helper.
- `codex/skills/skill-benchmark` - skill regression benchmark harness.
- `codex/skills/post-implementation-test-pipeline` - post-implementation test planning workflow.
- `codex/agents/` - reusable reviewer/scout agent definitions used by those skills.
- `codex/manifests/components.yaml` - component versions for the included subset.

## Excluded

- Local `config*.toml`, sessions, memories, worktrees, cache, plugins, and logs.
- Project-specific bundle, hotfix, deployment, and local backend/frontend runners.
- Repository-specific rules and benchmark cases with private commit/session data.

## Maintenance

Repository-level publication and cleanup rules live in `AGENTS.md`.
