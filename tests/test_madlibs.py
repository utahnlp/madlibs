import pytest

from madlibs import MadLibs, __version__, make_madlibs


def test_version():
    assert __version__ == "0.1.0"


def test_generate():
    template = {"s1": "{{person}} likes {{object}}."}

    fillers = {
        "object": ["cake", "coffee"],
        "person": ["Jack", "Jill"],
    }
    m = MadLibs(template, fillers)
    g = list(m.generate())
    assert len(g) == 4

    for item in g:
        params = item[0]
        text = item[1]
        assert "s1" in text
        assert text["s1"] == f"{params['person']} likes {params['object']}."


def test_generate_from_dictionary():
    template = {"s1": "{{name}} likes {{object}}. {{pronoun}} does."}

    fillers = {
        "object": ["cake", "coffee"],
        "person": [
            {"name": "Jack", "pronoun": "He"},
            {"name": "Jill", "pronoun": "She"},
        ],
    }
    m = MadLibs(template, fillers)
    g = list(m.generate())
    assert len(g) == 4

    for item in g:
        params = item[0]
        text = item[1]
        assert "s1" in text
        assert (
            text["s1"]
            == f"{params['name']} likes {params['object']}. {params['pronoun']} does."
        )


def test_from_file():
    m = make_madlibs("data/test_fillers.json", "data/test_templates.json")
    assert "group1" in m
    g = list(m["group1"].generate())

    assert len(g) == 4

    for item in g:
        params = item[0]
        text = item[1]
        assert "s1" in text
        assert (
            text["s1"]
            == f"{params['name']} likes {params['object']}. {params['pronoun']} does."
        )


def test_filler_constraints():
    s1 = '{{person}} is a {{n | range(2, 10, 2)}}-time {{x | type("profession")}}.'
    s2 = '{{person}} is a {{m | range(1, 9, 2)}}-time {{x | type("profession") | title}}.'

    templates = {"s1": s1, "s2": s2}
    fillers = {
        "person": ["John", "Mary"],
        "profession": ["president", "convict"],
    }
    m = MadLibs(templates, fillers)

    items = list(m.generate())
    assert len(items) == 64

    sentences = set(map(lambda item: item[1]["s1"], items))

    for p in {"John", "Mary"}:
        for n in {"2", "4", "6", "8"}:
            for j in {"president", "convict"}:
                assert f"{p} is a {n}-time {j}." in sentences

    sentences = set(map(lambda item: item[1]["s2"], items))

    for p in {"John", "Mary"}:
        for n in {"1", "3", "5", "7"}:
            for j in {"President", "Convict"}:
                assert f"{p} is a {n}-time {j}." in sentences


def test_multiple_type_exception():
    s = '{{a | type("person") | type("profession")}}'
    templates = {"s": s}
    fillers = {
        "person": ["John", "Mary"],
        "profession": ["president", "convict"],
    }

    with pytest.raises(Exception):
        MadLibs(templates, fillers)


def test_filler_pruning():
    s1 = '{{person}} is a {{x | type("profession")}}.'

    templates = {"s1": s1}
    fillers = {
        "person": ["John", "Mary"],
        "profession": ["president", "convict"],
        "adjective": ["great", "bad"],
        "dummy": [
            {"a": "b", "c": "d"},
            {"a": "b1", "c": "d1"},
        ],
    }
    m = MadLibs(templates, fillers)

    items = list(m.generate())
    assert len(items) == 4

    for item in items:
        assignments, sentences = item
        assert len(assignments) == 2
        assert "person" in assignments
        assert "x" in assignments

        p = assignments["person"]
        j = assignments["x"]

        assert "s1" in sentences
        assert sentences["s1"] == f"{p} is a {j}."


def test_valid_types():
    s1 = '{{person}} is a {{x | type("profession")}}.'

    templates = {"s1": s1}
    fillers = {
        "person": ["John", "Mary"],
    }

    m = MadLibs(templates, fillers)

    with pytest.raises(Exception):
        list(m.generate())


def test_consistent_types():
    s1 = '{{person}} is a {{x | type("profession")}}.'

    s2 = '{{x | type("person")}} is a {{profession}}.'

    templates = {"s1": s1, "s2": s2}
    fillers = {
        "person": ["John", "Mary"],
        "profession": ["president", "convict"],
    }
    with pytest.raises(Exception):
        MadLibs(templates, fillers)
