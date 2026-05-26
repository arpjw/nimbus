from __future__ import annotations

from nimbus_core.rag import _rrf


def test_rrf_single_list():
    ranks = [["a", "b", "c"]]
    scores = _rrf(ranks)
    assert scores["a"] > scores["b"] > scores["c"]


def test_rrf_two_lists_agreement_boosts():
    agreed = _rrf([["a", "b"], ["a", "b"]])
    single = _rrf([["a", "b"]])
    assert agreed["a"] > single["a"]
    assert agreed["b"] > single["b"]


def test_rrf_two_lists_disagreement():
    ranks = [["a", "b", "c"], ["c", "b", "a"]]
    scores = _rrf(ranks)
    assert scores["a"] == scores["c"]
    all_scores = sorted(scores.values(), reverse=True)
    assert len(all_scores) == 3


def test_rrf_empty_lists():
    scores = _rrf([])
    assert scores == {}


def test_rrf_single_item():
    scores = _rrf([["x"]])
    assert "x" in scores
    assert scores["x"] == pytest.approx(1.0 / 61, rel=1e-5)


def test_rrf_k_parameter():
    scores_default = _rrf([["a"]])
    scores_k1 = _rrf([["a"]], k=1)
    assert scores_k1["a"] > scores_default["a"]


def test_rrf_disjoint_lists():
    ranks = [["a", "b"], ["c", "d"]]
    scores = _rrf(ranks)
    assert set(scores.keys()) == {"a", "b", "c", "d"}
    assert scores["a"] > scores["b"]
    assert scores["c"] > scores["d"]


import pytest
