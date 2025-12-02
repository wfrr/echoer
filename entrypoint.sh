#!/bin/env sh
set -e

export $(grep '^HOST' .env | xargs)
export $(grep '^PORT' .env | xargs)

exec uwsgi --http ${HOST}:${PORT} --ini uwsgi.ini