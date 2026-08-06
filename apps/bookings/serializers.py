from rest_framework import serializers
from .models import Booking
from apps.flights.serializers import FlightSerializer
from apps.transport.serializers import TransportTripSerializer


class BookingSerializer(serializers.ModelSerializer):
    """Serializer for Booking model."""

    flight_details = FlightSerializer(source="flight", read_only=True)
    transport_details = TransportTripSerializer(source="transport_trip", read_only=True)

    class Meta:
        model = Booking
        fields = "__all__"
        read_only_fields = ("tracking_code", "status", "created_at", "updated_at")

    def validate(self, data):
        """Validate that either flight or transport_trip is provided."""
        booking_type = data.get("booking_type")

        if booking_type == "flight" and not data.get("flight"):
            raise serializers.ValidationError("Flight is required for flight bookings")

        if booking_type in ["bus", "train"] and not data.get("transport_trip"):
            raise serializers.ValidationError(
                "Transport trip is required for bus/train bookings"
            )

        return data


class BookingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating bookings."""

    class Meta:
        model = Booking
        fields = (
            "booking_type",
            "flight",
            "transport_trip",
            "passengers",
            "contact_email",
            "contact_phone",
            "total_price",
            "seat_numbers",
        )

    def create(self, validated_data):
        if self.context["request"].user.is_authenticated:
            validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


