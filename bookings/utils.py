import os
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from google.oauth2 import service_account
from googleapiclient.discovery import build


# ---------------------------------------------
#  Google Calendar Setup
# ---------------------------------------------

SCOPES = ["https://www.googleapis.com/auth/calendar"]

creds = service_account.Credentials.from_service_account_info(
    json.loads(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")),
    scopes=SCOPES,
)

calendar_service = build("calendar", "v3", credentials=creds)
calendar_id = os.getenv("GOOGLE_CALENDAR_ID")


# ---------------------------------------------
#  Utility Functions
# ---------------------------------------------


def get_busy_times(time_min: str, time_max: str, timezone: str):
    try:
        response = (
            calendar_service.freebusy()
            .query(
                body={
                    "timeMin": time_min,
                    "timeMax": time_max,
                    "timeZone": timezone,
                    "items": [{"id": calendar_id}],
                }
            )
            .execute()
        )
        return response["calendars"][calendar_id].get("busy", [])
    except Exception as e:
        print("Error fetching busy times:", e)
        return []


def _round_up_to_next_30(dt: datetime) -> datetime:
    dt = dt.replace(second=0, microsecond=0)
    remainder = dt.minute % 30
    if remainder:
        dt += timedelta(minutes=(30 - remainder))
    return dt


def _move_to_next_open_local(
    dt_local: datetime, start_hour: int, end_hour: int
) -> datetime:
    # Skip weekends
    while dt_local.weekday() >= 5:
        dt_local = (dt_local + timedelta(days=1)).replace(
            hour=start_hour, minute=0, second=0, microsecond=0
        )

    # Before opening → snap to opening
    if dt_local.hour < start_hour or (
        dt_local.hour == start_hour and dt_local.minute < 0
    ):
        dt_local = dt_local.replace(hour=start_hour, minute=0, second=0, microsecond=0)

    # After closing → next workday opening
    if dt_local.hour > end_hour or (dt_local.hour == end_hour and dt_local.minute > 0):
        dt_local = (dt_local + timedelta(days=1)).replace(
            hour=start_hour, minute=0, second=0, microsecond=0
        )
        while dt_local.weekday() >= 5:
            dt_local = (dt_local + timedelta(days=1)).replace(
                hour=start_hour, minute=0, second=0, microsecond=0
            )

    return dt_local


def generate_available_slots(
    time_min: str, time_max: str, timezone: str, working_hours: dict
):
    """
    Generates available 30-minute slots in the clinic timezone between time_min and time_max,
    starting at "now" (rounded up), skipping weekends, and respecting working hours.
    Returns a list of {"start": ISO, "end": ISO} where ISO includes the offset of the clinic TZ.
    """
    clinic_tz = ZoneInfo(timezone)
    start_hour = working_hours["startHour"]
    end_hour = working_hours["endHour"]

    # Convert bounds (possibly UTC ISO) to aware datetimes then to clinic local
    start_utc = datetime.fromisoformat(time_min.replace("Z", "+00:00"))
    end_utc = datetime.fromisoformat(time_max.replace("Z", "+00:00"))

    cursor_local = start_utc.astimezone(clinic_tz)
    cursor_local = _round_up_to_next_30(cursor_local)
    cursor_local = _move_to_next_open_local(cursor_local, start_hour, end_hour)

    window_end_local = end_utc.astimezone(clinic_tz)

    # Busy times → parse and convert to clinic local for consistent comparison
    busy_raw = get_busy_times(time_min, time_max, timezone)
    busy_local = []
    for b in busy_raw:
        bs = datetime.fromisoformat(b["start"].replace("Z", "+00:00")).astimezone(
            clinic_tz
        )
        be = datetime.fromisoformat(b["end"].replace("Z", "+00:00")).astimezone(
            clinic_tz
        )
        busy_local.append((bs, be))

    slot = timedelta(minutes=30)
    slots = []

    while cursor_local < window_end_local:
        # Skip weekends
        if cursor_local.weekday() >= 5:
            cursor_local = (cursor_local + timedelta(days=1)).replace(
                hour=start_hour, minute=0, second=0, microsecond=0
            )
            continue

        start_local = cursor_local
        end_local = cursor_local + slot

        # If the slot spills past closing, move to next day opening
        if (end_local.hour > end_hour) or (
            end_local.hour == end_hour and end_local.minute > 0
        ):
            cursor_local = (cursor_local + timedelta(days=1)).replace(
                hour=start_hour, minute=0, second=0, microsecond=0
            )
            continue

        # Overlap check in local tz
        is_busy = any(
            start_local < b_end and end_local > b_start
            for (b_start, b_end) in busy_local
        )

        if not is_busy:
            # Keep local offset in ISO; we’ll format to HH:MM in the view
            slots.append(
                {
                    "start": start_local.isoformat(),
                    "end": end_local.isoformat(),
                }
            )

        cursor_local += slot

    return slots


def create_google_calendar_event(name: str, email: str, slot: dict):
    """
    Creates a Google Calendar event for a confirmed booking.
    Returns the created event object (includes HTML link).
    """
    try:
        event = {
            "summary": f"{name} - Demo Appointment",
            "location": "123 Demo St. AI City MA, 99999",
            "description": f"Booked by {email}",
            "start": {"dateTime": slot["start"], "timeZone": "America/Los_Angeles"},
            "end": {"dateTime": slot["end"], "timeZone": "America/Los_Angeles"},
        }

        created_event = (
            calendar_service.events()
            .insert(calendarId=calendar_id, body=event)
            .execute()
        )

        return {
            "success": True,
            "event_id": created_event.get("id"),
            "link": created_event.get("htmlLink"),
        }

    except Exception as e:
        print("Error creating calendar event:", e)
        return {"success": False, "error": str(e)}
