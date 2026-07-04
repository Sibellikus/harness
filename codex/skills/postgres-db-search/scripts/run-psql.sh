#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Load only PG* values from .env without executing the file contents.
source "$script_dir/load-pg-env.sh"

usage() {
  cat <<'EOF'
Usage:
  run-psql.sh "select * from table where id = '...';"
  cat query.sql | run-psql.sh
  run-psql.sh -f /path/to/query.sql

Required environment variables:
  PGHOST
  PGPORT
  PGDATABASE
  PGUSER
  PGPASSWORD

Behavior:
  - uses psql with ON_ERROR_STOP=1
  - disables .psqlrc loading
  - forces default_transaction_read_only=on
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

  require_env

  export PGOPTIONS="${PGOPTIONS:-} -c default_transaction_read_only=on"

  local -a psql_cmd=(
    psql
    -X
    --no-psqlrc
    -v ON_ERROR_STOP=1
    -P pager=off
  )

  if (( $# == 0 )); then
    if [[ -t 0 ]]; then
      usage >&2
      exit 1
    fi

    exec "${psql_cmd[@]}"
  fi

  if [[ "$1" == "-f" ]]; then
    if (( $# != 2 )); then
      usage >&2
      exit 1
    fi

    exec "${psql_cmd[@]}" -f "$2"
  fi

  exec "${psql_cmd[@]}" -c "$*"
}

main "$@"
