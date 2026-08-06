from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import TransportTrip
from .serializers import TransportTripSerializer, TransportSearchSerializer


class TransportSearchView(APIView):
    """API endpoint for searching transport trips."""

    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = TransportSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        transport_type = serializer.validated_data["transport_type"]
        origin = serializer.validated_data["origin"]
        destination = serializer.validated_data["destination"]
        departure_date = serializer.validated_data["departure_date"]

        # Search for transport trips
        trips = TransportTrip.objects.filter(
            transport_type=transport_type,
            origin=origin,
            destination=destination,
            departure_time__date=departure_date,
            is_active=True,
            available_seats__gt=0,
        )

        serializer = TransportTripSerializer(trips, many=True)
        return Response(
            {"trips": serializer.data, "count": trips.count()},
            status=status.HTTP_200_OK,
        )


class TransportTripDetailView(generics.RetrieveAPIView):
    """API endpoint for retrieving transport trip details."""

    queryset = TransportTrip.objects.filter(is_active=True)
    serializer_class = TransportTripSerializer
    permission_classes = (permissions.AllowAny,)


class TransportTripListCreateView(generics.ListCreateAPIView):
    """API endpoint for listing and creating transport trips (admin only)."""

    queryset = TransportTrip.objects.all()
    serializer_class = TransportTripSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]


class TransportTripUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """API endpoint for updating and deleting transport trips (admin only)."""

    queryset = TransportTrip.objects.all()
    serializer_class = TransportTripSerializer
    permission_classes = (permissions.IsAdminUser,)


