import pytest

from madlibs.template import MadLibTemplate


def test_template_simple():
    fillers = {
        "item": ["book", "page"],
        "location": ["table", "chair"],
    }
    m = MadLibTemplate("The {{item}} is on the {{location}}.", fillers)

    generated = m.render({"item": "book", "location": "table"})
    expected = "The book is on the table."

    assert expected == generated


def test_template_repeated_variable():
    fillers = {
        "item": ["book", "page"],
        "location": ["table", "chair"],
    }
    m = MadLibTemplate("The {{item}} is on the {{item}}.", fillers)
    generated = m.render({"item": "book", "location": "table"})
    expected = "The book is on the book."

    assert expected == generated


def test_template_missing_domain_exception():
    fillers = {
        "item": ["book", "page"],
    }
    with pytest.raises(Exception):
        MadLibTemplate("The {{item}} is on the {{location}}.", fillers)

    fillers = {"thing": [{"item": "book"}, {"item": "page"}]}
    with pytest.raises(Exception):
        MadLibTemplate("The {{item}} is on the {{location}}.", fillers)


def test_template_missing_filler_exception():
    fillers = {
        "item": ["book", "page"],
        "location": ["table", "chair"],
    }
    m = MadLibTemplate("The {{item}} is on the {{location}}.", fillers)

    with pytest.raises(Exception):
        m.render({"item": "book"})


def test_template_parameters_simple():
    fillers = {
        "item": ["book", "page"],
        "location": ["table", "chair"],
    }
    m = MadLibTemplate("The {{item}} is on the {{location}}.", fillers)

    assert len(m.variables) == 2
    assert "item" in m.variables
    assert "location" in m.variables

    assert len(m.domains) == 2
    assert m.domains["item"].variable_name == "item"
    assert m.domains["item"].variable_type == "item"

    assert m.domains["location"].variable_name == "location"
    assert m.domains["location"].variable_type == "location"

    assert len(m.constraints) == 2
    assert len(m.constraints["item"]) == 0
    assert len(m.constraints["location"]) == 0


def test_template_with_filters():
    fillers = {
        "item": ["book", "page"],
        "location": ["table", "chair"],
    }
    m = MadLibTemplate("The {{item | upper}} is on the {{location}}.", fillers)

    generated = m.render({"item": "book", "location": "table"})
    expected = "The BOOK is on the table."

    assert expected == generated

    m = MadLibTemplate(
        "The {{item | upper}} is on the {{location | lower | title}}.", fillers
    )

    generated = m.render({"item": "book", "location": "table"})
    expected = "The BOOK is on the Table."
    assert expected == generated


def test_template_parameters_with_filters():
    fillers = {
        "item": ["book", "page"],
        "location": ["table", "chair"],
    }
    m = MadLibTemplate("The {{item | upper}} is on the {{location}}.", fillers)

    assert len(m.variables) == 2
    assert "item" in m.variables
    assert "location" in m.variables

    assert len(m.domains) == 2
    assert m.domains["item"].variable_name == "item"
    assert m.domains["item"].variable_type == "item"

    assert m.domains["location"].variable_name == "location"
    assert m.domains["location"].variable_type == "location"

    assert len(m.constraints) == 2
    assert len(m.constraints["item"]) == 0
    assert len(m.constraints["location"]) == 0

    m = MadLibTemplate(
        "The {{item | upper}} is on the {{location | lower | title}}.", fillers
    )

    assert len(m.variables) == 2
    assert "item" in m.variables
    assert "location" in m.variables

    assert len(m.domains) == 2
    assert m.domains["item"].variable_name == "item"
    assert m.domains["item"].variable_type == "item"

    assert m.domains["location"].variable_name == "location"
    assert m.domains["location"].variable_type == "location"

    assert len(m.constraints) == 2
    assert len(m.constraints["item"]) == 0
    assert len(m.constraints["location"]) == 0


