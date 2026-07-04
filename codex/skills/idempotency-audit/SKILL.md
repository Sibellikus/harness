---
name: idempotency-audit
description: Проводит системный аудит идемпотентности frontend/backend/infra потоков. Используй, когда пользователь просит проверить идемпотентность, exactly-once/duplicate side effects, retries, webhooks, фоновые jobs, платежи, заказы, импорты, уведомления или другие операции с повторными входами и внешними эффектами. Если контекста по всей цепочке недостаточно, сначала верни уточнения.
---

# Idempotency Audit

Проводить это нужно как системный review, а не как имплементацию.

Цель: доказать, где система гарантирует один бизнес-эффект на одно намерение, и показать разрывы, где повторный вход может создать дубли, потерю состояния, устаревший replay или неразрешимое `unknown` состояние.

## Core Premise

Идемпотентность - свойство бизнес-операции, а не HTTP-запроса, заголовка или retry middleware.

Проверяй всю цепочку:
- frontend/user intent
- API/backend use case
- persistence and uniqueness constraints
- async infra: queues, outbox/inbox, schedulers, background jobs, retries, redrive
- external systems and providers
- webhooks/callbacks
- response replay and current-state reads
- reconciliation and observability

Не принимай `Idempotency-Key` как доказательство. Это только один возможный носитель идентичности операции.

## Scope Gate

Перед аудитом явно зафиксируй проверяемые операции и доступный контекст.

Если пользователь просит аудит системы целиком, но отсутствует хотя бы один критичный слой, остановись и верни уточнения вместо уверенного отчета:
- frontend flows and retry/offline behavior
- backend entrypoints and command/use-case code
- storage schema, indexes, uniqueness and transaction boundaries
- queues/jobs/webhook consumers and retry policies
- external provider contracts and callback semantics
- infra timeout/retry/redrive settings
- known operational runbooks or reconciliation jobs

Можно делать partial audit только если пользователь явно согласился на частичный срез. В таком случае пометь все выводы как ограниченные этим scope.

## Workflow

### 1. Freeze The Operation

Для каждой операции определи:
- субъект: user/org/account/client
- бизнес-объект: order, booking, payment, import, notification, report, subscription, etc.
- желаемый side effect
- какие повторные входы считаются тем же намерением
- какие повторные входы являются новой легитимной операцией
- окно намерения, если оно существует, и почему именно такое

Не используй фиксированные окна вроде `5 minutes` как правило. Окно должно следовать из бизнес-семантики и retry/offline windows.

### 2. Draw The End-to-End Path

Построй путь:

`user action -> frontend state/retry -> API -> validation/auth -> use case -> DB transaction -> async publish/job -> external call -> callback/webhook -> final state -> replay/read model`

Для каждого шага отметь:
- что является source of truth
- где создается operation identity
- где может произойти retry
- где возможен concurrent duplicate
- где появляется внешний side effect
- где результат кэшируется или replayed

### 3. Check Intent Identity

Проверь:
- ключ живет столько же, сколько намерение пользователя, а не один технический HTTP attempt
- retry, RxJS retry, service worker/background sync, browser restore, mobile offline queue and manual double-click reuse the same identity when they mean the same operation
- server can derive or validate business intent; client UUID alone is not sufficient proof
- request-body hashes do not accidentally include unstable fields such as timestamp, nonce, trace id, UI-generated random ids, sorting, localized formatting
- the design can distinguish a quick duplicate from a legitimate later retry after a real failure

### 4. Check Atomicity And Concurrency

Проверь, что duplicate detection is atomic:
- `INSERT ... ON CONFLICT`, unique index, compare-and-set, `SETNX`, advisory lock, or transaction-backed reservation
- no check-then-insert race
- parallel duplicates with the same identity cannot both perform the side effect
- `InProgress`, `Completed`, `Failed`, `Unknown/NeedsReconciliation` are represented deliberately
- exceptions after possible side effects do not release the reservation as if nothing happened

If an external side effect may have happened, the state must not be blindly unlocked for a fresh repeat. It should usually become `Unknown`, `InProgress`, or `NeedsReconciliation`.

### 5. Check Retention Windows

Retention must cover the maximum duplicate arrival window, not a convenient cache TTL:
- frontend retry policy
- service worker/offline queue duration
- mobile background retries
- load balancer/proxy retries
- message queue retry and dead-letter redrive
- webhook redelivery window
- manual support retry/runbook window
- provider callback delay
- business lifecycle of the operation

If retention is too expensive for Redis/cache, the finding is to move idempotency records into durable operation storage, not to shorten the TTL silently.

### 6. Check External Boundaries

For every external system call:
- does the provider accept and enforce our idempotency key/reference?
- if not, is there a provider reference, two-step reservation/commit, or local adapter that makes retry safe?
- where is the local intent key linked to provider reference?
- what happens if process crashes between provider acquire and local save?
- is there reconciliation for orphaned provider operations or callbacks without local state?
- do webhooks deduplicate by provider event id and by resulting business transition?

Идемпотентность цепочки равна идемпотентности самого слабого звена.

### 7. Check Response Replay

For repeated requests after completion, verify the contract:
- return original response only when it cannot become semantically stale inside the replay window
- otherwise return a link/id to the operation and let the client read current state
- mark replay vs first execution if the client must behave differently
- cached success must not claim current active state after cancellation, refund, rollback, expiry, or replacement

### 8. Check Tests And Observability

Look for tests that prove the risky cases:
- same intent, network timeout, retry
- same intent, concurrent duplicate
- new legitimate intent after failed prior attempt
- duplicate after TTL/window boundary
- external timeout after provider accepted the operation
- webhook duplicate and out-of-order callback
- replay after business state changed
- crash between local save and external call, and external call and local save

Observability should expose:
- operation identity and business key
- idempotency state transitions
- duplicate/replay count
- provider reference linkage
- unknown/reconciliation queue size
- alertable duplicate side effects

## Output Contract

If context is incomplete, output:

```text
BLOCKED_FOR_CONTEXT
Missing:
- ...
Questions:
- ...
Partial facts already known:
- ...
```

If audit is possible, output:

1. `Scope`: operations and layers reviewed.
2. `System Map`: concise path of frontend/backend/infra/external boundaries.
3. `Idempotency Contract`: what one business intent means, key/source of truth, retention, replay behavior.
4. `Findings`: ordered by severity with evidence and affected flow.
5. `Risk Matrix`: duplicate effect, stale replay, lost callback, stuck in-progress, invalid legitimate retry, missing reconciliation.
6. `Required Tests`: concrete scenarios that must exist or be added.
7. `Open Questions`: only blockers that cannot be answered from available context.

Findings must be grounded in code/config/docs/runtime facts. Label assumptions explicitly.

## Reference

Read `references/audit-checklist.md` when doing a real audit or when you need the detailed checklist and report skeleton.
