#!/bin/env bash

export $(grep '^HOST' .env | xargs)
export $(grep '^PORT' .env | xargs)
uwsgi --http ${HOST}:${PORT} --master -p 1 -w wsgi:app
