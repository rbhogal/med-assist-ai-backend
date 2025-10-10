from django.contrib import admin
from .models import Appointment

from django.contrib import admin

admin.site.site_header = "MedAssist Admin"
admin.site.site_title = "MedAssist Admin Portal"
admin.site.index_title = "Welcome to the MedAssist Dashboard"


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "start_time", "end_time", "created_at")
    ordering = ("-created_at",)
