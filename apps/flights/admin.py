from django.contrib import admin
from .models import City, Flight, PopularFlight, Destination


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "country")
    search_fields = ("code", "name", "country")
    ordering = ("name",)


@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = (
        "flight_number",
        "airline",
        "origin",
        "destination",
        "departure_time",
        "price",
        "available_seats",
        "is_active",
    )
    list_filter = ("airline", "flight_class", "is_active", "departure_time")
    search_fields = ("flight_number", "airline", "origin", "destination")
    ordering = ("-departure_time",)


@admin.register(PopularFlight)
class PopularFlightAdmin(admin.ModelAdmin):
    list_display = ("from_city", "to_city", "price", "is_active", "order")
    list_filter = ("is_active",)
    ordering = ("order",)


@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ("title", "destination_code", "is_active", "order")
    list_filter = ("is_active",)
    ordering = ("order",)


