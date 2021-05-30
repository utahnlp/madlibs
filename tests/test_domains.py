import pytest

from madlibs.domains import (
    FillerDependentDomain,
    FillerDomain,
    RangeDomain,
    make_filler_domain,
    make_range_domain,
)


def test_simple_domain():
    f = FillerDomain("x", "x", ["Jack", "Jill"])
    assert f.variable_name == "x"
    assert f.variable_type == "x"
    assert f.values == ["Jack", "Jill"]
    assert len(f.dependent_variables) == 0
    assert len(f.dependents) == 0

    assert not f.is_reference_to_type()

    assert f.generate_domain() == ["Jack", "Jill"]
    with pytest.raises(Exception):
        assert f.lookup_dependent("a", "b")

    assert str(f) == "x: [Jack, Jill]"


def test_filler_domain():
    f = FillerDomain("x", "person", ["Jack", "Jill"])
    assert f.variable_name == "x"
    assert f.variable_type == "person"
    assert f.values == ["Jack", "Jill"]
    assert len(f.dependent_variables) == 0
    assert len(f.dependents) == 0

    assert f.is_reference_to_type()
    assert str(f) == "x: person [Jack, Jill]"

    assert f.generate_domain() == ["Jack", "Jill"]
    with pytest.raises(Exception):
        assert f.lookup_dependent("a", "b")

    f = FillerDomain(
        "x",
        "name",
        [
            {"name": "Jack", "pronoun": "he"},
            {"name": "Jill", "pronoun": "she"},
        ],
    )

    assert f.variable_name == "x"
    assert f.variable_type == "name"
    assert f.values == ["Jack", "Jill"]
    assert len(f.dependent_variables) == 1
    assert "pronoun" in f.dependent_variables
    assert len(f.dependents) == 2

    assert "Jack" in f.dependents
    assert "pronoun" in f.dependents["Jack"]
    assert f.dependents["Jack"]["pronoun"] == "he"

    assert "Jill" in f.dependents
    assert "pronoun" in f.dependents["Jill"]
    assert f.dependents["Jill"]["pronoun"] == "she"

    assert f.is_reference_to_type()

    assert f.generate_domain() == ["Jack", "Jill"]
    with pytest.raises(Exception):
        assert f.lookup_dependent("a", "b")

    assert f.lookup_dependent("Jack", "pronoun") == "he"
    assert f.lookup_dependent("Jill", "pronoun") == "she"


def test_filler_creation_exception():
    values = {
        "person": [
            {"name": "Jack", "pronoun": "he"},
            {"name": "Jill", "pronoun": "she"},
        ],
    }

    with pytest.raises(Exception):
        make_filler_domain("x", values)

    with pytest.raises(Exception):
        make_filler_domain("x", values, "person")

    with pytest.raises(Exception):
        make_filler_domain("x", values, "location")

    values = {
        "person": [{"name": "Jack", "pronoun": "he"}, "Jill"],
    }
    with pytest.raises(Exception):
        make_filler_domain("x", values, "name")

    values = {
        "person": ["James", {"name": "Jack", "pronoun": "he"}, "Jill"],
    }
    with pytest.raises(Exception):
        make_filler_domain("x", values, "name")


def test_filler_unification():
    f1 = FillerDomain("x", "person", ["Jack", "Jill"])
    f2 = FillerDomain("x", "x", ["Jack", "Jill"])

    u21 = f2.unify_with(f1)
    assert u21.variable_name == "x"
    assert u21.variable_type == "person"
    assert u21.values == ["Jack", "Jill"]
    assert len(u21.dependent_variables) == 0
    assert len(u21.dependents) == 0

    assert u21.is_reference_to_type()

    assert u21.generate_domain() == ["Jack", "Jill"]
    with pytest.raises(Exception):
        assert u21.lookup_dependent("a", "b")

    u12 = f1.unify_with(f2)
    assert u12.variable_name == "x"
    assert u12.variable_type == "person"
    assert u12.values == ["Jack", "Jill"]
    assert len(u12.dependent_variables) == 0
    assert len(u12.dependents) == 0

    assert u12.is_reference_to_type()

    assert u12.generate_domain() == ["Jack", "Jill"]
    with pytest.raises(Exception):
        assert u12.lookup_dependent("a", "b")

    u11 = f1.unify_with(f1)
    assert u11 == f1


