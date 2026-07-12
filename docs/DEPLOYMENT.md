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

To view your data safely from your laptop using SSH Tunnel (since port 27017 is blocked by firewall):

1.  Open **MongoDB Compass**.
2.  Set Connection String URI: `mongodb://YOUR_MONGO_ROOT_USERNAME:YOUR_MONGO_ROOT_PASSWORD@localhost:27017`
3.  Go to the **Proxy/SSH** tab and configure your tunnel:

    **Option A: Using SSH Key (Recommended & Required if Password Auth is disabled)**
    - Select **SSH with Identity File**
    - **SSH Hostname**: `Your Server IP`
    - **SSH Port**: `22`
    - **SSH Username**: `Your VPS Username` (e.g., ubuntu / myusername)
    - **SSH Identity File**: Select `~/.ssh/id_ed25519` (In the Mac file picker, press `Cmd+Shift+G` and type `~/.ssh` to easily find this hidden folder).
    - **SSH Passphrase**: Enter your local SSH key password (if you set one).

    **Option B: Using Password**
    - Select **SSH with Password**
    - **SSH Hostname**: `Your Server IP`
    - **SSH Port**: `22`
    - **SSH Username**: `Your VPS Username`
    - **SSH Password**: `Your VPS Password`

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

---

## 9. Auto-Deployment (CI/CD Setup)

To enable automatic updates every time you `git push origin main`, follow these steps to link GitHub with your VPS.

### 9.1 Generate Deployment Key
Run this on your laptop (or anywhere) to create a dedicated key for GitHub:
```bash
ssh-keygen -t rsa -b 4096 -f github_deploy_key
```
*Note: Press **Enter** when asked for a passphrase (leave it empty) so the process can be automated.*

### 9.2 Add Public Key to VPS
You need to tell your VPS to trust this new key:
1.  Copy the content of `github_deploy_key.pub`.
2.  Login to your VPS and run: `nano ~/.ssh/authorized_keys`.
3.  Paste the key on a **new line** at the bottom.
4.  Save and exit (**Ctrl+O, Enter, Ctrl+X**).
5.  **Set Permissions** (Required for security):
    ```bash
    chmod 700 ~/.ssh
    chmod 600 ~/.ssh/authorized_keys
    ```

### 9.3 Add Private Key to GitHub Secrets
1.  **View Private Key**: Run this on your laptop to see the content:
    ```bash
    cat github_deploy_key
    ```
2.  Go to your GitHub Repository -> **Settings** -> **Secrets and variables** -> **Actions**.
3.  Add a **New repository secret** named `SSH_PRIVATE_KEY`.
4.  Paste the **entire content** (including the BEGIN/END lines).
5.  Add other required secrets: `REMOTE_HOST` (IP), `REMOTE_USER` (e.g. `myremote`), and `REMOTE_TARGET` (e.g. `/home/myremote/mypage48`).

Now, every push to `main` will trigger a fresh deployment!

---

## 10. Troubleshooting UFW & Docker (Firewall)

This project uses `ufw-docker` to solve the classic Docker firewall bypass issue. By default, we lock down Docker exposed ports (80, 443) to ONLY accept traffic from Cloudflare IPs.

If you ever encounter "502 Bad Gateway" internally or your website becomes completely unreachable from Cloudflare, the firewall might be misconfigured.

### How to verify the problem:
1. **Check if ports are externally open**: From your personal laptop, run `nmap -Pn YOUR_VPS_IP`. If 80/443 are "open" instead of "filtered" or "closed", your Docker is bypassing UFW.
2. **Check UFW Rules**: Run `sudo ufw status numbered` in the VPS.
   - You should see rules labeled `ALLOW FWD` for Cloudflare IPs.
   - If you see `ALLOW IN Anywhere` for port 80 or 443, **DELETE IT** (`sudo ufw delete [number]`), as it leaks your IP to attackers.

### Rollback / Emergency Fix
If `ufw-docker` accidentally blocks internal container communication (e.g. Nginx cannot reach the backend) or Cloudflare cannot connect:

1. **Clear ufw-docker rules**:
   ```bash
   sudo ufw-docker clear
   ```
2. **Temporarily Disable UFW** (Optional, if still completely broken):
   ```bash
   sudo ufw disable
   ```
