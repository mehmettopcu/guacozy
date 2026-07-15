"""Tests for the object-level permission predicates in backend/rules.py.

Folder access inheritance and ticket ownership are the most security-sensitive
pieces of logic in the project, so they are the priority safety net before any
framework upgrade.
"""
import pytest
import rules
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from backend.models import ConnectionRdp, Folder, FolderPermission, Ticket

User = get_user_model()
pytestmark = pytest.mark.django_db


def make_user(username="alice"):
    return User.objects.create_user(username=username, password="pw")


def test_direct_permission_granted_to_user():
    user = make_user()
    folder = Folder.objects.create(name="root")
    FolderPermission.objects.create(folder=folder, user=user)

    assert rules.test_rule("has_direct_permission", user, folder)


def test_direct_permission_denied_without_grant():
    user = make_user()
    folder = Folder.objects.create(name="root")

    assert not rules.test_rule("has_direct_permission", user, folder)


def test_group_permission_granted():
    user = make_user()
    group = Group.objects.create(name="team")
    user.groups.add(group)
    folder = Folder.objects.create(name="root")
    FolderPermission.objects.create(folder=folder, group=group)

    assert rules.test_rule("has_direct_permission", user, folder)


def test_inherited_permission_flows_to_descendants():
    user = make_user()
    root = Folder.objects.create(name="root")
    child = Folder.objects.create(name="child", parent=root)
    grandchild = Folder.objects.create(name="grandchild", parent=child)
    FolderPermission.objects.create(folder=root, user=user)

    grandchild = Folder.objects.get(pk=grandchild.pk)
    assert rules.test_rule("has_inherited_permission", user, grandchild)
    # inheritance must not be mistaken for a direct grant on the descendant
    assert not rules.test_rule("has_direct_permission", user, grandchild)


def test_ticket_visible_only_to_user_or_author():
    author = make_user("author")
    other = make_user("other")
    folder = Folder.objects.create(name="root")
    conn = ConnectionRdp.objects.create(name="c1", host="10.0.0.1", parent=folder)
    ticket = Ticket.objects.create(connection=conn, user=author, author=author)

    assert author.has_perm("backend.view_ticket", ticket)
    assert not other.has_perm("backend.view_ticket", ticket)