def test_filler_unification_failures():
    f1 = FillerDomain("x", "person", ["Jack", "Jill"])
    f2 = FillerDomain("y", "person", ["Jack", "Jill"])
    f3 = FillerDomain("x", "dog", ["Jack", "Jill"])
    f4 = FillerDomain("x", "person", ["Jack"])

    domains = [f1, f2, f3, f4]
    for a in domains:
        for b in domains:
            if a != b:
                assert a.unify_with(b) is None

    f1 = FillerDomain("x", "x", ["Jack"])
    f2 = FillerDomain("x", "x", ["Jill"])
    f3 = FillerDomain("y", "y", ["Jack"])

    domains = [f1, f2, f3]
    for a in domains:
        for b in domains:
            if a != b:
                assert a.unify_with(b) is None


def test_range_domain():
    r = RangeDomain("x", 1, 5, 1)
    assert r.generate_domain() == ["1", "2", "3", "4"]

    assert str(r) == "x: range(1, 5, 1)"

    r = RangeDomain("x", 1, 5)
    assert r.generate_domain() == ["1", "2", "3", "4"]
    assert str(r) == "x: range(1, 5, 1)"

    r = RangeDomain("x", 0.1, 0.5, 0.1)
    assert str(r) == "x: range(0.1, 0.5, 0.1)"

    generated = r.generate_domain()
    expected = [0.1, 0.2, 0.3, 0.4]
    assert len(generated) == len(expected)
    for g, e in zip(generated, expected):
        assert abs(float(g) - e) < 0.00001

    r = make_range_domain("x", 1, 5, 1)
    assert r.generate_domain() == ["1", "2", "3", "4"]

    r = make_range_domain("x", 1, 5)
    assert r.generate_domain() == ["1", "2", "3", "4"]

    r = make_range_domain("x", 0.1, 0.5, 0.1)
    generated = r.generate_domain()
    expected = [0.1, 0.2, 0.3, 0.4]
    assert len(generated) == len(expected)
    for g, e in zip(generated, expected):
        assert abs(float(g) - e) < 0.00001

    with pytest.raises(Exception):
        make_range_domain("x", 1, 5, 10, 3)

    with pytest.raises(Exception):
        make_range_domain("x", 1)


def test_range_unification():
    r1 = RangeDomain("x", 1, 5, 1)
    r2 = RangeDomain("x", 1, 5, 1)
    r3 = RangeDomain("y", 1, 5, 1)
    r4 = RangeDomain("x", 2, 5, 1)
    r5 = RangeDomain("x", 1, 6, 1)
    r6 = RangeDomain("x", 1, 5, 2)
    o = FillerDomain("x", "x", [])

    assert r1.unify_with(r2) == r1
    assert r1.unify_with(o) == r1
    assert o.unify_with(r1) == r1

    domains = [r1, r3, r4, r5, r6]
    for a in domains:
        for b in domains:
            if a != b:
                assert a.unify_with(b) is None


def test_dependent_domain_simple():
    f = FillerDomain(
        "x",
        "name",
        [
            {"name": "Jack", "pronoun": "he"},
            {"name": "Jill", "pronoun": "she"},
        ],
    )

    d = FillerDependentDomain("pronoun", f)

    assert str(d) == "pronoun(x)"
    assert d.value({"x": "Jack"}) == "he"
    assert d.value({"x": "Jill"}) == "she"

    with pytest.raises(Exception):
        d.value({})

    with pytest.raises(Exception):
        d.value({"name": "Jack"})

    with pytest.raises(Exception):
        d.value({"a": "Jack"})


def test_dependent_domain_unification():
    f = FillerDomain(
        "x",
        "name",
        [
            {"name": "Jack", "pronoun": "he", "location": "Germany"},
            {"name": "Jill", "pronoun": "she", "location": "Nairobi"},
        ],
    )

    d1 = FillerDependentDomain("pronoun", f)
    d2 = FillerDomain("pronoun", "pronoun", ["he", "she"])
    d3 = FillerDependentDomain("location", f)
    d4 = FillerDomain("location", "location", ["Germany", "Nairobi"])

    assert d1.unify_with(d2) == d1
    assert d2.unify_with(d1) == d1

    r = RangeDomain("x", 1, 5, 1)

    failures = [f, r, d3, d4]
    for a in failures:
        assert d1.unify_with(a) is None
        assert a.unify_with(d1) is None
