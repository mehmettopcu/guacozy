"""Tests for the folder-visibility helpers in backend/api/utils.py.

These functions drive queryset filtering in the REST API, so the difference
between "list" access (needs ancestors to render the tree path) and "view"
access (grant folder + its descendants only) must stay correct.
"""
import pytest
from django.contrib.auth import get_user_model

from backend.api.utils import user_allowed_folders_ids
from backend.models import Folder, FolderPermission

User = get_user_model()
pytestmark = pytest.mark.django_db


def _tree_with_grant_on_mid():
    user = User.objects.create_user(username="u", password="pw")
    root = Folder.objects.create(name="root")
    mid = Folder.objects.create(name="mid", parent=root)
    leaf = Folder.objects.create(name="leaf", parent=mid)
    FolderPermission.objects.create(folder=mid, user=user)
    return user, root, mid, leaf


def test_view_permission_covers_folder_and_descendants_not_ancestors():
    user, root, mid, leaf = _tree_with_grant_on_mid()

    view_ids = user_allowed_folders_ids(user, require_view_permission=True)

    assert mid.id in view_ids
    assert leaf.id in view_ids
    assert root.id not in view_ids


def test_list_permission_includes_ancestors_for_tree_path():
    user, root, mid, leaf = _tree_with_grant_on_mid()

    list_ids = user_allowed_folders_ids(user, require_view_permission=False)

    # ancestors are needed so the frontend can render the path down to `mid`
    assert root.id in list_ids
    assert mid.id in list_ids
    assert leaf.id in list_ids
