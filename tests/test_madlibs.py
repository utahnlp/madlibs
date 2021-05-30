import pytest

from madlibs.madlibs import MadLibs
from madlibs.utils import make_madlibs


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


def test_generate_unique():
    template = {"s1": "{{person}} likes {{object}}."}

    fillers = {
        "object": ["cake", "coffee", "coffee"],
        "person": ["Jack", "Jill", "Jill"],
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
    template = {"s1": "{{name}} likes {{object}}. {{pronoun | title}} does."}

    fillers = {
        "object": ["cake", "coffee"],
        "person": [
            {"name": "Jack", "pronoun": "he"},
            {"name": "Jill", "pronoun": "she"},
        ],
    }
    m = MadLibs(template, fillers)
    g = list(m.generate())
    assert len(g) == 4

    for item in g:
        params = item[0]
        text = item[1]
        assert "s1" in text
        n = params["name"]
        o = params["object"]
        p = params["pronoun"].capitalize()
        assert text["s1"] == f"{n} likes {o}. {p} does."


def test_from_file():
    m = make_madlibs("data/test_fillers.json", "data/test_templates.json")
    assert "group1" in m
    g = list(m["group1"].generate())

    assert len(g) == 4

    for item in g:
        params = item[0]
        text = item[1]
        assert "s1" in text
        n = params["name"]
        o = params["object"]
        p = params["pronoun"].capitalize()
        assert text["s1"] == f"{n} likes {o}. {p} does."


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
    with pytest.raises(Exception):
        MadLibs(templates, fillers)


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


def test_equals_numeric():
    s = '{{n | range(0, 10, 2)}} equals {{m | range(0, 10, 2) | equals("n")}}'
    templates = {"s": s}
    m = MadLibs(templates, {})

    items = list(m.generate())

    assert len(items) == 5
    sentences = set(map(lambda item: item[1]["s"], items))

    for i in range(0, 10, 2):
        assert f"{i} equals {i}" in sentences


def test_equals_string():
    s = '{{n | type("person")}} equals {{m | type("person") | equals("n")}}'
    templates = {"s": s}
    m = MadLibs(templates, {"person": ["A", "B"]})

    items = list(m.generate())

    assert len(items) == 2
    sentences = set(map(lambda item: item[1]["s"], items))

    for i in ["A", "B"]:
        assert f"{i} equals {i}" in sentences


def test_less_than():
    s = '{{n | range(0, 10, 2) | less_than("m")}} less than {{m | range(0, 10, 2)}}'
    templates = {"s": s}
    items = list(MadLibs(templates, {}).generate())

    assert len(items) == 10
    sentences = set(map(lambda item: item[1]["s"], items))

    for m in range(0, 10, 2):
        for n in range(0, m, 2):
            assert f"{n} less than {m}" in sentences


def test_greater_than():
    s = '{{n | range(0, 10, 2) | greater_than("m")}} greater than {{m | range(0, 10, 2)}}'
    templates = {"s": s}
    items = list(MadLibs(templates, {}).generate())

    assert len(items) == 10
    sentences = set(map(lambda item: item[1]["s"], items))

    for n in range(0, 10, 2):
        for m in range(0, n, 2):
            assert f"{n} greater than {m}" in sentences


def test_constraint_chaining():
    s = (
        "{{n | range(0, 5, 1)}} and {{m | range(1, 6, 1)}} are both "
        + 'less than {{r | range(0, 7, 1) | greater_than("m") | greater_than("n")}}.'
    )
    templates = {"s": s}
    m = MadLibs(templates, {})
    items = list(m.generate())
    sentences = set(map(lambda item: item[1]["s"], items))

    count = 0
    for i in range(0, 5):
        for j in range(1, 6):
            for k in range(0, 7):
                if i < k and j < k:
                    assert f"{i} and {j} are both less than {k}." in sentences
                    count = count + 1

    assert len(items) == count


def test_generate_with_dependents():
    fillers = {
        "person": [
            {"name": "Jack", "pronoun": "he"},
            {"name": "Jill", "pronoun": "she"},
        ],
        "location": ["New York", "Chicago"],
    }

    template = {"a": '{{p | type("name")}} {{pronoun}}'}
    m = MadLibs(template, fillers)

    items = list(m.generate())
    sentences = set(map(lambda item: item[1]["a"], items))
    assert len(sentences) == 2
    assert "Jack he" in sentences
    assert "Jill she" in sentences
