import asyncio
import datetime

import httpx

from src.config import config
from src.database import database_instance
from src.health.repository import HealthRepository
from src.logging_config import create_logger
from src.utils import fernet_decrypt_value

logger = create_logger("health_monitor", __name__)


DOWN_MESSAGES = {
    "all": "Mohon maaf, sistem notifikasi live, perekaman, upload rekaman, dan info terkait JKT48 sedang mengalami kendala. Seluruh notifikasi mungkin mengalami delay atau tidak muncul, dan live member sementara waktu tidak terekam.",
    "record": "Mohon maaf, sistem notifikasi live dan perekaman sedang mengalami kendala. Notifikasi live mungkin mengalami delay atau tidak muncul, dan live member sementara waktu tidak terekam.",
    "upload": "Mohon maaf, sistem upload rekaman live sedang mengalami kendala. Notifikasi end-live dan proses upload ke YouTube akan mengalami delay.",
    "theater": "Mohon maaf, sistem notifikasi info JKT48 (berita, jadwal, dll) sedang mengalami kendala. Notifikasi mungkin akan mengalami delay atau tidak muncul sama sekali.",
}

UP_MESSAGES = {
    "all": "Sistem notifikasi live, perekaman, upload rekaman, dan info JKT48 telah kembali beroperasi dengan normal. Seluruh notifikasi, proses perekaman, dan upload akan berjalan seperti biasa.",
    "record": "Sistem notifikasi live dan perekaman telah kembali beroperasi dengan normal. Notifikasi live dan proses perekaman sudah aktif kembali.",
    "upload": "Sistem upload rekaman live telah kembali beroperasi dengan normal. Notifikasi end-live dan antrean upload ke YouTube akan segera dilanjutkan.",
    "theater": "Sistem notifikasi info JKT48 (berita, jadwal, dll) telah kembali beroperasi dengan normal. Notifikasi info dan jadwal terbaru sudah aktif kembali.",
}


async def monitor_recorder_heartbeat():
    """Background task to monitor recorder heartbeats and send Telegram alerts if down."""
    health_repo = HealthRepository(database_instance.database)

    while True:
        try:
            heartbeats = await health_repo.get_all_heartbeats()
            now = datetime.datetime.now(datetime.timezone.utc)

            for hb in heartbeats:
                updated_at = hb.get("updated_at")
                if not updated_at:
                    continue

                # Ensure updated_at is UTC aware
                if updated_at.tzinfo is None:
                    updated_at = updated_at.replace(tzinfo=datetime.timezone.utc)

                mode = hb.get("mode", "unknown")
                is_down = hb.get("is_down", False)
                encrypted_bot_token = hb.get("encrypted_bot_token")
                encrypted_chat_id = hb.get("encrypted_chat_id")

                diff = now - updated_at
                is_stale = (
                    diff.total_seconds() > config.recorder_heartbeat_timeout_seconds
                )

                if is_stale and not is_down:
                    # Recorder is DOWN
                    logger.warning(
                        f"Recorder (mode: {mode}) is DOWN. Last seen: {updated_at}"
                    )
                    msg_text = DOWN_MESSAGES.get(
                        mode, f"Recorder (Mode: {mode}) is DOWN."
                    )
                    await _send_telegram_alert(
                        encrypted_bot_token,
                        encrypted_chat_id,
                        f"🔴 <b>Monitoring Alert</b>\n\n{msg_text}\n\n~ <i>MyPage48</i> ~",
                    )
                    await health_repo.mark_as_down(hb["_id"])

                elif not is_stale and is_down:
                    # Recorder is UP again
                    logger.info(f"Recorder (mode: {mode}) is UP again.")
                    msg_text = UP_MESSAGES.get(mode, f"Recorder (Mode: {mode}) is UP.")
                    await _send_telegram_alert(
                        encrypted_bot_token,
                        encrypted_chat_id,
                        f"🟢 <b>Monitoring Alert</b>\n\n{msg_text}\n\n~ <i>MyPage48</i> ~",
                    )
                    await health_repo.mark_as_up(hb["_id"])

        except Exception as e:
            logger.error(f"Error in monitor_recorder_heartbeat: {e}")

        await asyncio.sleep(60)


async def _send_telegram_alert(
    encrypted_bot_token: str, encrypted_chat_id: str, message: str
):
    if not encrypted_bot_token or not encrypted_chat_id:
        return

    bot_token = fernet_decrypt_value(encrypted_bot_token)
    chat_id = fernet_decrypt_value(encrypted_chat_id)

    if not bot_token or not chat_id:
        return

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            tg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            await client.post(
                tg_url,
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
            )
    except Exception as e:
        logger.error(f"Failed to send Telegram alert: {e}")
