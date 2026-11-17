"""Offline title formatting and privacy regressions."""

import pytest

from recorder.src.upload.youtube_uploader import _format_title, _get_privacy_status

PREFIX = "LIVE IDN JKT48"
SUFFIX = " | Minggu, 15 November 2026 18:44 WIB"


@pytest.fixture
def meta():
    return {
        "title": "Pertaruhan Cinta - 2026/11/15",
        "member_name": "JKT48",
        "member_nickname": "JKT48",
        "platform": "idn",
        "live_type": "idnliveplus",
        "start_at": "2026-11-15T11:44:14Z",
    }


def test_exact_sample(meta):
    assert _format_title(meta) == (
        "LIVE IDN JKT48 Pertaruhan Cinta | Minggu, 15 November 2026 18:44 WIB"
    )


@pytest.mark.parametrize(
    "title,event",
    [
        ("Event - 2026-11-15", "Event"),
        ("Event | 2026/11/15", "Event"),
        ("Event — 2026/11/15", "Event"),
        ("Event - 2026/02/30", "Event - 2026/02/30"),
        ("Event - 2026/13/15", "Event - 2026/13/15"),
        ("Event - 2026/11/14", "Event - 2026/11/14"),
        ("Event - 15/11/2026", "Event - 15/11/2026"),
        ("Event - 2026/11-15", "Event - 2026/11-15"),
        ("Event - 2026/11/15 encore", "Event - 2026/11/15 encore"),
        ("Event 2026/11/15", "Event 2026/11/15"),
        ("Event-2026/11/15", "Event-2026/11/15"),
        ("Cinta - Part-2 - 2026/11/15", "Cinta - Part-2"),
        ("<Event>\x00\nEncore - 2026/11/15", "Event Encore"),
    ],
)
def test_conservative_event_cleaning(meta, title, event):
    meta["title"] = title
    assert _format_title(meta) == f"{PREFIX} {event}{SUFFIX}"


@pytest.mark.parametrize(
    "title", [None, 123, False, [], {}, "", "  \n", "<>", "2026/11/15"]
)
def test_empty_or_nonstring_event_falls_back(meta, title):
    meta["title"] = title
    assert _format_title(meta) == PREFIX + SUFFIX


def test_missing_title_falls_back(meta):
    del meta["title"]
    assert _format_title(meta) == PREFIX + SUFFIX


def test_long_event_preserves_prefix_and_timestamp(meta):
    meta["title"] = "A" * 300 + " - 2026/11/15"
    title = _format_title(meta)
    budget = 100 - len(PREFIX) - len(SUFFIX) - 1
    assert title == PREFIX + " " + "A" * budget + SUFFIX
    assert len(title) == 100


def test_date_matching_uses_wib_not_utc(meta):
    meta["start_at"] = "2026-11-14T23:44:14Z"
    assert _format_title(meta) == (
        "LIVE IDN JKT48 Pertaruhan Cinta | Minggu, 15 November 2026 06:44 WIB"
    )


@pytest.mark.parametrize("start_at", ["", "not-a-date", None])
def test_unparseable_start_preserves_event_date(meta, start_at):
    meta["start_at"] = start_at
    assert _format_title(meta) == PREFIX + " Pertaruhan Cinta - 2026/11/15"


@pytest.mark.parametrize(
    "updates,prefix,privacy",
    [
        ({}, "LIVE IDN JKT48 Pertaruhan Cinta", "private"),
        ({"live_type": "public"}, "LIVE IDN JKT48", "unlisted"),
        ({"live_type": "other"}, "LIVE IDN JKT48", "private"),
        ({"platform": "showroom"}, "LIVE SHOWROOM JKT48", "private"),
        (
            {"member_name": "Member", "member_nickname": "Erine"},
            "LIVE IDN Erine JKT48",
            "public",
        ),
        (
            {"member_name": "Member", "member_nickname": "JKT48"},
            "LIVE IDN JKT48",
            "public",
        ),
        (
            {
                "platform": "showroom",
                "member_name": "Member",
                "member_nickname": "Erine",
            },
            "LIVE SHOWROOM Erine JKT48",
            "public",
        ),
    ],
)
def test_existing_titles_and_privacy(meta, updates, prefix, privacy):
    meta.update(updates)
    assert _format_title(meta) == prefix + SUFFIX
    assert _get_privacy_status(meta, "public") == privacy


@pytest.mark.parametrize("default", ["private", "unlisted", "public"])
def test_member_privacy_retains_configured_default(meta, default):
    meta.update(member_name="Member", member_nickname="Erine")
    assert _get_privacy_status(meta, default) == default


def test_official_without_nickname(meta):
    del meta["member_nickname"]
    assert _format_title(meta) == PREFIX + " Pertaruhan Cinta" + SUFFIX
    assert _get_privacy_status(meta, "public") == "private"
