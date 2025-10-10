from django.urls import path
from .views import CreateBookingView, AvailableSlotsView

urlpatterns = [
    path("calendar/create/", CreateBookingView.as_view(), name="create-booking"),
    path(
        "calendar/available-slots/",
        AvailableSlotsView.as_view(),
        name="available-slots",
    ),
]
