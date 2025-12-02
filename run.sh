#!/bin/env bash
set -e

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export $(grep '^HOST' .env | xargs)
export $(grep '^PORT' .env | xargs)
uwsgi --http ${HOST}:${PORT} --ini uwsgi.ini
