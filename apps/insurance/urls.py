from django.urls import path
from .views import (
    InsurancePlanListView,
    InsurancePlanDetailView,
    InsuranceBookingCreateView,
    InsuranceBookingListView,
    InsuranceBookingDetailView,
)

urlpatterns = [
    path("plans/", InsurancePlanListView.as_view(), name="insurance-plan-list"),
    path(
        "plans/<int:pk>/",
        InsurancePlanDetailView.as_view(),
        name="insurance-plan-detail",
    ),
    path(
        "bookings/",
        InsuranceBookingCreateView.as_view(),
        name="insurance-booking-create",
    ),
    path(
        "my-bookings/",
        InsuranceBookingListView.as_view(),
        name="insurance-booking-list",
    ),
    path(
        "bookings/<str:tracking_code>/",
        InsuranceBookingDetailView.as_view(),
        name="insurance-booking-detail",
    ),
]

