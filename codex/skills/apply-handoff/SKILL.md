---
name: apply-handoff
description: Apply a READY slice from a plan-pipeline HardenedTaskHandoff to code. Use after plan-pipeline produced a worker-ready handoff and the user asks to implement, apply, continue from the plan, or execute a selected slice. Do not use for raw ambiguous requests; run plan-pipeline first.
---

# Apply Handoff

Use this skill as a bounded applier for `plan-pipeline` output. It does not plan, rediscover business rules, broaden scope, or invent missing decisions.

## Input

Required:

- `plan_artifact` path containing a `HardenedTaskHandoff`;
- selected slice id, or exactly one `READY` slice in the handoff.

If the artifact is missing, stale, not a harden-task handoff, or has no selected `READY` slice, stop with `PLAN_GAP`.

## Apply Rules

1. Read only the selected slice and the handoff sections it references:
   - `DecisionPacket`;
   - `AcceptanceHandoff`;
   - `TaskReadinessReportPerSlice`;
   - `WorkerSurfaceForReadySlices`;
   - `ImplementationOrder`;
   - `TestsRequired`;
   - `StopConditions`.
2. Verify the current repo/project owns the work. If not, use `route-to-correct-project` before editing.
3. Implement only the selected `READY` slice.
4. Follow existing code patterns for mechanical placement, naming, mappings, and test style.
5. Run the checks named in `TestsRequired`, plus the narrowest behavior check that proves the selected acceptance scenario.
6. Do not update accepted decisions. Do not convert blocked or under-specified slices into implementation work.

## Mechanical Choice vs Plan Gap

Mechanical implementation choices are allowed when the handoff already defines the behavior:

- choosing the local file that matches the existing pattern;
- adapting to an equivalent existing type or method name;
- adding the test in the nearest established test folder;
- using project conventions for formatting, DI wiring, endpoint metadata, or mapping extensions.

Stop with `PLAN_GAP` when implementation requires a new decision:

- behavior, fallback, default, status, permission, date semantics, ownership, retry, idempotency, lifecycle, or external side effect is not in `DecisionPacket`;
- required file, symbol, endpoint, DTO, event, job, or test surface does not exist and the handoff did not authorize creating it;
- the selected work would touch files or flows outside `WorkerSurfaceForReadySlices`;
- code reality contradicts the handoff;
- the test oracle is missing or depends on an unresolved decision.

## Output

For success:

```text
ApplyHandoffResult
- status: APPLIED
- slice_id:
- files_changed:
- verification:
- behavior_check:
- evidence:
```

For missing plan detail:

```text
ApplyHandoffResult
- status: PLAN_GAP
- slice_id:
- blocking_question:
- missing_decision_field:
- evidence:
- next_action: return to plan-pipeline or ask the user for the missing decision
```

For environment or routing blockers:

```text
ApplyHandoffResult
- status: BLOCKED
- reason:
- evidence:
- next_action:
```

Do not paste or rewrite the full handoff in chat. Keep the result compact and point to changed files, checks, and the exact blocker when blocked.
