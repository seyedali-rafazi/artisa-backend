from django.db import models
from djongo import models as djongo_models


class InsurancePlan(models.Model):
    """Insurance plan model."""

    title = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    coverage = models.CharField(max_length=200)
    popular = models.BooleanField(default=False)
    features = djongo_models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "insurance_plans"
        verbose_name = "Insurance Plan"
        verbose_name_plural = "Insurance Plans"
        ordering = ["-popular", "price"]

    def __str__(self):
        return self.title


class InsuranceBooking(models.Model):
    """Insurance booking model."""

    plan = models.ForeignKey(
        InsurancePlan, on_delete=models.CASCADE, related_name="bookings"
    )
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="insurance_bookings",
        null=True,
        blank=True,
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    national_id = models.CharField(max_length=20)
    birth_date = models.DateField()
    destination = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    tracking_code = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "insurance_bookings"
        verbose_name = "Insurance Booking"
        verbose_name_plural = "Insurance Bookings"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.tracking_code} - {self.first_name} {self.last_name}"


