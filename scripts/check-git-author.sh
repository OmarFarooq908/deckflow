#!/usr/bin/env bash
set -euo pipefail

allowed_name="omarfarooq908"
allowed_email="mohamed.omar.farooq@gmail.com"

name="$(git config user.name || true)"
email="$(git config user.email || true)"

if [[ "$name" != "$allowed_name" || "$email" != "$allowed_email" ]]; then
  echo "Git author must be ${allowed_name} <${allowed_email}> (found: ${name:-unset} <${email:-unset}>)." >&2
  echo "Set with: git config user.name ${allowed_name} && git config user.email ${allowed_email}" >&2
  exit 1
fi
