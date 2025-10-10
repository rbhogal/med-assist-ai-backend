import os
import json
from datetime import datetime, timedelta
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
    """
    Fetches busy time ranges from the Google Calendar API.
    Returns a list of {start, end} objects.
    """
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

        busy_times = response["calendars"][calendar_id].get("busy", [])
        return busy_times

    except Exception as e:
        print("Error fetching busy times:", e)
        return []


def generate_available_slots(
    time_min: str, time_max: str, timezone: str, working_hours: dict
):
    """
    Generates available 30-minute appointment slots between two dates,
    skipping weekends and existing busy times.
    """
    busy_times = get_busy_times(time_min, time_max, timezone)
    slots = []
    slot_duration = timedelta(minutes=30)

    current = datetime.fromisoformat(time_min.replace("Z", "+00:00"))
    window_end = datetime.fromisoformat(time_max.replace("Z", "+00:00"))

    while current < window_end:
        # Skip weekends (Sat=5, Sun=6)
        if current.weekday() >= 5:
            current += timedelta(days=1)
            current = current.replace(
                hour=working_hours["startHour"], minute=0, second=0
            )
            continue

        # Adjust to start of workday if before
        if current.hour < working_hours["startHour"]:
            current = current.replace(
                hour=working_hours["startHour"], minute=0, second=0
            )

        # Define slot end time
        slot_end = current + slot_duration

        # Skip after work hours
        if slot_end.hour >= working_hours["endHour"]:
            current += timedelta(days=1)
            current = current.replace(
                hour=working_hours["startHour"], minute=0, second=0
            )
            continue

        # Check overlap with busy times
        overlap = any(
            datetime.fromisoformat(b["start"].replace("Z", "+00:00")) < slot_end
            and datetime.fromisoformat(b["end"].replace("Z", "+00:00")) > current
            for b in busy_times
        )

        if not overlap:
            slots.append(
                {
                    "start": current.isoformat(),
                    "end": slot_end.isoformat(),
                }
            )

        current += slot_duration

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
