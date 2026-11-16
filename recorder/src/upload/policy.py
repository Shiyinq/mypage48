"""Small policies shared by local and Drive-backed YouTube scheduling."""

from .youtube_uploader import is_official_jkt48


def youtube_queue_key(config, meta, size, identity):
    ranks = config.youtube_upload_priority_ranks
    return (
        ranks.get((meta.get("member_nickname") or "").strip().casefold(), len(ranks)),
        -size,
        identity,
    )


def replay_notification_eligible(config, meta):
    return (
        not is_official_jkt48(meta)
        and str(meta.get("live_type") or "public").strip().lower() == "public"
        and config.youtube_privacy_status.lower() == "public"
    )
