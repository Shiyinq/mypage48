# Liverecorder

Auto-record live stream video + chat from SHOWROOM and IDN Live, ready for YouTube upload.

## Prerequisites

| Tool | Minimum |
|------|---------|
| Python | 3.10+ |
| ffmpeg | 4.4+ (`ffmpeg -version`) |
| Backend | `make dev-be` running on `localhost:8000` |

## Quick Start

```bash
# 1. From repo root
source .venv/bin/activate

# 2. Install dependencies (one-time)
pip install -r recorder/requirements.txt

# 3. Run
python -m recorder.main
```

Output is in `recorder/recordings/raw/`:

```
recorder/recordings/raw/
├── idn_ayo-ngobrol-bareng-260701223500/
│   ├── ayo-ngobrol-bareng-260701223500.mp4
│   ├── ayo-ngobrol-bareng-260701223500.srt
│   ├── ayo-ngobrol-bareng-260701223500.json
│   ├── ayo-ngobrol-bareng-260701223500.jpg
│   └── ayo-ngobrol-bareng-260701223500.log
└── showroom_123456-1782911092/
    ├── 123456-1782911092.mp4
    ├── 123456-1782911092.srt
    ├── 123456-1782911092.json
    ├── 123456-1782911092.jpg
    └── 123456-1782911092.log
```

> **Note**: Recording uses `.mkv` (Matroska) so the file appears immediately and grows in real-time.
> When the session ends, it is automatically remuxed to `.mp4` (H.264 + AAC, `-movflags +faststart`).

## How It Works

1. Poll `GET /api/jkt48/live` every 10 seconds
2. New live detected → start ffmpeg + chat capture
3. Live ends → stop, remux `.mkv` → `.mp4`, generate `.srt` + `.json` + thumbnail
4. Output: `.mp4` (video) + `.srt` (chat) + `.json` (metadata) + `.jpg` (thumbnail)

## Output Files

| File | Description |
|------|-------------|
| `*.mp4` | Final video (HLS → Matroska → MP4, `-c copy`, no re-encode) |
| `*.mkv` | Temporary recording file (deleted after remux) |
| `*.log` | Raw chat log (intermediate) |
| `*.srt` | Chat transcript synced to video |
| `*.json` | Metadata (member, timestamps, title, etc.) |
| `*.jpg` | Video thumbnail (captured at 30s, then replaced at 5 min) |

## Metadata JSON Format

```json
{
  "live_id": "ayo-ngobrol-bareng-260701223500",
  "platform": "idn",
  "room_id": "",
  "room_identifier": "cit-rbwoihikwwldms",
  "title": "Ayo ngobrol bareng!",
  "member_name": "Citra Ayu Pranajaya",
  "start_at": "2026-07-01T15:35:15Z",
  "recording_started_at": "2026-07-01T16:38:13Z",
  "recording_ended_at": "2026-07-01T16:41:25Z",
  "duration_seconds": 192,
  "youtube_id": null
}
```

## SRT Format

```
1
00:00:03,500 --> 00:00:03,500
user_a: hello everyone

2
00:00:12,100 --> 00:00:12,100
[GIFT] user_b: sending gift
```

This format is 100% compatible with the `ReplayChat.svelte` parser on the frontend.

## Configuration (via .env)

| Variable | Default | Description |
|----------|---------|-------------|
| `REC_API_BASE_URL` | `http://localhost:8000/api` | Backend API URL |
| `REC_POLL_INTERVAL` | `10` | Live poll interval in seconds |
| `REC_RECORDINGS_DIR` | `recorder/recordings/raw` | Output directory |
| `REC_MAX_RECORDING_HOURS` | `4` | Max recording duration |
| `REC_SHOWROOM_COMMENT_INTERVAL` | `2.0` | SHOWROOM chat poll interval |
| `REC_LOG_LEVEL` | `INFO` | Logging level |

## Platform Support

| Platform | Stream Source | Chat Method |
|----------|--------------|-------------|
| SHOWROOM | HLS via `/api/jkt48/live/showroom/{id}/streaming-url` (uses `room_id`, picks original quality) | HTTP poll `comment_log` API every 2s |
| IDN Live | HLS via `/api/jkt48/live/idn/{slug}/streaming-url` (uses `live_id`) | WebSocket IRC `wss://chat.idn.app/` |

## FAQ

**Q: No video output?**
A: Make sure the backend is running (`make dev-be`) and a member is live.

**Q: ffmpeg error?**
A: Run `ffmpeg -version` to verify installation. Minimum version 4.4.

**Q: Only chat recorded, video is empty?**
A: Check the HLS URL from the `streaming-url` endpoint. The platform may be having issues.

**Q: Want to change output directory?**
A: Set `REC_RECORDINGS_DIR` in `.env` or as an environment variable.

**Q: How to skip specific members?**
A: (Not yet implemented — currently records all active streams.)
