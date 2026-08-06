from django.urls import path
from .views import (
    TransportSearchView,
    TransportTripDetailView,
    TransportTripListCreateView,
    TransportTripUpdateDeleteView,
)

urlpatterns = [
    path("search/", TransportSearchView.as_view(), name="transport-search"),
    path("", TransportTripListCreateView.as_view(), name="transport-list-create"),
    path("<int:pk>/", TransportTripDetailView.as_view(), name="transport-detail"),
    path(
        "<int:pk>/manage/",
        TransportTripUpdateDeleteView.as_view(),
        name="transport-update-delete",
    ),
]

