from django.contrib import admin
from .models import TransportTrip


@admin.register(TransportTrip)
class TransportTripAdmin(admin.ModelAdmin):
    list_display = (
        "trip_number",
        "company",
        "transport_type",
        "origin",
        "destination",
        "departure_time",
        "price",
        "available_seats",
        "is_active",
    )
    list_filter = ("transport_type", "company", "is_active", "departure_time")
    search_fields = ("trip_number", "company", "origin", "destination")
    ordering = ("-departure_time",)


