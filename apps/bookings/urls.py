from django.urls import path
from .views import (
    BookingCreateView,
    BookingListView,
    BookingDetailView,
    BookingCancelView,
    UserTicketsView,
)

urlpatterns = [
    path("create/", BookingCreateView.as_view(), name="booking-create"),
    path("my-bookings/", BookingListView.as_view(), name="booking-list"),
    path("my-tickets/", UserTicketsView.as_view(), name="user-tickets"),
    path("<str:tracking_code>/", BookingDetailView.as_view(), name="booking-detail"),
    path(
        "<str:tracking_code>/cancel/",
        BookingCancelView.as_view(),
        name="booking-cancel",
    ),
]

