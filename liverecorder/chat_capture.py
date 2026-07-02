import asyncio
import json
import os
import random
import time
import uuid

import httpx
import websockets


async def capture_showroom(
    api_base_url: str,
    room_id: str,
    log_path: str,
    jsonl_path: str,
    recording_start_time: float,
    poll_interval: float,
    stop_event,
):
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    api_base_url = api_base_url.rstrip("/")

    last_created_at: int = 0

    client = httpx.AsyncClient(timeout=10.0)
    try:
        with open(log_path, "w") as f:
            jsonl_f = open(jsonl_path, "a") if jsonl_path else None
            try:
                while not stop_event.is_set():
                    try:
                        resp = await client.get(
                            f"{api_base_url}/jkt48/live/showroom/comments",
                            params={"room_id": room_id},
                        )
                        resp.raise_for_status()
                        data = resp.json()

                        comment_log = data.get("comment_log") or []
                        for comment in reversed(comment_log):
                            created_at = comment.get("created_at", 0)
                            if created_at <= last_created_at:
                                continue
                            last_created_at = created_at

                            offset = created_at - recording_start_time
                            if offset < 0:
                                offset = time.time() - recording_start_time

                            name = comment.get("name", "Unknown")
                            text = comment.get("comment", "")
                            is_gift = _is_showroom_gift(text)

                            f.write(f"{offset:.3f}\t{name}\t{text}\t{is_gift}\n")
                            f.flush()

                            if jsonl_f:
                                jsonl_f.write(json.dumps(comment, ensure_ascii=False) + "\n")
                                jsonl_f.flush()

                    except Exception as e:
                        print(f"[showroom_chat] Error: {e}")

                    try:
                        await asyncio.wait_for(stop_event.wait(), timeout=poll_interval)
                    except asyncio.TimeoutError:
                        pass
            finally:
                if jsonl_f:
                    jsonl_f.close()
    finally:
        await client.aclose()


def _is_showroom_gift(text: str) -> bool:
    if not text:
        return True
    if text.isdigit():
        return True
    return False


async def capture_idn(
    room_identifier: str,
    log_path: str,
    jsonl_path: str,
    recording_start_time: float,
    stop_event,
):
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    with open(log_path, "w") as f:
        jsonl_f = open(jsonl_path, "a") if jsonl_path else None
        try:
            retry_delay = 1.0
            while not stop_event.is_set():
                try:
                    async with websockets.connect(
                        "wss://chat.idn.app/",
                        ping_interval=None,
                        origin="https://www.idn.app",
                        user_agent_header="Mozilla/5.0",
                    ) as ws:
                        retry_delay = 1.0

                        await ws.send(f"NICK idn-{random.randint(1, 999999)}-{int(time.time() * 1000)}\n")
                        await ws.send(f"USER {random.randint(1, 999999)}_{uuid.uuid4().hex[:8]} 0 * null\n")
                        await ws.send("CAP LS 302\n")
                        await ws.send("CAP REQ :idn.app/tags idn.app/commands idn.app/membership\n")
                        await ws.send("CAP END\n")

                        joined = False

                        async for message in ws:
                            if stop_event.is_set():
                                return

                            if message.startswith("PING"):
                                await ws.send(message.replace("PING", "PONG") + "\n")
                                continue

                            if ":Welcome" in message and not joined:
                                await ws.send(f"@label=1 JOIN #{room_identifier}\n")
                                joined = True
                                continue

                            if "PRIVMSG" not in message:
                                continue

                            offset = time.time() - recording_start_time
                            username, text, is_gift = _parse_idn_message(message)
                            if username == "" and text == "":
                                continue
                            f.write(f"{offset:.3f}\t{username}\t{text}\t{is_gift}\n")
                            f.flush()

                            if jsonl_f:
                                jsonl_f.write(message + "\n")
                                jsonl_f.flush()

                except websockets.ConnectionClosed:
                    if stop_event.is_set():
                        return
                except Exception as e:
                    print(f"[idn_chat] Connection error: {e}")

                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=retry_delay)
                except asyncio.TimeoutError:
                    pass
                retry_delay = min(retry_delay * 2, 30.0)
        finally:
            if jsonl_f:
                jsonl_f.close()


def _parse_idn_message(raw: str) -> tuple:
    username = ""
    text = ""
    is_gift = False

    tags = {}
    if raw.startswith("@"):
        space_idx = raw.find(" ")
        if space_idx != -1:
            tag_section = raw[1:space_idx]
            for t in tag_section.split(";"):
                if "=" in t:
                    key, value = t.split("=", 1)
                    tags[key] = value

    msg_idx = raw.find(" :", raw.find("PRIVMSG"))
    if msg_idx == -1:
        return username, text, is_gift

    body = raw[msg_idx + 2:]

    if body.startswith("***"):
        return "", "", False

    username = tags.get("display-name") or tags.get("idn.app/display-name") or ""

    if body.startswith("{"):
        try:
            parsed = json.loads(body)
            if parsed.get("user"):
                username = (
                    parsed["user"].get("name")
                    or parsed["user"].get("display_name")
                    or parsed["user"].get("username")
                    or username
                )

            if parsed.get("gift"):
                is_gift = True
                gift_name = parsed["gift"].get("name", "Gift")
                text = f"GIFT: {gift_name}"
            elif parsed.get("chat") and parsed["chat"].get("message"):
                text = parsed["chat"]["message"]
            elif parsed.get("letter") and parsed["letter"].get("message"):
                text = parsed["letter"]["message"]
            elif parsed.get("system") and parsed["system"].get("message"):
                text = parsed["system"]["message"]
            else:
                text = parsed.get("message") or parsed.get("text") or ""
        except json.JSONDecodeError:
            text = body
    else:
        text = body

    if not username and not text:
        return "", "", False

    return username, text, is_gift
