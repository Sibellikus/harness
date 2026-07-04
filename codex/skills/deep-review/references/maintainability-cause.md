# Maintainability Cause Contract

Run this as an independent lens after `InvariantMap` exists and before final planning.

Use accepted decisions, rejected approaches, review non-findings, and scope boundaries as binding constraints. A solution shape is not a maintainability cause merely because it follows an accepted business decision. If the only way to call the shape bad is to reject an accepted decision, return `shape_is_cause=no` with that decision as evidence.

## Question

Is the implementation shape itself the cause of the invariant failure class?

Also classify whether the proposed closure is the root fix inside the current bounded context, or only a symptom patch for a larger architectural problem.

## Signals

- repeated local guards;
- duplicated validation or copied selection logic;
- split source of truth;
- scattered fallback branches;
- broad orchestration beyond accepted scope;
- generic resolver or abstraction without current need;
- wrong ownership boundary;
- several observations in one area that all depend on the same confusing shape;
- a previous review fix produced another same-invariant failure mode.
- a lifecycle/state invariant spans multiple participating domains, but the current solution shape covers only one operation path while leaving sibling create/read/store/poll/cleanup/docs/tests paths to repeat the same decision.

## Output

```text
MaintainabilityCause
- invariant_id:
- shape_is_cause: yes|no|unclear
- root_scope: local_boundary_root|symptom_of_larger_architecture|unclear
- evidence:
- current_failure_modes_caused:
- likely_future_failure_modes:
- smaller_owning_boundary_or_shape:
- minimal_owning_boundary_that_closes_root:
- larger_architecture_candidate:
- participating_domain_shape_assessment:
- semantic_entity_path_gaps:
- why_this_is_not_larger_architecture:
- why_this_is_not_just_local_patch:
- why_this_is_not_style_preference:
- decision_conformance:
- blocker_if_unclear:
```

If `shape_is_cause=yes`, the orchestrator should report the shape as the root finding. Do not bury it behind local observations.

Use `local_boundary_root` only when the owning boundary named by the `InvariantMap` is sufficient to close all known same-invariant failure modes. Use `symptom_of_larger_architecture` when the candidate plan only moves the failure to another boundary, repeated failure modes show the source of truth or ownership boundary is wrong, or the fix depends on scattered local guards. Use `unclear` when evidence is insufficient; the closure planner must then return `BLOCKER`.

A local guard cannot be `local_boundary_root`. A bounded contract or source-of-truth change can be `local_boundary_root` even when it touches several files. Do not require a larger redesign unless code evidence shows the current owning boundary cannot close the invariant.

If `shape_is_cause=yes` would require a rejected approach or contradict a review non-finding, reject that maintainability cause. If the accepted decision is genuinely impossible to satisfy, return a blocker rather than a maintainability finding.
