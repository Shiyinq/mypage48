"""Notification fan-out via a channel registry.

Every event is delivered to each *enabled* channel. The result returned to
callers comes from the first enabled channel in :data:`CHANNELS` order --
Telegram when it is configured, otherwise Page48 -- so the retry gates keep
working even when the primary channel is turned off. Disabled channels are
skipped entirely; when no channel is enabled the event is treated as delivered
(so pending files are not retried forever).

Adding a channel means appending one :class:`Channel` to :data:`CHANNELS` and
implementing the same ``send_*_notification`` functions on its module.
"""

import logging
from typing import Any, Callable, List, NamedTuple

from ..config import RecorderConfig
from ..models import LiveInfo
from . import page48_notifier, telegram_notifier

log = logging.getLogger("notify")


class Channel(NamedTuple):
    """A notification destination.

    ``module`` exposes the ``send_*_notification`` functions; ``is_enabled``
    says whether the channel is currently configured, so a turned-off channel is
    skipped (and never decides the result).
    """

    name: str
    module: Any
    is_enabled: Callable[[RecorderConfig], bool]


# Ordered by priority: the first *enabled* channel's result is returned.
CHANNELS: List[Channel] = [
    Channel("telegram", telegram_notifier, telegram_notifier._is_enabled),
    Channel("page48", page48_notifier, page48_notifier._enabled),
]

# Event name -> notifier function name (the same name on every channel module).
EVENT_HANDLERS = {
    "live_start": "send_live_start_notification",
    "end_live": "send_end_live_notification",
    "recap": "send_recap_end_live_notification",
    "replay": "send_replay_live_notification",
    "news": "send_news_notification",
    "schedule": "send_schedule_notification",
    "idn_live_plus": "send_idn_live_plus_notification",
    "daily_reminder": "send_daily_schedule_reminder",
    "upcoming_reminder": "send_upcoming_schedule_reminder",
    "birthday": "send_birthday_notification",
    "monthly_birthday": "send_monthly_birthday_list",
    "health": "send_health_notification",
}


async def _deliver(channel: Channel, func_name: str, payload: dict) -> bool:
    """Run one channel's handler, isolating it from the rest of the fan-out."""
    handler = getattr(channel.module, func_name, None)
    if handler is None:
        log.warning("Channel %s is missing handler %s", channel.name, func_name)
        return False
    try:
        return bool(await handler(**payload))
    except Exception:
        log.exception("Channel %s failed on %s", channel.name, func_name)
        return False


async def notify(event: str, **payload: Any) -> bool:
    """Deliver `event` to every enabled channel.

    Returns the result of the first enabled channel, so a failed delivery is
    retried by the caller while a disabled channel never blocks it. No enabled
    channel means there is nothing to deliver, so it reports success.
    """
    func_name = EVENT_HANDLERS.get(event)
    if func_name is None:
        log.error("Unknown notification event: %s", event)
        return False

    config = payload.get("config")
    result = True
    settled = False
    for channel in CHANNELS:
        if config is not None and not channel.is_enabled(config):
            continue
        channel_result = await _deliver(channel, func_name, payload)
        if not settled:
            result = channel_result
            settled = True
    return result


# Thin, typed wrappers so call sites keep their explicit, checked API. Each one
# just names its event; adding a channel never touches these.
async def send_live_start_notification(live: LiveInfo, config: RecorderConfig) -> bool:
    return await notify("live_start", live=live, config=config)


async def send_end_live_notification(config: RecorderConfig, data: dict) -> bool:
    return await notify("end_live", config=config, data=data)


async def send_recap_end_live_notification(
    live_id: str, config: RecorderConfig, folder_path: str = ""
) -> bool:
    return await notify(
        "recap", live_id=live_id, config=config, folder_path=folder_path
    )


async def send_replay_live_notification(
    live_id: str,
    youtube_title: str,
    youtube_id: str,
    config: RecorderConfig,
    folder_path: str,
) -> bool:
    return await notify(
        "replay",
        live_id=live_id,
        youtube_title=youtube_title,
        youtube_id=youtube_id,
        config=config,
        folder_path=folder_path,
    )


async def send_news_notification(news_data: dict, config: RecorderConfig) -> bool:
    return await notify("news", news_data=news_data, config=config)


async def send_schedule_notification(payload: dict, config: RecorderConfig) -> bool:
    return await notify("schedule", payload=payload, config=config)


async def send_idn_live_plus_notification(
    payload: dict, config: RecorderConfig
) -> bool:
    return await notify("idn_live_plus", payload=payload, config=config)


async def send_daily_schedule_reminder(payload: dict, config: RecorderConfig) -> bool:
    return await notify("daily_reminder", payload=payload, config=config)


async def send_upcoming_schedule_reminder(sch: dict, config: RecorderConfig) -> bool:
    return await notify("upcoming_reminder", sch=sch, config=config)


async def send_birthday_notification(member: dict, config: RecorderConfig) -> bool:
    return await notify("birthday", member=member, config=config)


async def send_monthly_birthday_list(
    month_name: str, members: list, config: RecorderConfig
) -> bool:
    return await notify(
        "monthly_birthday", month_name=month_name, members=members, config=config
    )


async def send_health_notification(payload: dict, config: RecorderConfig) -> bool:
    return await notify("health", payload=payload, config=config)
