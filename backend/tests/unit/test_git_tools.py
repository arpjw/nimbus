from __future__ import annotations

import re
from unittest.mock import MagicMock, patch

import pytest

from tools.git_tools import GitManager


@pytest.fixture
def git_manager():
    with patch("tools.git_tools.Github"), patch("tools.git_tools.Auth"):
        gm = GitManager()
    return gm


def test_inject_token_github_url(git_manager: GitManager):
    with patch("tools.git_tools.settings") as mock_settings:
        mock_settings.github_token = "mytoken"
        result = git_manager._inject_token("https://github.com/owner/repo.git")
    assert "mytoken@github.com" in result


def test_inject_token_non_github_url(git_manager: GitManager):
    url = "https://gitlab.com/owner/repo.git"
    result = git_manager._inject_token(url)
    assert result == url


def test_generate_branch_name_basic(git_manager: GitManager):
    name = git_manager.generate_branch_name("Add logging to auth module")
    assert name.startswith("nimbus/")
    assert "add-logging-to-auth-module" in name


def test_generate_branch_name_truncates_long(git_manager: GitManager):
    long_desc = "A" * 200
    name = git_manager.generate_branch_name(long_desc)
    slug_part = name.removeprefix("nimbus/").rsplit("-", 12)[0]
    assert len(slug_part) <= 40


def test_generate_branch_name_special_chars(git_manager: GitManager):
    name = git_manager.generate_branch_name("Fix bug: null pointer @ line 42!")
    assert re.match(r"^nimbus/[a-z0-9-]+-\d{12}$", name)


def test_generate_branch_name_has_timestamp(git_manager: GitManager):
    name = git_manager.generate_branch_name("Update deps")
    ts_match = re.search(r"-(\d{12})$", name)
    assert ts_match is not None
    assert len(ts_match.group(1)) == 12
