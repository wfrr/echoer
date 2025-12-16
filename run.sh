#!/bin/env bash
set -e

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export $(grep '^BIND_HOST' .env | xargs)
export $(grep '^BIND_PORT' .env | xargs)
uwsgi --http ${BIND_HOST}:${BIND_PORT} --ini uwsgi.ini
