from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from recorder.src.ytpublic.policy import Decision, evaluate_video

UTC = timezone.utc
NOW = datetime(2026, 11, 19, 22, 10, tzinfo=UTC)
TITLE = "LIVE IDN Erine JKT48 | Senin, 16 November 2026 21:10 WIB"


def video(title=TITLE, privacy="private", **status):
    return {
        "id": "test-video",
        "snippet": {"title": title},
        "status": {"privacyStatus": privacy, **status},
    }


@pytest.mark.parametrize(
    "offset,action,reason",
    [
        (-1, "wait", "idn_delay"),
        (0, "eligible", "idn_ready"),
        (1, "eligible", "idn_ready"),
    ],
)
def test_default_deadline_boundary(offset, action, reason):
    result = evaluate_video(video(), NOW + timedelta(microseconds=offset))
    assert result == Decision(
        action, reason, "idn", datetime(2026, 11, 16, 14, 10, tzinfo=UTC), NOW
    )


def test_base_alone_is_insufficient_and_zero_buffer_is_explicit():
    at_72 = NOW - timedelta(hours=8)
    assert evaluate_video(video(), at_72).action == "wait"
    assert evaluate_video(video(), at_72, buffer_hours=0).action == "eligible"
    assert evaluate_video(video(), NOW, base_delay_hours=73).action == "wait"
    assert evaluate_video(video(), NOW - timedelta(days=20)).action == "wait"


@pytest.mark.parametrize(
    "title,start",
    [
        (
            "LIVE IDN A JKT48 | Kamis, 29 Februari 2024 00:15 WIB",
            datetime(2024, 2, 28, 17, 15, tzinfo=UTC),
        ),
        (
            "LIVE IDN A JKT48 | Jumat, 1 Januari 2027 00:00 WIB",
            datetime(2026, 12, 31, 17, tzinfo=UTC),
        ),
        (
            "LIVE IDN A JKT48 | Minggu, 1 Maret 2026 00:00 WIB",
            datetime(2026, 2, 28, 17, tzinfo=UTC),
        ),
        (
            "LIVE IDN A JKT48 | Sabtu, 1 Januari 2000 00:00 WIB",
            datetime(1999, 12, 31, 17, tzinfo=UTC),
        ),
        (
            "LIVE IDN A JKT48 | Jumat, 1 Januari 2100 00:00 WIB",
            datetime(2099, 12, 31, 17, tzinfo=UTC),
        ),
    ],
)
def test_wib_calendar_conversion(title, start):
    result = evaluate_video(video(title), NOW)
    assert result.start_at == start
    assert result.eligible_at == start + timedelta(hours=80)
    assert result.start_at.tzinfo is UTC


@pytest.mark.parametrize(
    "zone", ["UTC", "Asia/Jakarta", "America/New_York", "Europe/Berlin"]
)
def test_dst_independent_comparison(zone):
    title = "LIVE IDN A JKT48 | Jumat, 6 Maret 2026 21:00 WIB"
    deadline = datetime(2026, 3, 9, 22, tzinfo=UTC)
    local = deadline.astimezone(ZoneInfo(zone))
    result = evaluate_video(video(title), local)
    assert result.action == "eligible"
    assert result.eligible_at == deadline
    assert evaluate_video(video(title), local - timedelta(seconds=1)).action == "wait"


def test_whitespace_casefold_and_member_text():
    title = " \tLiVe  IdN  Erine Putri\n JKT48 | sENIN, 16 NOVEMBER 2026 21:10 wIb "
    assert evaluate_video(video(title), NOW) == evaluate_video(video(), NOW)


@pytest.mark.parametrize(
    "title",
    [
        "LIVE SHOWROOM A JKT48",
        "SHOWROOM",
        "A (showroom) recording",
        "anything SHOWROOM not-a-date 99 November 0000 25:99 UTC",
        "\nShOwRoOm\t",
        "Straße SHOWROOM",
        "recording SHOWROOM",
    ],
)
def test_showroom_immediate_without_date(title):
    assert evaluate_video(video(title), NOW) == Decision(
        "eligible", "showroom_immediate", "showroom"
    )


@pytest.mark.parametrize(
    "title", ["MYSHOWROOM", "SHOWROOMISH", "x_SHOWROOM", "IDNSHOWROOM"]
)
def test_showroom_substrings_do_not_qualify(title):
    assert evaluate_video(video(title), NOW).action == "skip"


@pytest.mark.parametrize(
    "title",
    [
        "LIVE IDN JKT48 | Minggu, 15 November 2026 18:44 WIB",
        "LIVE IDN JKT48 Pertaruhan Cinta | Minggu, 15 November 2026 18:44 WIB",
        " live\tIDN  jKt48 SHOWROOM Special | invalid ",
        "LIVE IDN JKT48: event",
        "LIVE IDN JKT48",
        "IDN SHOWROOM",
        "LIVE IDN Erine JKT48 SHOWROOM | invalid",
        "SHOWROOM and (idn)",
    ],
)
@pytest.mark.parametrize("privacy", ["private", "public", "unlisted", "unknown", None])
def test_official_and_mixed_never_eligible_in_any_status(title, privacy):
    result = evaluate_video(video(title, privacy), NOW)
    assert result.action == "skip"
    if privacy == "private":
        assert result.reason == (
            "official_idn"
            if "live" in title.casefold() and "erine" not in title.casefold()
            else "mixed_platforms"
        )


