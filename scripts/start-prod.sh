#!/usr/bin/env bash

set -e

DEFAULT_MODULE_NAME=src.main

MODULE_NAME=${MODULE_NAME:-$DEFAULT_MODULE_NAME}
VARIABLE_NAME=${VARIABLE_NAME:-app}
export APP_MODULE=${APP_MODULE:-"$MODULE_NAME:$VARIABLE_NAME"}

HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8080}
LOG_LEVEL=${LOG_LEVEL:-info}
# Smart worker detection
# Calculate workers based on CPU (2*cores + 1) but capped by RAM (TotalRAM / 512MB)
if [ -z "$WORKERS" ]; then
    CPU_CORES=$(nproc 2>/dev/null || grep -c ^processor /proc/cpuinfo)
    TOTAL_RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}' 2>/dev/null || echo 0)
    
    if [ "$TOTAL_RAM_KB" -gt 0 ]; then
        TOTAL_RAM_MB=$(( TOTAL_RAM_KB / 1024 ))
        # 512MB is a safe division to allow room for OS + DB (MongoDB/Postgres) + Nginx
        WORKERS_BY_RAM=$(( TOTAL_RAM_MB / 512 ))
        WORKERS_BY_CPU=$(( CPU_CORES * 2 + 1 ))
        
        # Pick the minimum, ensuring at least 1 worker
        if [ "$WORKERS_BY_CPU" -lt "$WORKERS_BY_RAM" ]; then
            WORKERS=$WORKERS_BY_CPU
        else
            WORKERS=$WORKERS_BY_RAM
        fi
    else
        # Fallback if RAM cannot be detected
        WORKERS=$(( CPU_CORES + 1 ))
    fi
    
    # Final safety check
    if [ "$WORKERS" -lt 1 ]; then WORKERS=1; fi
    # Cap workers at 4 for a 2GB RAM VPS to ensure stability
    if [ "$WORKERS" -gt 4 ]; then WORKERS=4; fi
fi

export WORKERS
ACCESS_LOG_FILE=${ACCESS_LOG_FILE:-/var/log/mypage48/access.log}
ERROR_LOG_FILE=${ERROR_LOG_FILE:-/var/log/mypage48/error.log}

mkdir -p $(dirname "$ACCESS_LOG_FILE")
mkdir -p $(dirname "$ERROR_LOG_FILE")

exec gunicorn -k uvicorn.workers.UvicornWorker "$APP_MODULE" --bind $HOST:$PORT --workers $WORKERS --log-level $LOG_LEVEL --access-logfile "$ACCESS_LOG_FILE" --error-logfile "$ERROR_LOG_FILE"