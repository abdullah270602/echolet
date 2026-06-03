"""
Demo calendar for the landing-page clinic.

Gives the demo receptionist a believable diary: opening hours come from the clinic
config, roughly half the slots are already taken (seeded by date, so every caller sees
the same diary that day), and bookings made during a call hold for that call only.
Nothing is stored. Real businesses don't get these tools until a calendar integration
exists; their agent tells callers the front desk will confirm.
"""

from __future__ import annotations

import hashlib
import re
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

SLOT_MINUTES = 30
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

CALENDAR_PROMPT = """
<calendar>
For this call you CAN see and book the clinic's calendar, using two tools:
- check_availability(day, service, part_of_day): a few open start times for a day
  ("today", "tomorrow", a weekday, or a date). Pass the service, and morning or
  afternoon if the caller said one.
- book_appointment(day, time, service, caller_name): books the slot. It is final.
This replaces any earlier instruction saying you can't see the calendar or that the front
desk will confirm. Before you check the calendar, say a quick "One sec, let me check."
Offer two or three open times, not the whole list. Book exactly the time the caller
chose: "the first one" or "the earliest" means the first of the times you just offered,
in the order you said them. Never book a time you didn't offer or they didn't say. Book
as soon as you have their name, the service and the chosen time, then tell them in one
sentence that they're booked and a confirmation text is on its way.
</calendar>
"""


