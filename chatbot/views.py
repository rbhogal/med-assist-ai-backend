from datetime import datetime, timedelta, timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from openai import OpenAI
import os
from .faqs import FaqSystemPrompt

SYSTEM_PROMPT = """
You are a friendly and helpful medical assistant at a primary care clinic. If a user isn't asking questions relevant to a primary care clinic, don't answer but instead gently remind them to answer questions regarding a primary care clinic. You can reply to general greetings however. Analyze the user's message and determine if they are asking to book an appointment. Reply with 'MED ASSIST BOOK AN APPOINTMENT' otherwise reply normally.
"""


class ChatbotAPIView(APIView):
    @method_decorator(ratelimit(key="ip", rate="20/8h", method="POST", block=False))
    def post(self, request):
        if getattr(request, "limited", False):
            reset_time = datetime.now(timezone.utc) + timedelta(hours=8)
            headers = {
                "X-RateLimit-Limit": "20",
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(reset_time.timestamp())),
            }
            return Response(
                {"error": "You've reached your limit. Try again in 8 hours."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
                headers=headers,
            )

        try:
            history = request.data.get("history", [])
            if not isinstance(history, list):
                return Response(
                    {"error": "Invalid chat history"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            messages = [
                {"role": "system", "content": FaqSystemPrompt},
                {"role": "system", "content": SYSTEM_PROMPT},
                *history,
            ]
            response = client.chat.completions.create(
                model="gpt-4o-mini", messages=messages
            )

            bot_reply = response.choices[0].message.content.strip()
            url = None
            if "med assist book an appointment" in bot_reply.lower():
                bot_reply = "Click here to book your appointment"
                url = "/demo/booking"

            return Response({"reply": bot_reply, "url": url})

        except Exception as e:
            print("Chatbot error 🤖:", e)
            return Response(
                {"error": "Something went wrong."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
