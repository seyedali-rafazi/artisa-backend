from rest_framework import serializers
from .models import InsurancePlan, InsuranceBooking
import random
import string


class InsurancePlanSerializer(serializers.ModelSerializer):
    """Serializer for InsurancePlan model."""

    class Meta:
        model = InsurancePlan
        fields = "__all__"


class InsuranceBookingSerializer(serializers.ModelSerializer):
    """Serializer for InsuranceBooking model."""

    plan_details = InsurancePlanSerializer(source="plan", read_only=True)

    class Meta:
        model = InsuranceBooking
        fields = "__all__"
        read_only_fields = ("tracking_code", "status", "created_at", "updated_at")

    def create(self, validated_data):
        # Generate unique tracking code
        validated_data["tracking_code"] = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=10)
        )
        return super().create(validated_data)