3. **Restart Docker** (Crucial step to reset internal iptables):
   ```bash
   sudo systemctl restart docker
   ```
4. **Re-apply Securely**: Once everything is back online and tested, you can safely re-run `bash scripts/setup-server.sh` to apply the secure patch again.

### Updating Cloudflare IPs (Routine Maintenance)
Cloudflare occasionally adds new IP ranges to their network (roughly every 1-2 years). If Cloudflare introduces a new IP and your firewall isn't updated, some legitimate visitors might get blocked because their traffic originates from that new Cloudflare edge node.

**Solution:**
If users report that the website is suddenly unreachable from certain regions, or just as a routine check every 6 months, simply refresh the firewall rules by running the setup script again:
```bash
bash scripts/setup-server.sh
```
This script will safely re-download the latest official Cloudflare IPs (`https://www.cloudflare.com/ips-v4`) and apply them to your UFW Docker rules.

---

## 11. SSH Hardening & Local Access

For maximum security against brute-force attacks, it is highly recommended to disable password authentication and use SSH Keys exclusively. You can also configure an SSH alias on your local machine for faster logins.

### 11.1 Generating a Personal SSH Key
If you haven't already, generate a modern `ed25519` SSH key on your personal computer (Mac/Linux):
```bash
ssh-keygen -t ed25519
```
*Note: Press Enter to save in the default location (`~/.ssh/id_ed25519`). You can leave the passphrase empty for seamless logins.*

**Tip: Adding or Changing a Passphrase Later**
If you initially created the key without a passphrase but later decide you want extra local security (e.g., if you share your laptop), you don't need to generate a new key. You can add a passphrase to your existing key by running:
```bash
ssh-keygen -p -f ~/.ssh/id_ed25519
```
Just press Enter for the old passphrase, then type your new secure passphrase.


### 11.2 Copying the Key to the VPS
Send your public key to the server:
```bash
ssh-copy-id -i ~/.ssh/id_ed25519.pub username@YOUR_VPS_IP
```
*After running this, it will ask for your VPS password one last time. Once successful, test it by running `ssh username@YOUR_VPS_IP` again—you should instantly log in without a password!*


### 11.3 Setting Up an SSH Alias (Optional)
To avoid typing `ssh username@IP` every time, configure an alias in your local `~/.ssh/config` file:
```bash
nano ~/.ssh/config
```
Add the following block:
```text
Host mypage48
    HostName YOUR_VPS_IP
    User YOUR_VPS_USERNAME
    IdentityFile ~/.ssh/id_ed25519
```
Now you can instantly log in from your terminal by just typing:
```bash
ssh mypage48
```

### 11.4 Disabling Password Authentication (Crucial)
Once you have verified that you can log in without a password using your SSH key, you MUST disable password authentication to prevent bots from brute-forcing your server.

Log into your VPS and run:
```bash
sudo sed -i 's/^#*PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/^PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart ssh
```
Your server is now 100% immune to SSH brute-force attacks!

### 11.4b Alternative: Defending Password Auth with Fail2Ban
If you decide to keep Password Authentication enabled for convenience or safety against lockouts, you **must** protect your server against brute-force bots using `fail2ban`. This tool will automatically ban the IP addresses of hackers who repeatedly guess the wrong password.

Log into your VPS and run these commands to install and activate it:
```bash
sudo apt update
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```
*(By default, Fail2Ban is automatically configured to monitor SSH. If an IP fails to log in 5 times within 10 minutes, they will be blocked for 10 minutes. This eliminates 99% of brute-force spam.)*

### 11.5 Emergency Access & Adding New Devices
**Q: What if I lose my laptop or my SSH key gets deleted? Am I locked out forever?**
No. You can always log into your VPS provider's website (e.g., Hostinger, DigitalOcean, AWS) and use their **Web Console / VNC** feature. This console acts like a physical monitor plugged directly into the server, bypassing SSH entirely, so it will still accept your VPS password.

**Q: How do I grant access to a new laptop?**
1. Generate a new key on the new laptop (`ssh-keygen -t ed25519`).
2. Print the public key: `cat ~/.ssh/id_ed25519.pub` and copy the text.
3. From your original laptop (or the Web Console), SSH into the server and run `nano ~/.ssh/authorized_keys`.
4. Paste the copied text onto a **new line** at the bottom, save, and exit.
5. The new laptop now has secure access!
