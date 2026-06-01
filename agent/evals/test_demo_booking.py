"""
The landing-page demo books for real (in the call's diary) and confirms by text.
Checks look at the calendar itself, not just at what the agent says.
"""

import pytest

from conftest import called, reply_text

pytestmark = pytest.mark.eval


def _fmt(t):
    return t.strftime("%I:%M %p").lstrip("0").replace(":00", "")


def _open_weekday(cal):
    """(weekday name, date) of the next weekday with room for a cleaning, skipping today."""
    for name in ("monday", "tuesday", "wednesday", "thursday", "friday"):
        day = cal.resolve_day(name)
        if day != cal.now.date() and len(cal.starts_for(day, 45)) >= 2:
            return name.capitalize(), day
    raise AssertionError("no open weekday in the diary")


async def test_offers_real_open_times(demo_call):
    call, cal = demo_call
    name, day = _open_weekday(cal)
    result = await call.say(f"Hi, what times do you have on {name} for a cleaning?")
    assert called(result, "check_availability"), "didn't look at the calendar"
    text = reply_text(result)
    fits = [_fmt(t) for t in cal.starts_for(day, 45)]
    assert any(t.lower() in text.lower() for t in fits), f"offered times not from the diary: {text!r}"
    await call.judge(result, "Offers two or three specific open times on the weekday the caller asked about, and asks which suits them.")


async def test_books_an_open_slot_and_confirms_by_text(demo_call):
    call, cal = demo_call
    name, day = _open_weekday(cal)
    slot = _fmt(cal.starts_for(day, 45)[0])
    await call.say(f"I'd like to book a check-up and cleaning on {name}.")
    result = await call.say(f"{slot} works. My name is Dana Reyes.")
    assert cal.bookings, f"nothing was booked: {reply_text(result)!r}"
    assert "Dana" in cal.bookings[-1]["name"]
    await call.judge(
        result,
        "Tells the caller they are booked for that time and that a confirmation text is on its "
        "way. Does not say the front desk will confirm later.",
    )


async def test_refuses_a_taken_slot_and_offers_others(demo_call):
    call, cal = demo_call
    name, day = _open_weekday(cal)
    free = set(cal.starts_for(day, 45))
    # a time inside opening hours that the diary already has booked
    from datetime import time as _t
    taken = next(
        _t(h, m) for h in range(9, 17) for m in (0, 30)
        if _t(h, m) not in free
    )
    await call.say(f"Hi, my name is Sam Okafor, I need a cleaning on {name}.")
    result = await call.say(f"Can you put me in at {_fmt(taken)}?")
    assert not cal.bookings, "booked a slot that was already taken"
    await call.judge(result, "Says that time isn't available and offers other open times.")


async def test_closed_on_sunday(demo_call):
    call, cal = demo_call
    result = await call.say("Could I come in this Sunday for a cleaning?")
    assert not cal.bookings
    await call.judge(result, "Says the clinic is closed on Sunday and offers another day.")


async def test_asks_for_a_name_before_booking(demo_call):
    call, cal = demo_call
    name, day = _open_weekday(cal)
    slot = _fmt(cal.starts_for(day, 45)[0])
    result = await call.say(f"Book me a cleaning on {name} at {slot}.")
    assert not cal.bookings, "booked without the caller's name"
    await call.judge(result, "Asks for the caller's name before booking.")
