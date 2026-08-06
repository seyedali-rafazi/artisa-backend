from rest_framework import serializers
from .models import TransportTrip


class TransportTripSerializer(serializers.ModelSerializer):
    """Serializer for TransportTrip model."""

    class Meta:
        model = TransportTrip
        fields = "__all__"


class TransportSearchSerializer(serializers.Serializer):
    """Serializer for transport search parameters."""

    transport_type = serializers.ChoiceField(choices=["bus", "train"], required=True)
    origin = serializers.CharField(required=True)
    destination = serializers.CharField(required=True)
    departure_date = serializers.DateField(required=True)
    passengers = serializers.IntegerField(required=True, min_value=1)


