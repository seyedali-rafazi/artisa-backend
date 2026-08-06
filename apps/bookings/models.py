from django.db import models
from djongo import models as djongo_models
import random
import string


class Passenger(djongo_models.Model):
    """Embedded passenger model."""

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    national_id = models.CharField(max_length=20)
    birth_date = models.DateField()
    gender = models.CharField(
        max_length=10, choices=[("male", "Male"), ("female", "Female")]
    )

    class Meta:
        abstract = True


class Booking(models.Model):
    """Main booking model for flights and transport."""

    BOOKING_TYPE_CHOICES = [
        ("flight", "Flight"),
        ("bus", "Bus"),
        ("train", "Train"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="bookings",
        null=True,
        blank=True,
    )
    booking_type = models.CharField(max_length=20, choices=BOOKING_TYPE_CHOICES)

    # Flight or Transport reference
    flight = models.ForeignKey(
        "flights.Flight",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
    )
    transport_trip = models.ForeignKey(
        "transport.TransportTrip",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
    )

    # Passengers data (stored as JSON)
    passengers = djongo_models.JSONField()

    # Contact information
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)

    # Booking details
    tracking_code = models.CharField(max_length=20, unique=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Seat information
    seat_numbers = djongo_models.JSONField(default=list)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bookings"
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.tracking_code} - {self.booking_type}"

    def save(self, *args, **kwargs):
        if not self.tracking_code:
            self.tracking_code = "".join(
                random.choices(string.ascii_uppercase + string.digits, k=10)
            )
        super().save(*args, **kwargs)


