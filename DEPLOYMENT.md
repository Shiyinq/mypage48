# MyPage48 Deployment Guide

Follow this guide to deploy MyPage48 on a single Linux VPS with full security and automation.

---

## 0. Quick Setup (Automated - Recommended)

If you are starting on a fresh Ubuntu VPS, you can automate sections 2 and 3 using our setup script:

```bash
# Download and run the setup script
curl -fsSL https://raw.githubusercontent.com/Shiyinq/mypage48/main/scripts/setup-server.sh | bash
```
This script will handle system updates, Docker installation, Firewall configuration, Swap file creation, and interactive `.env` setup.

---

## 1. DNS & Cloudflare Setup

Before setting up the server, configure your domain in Cloudflare:

1.  **Add Site**: Add your domain (e.g., `mypage48.com`) to Cloudflare.
2.  **DNS Records**: Add **A Records** pointing to your VPS IP for these 4 hostnames:
    - `mypage48.com` (Main App)
    - `api` (Backend API)
    - `analytics` (Umami Dashboard)
    - `storage` (MinIO Console)
3.  **Proxy Status**: Ensure the cloud icon is **Orange** (Proxied) for all records.
4.  **SSL/TLS**: Set mode to **Full (Strict)**.

---

## 2. Server Preparation

Connect to your VPS and install Docker:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install UFW (Firewall)
sudo apt install ufw -y

# ALLOW SSH (Crucial!)
sudo ufw allow ssh

# ALLOW Traffic ONLY from Cloudflare
# List found at: https://www.cloudflare.com/ips/
for ip in $(curl -s https://www.cloudflare.com/ips-v4); do sudo ufw allow from $ip to any port 80; done
for ip in $(curl -s https://www.cloudflare.com/ips-v4); do sudo ufw allow from $ip to any port 443; done

# Enable Firewall
sudo ufw enable
```

### 2.1 Memory Management (Optional but Recommended)
If your VPS has less than 4GB RAM, the frontend build process might crash with a `SIGABRT` error. It is highly recommended to create a **Swap File**:

```bash
# Disable existing swap (if any)
sudo swapoff -a

# Create a 2GB swap file
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make it permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Verify swap status
free -h
```

If you still encounter `JavaScript heap out of memory`, ensure your `frontend/Dockerfile` has the following line for the build stage:
```dockerfile
RUN NODE_OPTIONS="--max-old-space-size=1536" npm run build
```

---

## 3. Application Setup

1.  **Clone Repo**: `git clone <your-repo-url> && cd mypage48`
2.  **Create Folders & Permissions**:
    ```bash
    mkdir -p logs/backend logs/nginx certbot/conf certbot/www
    sudo chown -R $USER:$USER logs/
    ```
3.  **Setup Environment**:
    ```bash
    cp .env.production.example .env
    nano .env
    ```
    *Fill in all the secrets, passwords, and your actual domain name.*

3.  **Launch**:
    ```bash
    docker compose -f docker-compose.prod.yml up -d
    ```

---

## 4. SSL Certificates (Cloudflare Origin CA)

We are using Cloudflare Proxy, so we use **Cloudflare Origin Certificates** for 15 years of valid SSL.

1.  **Generate Certificate**:
    - Go to Cloudflare Dashboard -> **SSL/TLS** -> **Origin Server**.
    - Click **Create Certificate**.
    - Keep defaults (RSA 2048, 15 years) and click **Create**.
2.  **Save to VPS**:
    - Copy the **Origin Certificate** and save it to: `certbot/conf/live/mypage48.com/fullchain.pem`
    - Copy the **Private Key** and save it to: `certbot/conf/live/mypage48.com/privkey.pem`
3.  **Active SSL Mode**:
    - In Cloudflare, set SSL/TLS mode to **Full (Strict)**.
4.  **Apply to Nginx**:
    ```bash
    docker exec mypage48-nginx nginx -s reload
    ```

---

## 5. Secure Database Access (MongoDB Compass)

To view your data safely from your laptop:

1.  Open **MongoDB Compass**.
2.  Set Connection String: `mongodb://admin:secret@localhost:27017`
3.  Go to **More Options** -> **SSH Tunnel**.
4.  SSH Host: `Your Server IP`
5.  SSH Username: `Your VPS Username` (e.g. root/ubuntu)
6.  SSH Key: `Path to your .pem or .id_rsa file`

---

## 6. Post-Setup Checklist

1.  **Umami**: Go to `https://analytics.yourdomain.com`. Login with `admin` / `umami`. **Change password immediately!** Create a website, copy the `ID`, and put it into your `.env`. Rebuild frontend: `docker compose build frontend && docker compose up -d`.
2.  **MinIO**: Go to `https://storage.yourdomain.com`. Create a bucket named `mypage48-images` and set access to **Public** (or use our proxy).
3.  **Scraper**: Check `docker logs mypage48-scraper-cron` to ensure it's waiting for its midnight run.

---

## 7. Maintenance

Since we use Cloudflare Origin Certificates (15 years) and a Swap File, maintenance is minimal:

1.  **Logs**: Check logs in `./logs/` if anything goes wrong.
2.  **Backups**: Regularly backup your `mongodb_data` and `minio_data` volumes.
3.  **Updates**: To update the app, run `git pull` followed by `docker compose -f docker-compose.prod.yml up -d --build`.

---

## 8. Troubleshooting

### 8.1 Nginx Management & Debugging
- **Test Config**: `docker exec mypage48-nginx nginx -t` (Check for syntax errors).
- **Hot Reload**: `docker exec mypage48-nginx nginx -s reload` (Apply changes without downtime).
- **Verify Active Config**: `docker exec mypage48-nginx nginx -T` (See what's actually running).
- **Live Logs**: `docker logs -f mypage48-nginx` (See real-time traffic and errors).
- **Force Refresh**: `docker compose -f docker-compose.prod.yml up -d --force-recreate nginx` (Use this if `reload` doesn't pick up file changes).

### 8.2 502 Bad Gateway (Too Big Header)
If you see 502 in the browser and Nginx logs show `upstream sent too big header`:
- **Cause**: The frontend (SvelteKit) is sending large headers/cookies that exceed Nginx's default buffer.
- **Fix**: Increase `proxy_buffer_size`, `proxy_buffers`, and `large_client_header_buffers` to `512k` or `1m` inside the `server` block in `nginx/default.conf`.

### 8.3 Backend "Unhealthy" (503)
If `docker ps` shows the backend as unhealthy:
- **Log Check**: `docker logs mypage48-backend --tail 100` or `docker exec mypage48-backend cat /var/log/mypage48/error.log`.
- **MinIO Connection**: Ensure `MINIO_ENDPOINT=minio:9000` and `MINIO_SECURE=false` in `.env` for internal communication.
- **Database Connection**: Ensure MongoDB is healthy and the connection string uses the hostname `mongodb`.
