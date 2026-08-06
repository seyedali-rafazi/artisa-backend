"""
ASGI config for aircraft_tickets project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aircraft_tickets.settings")

application = get_asgi_application()

# Made with Bob
