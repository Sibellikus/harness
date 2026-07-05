# Research Mode

Use research mode to answer: what is true, what is in scope, and what decisions must be answered before hardening implementation tasks.

Read first:
- [output-contracts.md](output-contracts.md)
- [scout-protocol.md](scout-protocol.md)
- [reviewer-contract.md](reviewer-contract.md) for deep validation

## Required Shape

Write `ResearchPlanDossier` from `output-contracts.md` into the main plan artifact. Do not use the old 20-section dossier. Do not replace row blocks with prose summaries.

Keep `accepted_scope` strict: if a behavior or capability still needs a decision row, put it in `open_decisions` or candidate/future scope, not accepted scope.

The center of research mode is:
- accepted invariants;
- `ResearchGateCoverageTable`;
- `DecisionQuestionMatrix`;
- candidate slice verdicts with no false `READY`.

## Research Gate Classes

For each applicable task, decide which classes apply. If a class might apply from the risk scan but is skipped, give a `non_applicable` or `future_scope` reason in a `ResearchGateCoverageRow`.

- `scope_and_authority`: business owner, authenticated principal, permission surface, durable owner, external/customer identity.
- `initiation_and_trigger`: who/what starts the workflow, whether it creates or updates an existing entity, prerequisites, repeated initiation, expiry/TTL, reuse/retry policy.
- `operation_identity`: local id, external id, correlation id, idempotency key, uniqueness, attempt cardinality, state reuse policy.
- `state_mapping`: external/internal statuses, terminal/non-terminal states, activation/deactivation point, unsupported statuses, out-of-order precedence.
- `failure_ack_and_retry`: validation failures, callback ACK/NAK policy, duplicate handling, provider/network errors, retry visibility.
- `concurrency_and_consistency`: atomic acquire/update, race conditions, transaction boundary, stale state, partial side-effect recovery.
- `read_model_and_frontend_contract`: read endpoints, response shape, stale/unknown signal, polling/foreground sync behavior, consumer fields.
- `background_lifecycle`: scheduled/manual repair, reconciliation/backfill/expiration, orphan handling, batch scope, cadence, stop conditions.
- `reversal_or_repair_effect`: refund/cancel/rollback/delete/manual override behavior, access/data effect, partial reversal policy.
- `legal_contact_or_compliance`: contact/legal/fiscal/consent data, data source, missing-data behavior.
- `test_oracle`: acceptance scenarios, regression cases, concurrency/idempotency tests, external/mock fixtures, verification command.

Do not require provider-specific operation names or statuses. The row must cover generic subfields; provider-specific content appears only when evidence makes it relevant.

## Decision Questions

Every material open decision must become a `DecisionQuestionRow`. A row is valid only if it uses the required field names from `output-contracts.md`, maps to a future `DecisionPacket` field, or explicitly moves scope to future/out-of-scope. Compact inline rows are acceptable when the field names are present.

Avoid loose question lists. If a future hardening worker would still have to invent lifecycle, money/access, provider, ownership, retry, storage, or public-contract semantics, research is incomplete.

## Slice Readiness

Use enum verdicts only. In research mode, prefer:
- `BLOCKED` for materially different business/access/provider/compliance/lifecycle outcomes.
- `UNDER_SPECIFIED` when behavior direction is known but the worker surface, contract, storage, failure behavior, or tests still need hardening.

Do not mark a slice `READY` while material decision rows remain unanswered.
