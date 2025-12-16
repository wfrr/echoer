#!/bin/env sh
set -e

export $(grep '^BIND_HOST' .env | xargs)
export $(grep '^BIND_PORT' .env | xargs)

exec uwsgi --http ${BIND_HOST}:${BIND_PORT} --ini uwsgi.ini