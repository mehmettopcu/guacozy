"""Global pytest configuration.

These environment defaults are set at import time — before pytest-django loads
Django settings — so the suite runs without external configuration:

* ``DEBUG`` avoids the production insecure-default-secret guard in settings.py.
* ``DJANGO_SECRET_KEY`` / ``FIELD_ENCRYPTION_KEY`` provide real values; the
  latter must be a valid Fernet key because models use ``EncryptedCharField``.

Real environment variables (e.g. those set in CI) take precedence — we only
fill in defaults when a value is missing.
"""
import os

os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault(
    "FIELD_ENCRYPTION_KEY", "qjq4ObsXMqiqQyfKgD-jjEGm4ep8RaHKGRg4ohGCi1A="
)
