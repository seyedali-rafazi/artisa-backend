"""
URL configuration for aircraft_tickets project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.users.urls")),
    path("api/flights/", include("apps.flights.urls")),
    path("api/transport/", include("apps.transport.urls")),
    path("api/insurance/", include("apps.insurance.urls")),
    path("api/bookings/", include("apps.bookings.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

