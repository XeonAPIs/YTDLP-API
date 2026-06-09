#!/usr/bin/env bash
set -euo pipefail

# If COOKIES_CONTENT is provided (via Render secret/env), write it to cookies.txt
if [ -n "${COOKIES_CONTENT:-}" ]; then
  echo "Writing provided cookies to ./cookies.txt"
  printf "%s" "$COOKIES_CONTENT" > ./cookies.txt
  chmod 600 ./cookies.txt || true
fi

echo "Starting gunicorn..."
exec gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 app:app
