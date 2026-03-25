#!/usr/bin/env sh
set -eu

DB_HOST="postgres"
DB_PORT="5432"

echo "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."
until nc -z "$DB_HOST" "$DB_PORT"; do
  sleep 1
done
echo "PostgreSQL is reachable."
