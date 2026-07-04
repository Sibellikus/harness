#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Load only PG* values from .env without executing the file contents.
source "$script_dir/load-pg-env.sh"

usage() {
  cat <<'EOF'
Usage:
  search-value.sh <value> [exact|contains] [limit]

Examples:
  search-value.sh "019aa2c5-e5d2-7499-9932-78a2d8cbae68"
  search-value.sh "user@example.test" contains 25

Search scope:
  - non-system schemas
  - uuid columns
  - text, varchar, char columns
  - json/jsonb columns via column::text

Required environment variables:
  PGHOST
  PGPORT
  PGDATABASE
  PGUSER
  PGPASSWORD
EOF
}

require_env() {
  load_pg_env_if_needed

  local missing=()
  local name

  for name in PGHOST PGPORT PGDATABASE PGUSER PGPASSWORD; do
    if [[ -z "${!name:-}" ]]; then
      missing+=("$name")
    fi
  done

  if (( ${#missing[@]} > 0 )); then
    printf 'Missing required environment variables: %s\n' "${missing[*]}" >&2
    if [[ -n "${DB_ENV_LOADED_FROM:-}" ]]; then
      printf 'Checked .env file: %s\n' "$DB_ENV_LOADED_FROM" >&2
    else
      printf 'No .env file found in %s or its parent directories.\n' "$PWD" >&2
    fi
    exit 1
  fi
}

main() {
  if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    usage
    exit 0
  fi

  if (( $# < 1 || $# > 3 )); then
    usage >&2
    exit 1
  fi

  local search_value="$1"
  local mode="${2:-exact}"
  local result_limit="${3:-50}"

  case "$mode" in
    exact|contains)
      ;;
    *)
      printf 'Unsupported mode: %s\n' "$mode" >&2
      usage >&2
      exit 1
      ;;
  esac

  if ! [[ "$result_limit" =~ ^[0-9]+$ ]]; then
    printf 'Limit must be a positive integer, got: %s\n' "$result_limit" >&2
    exit 1
  fi

  require_env

  export PGOPTIONS="${PGOPTIONS:-} -c default_transaction_read_only=on"

  local -a psql_cmd=(
    psql
    -X
    --no-psqlrc
    -v ON_ERROR_STOP=1
    -P pager=off
    -At
  )

  local generated_sql
  generated_sql="$("${psql_cmd[@]}" \
    --set=search_value="$search_value" \
    --set=mode="$mode" \
    --set=result_limit="$result_limit" <<'SQL'
WITH candidates AS (
    SELECT
        c.table_schema,
        c.table_name,
        c.column_name,
        c.data_type,
        c.udt_name
    FROM information_schema.columns AS c
    WHERE c.table_schema NOT IN ('pg_catalog', 'information_schema')
      AND (
          c.data_type IN ('uuid', 'text', 'character varying', 'character')
          OR c.udt_name IN ('json', 'jsonb')
      )
),
statements AS (
    SELECT format(
        $fmt$
SELECT %L AS schema_name, %L AS table_name, %L AS column_name, count(*) AS match_count
FROM %I.%I
WHERE %s
HAVING count(*) > 0
        $fmt$,
        table_schema,
        table_name,
        column_name,
        table_schema,
        table_name,
        CASE
            WHEN udt_name IN ('json', 'jsonb') THEN format('%I::text ILIKE %L', column_name, '%%' || :'search_value' || '%%')
            WHEN :'mode' = 'contains' THEN format('%I::text ILIKE %L', column_name, '%%' || :'search_value' || '%%')
            ELSE format('%I::text = %L', column_name, :'search_value')
        END
    ) AS sql
    FROM candidates
)
SELECT COALESCE(
    'WITH matches AS (' || E'\n' || string_agg(sql, E'\nUNION ALL\n') || E'\n)\n' ||
    'SELECT schema_name, table_name, column_name, match_count FROM matches ORDER BY match_count DESC, schema_name, table_name, column_name LIMIT ' || :'result_limit' || ';',
    'SELECT ''no matches'' AS schema_name, '''' AS table_name, '''' AS column_name, 0 AS match_count WHERE FALSE;'
)
FROM statements;
SQL
)"

  psql \
    -X \
    --no-psqlrc \
    -v ON_ERROR_STOP=1 \
    -P pager=off <<SQL
$generated_sql
SQL
}

main "$@"
