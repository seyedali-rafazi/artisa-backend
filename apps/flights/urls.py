from django.urls import path
from .views import (
    CityListView,
    FlightSearchView,
    FlightDetailView,
    PopularFlightsView,
    DestinationsView,
    FlightListCreateView,
    FlightUpdateDeleteView,
)

urlpatterns = [
    path("cities/", CityListView.as_view(), name="city-list"),
    path("search/", FlightSearchView.as_view(), name="flight-search"),
    path("popular/", PopularFlightsView.as_view(), name="popular-flights"),
    path("destinations/", DestinationsView.as_view(), name="destinations"),
    path("", FlightListCreateView.as_view(), name="flight-list-create"),
    path("<int:pk>/", FlightDetailView.as_view(), name="flight-detail"),
    path(
        "<int:pk>/manage/",
        FlightUpdateDeleteView.as_view(),
        name="flight-update-delete",
    ),
]

