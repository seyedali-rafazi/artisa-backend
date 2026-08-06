from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "tracking_code",
        "user",
        "booking_type",
        "status",
        "total_price",
        "created_at",
    )
    list_filter = ("booking_type", "status", "created_at")
    search_fields = ("tracking_code", "contact_email", "contact_phone")
    readonly_fields = ("tracking_code", "created_at", "updated_at")

    fieldsets = (
        (
            "Booking Information",
            {"fields": ("tracking_code", "user", "booking_type", "status")},
        ),
        ("Trip Details", {"fields": ("flight", "transport_trip")}),
        (
            "Passenger & Contact",
            {"fields": ("passengers", "contact_email", "contact_phone")},
        ),
        ("Payment & Seats", {"fields": ("total_price", "seat_numbers")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


