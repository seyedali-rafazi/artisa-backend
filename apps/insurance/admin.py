from django.contrib import admin
from .models import InsurancePlan, InsuranceBooking


@admin.register(InsurancePlan)
class InsurancePlanAdmin(admin.ModelAdmin):
    list_display = ("title", "price", "coverage", "popular", "is_active")
    list_filter = ("popular", "is_active")
    search_fields = ("title", "coverage")


@admin.register(InsuranceBooking)
class InsuranceBookingAdmin(admin.ModelAdmin):
    list_display = (
        "tracking_code",
        "first_name",
        "last_name",
        "plan",
        "destination",
        "status",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("tracking_code", "first_name", "last_name", "email", "phone")
    readonly_fields = ("tracking_code", "created_at", "updated_at")


