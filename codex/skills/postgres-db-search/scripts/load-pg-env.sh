#!/usr/bin/env bash
set -euo pipefail

trim_whitespace() {
  local value="$1"

  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"

  printf '%s' "$value"
}

find_db_env_file() {
  if [[ -n "${DB_ENV_FILE:-}" ]]; then
    if [[ -f "$DB_ENV_FILE" ]]; then
      printf '%s\n' "$DB_ENV_FILE"
      return 0
    fi

    return 1
  fi

  local dir="${PWD}"
  while [[ -n "$dir" && "$dir" != "/" ]]; do
    if [[ -f "$dir/.env" ]]; then
      printf '%s\n' "$dir/.env"
      return 0
    fi

    dir="$(dirname "$dir")"
  done

  if [[ -f "/.env" ]]; then
    printf '/.env\n'
    return 0
  fi

  return 1
}

load_pg_env_from_file() {
  local env_file="$1"
  local line=""
  local key=""
  local raw_value=""
  local value=""

  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%$'\r'}"
    line="$(trim_whitespace "$line")"

    if [[ -z "$line" || "${line:0:1}" == "#" ]]; then
      continue
    fi

    if [[ "$line" == export[[:space:]]* ]]; then
      line="${line#export }"
      line="$(trim_whitespace "$line")"
    fi

    if [[ ! "$line" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]]; then
      continue
    fi

    key="${line%%=*}"
    raw_value="${line#*=}"
    raw_value="$(trim_whitespace "$raw_value")"

    case "$key" in
      PGHOST|PGPORT|PGDATABASE|PGUSER|PGPASSWORD)
        ;;
      *)
        continue
        ;;
    esac

    if [[ -n "${!key:-}" ]]; then
      continue
    fi

    value="$raw_value"

    if [[ "$value" == \"*\" && "$value" == *\" ]]; then
      value="${value:1:${#value}-2}"
    elif [[ "$value" == \'*\' && "$value" == *\' ]]; then
      value="${value:1:${#value}-2}"
    else
      value="${value%%#*}"
      value="$(trim_whitespace "$value")"
    fi

    printf -v "$key" '%s' "$value"
    export "$key"
  done < "$env_file"
}

load_pg_env_if_needed() {
  local env_file=""

  if [[ -n "${PGHOST:-}" && -n "${PGPORT:-}" && -n "${PGDATABASE:-}" && -n "${PGUSER:-}" && -n "${PGPASSWORD:-}" ]]; then
    return 0
  fi

  if env_file="$(find_db_env_file)"; then
    load_pg_env_from_file "$env_file"
    export DB_ENV_LOADED_FROM="$env_file"
  fi
}
