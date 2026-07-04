---
name: issue-research
description: Investigate production and server-side bugs where API behavior, analytics outputs, logs, and database facts do not match. Use for count mismatches, missing rows, endpoint-vs-DB discrepancies, off-by-one issues, dropped records, suspicious filters, timezone suspicions, and "DB says X, API returns Y" debugging across code and live data.
---

# Issue Research

Trace a discrepancy to a concrete object, filter, or contract mismatch.

Prefer server-side facts over plausible stories.

## Core Rules

- Start from the exact symptom: route, payload, response fragment, environment, date range, provider/source system when relevant, entity id, and the exact delta.
- Build the full data path before prioritizing hypotheses: request -> auth/org resolution -> filters -> upstream clients -> repositories/storage -> post-load filters -> aggregation -> response mapping.
- Prefer deployed or server-side data when the complaint is about a deployed response. Do not default to local snapshots unless the user explicitly wants local state.
- Default to read-only investigation. Do not run inserts, updates, deletes, backfills, or "quick cleanup" SQL during diagnosis.
- If the user asks to change live/test DB data, stop after the investigation result and present the exact write plan first. Do not execute DB writes until the user explicitly confirms that exact plan in a separate step.
- Treat destructive DB actions as high risk even in test environments. Before any delete/update, verify a trusted recovery path for the affected tables and state it explicitly. If recovery is missing or unverified, do not execute the write.
- Treat the size of the delta as a first-class clue. `100 -> 99` suggests one object disappeared. Do not spend most of the time on explanations that would shift 5, 20, or 60 rows unless data supports them.
- Eliminate hypotheses with measurements, not intuition.
- Verify every query assumption against actual storage shape. Check whether the key is `_id` vs `id`, UTC vs local day, source row vs order vs line item, and raw row count vs distinct entity count.
- Keep a running list of hard eliminations so you do not revisit dead branches.
- When a domain validation error is caused by a persisted value, verify every current write path and validator for that value before proposing code changes. If current system entrypoints reject the bad value, classify the issue as stale/corrupt legacy data and propose a migration/backfill/data-repair plan; do not weaken validation, add runtime fallback, or calculate with defaults.
- Do not ask the user whether to continue while there are still concrete, non-speculative checks available in code or server data.
- Ask a blocking question only when the next step truly depends on missing context that cannot be discovered safely.

## Workflow

### 1. Freeze the symptom

Capture the exact mismatch in one line:

`Expected from source-of-truth: 100 source rows on 2026-01-15; API returned 99 in response.totalCount.`

Also capture:

- route and payload
- exact response field that is wrong
- environment
- business date and timezone semantics
- entity type being counted: source rows, orders, events, products, unique business ids, related metadata entities, etc.

If the symptom is not frozen precisely, do that before deep investigation.

### 2. Identify the source of truth

Decide what should win if systems disagree:

- raw provider storage
- internal report store
- pre-aggregated analytics table
- current API contract

Do not silently switch sources mid-investigation. If the API intentionally uses a derived source, say so explicitly.

### 3. Draw the pipeline

Before chasing hypotheses, identify the exact path that produces the wrong number.

For each stage, note:

- what enters
- what filters or reshapes data
- what leaves

Typical stages:

1. endpoint/request DTO
2. auth and organization resolution
3. account, tenant, credential, or API-key resolution
4. auxiliary datasets loaded first: links, configs, exclusions, ownership metadata, enrichment tables
5. primary source fetch
6. post-fetch filters
7. aggregation/grouping
8. response mapping

If two different codepaths can produce similar numbers, separate them early.

### 4. Generate hypotheses from the pipeline, not from habit

Rank hypotheses by fit to the symptom.

Prefer hypotheses that can explain the exact delta with one mechanism:

- one missing related entity
- one filtered source row
- one exclusion row
- one distinct-vs-raw mismatch
- one boundary timestamp

Deprioritize broad explanations unless evidence points there:

- generic timezone panic
- "maybe cancellations are removed"
- "maybe cache is stale"

