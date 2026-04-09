# MyPage48 Deployment Guide

Follow this guide to deploy MyPage48 on a single Linux VPS with full security and automation.

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

## 7. Maintenance (Automatic SSL Renewal)

Certificates expire every 3 meses. Run this to automate renewal:

```bash
# Open crontab
crontab -e

# Add this line to the end (runs every night at 3 AM)
0 3 * * * docker run --rm -v "$(pwd)/certbot/conf:/etc/letsencrypt" -v "$(pwd)/certbot/www:/var/www/certbot" certbot/certbot renew --quiet && docker exec mypage48-nginx nginx -s reload
```
