import pytest

from madlibs.domains import FillerDependentDomain, FillerDomain
from madlibs.group import MadLibTemplateGroup


def test_template_group_simple():
    templates = {
        "a": "{{name}} ate {{food}}.",
        "b": "{{pronoun | title}} ate something.",
        "c": "{{pronoun | title}} is not hungry.",
    }

    fillers = {
        "person": [
            {"name": "Jack", "pronoun": "he"},
            {"name": "Jill", "pronoun": "she"},
        ],
        "food": ["lasagna", "roti"],
    }

    g = MadLibTemplateGroup(templates, fillers)

    assert len(g.variables) == 3
    assert "name" in g.variables
    assert "food" in g.variables
    assert "pronoun" in g.variables

    assert len(g.constraints) == 3
    for v in ["name", "food", "pronoun"]:
        assert len(g.constraints[v]) == 0

    assert isinstance(g.domains["name"], FillerDomain)
    assert isinstance(g.domains["food"], FillerDomain)
    assert isinstance(g.domains["pronoun"], FillerDependentDomain)

    assert len(g.templates) == 3
    assert "a" in g.templates
    assert "b" in g.templates
    assert "c" in g.templates

    variables, generated = g.render({"name": "Jack", "food": "roti", "pronoun": "he"})
    assert len(generated) == 3
    assert "a" in generated
    assert generated["a"] == "Jack ate roti."

    assert "b" in generated
    assert generated["b"] == "He ate something."

    assert "c" in generated
    assert generated["c"] == "He is not hungry."


def test_template_group_missing_filler_exception():
    templates = {
        "a": "{{name}} ate {{food}}.",
        "b": "{{pronoun | title}} ate something.",
    }

    fillers = {
        "person": [
            {"name": "Jack", "pronoun": "he"},
            {"name": "Jill", "pronoun": "she"},
        ],
        "food": ["lasagna", "roti"],
    }

    g = MadLibTemplateGroup(templates, fillers)

    with pytest.raises(Exception):
        g.render({"name": "Jack", "food": "roti"})
