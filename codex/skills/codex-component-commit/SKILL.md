---
name: codex-component-commit
description: Commit local Codex skill or subagent changes from ${CODEX_HOME:-$HOME/.codex} by bumping manifests/components.yaml and committing the component files together; use when the user asks to commit a skill, subagent, agent, Codex local workflow, or versioned Codex config change.
---

# Codex Component Commit

Use this skill for commits that include local Codex skills or subagents in `${CODEX_HOME:-$HOME/.codex}`.

This is a low-freedom workflow: the version bump, staged files, and commit must travel together.

## Scope

Managed components:

- Skills: `skills/<skill-name>/...`
- Subagents: `agents/<agent-name>.toml`
- Version registry: `manifests/components.yaml`

Do not use this skill for runtime state such as `sessions`, `worktrees`, `plugins`, `memories`, logs, browser state, or live `config.toml`.

## Workflow

1. Inspect `git -C ${CODEX_HOME:-$HOME/.codex} status --short`.
2. Identify changed skills and subagents from the diff.
3. Decide version bump:
   - `patch` for wording, docs, validation, or compatible script fixes.
   - `minor` for a new compatible workflow capability.
   - `major` for invocation behavior, output contract, or role responsibility changes.
4. Run `scripts/commit_component_change.rb` from this skill, passing explicit components when the diff is mixed.
5. Let the script update `manifests/components.yaml`, stage the component files plus manifest, and create one commit.
6. Report the component names, version bump, commit SHA, and any unrelated files left unstaged.

## Commands

For one skill:

```bash
${CODEX_HOME:-$HOME/.codex}/skills/codex-component-commit/scripts/commit_component_change.rb \
  --skill ship \
  --bump patch \
  --message "[CHORE] Update Codex ship skill"
```

For one subagent:

```bash
${CODEX_HOME:-$HOME/.codex}/skills/codex-component-commit/scripts/commit_component_change.rb \
  --agent code-reality-scout \
  --bump patch \
  --message "[CHORE] Update Codex code reality scout"
```

For a new skill, use `minor` unless the user asks otherwise:

```bash
${CODEX_HOME:-$HOME/.codex}/skills/codex-component-commit/scripts/commit_component_change.rb \
  --skill new-skill-name \
  --bump minor \
  --message "[FEATURE] Add Codex new-skill-name skill"
```

If the changed component can be inferred safely from `git status`, the script may run without explicit `--skill` or `--agent`.

## Guardrails

- If unrelated tracked files are dirty, do not stage them unless the user explicitly includes them.
- If the script reports unrelated leftovers after commit, surface them.
- If `manifests/components.yaml` is missing an entry for a changed component, add it with `0.1.0` before applying the requested bump only when the component is new and the user is committing that component.
- Keep commit messages business-oriented and use `[FEATURE]`, `[CHORE]`, `[REFACTOR]`, `[BUGFIX]`, or `[SECURITY]`.
