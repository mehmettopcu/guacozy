"""Tests for Connection.get_guacamole_parameters credential resolution.

This is the code that decides which secrets are handed to guacd, so its
branches (plain fields, static credentials, passthrough) are worth pinning.
"""
import pytest
from django.contrib.auth import get_user_model

from backend.models import ConnectionRdp, Folder, StaticCredentials

User = get_user_model()
pytestmark = pytest.mark.django_db


def make_user():
    return User.objects.create_user(username="u", password="pw")


def test_plain_credentials_come_from_connection_fields():
    user = make_user()
    folder = Folder.objects.create(name="root")
    conn = ConnectionRdp.objects.create(
        name="c1", host="10.0.0.1", parent=folder,
        username="user1", password="pass1", domain="dom1",
    )

    params = conn.get_guacamole_parameters(user)

    assert params["protocol"] == "rdp"
    assert params["hostname"] == "10.0.0.1"
    assert params["username"] == "user1"
    assert params["password"] == "pass1"
    assert params["domain"] == "dom1"


def test_static_credentials_take_precedence_over_connection_fields():
    user = make_user()
    folder = Folder.objects.create(name="root")
    creds = StaticCredentials.objects.create(
        name="sc", username="su", password="sp", domain="sd",
    )
    conn = ConnectionRdp.objects.create(
        name="c2", host="10.0.0.2", parent=folder,
        username="ignored", password="ignored", credentials=creds,
    )

    params = conn.get_guacamole_parameters(user)

    assert params["username"] == "su"
    assert params["password"] == "sp"
    assert params["domain"] == "sd"


def test_passthrough_does_not_leak_stored_secrets():
    user = make_user()
    folder = Folder.objects.create(name="root")
    conn = ConnectionRdp.objects.create(
        name="c3", host="10.0.0.3", parent=folder,
        domain="corp", passthrough_credentials=True,
        username="should-not-leak", password="should-not-leak",
    )

    params = conn.get_guacamole_parameters(user)

    assert params["passthrough_credentials"] is True
    assert params["username"] == ""
    assert params["password"] == ""
    # domain is still forwarded so the remote login prompt is pre-filled
    assert params["domain"] == "corp"


def test_rdp_default_port_is_applied():
    user = make_user()
    folder = Folder.objects.create(name="root")
    conn = ConnectionRdp.objects.create(name="c4", host="10.0.0.4", parent=folder)

    params = conn.get_guacamole_parameters(user)

    assert conn.port == 3389
    assert params["port"] == 3389
