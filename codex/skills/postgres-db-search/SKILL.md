---
name: postgres-db-search
description: Read-only PostgreSQL inspection and record search using PGHOST, PGPORT, PGDATABASE, PGUSER, and PGPASSWORD from the environment. Use when the user asks to search the database, find a record by id/uuid/email/code/text, trace where a value is stored, inspect schema/table contents, or verify database state without modifying data.
---

# Postgres DB Search

Use this skill for PostgreSQL-only database diagnostics driven by `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, and `PGPASSWORD`.
If those variables are not already exported, the scripts try to load missing `PG*` values from the nearest `.env` file in the current directory or its parent directories.

## Workflow

1. Confirm the task is read-only. Do not use this skill for inserts, updates, deletes, migrations, or DDL.
2. Check that all five `PG*` variables are present. The scripts first use real env vars, then try the nearest `.env` file for missing `PG*` values. If any are still missing, stop and say which ones are missing.
3. If the table is unknown, start with `scripts/search-value.sh` to find candidate tables and columns.
4. Once the likely table is known, use `scripts/run-psql.sh` with targeted SQL to inspect exact rows, foreign keys, and neighboring records.
5. Summarize findings with concrete table and column names. If the data is stale or inconsistent, say so explicitly instead of inventing fallbacks.
6. If the user later wants a DB fix, stop at a written plan. Do not switch from this skill into ad-hoc write SQL. Any live/test DB write requires a separately confirmed plan and a trusted recovery path stated up front.

## Commands

Use the wrapper for direct SQL:

```bash
${CODEX_HOME:-$HOME/.codex}/skills/postgres-db-search/scripts/run-psql.sh \
  "select id, status from orders where id = '...';"
```

Use stdin for longer queries:

```bash
cat <<'SQL' | ${CODEX_HOME:-$HOME/.codex}/skills/postgres-db-search/scripts/run-psql.sh
select table_schema, table_name
from information_schema.tables
where table_schema not in ('pg_catalog', 'information_schema');
SQL
```

Use the generic search helper when the location of a value is unknown:

```bash
${CODEX_HOME:-$HOME/.codex}/skills/postgres-db-search/scripts/search-value.sh "019aa2c5-e5d2-7499-9932-78a2d8cbae68"
${CODEX_HOME:-$HOME/.codex}/skills/postgres-db-search/scripts/search-value.sh "user@example.test" contains 25
```

Arguments:
- `search-value.sh <value> [exact|contains] [limit]`
- default mode is `exact`
- default limit is `50`

## Guardrails

- Stay read-only. The scripts force `default_transaction_read_only=on`; keep it that way.
- Do not bypass the read-only wrappers with raw `psql` write commands while following this skill.
- Never run delete/update "cleanup" SQL as part of investigation, even if the data looks obviously broken.
- If a fix is requested, provide the exact target rows/tables and the rollback or restore path first, then wait for explicit confirmation before any write-capable workflow.
- Prefer exact match first for UUIDs, ids, emails, order numbers, and external codes.
- After `search-value.sh`, narrow immediately with explicit SQL. Do not stop at “matches exist somewhere”.
- If the value is absent everywhere, say that plainly.
- If the data in the database contradicts business invariants, report that as a data problem.

## scripts/

- `run-psql.sh` runs `psql` with the required `PG*` variables and a read-only transaction setting.
- `search-value.sh` searches non-system schemas across `uuid`, text-like, `json`, and `jsonb` columns and returns matching schema/table/column counts.