def test_template_with_domain():
    fillers = {
        "thing": ["book", "page"],
        "location": ["table", "chair"],
        "place": ["table", "chair"],
    }
    m = MadLibTemplate(
        'The {{item | upper | type("thing")}} is on the {{location}}.', fillers
    )

    generated = m.render({"item": "book", "location": "table"})
    expected = "The BOOK is on the table."

    assert expected == generated

    m = MadLibTemplate(
        'The {{thing | upper | type("thing")}} is '
        + 'on the {{location | lower | type("place") | title}}.',
        fillers,
    )
    generated = m.render({"thing": "book", "location": "table"})
    expected = "The BOOK is on the Table."
    assert expected == generated


def test_template_parameters_with_domain():
    fillers = {
        "thing": ["book", "page"],
        "location": ["table", "chair"],
        "place": ["table", "chair"],
    }
    m = MadLibTemplate(
        'The {{item | upper | type("thing")}} is on the {{location}}.', fillers
    )

    assert len(m.variables) == 2
    assert "item" in m.variables
    assert "location" in m.variables

    assert len(m.domains) == 2
    assert m.domains["item"].variable_name == "item"
    assert m.domains["item"].variable_type == "thing"

    assert m.domains["location"].variable_name == "location"
    assert m.domains["location"].variable_type == "location"

    assert len(m.constraints) == 2
    assert len(m.constraints["item"]) == 0
    assert len(m.constraints["location"]) == 0

    m = MadLibTemplate(
        'The {{item | upper | type("thing")}} is '
        + 'on the {{location | lower | type("place") | title}}.',
        fillers,
    )

    assert len(m.variables) == 2
    assert "item" in m.variables
    assert "location" in m.variables

    assert len(m.domains) == 2
    assert m.domains["item"].variable_name == "item"
    assert m.domains["item"].variable_type == "thing"

    assert m.domains["location"].variable_name == "location"
    assert m.domains["location"].variable_type == "place"

    assert len(m.constraints) == 2
    assert len(m.constraints["item"]) == 0
    assert len(m.constraints["location"]) == 0


def test_template_repeated_variables_domains():
    fillers = {"a": ["A1", "A2"], "b": ["B1", "B2"]}
    m = MadLibTemplate('{{a1 | type("a")}} is {{a1 | type("a")}}.', fillers)
    assert len(m.variables) == 1
    assert "a1" in m.variables

    assert m.domains["a1"].variable_name == "a1"
    assert m.domains["a1"].variable_type == "a"
    assert len(m.domains) == 1

    with pytest.raises(Exception):
        # the same variable can't have different types
        MadLibTemplate('{{a1 | type("a")}} is {{a1 | type("b")}}.', fillers)


def test_template_unification_failures():
    fillers = {
        "person": [
            {"name": "Jack", "pronoun": "he"},
            {"name": "Jill", "pronoun": "she"},
        ],
        "location": ["New York", "Chicago"],
    }

    template = '{{p | type("person")}} {{pronoun}} {{pronoun | type("location")}}'
    with pytest.raises(Exception):
        MadLibTemplate(template, fillers)

    template = '{{p | type("name")}} {{pronoun}} {{pronoun | type("location")}}'
    with pytest.raises(Exception):
        MadLibTemplate(template, fillers)

    template = '{{p | type("name")}} {{pronoun}} {{pronoun | range(1, 5, 1)}}'
    with pytest.raises(Exception):
        MadLibTemplate(template, fillers)

    template = '{{p | type("name")}} {{pronoun | type("location")}} {{pronoun}}'
    with pytest.raises(Exception):
        MadLibTemplate(template, fillers)

    template = '{{name}} {{pronoun}} {{pronoun | type("location")}}'
    with pytest.raises(Exception):
        MadLibTemplate(template, fillers)

    template = '{{name}} {{pronoun}} {{pronoun | type("name")}}'
    with pytest.raises(Exception):
        MadLibTemplate(template, fillers)
