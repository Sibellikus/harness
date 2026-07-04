---
name: post-implementation-test-pipeline
description: Use after production implementation exists and BDD/acceptance behavior is available to extract a neutral test surface, write behavior-focused tests, run targeted verification, and review tests for BDD coverage without coupling to implementation details.
---

# Post-Implementation Test Pipeline

Use this skill only after implementation work exists. It is not a planning or task-hardening workflow, and it is not test-first TDD for broad feature integrations.

The pipeline separates sources of truth:

- BDD/acceptance spec/user requirements define expected behavior. Prefer the `AcceptanceHandoff` produced by `plan-pipeline`.
- Implemented code/diff defines technical test surfaces: calls, setup, fixtures, persistence checkpoints, observable effects, and commands.
- Existing tests show setup patterns, not business truth.

If there is no implemented code/diff for the behavior, stop with `BLOCKED: implementation_missing`. For a new feature, do not run `test_surface_agent` before implementation.

## Relationship To Plan Pipeline

`plan-pipeline` produces BDD/acceptance scenarios from raw requirements plus discovered current behavior/invariants, then turns them into hardened tasks before coding. This skill runs downstream:

```text
plan-pipeline: raw requirements -> discovery -> BDD spec -> hardened tasks
execution: hardened tasks + BDD spec -> implementation
this skill: implementation + BDD spec -> test surface extraction -> test authoring -> test review
```

BDD is not a mutation of a hardened task. BDD is the behavior source; hardened tasks are implementation contracts that reference BDD scenarios.

## Input Contract

The preferred input is an `AcceptanceHandoff` from `plan-pipeline` plus the implementation diff. If the handoff is missing, reconstruct only the smallest behavior source from user requirements, accepted spec, or BDD notes. Do not treat the implementation as expected behavior.

Required behavior input:

- scenario id and name;
- expected observable behavior;
- source authority and evidence;
- invariant or sibling-flow evidence;
- scope/ownership/failure boundary relevant to the scenario;
- open decision status: resolved, blocked, or explicitly non-applicable;
- required proof type: API response, durable state, emitted event, external call, read model, job effect, or user-visible behavior.

Stop with `BLOCKED: bdd_missing` when this cannot be assembled without inventing expected behavior.

## Roles

- `test_surface_agent`: read-only scout that extracts technical building blocks from implemented code/tests. It must not define expected behavior.
- Test Author Agent: the main agent or a `worker` subagent assigned only to test files. It writes tests from BDD plus `TestSurfaceReport`.
- Test Review Agent: use the existing `test_reviewer` role for coverage, false-green fixtures, flaky risks, and implementation-detail assertions.

Use subagents only when the user explicitly authorizes delegation/subagents. Otherwise run the roles sequentially in the main session.

When subagents are authorized, prefer an isolated test-authoring context. Pass only the `AcceptanceHandoff`, implementation diff or relevant files, nearby test patterns, and project test instructions. Do not pass the full implementation discussion, draft plans, or unresolved design chatter unless it is needed as source evidence.

## Workflow

### 1. Input Gate

Confirm:

- BDD/acceptance scenarios or equivalent behavior source exists and is traceable.
- Implementation exists in the current branch/worktree, staged changes, unstaged changes, untracked files, or a supplied diff.
- The implementation scope can be mapped to one or more BDD scenarios.
- Each mapped scenario has a required proof type.

Stop conditions:

- `BLOCKED: bdd_missing` when expected behavior is not supplied or traceable.
- `BLOCKED: implementation_missing` when the behavior has not been implemented yet.
- `BLOCKED: implementation_not_mapped_to_bdd` when the diff cannot be tied to scenarios.
- `BLOCKED: unresolved_behavior_decision` when a scenario still depends on a business/product/technical decision.

### 2. Test Surface Extraction

Run `test_surface_agent` with:

- BDD/acceptance scenario references;
- implementation diff/files;
- existing tests and fixtures for the touched area;
- project test instructions and guardrails.

The output is `TestSurfaceReport`. It is a technical map, not a source of expected behavior.

Required output:

```text
TestSurfaceReport
- behavior_source
- callable_surfaces
- setup_building_blocks
- domain_and_contract_types
- persistence_checkpoints
- emitted_or_external_effects
- existing_test_patterns
- assertions_to_prefer
- assertions_to_avoid
- verification_commands_or_projects
- unknowns_or_missing_test_infrastructure
- evidence
- counter_evidence
```

Also build a coverage matrix before writing tests:

```text
BDDTestCoverageMatrix
- scenario_id
- expected_behavior
- implementation_surface
- proposed_test_files
- proof_type
- current_coverage: covered | partial | missing | not_testable
- gap_type: none | test_gap | implementation_gap | behavior_gap | infrastructure_gap
- notes
```

### 3. Test Authoring

Write tests using:

- expected behavior from BDD/acceptance scenarios;
- setup/calls/checkpoints from `TestSurfaceReport`;
- existing local test style and project guardrails.

Rules:

- Prefer observable behavior over implementation details.
- Assert public response, durable state, emitted events/outbox messages, external calls, or user-visible effects.
- Do not assert private flags, incidental enum/string names, intermediate method calls, repository internals, or current implementation branching unless they are public contract or observable persistence semantics.
- Do not copy implementation branching into tests as the oracle. The oracle is BDD/acceptance behavior.
- Do not make fixtures false-green by pre-seeding the state that the behavior under test must create or mutate.
- Do not change production behavior to make tests easier. If tests expose missing implementation, report the gap instead of hiding it in fixtures.

For broad integration or infrastructure slices, write tests after implementation surface extraction. For pure-domain slices with stable contracts, a lightweight test-first pass is allowed only when the expected behavior and callable surface are already explicit.

### 4. Verification

Run the narrowest meaningful test command first. Use project-specific output limits for noisy commands.

If tests fail:

- distinguish test setup mistakes from implementation gaps;
- fix tests only when the BDD behavior and implementation are consistent;
- report implementation gaps when production code fails the BDD behavior.
- use `implementation_gap` instead of silently changing expected behavior, weakening assertions, or adding production fallbacks.

### 5. Test Review

Run `test_reviewer` as the Test Review Agent over the test diff and relevant implementation diff.

Review focus:

- each BDD scenario has a test or explicit non-test rationale;
- tests do not merely repeat implementation details;
- fixtures cannot be false-green;
- risky interactions, boundary values, failure states, and lifecycle effects are covered;
- tests do not force production-only changes for test convenience.

## Output Contract

Return:

```text
PostImplementationTestPipelineReport
- input_gate: READY | BLOCKED
- behavior_sources
- implementation_scope
- test_surface_summary
- tests_added_or_changed
- verification_commands
- test_review_verdict: PASS | FINDINGS | NOT_RUN
- bdd_coverage
- coverage_matrix
- implementation_gaps
- implementation_detail_assertions_avoided
- open_gaps_or_blockers
```
