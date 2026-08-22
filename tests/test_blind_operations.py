"""Unit tests for blind match operations."""

import pytest

from blind_operations.blind_match import match


def test_blind_match_known_transitions():
    # Input matching state 0: '101001' -> '101010'
    res0 = match("101001")
    assert res0 == "101010"

    # Input matching state 1: '010110' -> '010101'
    res1 = match("010110")
    assert res1 == "010101"


def test_blind_match_non_matching_input():
    # Input not matching any transition in table
    res = match("000000")
    assert res == "000000"


def test_blind_match_invalid_characters():
    with pytest.raises(ValueError):
        match("102010")
