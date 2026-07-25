#!/bin/bash
# Disk cleanup script for MyPage48

set -euo pipefail

echo "=========================================="
echo "Starting MyPage48 Server Disk Cleanup..."
echo "=========================================="

# 1. Clean Docker builder cache and unused components
if command -v docker &> /dev/null; then
    echo "[1/4] Cleaning Docker build cache and system components..."
    docker builder prune -af
    docker system prune -f
else
    echo "[1/4] Docker is not installed, skipping..."
fi

# 2. Clean system logs (journalctl)
if command -v journalctl &> /dev/null; then
    echo "[2/4] Vacuuming system journal logs to 100M..."
    if [ "$EUID" -ne 0 ]; then
        sudo journalctl --vacuum-size=100M
    else
        journalctl --vacuum-size=100M
    fi
else
    echo "[2/4] journalctl is not available, skipping..."
fi

# 3. Clean APT cache
if command -v apt-get &> /dev/null; then
    echo "[3/4] Cleaning APT package cache..."
    if [ "$EUID" -ne 0 ]; then
        sudo apt-get clean
    else
        apt-get clean
    fi
else
    echo "[3/4] APT package manager is not available, skipping..."
fi

# 4. Clean MyPage48 project logs
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOGS_DIR="$PROJECT_DIR/logs"

if [ -d "$LOGS_DIR" ]; then
    echo "[4/4] Cleaning MyPage48 application logs in $LOGS_DIR..."
    # Delete rotated log files (*.log.20*)
    find "$LOGS_DIR" -type f -name "*.log.20*" -delete
    # Truncate active log files (*.log)
    find "$LOGS_DIR" -type f -name "*.log" -exec truncate -s 0 {} +
    echo "Application logs cleaned."
else
    echo "[4/4] Project logs directory not found at $LOGS_DIR, skipping..."
fi

echo "=========================================="
echo "Disk Cleanup Complete!"
echo "=========================================="
df -h /
