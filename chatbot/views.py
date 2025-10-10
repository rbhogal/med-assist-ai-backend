from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from openai import OpenAI
import os
from .faqs import FaqSystemPrompt

SYSTEM_PROMPT = """
You are a friendly and helpful medical assistant at a primary care clinic.
If the user isn't asking a question relevant to a primary care clinic,
gently remind them to focus on clinic-related topics.
If the user wants to book an appointment, reply with 'MED ASSIST BOOK AN APPOINTMENT'.
Otherwise, answer normally.
"""


class ChatbotAPIView(APIView):

    def post(self, request):
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
            print(f"BOT REPLY: {bot_reply}")
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
