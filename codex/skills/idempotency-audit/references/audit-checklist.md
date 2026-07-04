# Idempotency Audit Checklist

This reference expands the audit into concrete checks. Use it after the skill triggers.

## Severity Guide

- `Critical`: duplicate money movement, inventory/order creation, irreversible external side effect, or security-sensitive action can occur.
- `High`: duplicate durable state, stuck unknown operation, stale replay that can mislead users or support, or missing external reconciliation.
- `Medium`: weak tests, short retention, unclear retry window, partial observability, or hidden concurrency race with limited blast radius.
- `Low`: documentation, naming, dashboards, or non-critical UX ambiguity.

## Context Completeness Checklist

The audit is incomplete unless these are available or explicitly out of scope:

- User flows: clicks, form submit, disabled states, double-click behavior, navigation restore, offline/background sync, mobile retry.
- API contracts: endpoints, commands, DTOs, headers, status codes, replay semantics.
- Backend use cases: validation, authorization, transaction boundaries, domain state transitions.
- Persistence: tables/collections, unique indexes, idempotency store, operation ledger, TTL/retention, migrations.
- Async flows: outbox, inbox, queues, event consumers, schedulers, jobs, retry/redrive settings.
- External systems: provider idempotency/reference support, timeouts, callbacks, reconciliation APIs.
- Infra: gateway/proxy/load balancer retries, client/server timeouts, deployment restart behavior.
- Operations: support runbooks, manual retry tools, alerts, dashboards, reconciliation jobs.

## Finding Patterns

### Key Per Technical Attempt

Risk: one user intent creates multiple keys across retries.

Evidence examples:
- frontend interceptor calls `randomUUID()` for every HTTP attempt
- retry middleware wraps request creation
- background sync persists body but not key
- server creates a fresh operation id before deduplication

Expected fix direction: identity belongs to the business intent and must survive technical retries.

### TTL Shorter Than Duplicate Window

Risk: delayed retry arrives after key expiry and repeats the effect.

Evidence examples:
- Redis TTL is 24h while client offline queue or webhook redelivery can last days
- dead-letter redrive can happen after idempotency record expiry
- support can manually retry from old request ids

Expected fix direction: retention follows max duplicate arrival window, or idempotency becomes part of durable operation state.

### Request Hash Instead Of Business Intent

Risk: unstable fields prevent deduplication, or stable fields block a legitimate later attempt.

Evidence examples:
- key includes timestamp, nonce, trace id, localized amount string, request id
- key excludes business window/state and caches a soft failure too long
- body hash ignores user/org scope

Expected fix direction: define the business intent and its lifecycle explicitly.

### Check-Then-Insert Race

Risk: concurrent duplicates both pass pre-check and perform the side effect.

Evidence examples:
- `if not exists` then `insert`
- cache read before DB insert without atomic reservation
- no unique index on operation identity

Expected fix direction: atomic reservation with unique constraint/CAS/transaction and explicit `InProgress`.

### Unsafe Release After Unknown Side Effect

Risk: timeout after external side effect lets retry repeat the side effect.

Evidence examples:
- catch block deletes idempotency reservation after provider timeout
- operation is marked failed before provider state is known
- job retries external call without provider reference

Expected fix direction: transition to `Unknown` or `NeedsReconciliation`, then reconcile before retrying.

### External Boundary Not Idempotent

Risk: local dedup works, external provider still processes duplicates.

Evidence examples:
- provider call lacks provider idempotency key or stable reference
- local intent key is not linked to provider reference before commit
- crash between provider acquire and local save is not reconciled

Expected fix direction: provider idempotency key, reference/commit model, local adapter, and reconciliation for orphan references.

### Webhook Duplicate Or Reordering

Risk: duplicate/out-of-order callbacks repeat or regress business state.

Evidence examples:
- no provider event id inbox
- handler repeats side effects when receiving same status
- terminal state can be overwritten by older callback

Expected fix direction: inbox dedup, monotonic state machine, transition-level idempotency.

### Stale Response Replay

Risk: replay returns old success as if it were current state.

Evidence examples:
- cached response contains active booking/payment/subscription state
- entity can be cancelled/refunded/expired during replay window
- frontend cannot distinguish replay from first execution

Expected fix direction: replay returns operation id/status link or explicitly stale original response with client follow-up read.

## Report Skeleton

```markdown
**Scope**
- Operations:
- Layers reviewed:
- Explicitly out of scope:

**System Map**
`user action -> frontend retry -> API -> use case -> persistence -> async/external -> callback -> read/replay`

**Idempotency Contract**
- Business intent:
- Operation identity:
- Atomic reservation:
- Retention:
- External reference:
- Replay behavior:
- Reconciliation:

**Findings**
- [Severity] Title
  Evidence:
  Risk:
  Required fix direction:
  Required test:

**Risk Matrix**
| Risk | Status | Evidence |
| --- | --- | --- |
| Duplicate business effect |  |  |
| Concurrent duplicate |  |  |
| External timeout duplicate |  |  |
| Stale replay |  |  |
| Legitimate retry blocked |  |  |
| Orphan external operation |  |  |
| Missing reconciliation |  |  |

**Required Tests**
- 

**Open Questions**
- 
```

## Audit Heuristics

- Prefer operation ledger over cache-only idempotency for high-value side effects.
- Treat `exactly once` as a product of idempotent effects plus at-least-once delivery, not as a transport guarantee.
- Check both command idempotency and resulting state transition idempotency.
- A green happy-path test does not prove idempotency.
- A local transaction does not cover external side effects.
- A provider idempotency guarantee does not cover our webhook, replay, or support retry flows.
- If the root cause is invalid historical data, preserve strict behavior and propose data repair instead of silent fallback.
