#!/bin/bash

# =================================================================
# MYPAGE48 - AUTOMATED SERVER SETUP SCRIPT (Ubuntu/Debian)
# =================================================================
# This script prepares a fresh VPS for MyPage48 deployment.
# It is idempotent (safe to run multiple times).

set -e

# --- CONFIGURATION ---
REPO_URL="https://github.com/Shiyinq/mypage48.git"
PROJECT_DIR="$HOME/mypage48"
SWAP_SIZE="2G"

echo "🚀 Starting MyPage48 Server Setup..."

# 1. Update System
echo "🔄 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# 2. Check & Install Dependencies (Git, Curl, UFW, 7zip, Rclone)
echo "📦 Checking basic dependencies..."
sudo apt install -y git curl ufw p7zip-full rclone

# 3. Check & Install Docker
if ! [ -x "$(command -v docker)" ]; then
    echo "🐳 Docker not found. Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "✅ Docker installed successfully."
else
    echo "✅ Docker is already installed."
fi

# 4. Memory Management (Swap File)
if [ ! -f /swapfile ]; then
    echo "🧠 Creating ${SWAP_SIZE} swap file for build stability..."
    sudo fallocate -l $SWAP_SIZE /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    echo "✅ Swap file created."
else
    echo "✅ Swap file already exists."
fi

# 5. Firewall Configuration (UFW)
echo "🛡️ Configuring Firewall (UFW)..."
sudo ufw allow ssh
# Allow Cloudflare IPs
echo "☁️ Allowing Cloudflare IP ranges..."
for ip in $(curl -s https://www.cloudflare.com/ips-v4); do sudo ufw allow from $ip to any port 80; done
for ip in $(curl -s https://www.cloudflare.com/ips-v4); do sudo ufw allow from $ip to any port 443; done
sudo ufw --force enable
echo "✅ Firewall configured."

# 6. Project Directory Setup
if [ ! -d "$PROJECT_DIR" ]; then
    echo "📂 Cloning repository to $PROJECT_DIR..."
    git clone $REPO_URL "$PROJECT_DIR"
else
    echo "📂 Project directory already exists at $PROJECT_DIR."
fi

cd "$PROJECT_DIR"

# 7. Directory Structure
echo "📁 Creating necessary directories..."
mkdir -p logs/backend logs/nginx certbot/conf certbot/www
sudo chown -R $USER:$USER logs/

# 8. Interactive .env Setup
ENV_FILE=".env"
SHOULD_SETUP_ENV=true

if [ -f "$ENV_FILE" ]; then
    read -p "⚠️  File .env sudah ada. Apakah Anda ingin memperbaruinya? (y/n): " confirm_env
    if [[ $confirm_env != "y" ]]; then
        SHOULD_SETUP_ENV=false
        echo "⏭️  Skipping .env setup."
    fi
fi

if [ "$SHOULD_SETUP_ENV" = true ]; then
    echo "📝 Setting up environment variables (.env)..."
    
    # Use template as base
    cp .env.production.example .env.tmp
    
    # Prompt for critical inputs with defaults
    read -p "🌐 Enter your main domain (default: mypage48.com): " DOMAIN
    DOMAIN=${DOMAIN:-mypage48.com}

    read -p "🔐 Enter MongoDB Root Password (default: ChangeMe123!): " MONGO_ROOT_PASSWORD
    MONGO_ROOT_PASSWORD=${MONGO_ROOT_PASSWORD:-ChangeMe123!}

    read -p "📦 Enter MinIO Access Key (default: minioadmin): " MINIO_ACCESS_KEY
    MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY:-minioadmin}

    read -p "🔑 Enter MinIO Secret Key (default: minioadmin123): " MINIO_SECRET_KEY
    MINIO_SECRET_KEY=${MINIO_SECRET_KEY:-minioadmin123}

    read -p "🐘 Enter Umami Postgres Password (default: umami123!): " POSTGRES_PASSWORD
    POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-umami123!}

    echo "🔒 --- BACKUP SETTINGS (R2) ---"
    read -p "🔐 Enter a Password to ENCRYPT your backups: " BACKUP_PASSWORD
    read -p "🆔 Enter Cloudflare Account ID: " R2_ACCOUNT_ID
    read -p "🪣 Enter R2 Bucket Name: " R2_BUCKET
    read -p "🔑 Enter R2 Access Key ID: " R2_ACCESS_KEY
    read -p "🤫 Enter R2 Secret Access Key: " R2_SECRET_KEY
    
    # Generate random keys
    SECRET_KEY=$(openssl rand -hex 32)
    UMAMI_SECRET=$(openssl rand -hex 32)

    # Replace values in .env.tmp
    sed -i "s|FRONTEND_URL=.*|FRONTEND_URL=https://$DOMAIN|g" .env.tmp
    sed -i "s|PUBLIC_CLIENT_SIDE_API_BASE_URL=.*|PUBLIC_CLIENT_SIDE_API_BASE_URL=https://api.$DOMAIN|g" .env.tmp
    sed -i "s|API_BASE_URL=.*|API_BASE_URL=https://api.$DOMAIN|g" .env.tmp
    sed -i "s|PUBLIC_UMAMI_URL=.*|PUBLIC_UMAMI_URL=https://analytics.$DOMAIN|g" .env.tmp
    sed -i "s|MINIO_PUBLIC_URL=.*|MINIO_PUBLIC_URL=https://storage.$DOMAIN|g" .env.tmp
    sed -i "s|MINIO_BROWSER_REDIRECT_URL=.*|MINIO_BROWSER_REDIRECT_URL=https://storage.$DOMAIN|g" .env.tmp
    sed -i "s|ORIGINS=.*|ORIGINS=https://$DOMAIN,https://api.$DOMAIN,https://analytics.$DOMAIN,https://storage.$DOMAIN|g" .env.tmp
    
    sed -i "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|g" .env.tmp
    sed -i "s|UMAMI_SECRET=.*|UMAMI_SECRET=$UMAMI_SECRET|g" .env.tmp
    
    sed -i "s|MONGO_ROOT_PASSWORD=.*|MONGO_ROOT_PASSWORD=$MONGO_ROOT_PASSWORD|g" .env.tmp
    sed -i "s|MINIO_ACCESS_KEY=.*|MINIO_ACCESS_KEY=$MINIO_ACCESS_KEY|g" .env.tmp
    sed -i "s|MINIO_SECRET_KEY=.*|MINIO_SECRET_KEY=$MINIO_SECRET_KEY|g" .env.tmp
    sed -i "s|POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$POSTGRES_PASSWORD|g" .env.tmp
    sed -i "s|MINIO_SECURE=.*|MINIO_SECURE=false|g" .env.tmp

    # Backup settings
    sed -i "s|BACKUP_PASSWORD=.*|BACKUP_PASSWORD=$BACKUP_PASSWORD|g" .env.tmp
    sed -i "s|R2_ACCOUNT_ID=.*|R2_ACCOUNT_ID=$R2_ACCOUNT_ID|g" .env.tmp
    sed -i "s|R2_BUCKET=.*|R2_BUCKET=$R2_BUCKET|g" .env.tmp
    sed -i "s|R2_ACCESS_KEY=.*|R2_ACCESS_KEY=$R2_ACCESS_KEY|g" .env.tmp
    sed -i "s|R2_SECRET_KEY=.*|R2_SECRET_KEY=$R2_SECRET_KEY|g" .env.tmp

    mv .env.tmp .env
    echo "✅ .env file generated successfully."
