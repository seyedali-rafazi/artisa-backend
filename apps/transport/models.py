from django.db import models
from djongo import models as djongo_models


class TransportTrip(models.Model):
    """Transport trip model for bus and train."""

    TRANSPORT_TYPE_CHOICES = [
        ("bus", "Bus"),
        ("train", "Train"),
    ]

    transport_type = models.CharField(max_length=10, choices=TRANSPORT_TYPE_CHOICES)
    company = models.CharField(max_length=100)
    logo = models.URLField(blank=True, null=True)
    trip_number = models.CharField(max_length=20)
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    duration = models.CharField(max_length=20)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available_seats = models.IntegerField()
    features = djongo_models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "transport_trips"
        verbose_name = "Transport Trip"
        verbose_name_plural = "Transport Trips"
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.company} {self.trip_number} - {self.origin} to {self.destination}"
        )


