import pytest

from madlibs.constraints import make_constraint


def test_equality_constraint():
    c = make_constraint("equals", "a", "b")
    assert c.check({"a": "1", "b": "1"})
    assert not c.check({"a": "1", "b": "2"})


def test_equality_exceptions():
    with pytest.raises(Exception):
        c = make_constraint("equals", "a")

    with pytest.raises(Exception):
        c = make_constraint("equals", "a", "b", "c")

    with pytest.raises(Exception):
        c = make_constraint("equals", "a", "b")
        c.check({"a": "1"})

    with pytest.raises(Exception):
        c = make_constraint("equals", "a", "b")
        c.check({"b": "1"})


def test_less_than_constraint():
    c = make_constraint("less_than", "a", "b")
    assert not c.check({"a": "1", "b": "1"})
    assert c.check({"a": "1", "b": "2"})
    assert not c.check({"a": "2", "b": "1"})


def test_less_than_exceptions():
    with pytest.raises(Exception):
        c = make_constraint("less_than", "a")

    with pytest.raises(Exception):
        c = make_constraint("less_than", "a", "b", "c")

    with pytest.raises(Exception):
        c = make_constraint("less_than", "a", "b")
        c.check({"a": "1"})

    with pytest.raises(Exception):
        c = make_constraint("less_than", "a", "b")
        c.check({"b": "1"})


def test_greater_than_constraint():
    c = make_constraint("greater_than", "a", "b")
    assert not c.check({"a": "1", "b": "1"})
    assert not c.check({"a": "1", "b": "2"})
    assert c.check({"a": "2", "b": "1"})


def test_greater_than_exceptions():
    with pytest.raises(Exception):
        c = make_constraint("greater_than", "a")

    with pytest.raises(Exception):
        c = make_constraint("greater_than", "a", "b", "c")

    with pytest.raises(Exception):
        c = make_constraint("greater_than", "a", "b")
        c.check({"a": "1"})

    with pytest.raises(Exception):
        c = make_constraint("greater_than", "a", "b")
        c.check({"b": "1"})
