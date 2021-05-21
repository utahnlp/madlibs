from typing import Dict, Set, Tuple

from jinja2 import Environment, Template, meta


class MadLibTemplate:
    template: Template
    variables: Set[str]

    def __init__(self, template: str) -> None:
        self.template = Template(template, autoescape=True)
        env = Environment(autoescape=True)
        ast = env.parse(template)
        self.variables = meta.find_undeclared_variables(ast)

    def render(self, fillers: Dict[str, str]) -> str:
        return self.template.render(**fillers)


class MadLibTemplateGroup:
    templates: Dict[str, MadLibTemplate]
    variables: Set[str]

    def __init__(self, templates: Dict[str, str]) -> None:
        self.templates = {}
        self.variables = set()
        for k in templates:
            t = MadLibTemplate(templates[k])
            self.templates[k] = t
            self.variables.update(t.variables)

    def render(self, fillers: Dict[str, str]) -> Tuple[Dict[str, str], Dict[str, str]]:
        relevant_params: Dict[str, str] = {}
        generated: Dict[str, str] = {}
        for k in self.templates:
            generated[k] = self.templates[k].render(fillers)

        for v in self.variables:
            relevant_params[v] = fillers[v]

        return relevant_params, generated
