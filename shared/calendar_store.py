"""
CSV calendar backend.
Each agent creates a CalendarStore pointed at its own CSV file.
The agent's LangChain tools wrap methods from this class.
"""

import csv
import uuid
from datetime import date, time, datetime, timedelta
from pathlib import Path


FIELDNAMES = [
    "event_id", "date", "start_time", "end_time",
    "title", "location", "attendees", "category",
    "recurring", "notes",
]


class CalendarStore:

    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
        if not self.csv_path.exists():
            self._create_empty()

    def _create_empty(self):
        with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()

    def _read_all(self) -> list[dict]:
        with open(self.csv_path, "r", newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def _write_all(self, rows: list[dict]):
        with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows)

    def get_events(self, target_date: date) -> list[dict]:
        """Get all events for a specific date."""
        date_str = target_date.isoformat()
        return [r for r in self._read_all() if r["date"] == date_str]

    def get_events_range(self, start: date, end: date) -> list[dict]:
        """Get all events between start and end dates (inclusive)."""
        return [
            r for r in self._read_all()
            if start.isoformat() <= r["date"] <= end.isoformat()
        ]

    def is_available(self, target_date: date, start: time, end: time) -> bool:
        """Check if a time slot has no conflicts."""
        for event in self.get_events(target_date):
            evt_start = time.fromisoformat(event["start_time"])
            evt_end = time.fromisoformat(event["end_time"])
            if start < evt_end and end > evt_start:
                return False
        return True

    def get_free_slots(
        self, target_date: date, duration_minutes: int,
        day_start: time = time(9, 0), day_end: time = time(17, 0),
    ) -> list[dict]:
        """Find available slots of the given duration within the day window."""
        events = self.get_events(target_date)
        busy = sorted(
            [(time.fromisoformat(e["start_time"]), time.fromisoformat(e["end_time"]))
             for e in events],
            key=lambda x: x[0],
        )

        free = []
        cursor = datetime.combine(target_date, day_start)
        end_of_day = datetime.combine(target_date, day_end)
        duration = timedelta(minutes=duration_minutes)

        for busy_start, busy_end in busy:
            busy_start_dt = datetime.combine(target_date, busy_start)
            busy_end_dt = datetime.combine(target_date, busy_end)

            if cursor + duration <= busy_start_dt:
                free.append({
                    "date": target_date.isoformat(),
                    "start_time": cursor.time().strftime("%H:%M"),
                    "end_time": busy_start_dt.time().strftime("%H:%M"),
                })
            cursor = max(cursor, busy_end_dt)

        if cursor + duration <= end_of_day:
            free.append({
                "date": target_date.isoformat(),
                "start_time": cursor.time().strftime("%H:%M"),
                "end_time": end_of_day.time().strftime("%H:%M"),
            })

        return free

    def book_event(
        self, title: str, target_date: date, start: time, end: time,
        location: str = "", attendees: list[str] | None = None,
        category: str = "work", notes: str = "",
    ) -> dict | None:
        """Book a new event. Returns the event dict, or None if slot is taken."""
        if not self.is_available(target_date, start, end):
            return None

        event = {
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "date": target_date.isoformat(),
            "start_time": start.strftime("%H:%M"),
            "end_time": end.strftime("%H:%M"),
            "title": title,
            "location": location,
            "attendees": ";".join(attendees or []),
            "category": category,
            "recurring": "none",
            "notes": notes,
        }

        rows = self._read_all()
        rows.append(event)
        self._write_all(rows)
        return event

    def cancel_event(self, event_id: str) -> bool:
        """Remove an event by ID. Returns True if found and removed."""
        rows = self._read_all()
        filtered = [r for r in rows if r["event_id"] != event_id]
        if len(filtered) == len(rows):
            return False
        self._write_all(filtered)
        return True
