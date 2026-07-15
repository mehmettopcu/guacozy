#!/usr/bin/env bash
# Launch the Django backend for the E2E suite: isolated sqlite DB, migrated and
# seeded, served on 127.0.0.1:8000 (the frontend dev server proxies to it).
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../../guacozy_server"

export DEBUG=True
export DJANGO_SECRET_KEY=e2e-secret-key-not-for-production
export FIELD_ENCRYPTION_KEY=qjq4ObsXMqiqQyfKgD-jjEGm4ep8RaHKGRg4ohGCi1A=
export DJANGO_DB_URL=sqlite:///e2e_db.sqlite3
export DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

python manage.py migrate --no-input
python manage.py seed_e2e
exec python manage.py runserver 127.0.0.1:8000
