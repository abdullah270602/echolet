"""Demo calendar: hours from the clinic config, a stable diary, and bookings that respect length."""

import importlib.util
import json
import os
from datetime import datetime, time
from zoneinfo import ZoneInfo

import pytest

ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..")
_spec = importlib.util.spec_from_file_location("agent_demo_calendar", os.path.join(ROOT, "agent", "demo_calendar.py"))
cal_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cal_mod)

CONFIG = json.load(open(os.path.join(ROOT, "agent", "evals", "clinic_config.json"), encoding="utf-8"))
MONDAY_9AM = datetime(2026, 5, 18, 9, 0, tzinfo=ZoneInfo("America/New_York"))


@pytest.fixture
def cal():
    return cal_mod.DemoCalendar(CONFIG, now=MONDAY_9AM)


def test_resolves_relative_days(cal):
    assert cal.resolve_day("today").isoformat() == "2026-05-18"
    assert cal.resolve_day("tomorrow").isoformat() == "2026-05-19"
    assert cal.resolve_day("Thursday").isoformat() == "2026-05-21"
    assert cal.resolve_day("next monday").isoformat() == "2026-05-25"
    assert cal.resolve_day("2026-05-22").isoformat() == "2026-05-22"
    assert cal.resolve_day("someday") is None


def test_slots_follow_opening_hours(cal):
    saturday = cal.resolve_day("saturday")
    assert all(time(9) <= t < time(13) for t in cal.open_slots(saturday))
    assert cal.open_slots(cal.resolve_day("sunday")) == []
    assert "closed" in cal.check("sunday")
    # nothing in the next hour today
    assert all(t >= time(10) for t in cal.open_slots(cal.resolve_day("today")))


def test_diary_is_stable_and_partly_booked():
    a = cal_mod.DemoCalendar(CONFIG, now=MONDAY_9AM)
    b = cal_mod.DemoCalendar(CONFIG, now=MONDAY_9AM)
    day = a.resolve_day("wednesday")
    assert a.open_slots(day) == b.open_slots(day)
    all_slots = 20  # 8:00-18:00 in 30 minute slots
    assert 0 < len(a.open_slots(day)) < all_slots


def test_booking_takes_the_slot_and_rejects_a_double_booking(cal):
    day = cal.resolve_day("tomorrow")
    first = cal.starts_for(day, cal.minutes_for("Check-up and cleaning"))[0]
    hhmm = first.strftime("%H:%M")
    assert cal.book("tomorrow", hhmm, "Check-up and cleaning", "Dana").startswith("Booked:")
    assert first not in cal.open_slots(day)
    refusal = cal.book("tomorrow", hhmm, "Check-up and cleaning", "Sam")
    assert "not available" in refusal
    # alternatives offered must themselves be bookable for that service
    for alt in cal.starts_for(day, 45)[:3]:
        assert alt.strftime("%I:%M %p").lstrip("0").replace(":00", "") in refusal


def test_long_service_needs_every_slot_free(cal):
    day = cal.resolve_day("tomorrow")
    open_ = cal.open_slots(day)
    # find an open slot whose next half hour is NOT open
    lonely = next(t for t in open_ if time(t.hour + (t.minute + 30) // 60, (t.minute + 30) % 60) not in open_)
    assert "not available" in cal.book("tomorrow", lonely.strftime("%H:%M"), "Teeth whitening", "Dana")


def test_needs_name_and_clear_time(cal):
    assert "name" in cal.book("tomorrow", "2:00 pm", "Check-up and cleaning", " ")
    assert "clear day and time" in cal.book("tomorrow", "around lunch", "Check-up and cleaning", "Dana")


@pytest.mark.parametrize("text,expected", [
    ("2:30 pm", time(14, 30)), ("2pm", time(14)), ("14:30", time(14, 30)),
    ("9 am", time(9)), ("3", time(15)), ("12 pm", time(12)), ("2:15 pm", None),
])
def test_time_parsing(text, expected):
    assert cal_mod._parse_time(text) == expected


def test_booking_produces_a_confirmation_text(cal):
    assert cal.latest() is None
    day = cal.resolve_day("tomorrow")
    start = cal.starts_for(day, 60)[0]
    cal.book("tomorrow", start.strftime("%H:%M"), "Teeth whitening", "Dana")
    latest = cal.latest()
    assert latest["booked"].startswith("Teeth whitening, Tuesday May 19")
    assert latest["text"].startswith("Brightside Dental: you're booked for teeth whitening")
    assert "Reply C to cancel" in latest["text"]


def test_check_by_service_only_offers_times_it_fits(cal):
    day = cal.resolve_day("tomorrow")
    text = cal.check("tomorrow", "Teeth whitening")
    for t in cal.starts_for(day, 60):
        assert cal_mod._fmt(t) in text
    lonely = [t for t in cal.open_slots(day) if t not in cal.starts_for(day, 60)]
    for t in lonely:
        assert f" {cal_mod._fmt(t)}," not in f" {text.split(': ', 1)[1]},"
