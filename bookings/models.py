from django.db import models


class Appointment(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    google_event_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.start_time.strftime('%Y-%m-%d %H:%M')})"
