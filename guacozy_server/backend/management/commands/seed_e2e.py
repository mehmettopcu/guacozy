"""Seed deterministic data for the Playwright E2E suite.

Idempotent: safe to run before every E2E run. Creates a login user with an
explicit folder permission (folder access is enforced even for superusers) and
one connection that should appear in the tree.
"""
from django.contrib.auth import get_user_model
from django.core.management import BaseCommand

from backend.models import (
    AppSettings,
    ConnectionRdp,
    Folder,
    FolderPermission,
    GuacdServer,
)

User = get_user_model()

E2E_USERNAME = "e2e"
E2E_PASSWORD = "e2e-password-123"
E2E_FOLDER = "E2E Folder"
E2E_CONNECTION = "E2E Test RDP"


class Command(BaseCommand):
    help = "Seed deterministic data for E2E tests"

    def handle(self, *args, **options):
        user, _ = User.objects.get_or_create(username=E2E_USERNAME)
        user.is_staff = True
        user.is_superuser = True
        user.set_password(E2E_PASSWORD)
        user.save()

        folder, _ = Folder.objects.get_or_create(name=E2E_FOLDER, parent=None)
        FolderPermission.objects.get_or_create(folder=folder, user=user)

        ConnectionRdp.objects.get_or_create(
            name=E2E_CONNECTION,
            defaults={"host": "10.0.0.10", "parent": folder},
        )

        # A default guacd server is required: creating a ticket writes a
        # TicketLog whose guacdserver_port is NOT NULL. Production always runs
        # `initguacd`; mirror that here so the ticket flow works.
        guacd, _ = GuacdServer.objects.get_or_create(
            name="e2e guacd",
            defaults={"hostname": "localhost", "port": 4822},
        )
        app_settings = AppSettings.load()
        if app_settings.default_guacd_server is None:
            app_settings.default_guacd_server = guacd
            app_settings.save()

        self.stdout.write(self.style.SUCCESS("E2E seed complete"))
