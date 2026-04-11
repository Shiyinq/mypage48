#!/bin/bash

# =================================================================
# MYPAGE48 - AUTOMATED ENCRYPTED OFF-SITE BACKUP (R2)
# =================================================================
# This script dumps database, archives photos & secrets,
# encrypts with a password, and uploads to Cloudflare R2.

set -e

# Load environment variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PARENT_DIR"

if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "❌ Error: .env file not found in $PARENT_DIR"
    exit 1
fi

# Variables
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_NAME="mypage48_backup_$TIMESTAMP"
TEMP_BACKUP_DIR="/tmp/$BACKUP_NAME"
ENCRYPTED_FILE="/tmp/$BACKUP_NAME.7z"

# Ensure all backup config is present
if [ -z "$BACKUP_PASSWORD" ] || [ -z "$R2_ACCESS_KEY" ] || [ -z "$R2_SECRET_KEY" ] || [ -z "$R2_BUCKET" ] || [ -z "$R2_ACCOUNT_ID" ]; then
    echo "❌ Error: Missing backup configuration in .env"
    exit 1
fi

echo "🚀 Starting backup: $BACKUP_NAME"

# 1. Create temp directory
mkdir -p "$TEMP_BACKUP_DIR"

# 2. Backup MongoDB
echo "🍃 Dumping MongoDB..."
docker exec mypage48-mongodb mongodump --username "$MONGO_ROOT_USER" --password "$MONGO_ROOT_PASSWORD" --archive="$TEMP_BACKUP_DIR/mongodb.archive"

# 3. Archive MinIO Data, .env, and SSL Certs
echo "📸 Archiving photos and secrets..."
tar -czf "$TEMP_BACKUP_DIR/data_assets.tar.gz" .env certbot/ minio_data/ --exclude='*.7z' --exclude='logs/*'

# 4. Encrypt everything into a 7z archive
echo "🔐 Encrypting backup with password..."
7za a -p"$BACKUP_PASSWORD" -mhe=on "$ENCRYPTED_FILE" "$TEMP_BACKUP_DIR"

# 5. Upload to Cloudflare R2 using rclone
echo "☁️  Uploading to Cloudflare R2..."
export RCLONE_CONFIG_R2_TYPE=s3
export RCLONE_CONFIG_R2_PROVIDER=Cloudflare
export RCLONE_CONFIG_R2_ACCESS_KEY_ID="$R2_ACCESS_KEY"
export RCLONE_CONFIG_R2_SECRET_ACCESS_KEY="$R2_SECRET_KEY"
export RCLONE_CONFIG_R2_ENDPOINT="https://$R2_ACCOUNT_ID.r2.cloudflarestorage.com"

rclone copy "$ENCRYPTED_FILE" "R2:$R2_BUCKET/backups/"

# 6. Lifecycle: Clean up old backups in R2 (Keep only last 7 days)
echo "🧹 Cleaning up old backups in Cloudflare R2 (7-day retention)..."
rclone delete "R2:$R2_BUCKET/backups/" --min-age 7d --rmdirs

# 7. Cleanup local temp files
echo "🗑️ Cleaning up local temporary files..."
rm -rf "$TEMP_BACKUP_DIR"
rm -f "$ENCRYPTED_FILE"

echo "✅ BACKUP COMPLETED & UPLOADED SUCCESSFULLY!"
