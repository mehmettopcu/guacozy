"""
ASGI entrypoint. Configures Django and then exposes the Channels routing
application defined in guacozy_server/routing.py.
"""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "guacozy_server.settings")
django.setup()

# Imported after django.setup() so app registry / settings are ready
# (routing.py calls get_asgi_application() at import time).
from guacozy_server.routing import application  # noqa: E402

__all__ = ["application"]