class DemoCalendar:
    def __init__(self, config: dict, now: datetime | None = None):
        hours = config.get("conversation", {}).get("business_hours", {})
        try:
            self.tz = ZoneInfo(hours.get("timezone") or "UTC")
        except Exception:
            self.tz = ZoneInfo("UTC")
        self.now = now or datetime.now(self.tz)
        self.schedule = {
            d["day"].lower(): (d.get("open"), d.get("close")) for d in hours.get("schedule", [])
        }
        self.durations = {
            s["name"].lower(): s.get("duration_minutes") or SLOT_MINUTES for s in config.get("services", [])
        }
        self.booked_here: set[tuple[date, time]] = set()
        self.bookings: list[dict] = []
        self.business = config.get("agent", {}).get("business_name", "The clinic")

    # --- days -----------------------------------------------------------------------
    def resolve_day(self, text: str) -> date | None:
        """'today', 'tomorrow', a weekday name (next occurrence), or YYYY-MM-DD."""
        t = text.strip().lower()
        today = self.now.date()
        if t in ("today", "now"):
            return today
        if t == "tomorrow":
            return today + timedelta(days=1)
        for i, name in enumerate(DAYS):
            if name in t or t == name[:3]:
                ahead = (i - today.weekday()) % 7
                if "next" in t and ahead == 0:
                    ahead = 7
                return today + timedelta(days=ahead)
        try:
            return date.fromisoformat(t)
        except ValueError:
            return None

    # --- slots ------------------------------------------------------------------------
    def _hours(self, day: date) -> tuple[time, time] | None:
        open_, close = self.schedule.get(DAYS[day.weekday()], (None, None))
        if not open_ or not close:
            return None
        return time.fromisoformat(open_), time.fromisoformat(close)

    def _taken_in_diary(self, day: date, start: time) -> bool:
        # Deterministic per date and time: the same diary for everyone that day.
        h = hashlib.sha256(f"brightside:{day.isoformat()}:{start.isoformat()}".encode()).digest()
        return h[0] < 120  # about 47% of slots already booked

    def open_slots(self, day: date) -> list[time]:
        hours = self._hours(day)
        if not hours:
            return []
        start, end = (datetime.combine(day, h) for h in hours)
        earliest = self.now.replace(tzinfo=None) + timedelta(hours=1)  # no slots in the next hour
        slots = []
        while start + timedelta(minutes=SLOT_MINUTES) <= end:
            t = start.time()
            if start >= earliest and not self._taken_in_diary(day, t) and (day, t) not in self.booked_here:
                slots.append(t)
            start += timedelta(minutes=SLOT_MINUTES)
        return slots

    def minutes_for(self, service: str) -> int:
        return next((m for name, m in self.durations.items() if name in service.lower()), SLOT_MINUTES)

    @staticmethod
    def _needed(day: date, start: time, minutes: int) -> list[time]:
        """Every half-hour slot a service starting at `start` occupies."""
        s = datetime.combine(day, start)
        return [(s + timedelta(minutes=i)).time() for i in range(0, max(minutes, SLOT_MINUTES), SLOT_MINUTES)]

    def starts_for(self, day: date, minutes: int) -> list[time]:
        """Start times where the whole service fits (a 45-minute cleaning needs two free slots)."""
        free = set(self.open_slots(day))
        return [t for t in self.open_slots(day) if all(n in free for n in self._needed(day, t, minutes))]

    # --- tool bodies (plain strings the model reads) ---------------------------------
    def latest(self) -> dict | None:
        """The last booking made on this call, with the confirmation text the caller gets."""
        if not self.bookings:
            return None
        b = self.bookings[-1]
        text = (
            f"{self.business}: you're booked for {b['service'].lower()} on {b['when']}. "
            "Reply C to cancel or R to reschedule."
        )
        return {"booked": f"{b['service']}, {b['when']}", "text": text}

    def check(self, day_text: str, service: str = "", part_of_day: str = "") -> str:
        day = self.resolve_day(day_text)
        if not day:
            return f"Couldn't understand the day '{day_text}'. Ask the caller which day they mean."
        if day < self.now.date() or day > self.now.date() + timedelta(days=21):
            return "Only the next three weeks can be booked."
        label = day.strftime("%A %B %d").replace(" 0", " ")
        if not self._hours(day):
            return f"The clinic is closed on {label}."
        slots = self.starts_for(day, self.minutes_for(service)) if service else self.open_slots(day)
        part = part_of_day.strip().lower()
        if part.startswith("morn"):
            slots = [t for t in slots if t < time(12)]
        elif part.startswith(("after", "even")):
            slots = [t for t in slots if t >= time(12)]
        if not slots:
            return f"Nothing open on {label}{' in the ' + part if part else ''}."
        # A short, spread-out choice reads well on the phone; any open time can still be booked.
        shown = slots if len(slots) <= 3 else [slots[0], slots[len(slots) // 2], slots[-1]]
        more = f" ({len(slots) - len(shown)} more open times)" if len(slots) > len(shown) else ""
        return f"Some open times on {label} ({day.isoformat()}): " + ", ".join(_fmt(t) for t in shown) + more

    def book(self, day_text: str, time_text: str, service: str, caller_name: str) -> str:
        day = self.resolve_day(day_text)
        when = _parse_time(time_text)
        if not day or not when:
            return "Need a clear day and time to book. Ask the caller to confirm them."
        if not caller_name.strip():
            return "Ask for the caller's name before booking."
        minutes = self.minutes_for(service)
        if when not in self.starts_for(day, minutes):
            alternatives = ", ".join(_fmt(t) for t in self.starts_for(day, minutes)[:3]) or "none that day"
            return f"{_fmt(when)} on {day.isoformat()} is not available for that. Open times: {alternatives}."
        for t in self._needed(day, when, minutes):
            self.booked_here.add((day, t))
        label = day.strftime("%A %B %d").replace(" 0", " ")
        self.bookings.append({"service": service, "name": caller_name.strip(), "when": f"{label} at {_fmt(when)}"})
        return f"Booked: {service} for {caller_name.strip()} on {label} at {_fmt(when)}. A confirmation text is sent."


def _fmt(t: time) -> str:
    return t.strftime("%I:%M %p").lstrip("0").replace(":00", "")


def _parse_time(text: str) -> time | None:
    m = re.match(r"^\s*(\d{1,2})(?::(\d{2}))?\s*([ap])?\.?\s*m?\.?\s*$", text.strip().lower())
    if not m:
        return None
    hour, minute, ampm = int(m.group(1)), int(m.group(2) or 0), m.group(3)
    if ampm == "p" and hour < 12:
        hour += 12
    if ampm == "a" and hour == 12:
        hour = 0
    if ampm is None and 1 <= hour <= 6:
        hour += 12  # "at 3" on a dental phone line means 3 pm
    if not (0 <= hour < 24 and minute in (0, 30)):
        return None
    return time(hour, minute)


def calendar_tools(cal: DemoCalendar) -> list:
    """LiveKit function tools bound to one call's calendar."""
    from livekit.agents import function_tool

    @function_tool()
    async def check_availability(day: str, service: str = "", part_of_day: str = "") -> str:
        """Check open appointment times.

        day: 'today', 'tomorrow', a weekday name, or YYYY-MM-DD.
        service: the service wanted, if known, so only times it fits in are returned.
        part_of_day: 'morning' or 'afternoon' if the caller said one.
        """
        return cal.check(day, service, part_of_day)

    @function_tool()
    async def book_appointment(day: str, time: str, service: str, caller_name: str) -> str:
        """Book an appointment once the caller has chosen an open time.

        day: 'tomorrow', a weekday name, or YYYY-MM-DD. time: e.g. '2:30 pm' or '14:30'.
        service: the service name. caller_name: the caller's name.
        """
        return cal.book(day, time, service, caller_name)

    return [check_availability, book_appointment]
