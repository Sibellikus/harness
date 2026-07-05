# Agent Instructions

This repository is a public distributable Codex harness. Treat every change as
potentially publishable.

## Repository Boundary

- Keep this repository as a clean package under `codex/`; do not turn it into a
  live `$CODEX_HOME`.
- Do not add local Codex runtime state: `config*.toml`, sessions, memories,
  worktrees, cache, plugin cache, logs, temporary outputs, or generated traces.
- Do not add repository-specific delivery workflows unless they are generalized
  for public reuse.
- Do not add benchmark cases, examples, prompts, or docs that contain private
  commit hashes, session ids, customer data, production incidents, internal
  project names, local paths, or organization-specific process details.

## Public Copy Rules

When adapting a private/local skill for this repository:

1. Preserve the reusable behavior and contracts.
2. Remove private project assumptions, private command names, private branch
   names, private infrastructure details, and customer-specific examples.
3. Replace real ids, account names, emails, URLs, database names, server names,
   incident details, and numeric business facts with neutral examples.
4. Keep examples generic enough that they teach the skill without revealing
   where it came from.
5. Do not include credentials, credential file names, token names, secret
   formats, internal hostnames, private IPs, or live API details.
6. If a skill depends on agents, scripts, schemas, or reference files, include
   the complete public dependency set or remove the skill from the public
   manifest.

## Pre-Publication Guard

Before every publication, push, release, or history rewrite, agents must verify
that the repository and git history are clean.

Required checks:

1. Run a secret scan over the working tree and git history after repository
   initialization or rewrite.
2. Search for private project names, customer names, organization names, local
   absolute paths, session/worktree paths, and production data.
3. Search for generated/runtime files such as `__pycache__`, `.pyc`, `.DS_Store`,
   `.log`, `.tmp`, `.sqlite`, `.db`, and `.jsonl`.
4. Validate that `codex/manifests/components.yaml` points only to files present
   under `codex/`.
5. Validate every included skill frontmatter and referenced public dependency.
6. Confirm the README, license, install instructions, and included component
   list still match the actual repository layout.
7. Confirm git author identity is the user's configured identity, not a generic
   assistant identity.

Do not publish if any scan reports private data, sensitive data, broken
manifest paths, missing dependencies, stale README content, or unreviewed
generated files. Fix the package first, then rerun the checks.

## Git Discipline

- Do not commit or push unless the user explicitly asks for it.
- When committing, use the repository/user configured git identity.
- Keep changes scoped and review `git diff` before committing.
- Do not rewrite public history unless the user explicitly asks for a clean
  history or force-publish operation.