def test_official_prefix_boundary():
    assert (
        evaluate_video(video("LIVE IDN JKT480 SHOWROOM"), NOW).reason
        == "mixed_platforms"
    )
    assert (
        evaluate_video(video("LIVE IDN JKT480 | invalid"), NOW).reason
        == "invalid_idn_title"
    )


@pytest.mark.parametrize("title", [TITLE, "SHOWROOM", "unknown"])
@pytest.mark.parametrize(
    "privacy,reason",
    [
        ("public", "public"),
        ("unlisted", "unlisted"),
        (None, "unknown_status"),
        ("PRIVATE", "unknown_status"),
        ([], "unknown_status"),
    ],
)
def test_status_precedence(title, privacy, reason):
    assert (
        evaluate_video(video(title, privacy, publishAt="scheduled"), NOW).reason
        == reason
    )


def test_exclusion_priority():
    item = video("LIVE IDN JKT48 SHOWROOM", "unlisted", publishAt="scheduled")
    assert (
        evaluate_video(
            item, NOW, already_published=True, excluded_ids=["test-video"]
        ).reason
        == "already_published"
    )
    assert (
        evaluate_video(item, NOW, excluded_ids=["test-video"]).reason == "excluded_id"
    )
    assert evaluate_video(item, NOW).reason == "unlisted"
    item["status"]["privacyStatus"] = "private"
    assert evaluate_video(item, NOW).reason == "scheduled"


@pytest.mark.parametrize("publish_at", ["2026-01-01T00:00:00Z", "malformed", " "])
def test_preserve_any_nonempty_schedule(publish_at):
    assert (
        evaluate_video(video("SHOWROOM", publishAt=publish_at), NOW).reason
        == "scheduled"
    )


@pytest.mark.parametrize("publish_at", [None, ""])
def test_empty_schedule(publish_at):
    assert (
        evaluate_video(video("SHOWROOM", publishAt=publish_at), NOW).action
        == "eligible"
    )


@pytest.mark.parametrize(
    "title,reason",
    [
        (None, "invalid_title"),
        (123, "invalid_title"),
        ({}, "invalid_title"),
        ([], "invalid_title"),
        (" \n ", "invalid_title"),
        ("other", "unsupported_title"),
        (TITLE.replace("Senin", "Selasa"), "weekday_mismatch"),
        (TITLE.replace("Senin", "Monday"), "weekday_mismatch"),
        (TITLE.replace("November", "Nov"), "invalid_idn_date"),
        (TITLE.replace("16 November", "31 November"), "invalid_idn_date"),
        (TITLE.replace("2026", "1999"), "invalid_idn_date"),
        (TITLE.replace("2026", "2101"), "invalid_idn_date"),
        (TITLE.replace("21:10", "24:00"), "invalid_idn_date"),
        (TITLE.replace("21:10", "21:60"), "invalid_idn_date"),
        (TITLE.replace("16 November 2026", "29 Februari 2025"), "invalid_idn_date"),
        (TITLE.replace(" WIB", ""), "invalid_idn_title"),
        (TITLE.replace("WIB", "UTC"), "invalid_idn_title"),
        (TITLE.replace("Erine ", ""), "official_idn"),
        (TITLE.replace("Erine", "A | B"), "invalid_idn_title"),
        (TITLE + " | another date", "invalid_idn_title"),
        (TITLE + " extra", "invalid_idn_title"),
        (TITLE.replace(" | ", " - "), "invalid_idn_title"),
        (TITLE.replace("21:10", "1:10"), "invalid_idn_title"),
        (TITLE.replace("Erine", ""), "official_idn"),
    ],
)
def test_fail_closed(title, reason):
    result = evaluate_video(video(title), NOW)
    assert result.action == "skip"
    assert result.reason == reason
    assert result.start_at is result.eligible_at is None


@pytest.mark.parametrize("item", [{}, {"status": None}, {"status": []}])
def test_missing_status(item):
    assert evaluate_video(item, NOW).reason == "unknown_status"


@pytest.mark.parametrize("snippet", [None, [], {}, {"title": False}])
def test_missing_or_invalid_snippet(snippet):
    item = video()
    item["snippet"] = snippet
    assert evaluate_video(item, NOW).reason == "invalid_title"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"base_delay_hours": 71.99},
        {"buffer_hours": -0.01},
        {"base_delay_hours": float("nan")},
        {"buffer_hours": float("inf")},
        {"base_delay_hours": "72"},
        {"buffer_hours": None},
        {"base_delay_hours": True},
        {"buffer_hours": 1e100},
    ],
)
def test_invalid_delay_raises_even_for_showroom(kwargs):
    with pytest.raises(ValueError):
        evaluate_video(video("SHOWROOM"), NOW, **kwargs)


def test_naive_now_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        evaluate_video(video("SHOWROOM"), NOW.replace(tzinfo=None))


def test_no_mutation_or_metadata_dependency():
    item = video()
    item["metadata"] = {"platform": "showroom", "start_at": "invalid"}
    original = repr(item)
    assert evaluate_video(item, NOW).reason == "idn_ready"
    assert repr(item) == original
