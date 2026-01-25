#!/usr/bin/env bash
set -e

echo "Waiting for Postgres at ${DB_HOST:-db}:${DB_PORT:-5432} ..."
until python - <<'PY'
import os
import psycopg
host=os.getenv("DB_HOST","db")
port=int(os.getenv("DB_PORT","5432"))
db=os.getenv("DB_NAME","healthapp")
user=os.getenv("DB_USER","postgres")
pw=os.getenv("DB_PASSWORD","postgres")
psycopg.connect(host=host, port=port, dbname=db, user=user, password=pw).close()
print("DB is ready")
PY
do
  echo "DB not ready - sleeping 2s"
  sleep 2
done
