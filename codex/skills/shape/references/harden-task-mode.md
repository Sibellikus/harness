# Harden Task Mode

Use harden-task mode to answer: what can a coding worker implement now without inventing decisions.

Read first:
- [output-contracts.md](output-contracts.md)
- accepted research output or current accepted spec
- [reviewer-contract.md](reviewer-contract.md) for deep validation

## Entry Requirement

`harden-task` needs a `DecisionPacket` for every material decision used by a `READY` slice. Missing packet fields are blockers or under-specification, not creative freedom.

Accepted decisions may come from:
- explicit user answers;
- accepted spec/artifact;
- current code behavior;
- authoritative project or provider documentation when it truly decides the behavior.

## Hardened Task Content

Write `HardenedTaskHandoff` from `output-contracts.md` into the main plan artifact.

Each `TaskReadinessReport` must include:
- the exact decision packet fields used;
- BDD scenarios covered;
- owner/source-of-truth/scope vocabulary;
- write scope, public contract, storage, lifecycle entrypoints, credentials/context;
- failure/data behavior;
- tests and stop conditions;
- worker surface with concrete files/types only when evidenced by code or obvious local convention.

## Verdict Discipline

Use `READY` only when the worker can start coding safely. Use:
- `BLOCKED` for missing business/access/provider/compliance/lifecycle decisions.
- `UNDER_SPECIFIED` for missing contract/storage/failure/test/worker-surface details.
- `TOO_BROAD` when a slice should be recursively hardened.
- `OVERENGINEERED` when the proposed slice adds scope not supported by accepted decisions.

Never write conditional verdicts like `READY after ...`.
