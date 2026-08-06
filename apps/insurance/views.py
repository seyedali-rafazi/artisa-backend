from rest_framework import generics, permissions
from .models import InsurancePlan, InsuranceBooking
from .serializers import InsurancePlanSerializer, InsuranceBookingSerializer


class InsurancePlanListView(generics.ListAPIView):
    """API endpoint for listing insurance plans."""

    queryset = InsurancePlan.objects.filter(is_active=True)
    serializer_class = InsurancePlanSerializer
    permission_classes = (permissions.AllowAny,)


class InsurancePlanDetailView(generics.RetrieveAPIView):
    """API endpoint for retrieving insurance plan details."""

    queryset = InsurancePlan.objects.filter(is_active=True)
    serializer_class = InsurancePlanSerializer
    permission_classes = (permissions.AllowAny,)


class InsuranceBookingCreateView(generics.CreateAPIView):
    """API endpoint for creating insurance bookings."""

    queryset = InsuranceBooking.objects.all()
    serializer_class = InsuranceBookingSerializer
    permission_classes = (permissions.AllowAny,)

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save()


class InsuranceBookingListView(generics.ListAPIView):
    """API endpoint for listing user's insurance bookings."""

    serializer_class = InsuranceBookingSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return InsuranceBooking.objects.filter(user=self.request.user)


class InsuranceBookingDetailView(generics.RetrieveAPIView):
    """API endpoint for retrieving insurance booking details."""

    serializer_class = InsuranceBookingSerializer
    permission_classes = (permissions.AllowAny,)
    lookup_field = "tracking_code"

    def get_queryset(self):
        return InsuranceBooking.objects.all()


