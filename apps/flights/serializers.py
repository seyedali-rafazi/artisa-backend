from rest_framework import serializers
from .models import City, Flight, PopularFlight, Destination


class CitySerializer(serializers.ModelSerializer):
    """Serializer for City model."""

    class Meta:
        model = City
        fields = "__all__"


class FlightSerializer(serializers.ModelSerializer):
    """Serializer for Flight model."""

    class Meta:
        model = Flight
        fields = "__all__"


class FlightSearchSerializer(serializers.Serializer):
    """Serializer for flight search parameters."""

    origin = serializers.CharField(required=True)
    destination = serializers.CharField(required=True)
    departure_date = serializers.DateField(required=True)
    return_date = serializers.DateField(required=False, allow_null=True)
    passengers = serializers.IntegerField(required=True, min_value=1)
    flight_class = serializers.ChoiceField(
        choices=["economy", "business", "first"], default="economy"
    )


class PopularFlightSerializer(serializers.ModelSerializer):
    """Serializer for PopularFlight model."""

    class Meta:
        model = PopularFlight
        fields = "__all__"


class DestinationSerializer(serializers.ModelSerializer):
    """Serializer for Destination model."""

    class Meta:
        model = Destination
        fields = "__all__"


