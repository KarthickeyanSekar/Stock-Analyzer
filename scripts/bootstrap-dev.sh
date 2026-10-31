#!/bin/sh
# One-time setup of a fresh clone: .env, secrets, dev database + Redis, migrations.
# Safe to re-run: existing .env values and data are never overwritten.
# Usage: make bootstrap   (or: sh scripts/bootstrap-dev.sh)
set -eu
cd "$(dirname "$0")/.."

say() { printf '\n==> %s\n' "$1"; }

say "Checking prerequisites"
for tool in docker openssl; do
  command -v "$tool" >/dev/null 2>&1 || { echo "Missing: $tool"; exit 1; }
done
docker compose version >/dev/null

if [ ! -f .env ]; then
  say "Creating .env from .env.example with generated secrets"
  cp .env.example .env
  db_password=$(openssl rand -hex 16)
  # Replace the placeholder password in SA_DB_PASSWORD and SA_DATABASE_URL.
  sed -i.bak "s/change-me/${db_password}/g" .env && rm -f .env.bak
  echo "Generated a random database password."
else
  say ".env already exists: keeping its values"
fi

if grep -q '^SA_MASTER_KEY=$' .env; then
  # A Fernet key is 32 random bytes, URL-safe base64 encoded.
  master_key=$(openssl rand -base64 32 | tr '+/' '-_')
  sed -i.bak "s|^SA_MASTER_KEY=\$|SA_MASTER_KEY=${master_key}|" .env && rm -f .env.bak
  echo "Generated SA_MASTER_KEY. Keep a copy in a password manager."
fi

say "Starting the dev database and Redis"
make dev-db

say "Applying database migrations"
make db-upgrade

if command -v pre-commit >/dev/null 2>&1; then
  say "Installing git hooks"
  pre-commit install
else
  echo "pre-commit not found: run 'make setup' later to install the git hooks."
fi

say "Done. Start the app with: make dev"
