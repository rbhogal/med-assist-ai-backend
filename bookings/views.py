from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta, timezone
from .utils import generate_available_slots, create_google_calendar_event

import os
import json

from .models import Appointment
from .serializers import AppointmentSerializer


class CreateBookingView(APIView):
    """
    POST /api/calendar/create/
    Creates a Google Calendar event and saves it to the Appointment model.
    """

    def post(self, request):
        try:
            name = request.data.get("name")
            email = request.data.get("email")
            slot = request.data.get("slot")

            if not (name and email and slot):
                return Response(
                    {"error": "Missing required fields: name, email, slot"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Create event on Google Calendar
            result = create_google_calendar_event(name, email, slot)

            if not result.get("success"):
                return Response(
                    {"error": result.get("error", "Failed to create calendar event")},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Save appointment to database
            appointment = Appointment.objects.create(
                name=name,
                email=email,
                start_time=slot["start"],
                end_time=slot["end"],
                google_event_id=result.get("event_id"),
            )

            serializer = AppointmentSerializer(appointment)

            return Response(
                {
                    "success": True,
                    "link": result.get("link"),  # direct Google Calendar link
                    "appointment": serializer.data,  # saved DB record
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            print("Error creating booking:", e)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# class CreateBookingView(APIView):
#     """
#     POST /api/calendar/create/
#     Creates a Google Calendar event and saves it to the local Appointment model.
#     """

#     def post(self, request):
#         try:
#             name = request.data.get("name")
#             email = request.data.get("email")
#             slot = request.data.get("slot")

#             creds = service_account.Credentials.from_service_account_info(
#                 json.loads(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")),
#                 scopes=["https://www.googleapis.com/auth/calendar"],
#             )
#             service = build("calendar", "v3", credentials=creds)

#             event = {
#                 "summary": f"{name} - Demo Appointment",
#                 "location": "123 Demo St. AI City MA, 99999",
#                 "description": f"Booked by {email}",
#                 "start": {"dateTime": slot["start"], "timeZone": "America/Los_Angeles"},
#                 "end": {"dateTime": slot["end"], "timeZone": "America/Los_Angeles"},
#             }

#             response = (
#                 service.events()
#                 .insert(calenderId=os.getenv("GOOGLE_CALENDER_ID"), body=event)
#                 .execute()
#             )

#             # Save to database
#             appointment = Appointment.objects.create(
#                 name=name,
#                 email=email,
#                 start_time=slot["start"],
#                 end_time=slot["end"],
#                 google_event_id=response.get("id"),
#             )

#             serializer = AppointmentSerializer(appointment)

#             return Response(
#                 {
#                     "success": True,
#                     "link": response.get("htmlLink"),
#                     "appointment": serializer.data,
#                 },
#                 status=status.HTTP_201_CREATED,
#             )
#         except Exception as e:
#             print("Booking error :", e)
#             return Response(
#                 {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )


class AvailableSlotsView(APIView):
    """
    GET /api/calendar/available-slots/
    Returns available 30-min time slots for the next 4 weeks.
    """

    def get(self, request):
        try:
            timezone_str = "America/Los_Angeles"
            now = datetime.now(timezone.utc).isoformat()
            later = (datetime.now(timezone.utc) + timedelta(days=28)).isoformat()
            working_hours = {"startHour": 9, "endHour": 17}

            slots = generate_available_slots(now, later, timezone_str, working_hours)
            return Response(slots, status=status.HTTP_200_OK)

        except Exception as e:
            print("Error fetching available slots:", e)
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
