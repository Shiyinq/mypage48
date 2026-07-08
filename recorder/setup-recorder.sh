#!/bin/bash
set -e

RECORDER_DIR="$HOME/mypage48/recorder"
SERVICE_USER=$(whoami)

echo "🚀 MyPage48 Recorder Service Setup"
echo "=================================="

# Check system dependencies
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  ffmpeg is not installed. Please install it first:"
    echo "   sudo apt update && sudo apt install ffmpeg -y"
    exit 1
fi

if ! python3 -m venv -h &> /dev/null; then
    echo "⚠️  python3-venv is not installed. Please install it first:"
    echo "   sudo apt install python3-venv -y"
    exit 1
fi

# Step 1: Virtualenv
echo ""
echo "[1/5] Creating virtualenv..."
cd "$RECORDER_DIR"
python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt
playwright install chromium
sudo .venv/bin/playwright install-deps chromium

# Step 2: .env
echo "[2/5] Setting up .env..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  Edit .env first — at least set REC_API_BASE_URL:"
    echo "   nano $RECORDER_DIR/.env"
    echo "   Then run this script again."
    exit 1
fi

# Step 3: Create logs directory
echo "[3/5] Creating logs directory..."
mkdir -p logs

# Step 4: Create systemd service files
echo "[4/5] Creating systemd service files..."

sudo tee /etc/systemd/system/mypage48-record.service > /dev/null << EOF
[Unit]
Description=MyPage48 Live Recorder — Record
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$HOME/mypage48
ExecStart=$RECORDER_DIR/.venv/bin/python3 -m recorder.main --mode record
Restart=always
RestartSec=10
StandardOutput=append:$RECORDER_DIR/logs/record.log
StandardError=append:$RECORDER_DIR/logs/record.log

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/mypage48-upload.service > /dev/null << EOF
[Unit]
Description=MyPage48 Live Recorder — Upload
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$HOME/mypage48
ExecStart=$RECORDER_DIR/.venv/bin/python3 -m recorder.main --mode upload
Restart=always
RestartSec=10
StandardOutput=append:$RECORDER_DIR/logs/upload.log
StandardError=append:$RECORDER_DIR/logs/upload.log

[Install]
WantedBy=multi-user.target
EOF

# Step 5: Enable & Start
echo "[5/5] Enabling & starting services..."
sudo systemctl daemon-reload
sudo systemctl enable --now mypage48-record mypage48-upload

echo ""
echo "✅ Done!"
echo ""
echo "Check status:"
echo "  sudo systemctl status mypage48-record"
echo "  sudo systemctl status mypage48-upload"
echo ""
echo "Live logs:"
echo "  sudo journalctl -u mypage48-record -f"
