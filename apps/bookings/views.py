from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Booking
from .serializers import BookingSerializer, BookingCreateSerializer


class BookingCreateView(generics.CreateAPIView):
    """API endpoint for creating bookings."""

    queryset = Booking.objects.all()
    serializer_class = BookingCreateSerializer
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()

        return Response(
            {
                "booking": BookingSerializer(booking).data,
                "message": "Booking created successfully",
            },
            status=status.HTTP_201_CREATED,
        )


class BookingListView(generics.ListAPIView):
    """API endpoint for listing user's bookings."""

    serializer_class = BookingSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)


class BookingDetailView(generics.RetrieveAPIView):
    """API endpoint for retrieving booking details by tracking code."""

    serializer_class = BookingSerializer
    permission_classes = (permissions.AllowAny,)
    lookup_field = "tracking_code"

    def get_queryset(self):
        return Booking.objects.all()


class BookingCancelView(APIView):
    """API endpoint for cancelling a booking."""

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, tracking_code):
        try:
            booking = Booking.objects.get(
                tracking_code=tracking_code, user=request.user
            )

            if booking.status == "cancelled":
                return Response(
                    {"error": "Booking is already cancelled"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            booking.status = "cancelled"
            booking.save()

            return Response(
                {
                    "message": "Booking cancelled successfully",
                    "booking": BookingSerializer(booking).data,
                },
                status=status.HTTP_200_OK,
            )

        except Booking.DoesNotExist:
            return Response(
                {"error": "Booking not found"}, status=status.HTTP_404_NOT_FOUND
            )


class UserTicketsView(generics.ListAPIView):
    """API endpoint for listing all user tickets (bookings and insurance)."""

    serializer_class = BookingSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)


