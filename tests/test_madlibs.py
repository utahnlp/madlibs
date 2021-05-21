from madlibs import MadLibs, make_madlibs
from madlibs import __version__


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
