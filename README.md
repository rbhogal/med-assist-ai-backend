# 🏥 MedAssist AI — Backend

**MedAssist AI** is a Django REST Framework backend that powers a full-stack AI assistant for primary care clinics.  
It integrates **OpenAI GPT-4.1** for intelligent FAQ automation and **Google Calendar** for real-time appointment scheduling, with **Supabase (PostgreSQL)** for data storage and **Upstash Redis** for rate limiting.


### Next.js Frontend Repo
https://github.com/rbhogal/med-assist-ai

---

## 🚀 Tech Stack

- **Django REST Framework** — API backend
- **PostgreSQL (Supabase)** — database
- **Redis (Upstash)** — caching & rate limiting
- **OpenAI GPT-4.1 API** — AI chatbot responses
- **Google Calendar API** — appointment booking
- **Render** — backend hosting
- **Vercel (frontend)** — connected Next.js client

## ✨ Features

- **AI Chatbot API** – Uses OpenAI GPT-4.1 to understand patient messages, answer FAQs, and detect appointment intent.  
- **Appointment Scheduling** – Integrates with Google Calendar to list available time slots and create calendar events automatically.  
- **Dynamic Slot Generation** – Generates 30-minute appointment windows based on real-time availability and clinic working hours.  
- **Rate Limiting & Caching** – Protects endpoints using Redis (Upstash) to manage API call frequency and improve performance.  
- **Supabase (PostgreSQL) Database** – Stores appointment details and user data securely with relational integrity.  
- **Environment-Driven Configuration** – Easily switch between local and production setups using `.env` variables.  
- **CORS-Secured Endpoints** – Restricts API access to authorized frontend origins (Vercel + localhost).  
- **Scalable Deployment** – Deployed on Render with Gunicorn for production-grade performance and stability.  
- **RESTful Architecture** – Clean, modular API design following Django REST Framework best practices.  

## 🔌 API Endpoints

### 💬 Chatbot
**POST** `/api/chat/`  
Handles chat messages from users and returns responses generated via OpenAI GPT-4.1.

**Request Body**
```json
{
  "history": [
    { "role": "user", "content": "I need to book a check-up tomorrow morning." }
  ]
}
```

**Successful Response**
```json
{
  "reply": "Sure! I can help you book an appointment. Here’s the link to our scheduling page.",
  "url": "https://med-assist-ai.vercel.app/booking"
}
```


### 📅 Available Slots
**GET** `/api/calendar/available-slots/`  
Returns all available 30-minute appointment slots within the next four weeks, grouped by date and filtered by working hours.

**Sample Response**
```json
[
  {
    "date": "2025-10-13",
    "slots": ["13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30"]
  },
  {
    "date": "2025-10-14",
    "slots": ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "12:00"]
  }
]
```


### 🗓️ Create Appointment Event
**POST** `/api/calendar/create`  
Creates a new appointment event on Google Calendar and stores it in the Supabase (PostgreSQL) database

**Request Body**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "slot": {
    "start": "2025-10-14T13:30:00-07:00",
    "end": "2025-10-14T14:00:00-07:00"
  }
}
```

**Successful Response**
```json
{
  "success": true,
  "link": "https://calendar.google.com/event?eid=abc123xyz",
  "appointment": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "start_time": "2025-10-14T13:30:00-07:00",
    "end_time": "2025-10-14T14:00:00-07:00",
    "google_event_id": "abc123xyz"
  }
}
```