fi

# 9. SSL SSL Directory Setup
echo "🔑 Preparing SSL certificate directory structure..."
CERT_DIR="certbot/conf/live/$DOMAIN"
mkdir -p "$CERT_DIR"
touch "$CERT_DIR/fullchain.pem"
touch "$CERT_DIR/privkey.pem"
echo "✅ SSL directory and empty files created."

# 10. Automated Backup Setup (Cron Job)
echo "⏰ Setting up daily automated backup (00:00)..."
chmod +x scripts/backup-to-r2.sh
# Check if cron job already exists to avoid duplication
(crontab -l 2>/dev/null | grep -F "scripts/backup-to-r2.sh") || (crontab -l 2>/dev/null; echo "0 0 * * * $PROJECT_DIR/scripts/backup-to-r2.sh >> $PROJECT_DIR/logs/backup.log 2>&1") | crontab -
echo "✅ Cron job for daily backup at midnight created."

echo "--------------------------------------------------------"
echo "🎉 SETUP COMPLETE!"
echo "--------------------------------------------------------"
echo "Next steps:"
echo "1. Verify .env file: nano .env"
echo "2. Setup SSL (Cloudflare Origin CA):"
echo "   - Open fullchain.pem: nano certbot/conf/live/$DOMAIN/fullchain.pem (Paste Origin Certificate)"
echo "   - Open privkey.pem:   nano certbot/conf/live/$DOMAIN/privkey.pem   (Paste Private Key)"
echo "3. Add your GitHub SSH Public Key to your GitHub Profile."
echo "4. Run deployment: docker compose -f docker-compose.prod.yml up -d"
echo "5. Configure GitHub Secrets as per DEPLOYMENT.md for Auto-Updates."
echo "--------------------------------------------------------"
