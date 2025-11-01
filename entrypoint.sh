#!/usr/bin/env bash
set -euo pipefail

# wait for redis if needed (fast check)
if [ -n "${REDIS_HOST:-}" ]; then
  echo "Waiting for Redis at ${REDIS_HOST:-redis}:${REDIS_PORT:-6379}..."
  # simple wait loop; non-blocking for dev
  for i in $(seq 1 10); do
    if nc -z "${REDIS_HOST:-redis}" "${REDIS_PORT:-6379}"; then
      echo "Redis is up"
      break
    fi
    echo "Waiting for redis... ($i)"
    sleep 1
  done
fi

# Run migrations (safe in dev)
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Start gunicorn
exec gunicorn ecom.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers ${GUNICORN_WORKERS:-3} \
  --log-level ${GUNICORN_LOGLEVEL:-info} \
  --access-logfile '-' \
  --error-logfile '-'
