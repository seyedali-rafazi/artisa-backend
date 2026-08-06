from django.db import models
from djongo import models as djongo_models


class City(models.Model):
    """City model for flight origins and destinations."""

    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = "cities"
        verbose_name = "City"
        verbose_name_plural = "Cities"

    def __str__(self):
        return f"{self.name} ({self.code})"


class Flight(models.Model):
    """Flight model for storing flight information."""

    FLIGHT_CLASS_CHOICES = [
        ("economy", "Economy"),
        ("business", "Business"),
        ("first", "First Class"),
    ]

    airline = models.CharField(max_length=100)
    logo = models.URLField(blank=True, null=True)
    flight_number = models.CharField(max_length=20)
    origin = models.CharField(max_length=10)
    destination = models.CharField(max_length=10)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    duration = models.CharField(max_length=20)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available_seats = models.IntegerField()
    stops = models.IntegerField(default=0)
    flight_class = models.CharField(
        max_length=20, choices=FLIGHT_CLASS_CHOICES, default="economy"
    )
    features = djongo_models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "flights"
        verbose_name = "Flight"
        verbose_name_plural = "Flights"
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.airline} {self.flight_number} - {self.origin} to {self.destination}"
        )


class PopularFlight(models.Model):
    """Popular flight routes for homepage display."""

    from_city = models.CharField(max_length=100)
    to_city = models.CharField(max_length=100)
    from_code = models.CharField(max_length=10)
    to_code = models.CharField(max_length=10)
    price = models.CharField(max_length=50)
    image = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        db_table = "popular_flights"
        verbose_name = "Popular Flight"
        verbose_name_plural = "Popular Flights"
        ordering = ["order"]

    def __str__(self):
        return f"{self.from_city} to {self.to_city}"


class Destination(models.Model):
    """Popular destinations for homepage display."""

    title = models.CharField(max_length=100)
    subtitle = models.CharField(max_length=200)
    image = models.URLField()
    destination_code = models.CharField(max_length=10)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        db_table = "destinations"
        verbose_name = "Destination"
        verbose_name_plural = "Destinations"
        ordering = ["order"]

    def __str__(self):
        return self.title


