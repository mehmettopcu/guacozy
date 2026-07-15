"""Tests for Ticket validity / self-expiry logic."""
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from backend.models import ConnectionRdp, Folder, Ticket

User = get_user_model()
pytestmark = pytest.mark.django_db


def _make_ticket():
    user = User.objects.create_user(username="u", password="pw")
    folder = Folder.objects.create(name="root")
    conn = ConnectionRdp.objects.create(name="c1", host="10.0.0.1", parent=folder)
    return Ticket.objects.create(connection=conn, user=user, author=user)


def test_valid_ticket_is_kept():
    ticket = _make_ticket()
    assert ticket.check_validity() is True
    assert Ticket.objects.filter(pk=ticket.pk).exists()


def test_expired_ticket_deletes_itself():
    ticket = _make_ticket()
    # created is auto_now_add, so push it into the past via a queryset update
    Ticket.objects.filter(pk=ticket.pk).update(
        created=timezone.now() - timedelta(days=2),
        validityperiod=timedelta(days=1),
    )
    ticket.refresh_from_db()

    assert ticket.check_validity() is False
    assert not Ticket.objects.filter(pk=ticket.pk).exists()
