#!/usr/bin/env bash

set -e

DEFAULT_MODULE_NAME=src.main

MODULE_NAME=${MODULE_NAME:-$DEFAULT_MODULE_NAME}
VARIABLE_NAME=${VARIABLE_NAME:-app}
export APP_MODULE=${APP_MODULE:-"$MODULE_NAME:$VARIABLE_NAME"}

HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}
LOG_LEVEL=${LOG_LEVEL:-info}
WORKERS=${WORKERS:-4}
ACCESS_LOG_FILE=${ACCESS_LOG_FILE:-/var/log/fasmo/access.log}
ERROR_LOG_FILE=${ERROR_LOG_FILE:-/var/log/fasmo/error.log}

mkdir -p $(dirname "$ACCESS_LOG_FILE")
mkdir -p $(dirname "$ERROR_LOG_FILE")

exec gunicorn -k uvicorn.workers.UvicornWorker "$APP_MODULE" --bind $HOST:$PORT --workers $WORKERS --log-level $LOG_LEVEL --access-logfile "$ACCESS_LOG_FILE" --error-logfile "$ERROR_LOG_FILE"