from __future__ import annotations


def _count_diff_lines(diff_raw: str) -> int:
    return sum(
        1 for line in diff_raw.splitlines()
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
    )


def test_diff_count_additions_only():
    diff = "diff --git a/a.py b/a.py\n+++ b/a.py\n+new line\n+another\n"
    assert _count_diff_lines(diff) == 2


def test_diff_count_deletions_only():
    diff = "diff --git a/a.py b/a.py\n--- a/a.py\n-old line\n-another old\n"
    assert _count_diff_lines(diff) == 2


def test_diff_count_mixed():
    diff = (
        "diff --git a/a.py b/a.py\n"
        "--- a/a.py\n"
        "+++ b/a.py\n"
        "-old\n"
        "+new\n"
        " context\n"
    )
    assert _count_diff_lines(diff) == 2


def test_diff_count_empty():
    assert _count_diff_lines("") == 0


def test_diff_count_no_changes():
    diff = "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n context line\n"
    assert _count_diff_lines(diff) == 0


def test_diff_count_header_lines_excluded():
    diff = "--- a/old.py\n+++ b/new.py\n-deleted\n+added\n"
    assert _count_diff_lines(diff) == 2


def test_diff_count_multifile():
    diff = (
        "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n+added_a\n"
        "diff --git a/b.py b/b.py\n--- a/b.py\n+++ b/b.py\n-removed_b\n+added_b\n"
    )
    assert _count_diff_lines(diff) == 3