These are acceptable hypotheses only after checking whether they match the scale and shape of the discrepancy.

### 5. Prove or kill each hypothesis cheaply

For every hypothesis, choose the fastest proof:

- count rows before and after a filter
- compare distinct ids between API-reachable set and raw storage
- inspect the exact object expected to be missing
- query boundary timestamps only
- inspect one relevant cache document

Prefer narrow queries that can isolate the one disappearing object.

### 6. Resolve to a concrete missing object or filter

Do not stop at "likely caused by related metadata" or "looks like timezone".

Push until you can name at least one of:

- missing related entity id
- missing source row id
- exclusion document id
- dropped product link
- boundary timestamp row
- wrong distinct key
- exact line in code that excludes the object

This is the standard of proof for root cause.

### 7. Explain the mismatch numerically

Close the loop with arithmetic:

- raw source count = `100`
- object/filter removed = `1`
- resulting API count = `99`

If possible, do the same for amount, quantity, or profit so the explanation is complete, not count-only.

## Investigation Patterns

### Server-first discrepancy check

Use this when the complaint is about `dev`, `stage`, or `prod` behavior.

1. Reproduce the exact metric from server-side storage.
2. Check whether the API has secondary datasets that gate the result: links, exclusions, configs, ownership, enrichment metadata.
3. If the symptom is a domain validation error, inspect the API/write validators and persistence mapping for the failing field before blaming runtime validation.
4. Compare the raw entity set with the gated set.
5. Find the set difference.
6. Prove that the difference size equals the response delta.

### Timezone suspicion

Treat timezone as guilty only after checking boundary rows.

1. Compute the intended local-day UTC interval.
2. Count rows inside the disputed boundary windows.
3. Compare that boundary count to the observed delta.

If the boundary contains 5 rows and the discrepancy is 1, timezone alone is a poor fit.

### Cache suspicion

Do not stop at "cache is stale".

1. Identify the cache collection/table and its lookup key.
2. Verify the real storage schema first.
3. Compare the exact ids used by the response path to the cached ids.
4. Name the missing cached object and the runtime filter that depends on it.

## Anti-Patterns To Avoid

### Local-first drift

Using local DB or local Mongo when the bug is reported against a server environment. This creates false mismatches and wasted branches.

### Premature anchoring

Locking onto exclusions, cancellations, or timezone before tracing the full pipeline.

### Scale mismatch

Spending most effort on explanations that do not fit the size of the delta.

### Fuzzy entity counting

Switching between source rows, orders, unique business ids, products, and related metadata without stating which entity the API counts.

### Weak proof language

Saying "probably" or "most likely" when one more query can prove the exact missing object.

### Premature handoff

Asking the user whether to continue when there are still verifiable codepaths, datasets, or boundary checks left.

### Diagnosis-to-write jump

Moving from investigation straight to delete/update SQL without a separately confirmed plan and a verified recovery path.

### Validation weakening instead of migration

Changing domain validation, adding fallback, or using default values because existing storage contains bad data, without first proving that current write paths can still create that bad data.

### Query-shape bug

Trusting a query result without first confirming field names, key shape, or document structure.

## Output Contract

When reporting the result:

1. State the root cause in one sentence.
2. Show the proof chain in compact bullets or short prose.
3. Name the exact object/filter/line responsible.
4. Explicitly list hard eliminations if they were plausible alternatives.
5. Only then propose a fix.

Good ending:

`The endpoint drops one source row because the response path joins against related metadata first, and related entity ENTITY-123 is missing from the deployed metadata store. Raw storage has 100 rows; filtering out that missing related entity yields 99.`

Bad ending:

`Maybe related metadata is stale. Want me to investigate further?`

## Stop Condition

Stop only when one of these is true:

- the exact missing object or filter is proven
- a real blocker exists and you can state the missing artifact precisely
- the deployed system cannot be inspected further from the current environment, and you have exhausted all non-speculative server-side checks

Until then, keep driving the investigation forward.
