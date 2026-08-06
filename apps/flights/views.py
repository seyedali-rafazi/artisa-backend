from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from datetime import datetime
from .models import City, Flight, PopularFlight, Destination
from .serializers import (
    CitySerializer,
    FlightSerializer,
    FlightSearchSerializer,
    PopularFlightSerializer,
    DestinationSerializer,
)


class CityListView(generics.ListAPIView):
    """API endpoint for listing all cities."""

    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = (permissions.AllowAny,)


class FlightSearchView(APIView):
    """API endpoint for searching flights."""

    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = FlightSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        origin = serializer.validated_data["origin"]
        destination = serializer.validated_data["destination"]
        departure_date = serializer.validated_data["departure_date"]
        flight_class = serializer.validated_data.get("flight_class", "economy")

        # Search for flights
        flights = Flight.objects.filter(
            origin=origin,
            destination=destination,
            departure_time__date=departure_date,
            flight_class=flight_class,
            is_active=True,
            available_seats__gt=0,
        )

        serializer = FlightSerializer(flights, many=True)
        return Response(
            {"flights": serializer.data, "count": flights.count()},
            status=status.HTTP_200_OK,
        )


class FlightDetailView(generics.RetrieveAPIView):
    """API endpoint for retrieving flight details."""

    queryset = Flight.objects.filter(is_active=True)
    serializer_class = FlightSerializer
    permission_classes = (permissions.AllowAny,)


class PopularFlightsView(generics.ListAPIView):
    """API endpoint for listing popular flights."""

    queryset = PopularFlight.objects.filter(is_active=True)
    serializer_class = PopularFlightSerializer
    permission_classes = (permissions.AllowAny,)


class DestinationsView(generics.ListAPIView):
    """API endpoint for listing popular destinations."""

    queryset = Destination.objects.filter(is_active=True)
    serializer_class = DestinationSerializer
    permission_classes = (permissions.AllowAny,)


class FlightListCreateView(generics.ListCreateAPIView):
    """API endpoint for listing and creating flights (admin only)."""

    queryset = Flight.objects.all()
    serializer_class = FlightSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]


class FlightUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """API endpoint for updating and deleting flights (admin only)."""

    queryset = Flight.objects.all()
    serializer_class = FlightSerializer
    permission_classes = (permissions.IsAdminUser,)


