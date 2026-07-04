def seconds_to_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def generate(chat_log_path: str, srt_path: str):
    entries = []
    with open(chat_log_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t", 3)
            if len(parts) < 4:
                continue
            offset_str, username, message, is_gift_str = parts
            try:
                offset = float(offset_str)
            except ValueError:
                continue
            is_gift = is_gift_str.strip().lower() == "true"
            entries.append((offset, username.strip(), message.strip(), is_gift))

    entries.sort(key=lambda x: x[0])

    with open(srt_path, "w") as f:
        for i, (offset, username, message, is_gift) in enumerate(entries, 1):
            ts = seconds_to_srt_time(offset)
            prefix = "[GIFT] " if is_gift else ""
            text = f"{prefix}{username}: {message}"
            f.write(f"{i}\n{ts} --> {ts}\n{text}\n\n")
