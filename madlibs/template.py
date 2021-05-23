from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import jinja2.nodes as jnodes
from jinja2 import Environment, Template, meta


class MadLibTemplate:
    template: Template
    variables: Set[str]
    constraints: Dict[str, Dict[str, Any]]

    def __init__(self, template: str) -> None:
        def dummy_constraint_processor(x: str, value: str) -> str:
            return x

        def dummy_range_processor(x: str, start: Any, end: Any, step: Any) -> str:
            return x

        env = Environment(autoescape=True)

        env.filters["type"] = dummy_constraint_processor
        env.filters["range"] = dummy_range_processor
        ast = env.parse(template)
        self.constraints = self.__collect_constraints(ast)
        self.template = env.from_string(template)
        self.variables = meta.find_undeclared_variables(ast)

    def __walk_ast(
        self,
        ast: jnodes.Template,
        filter_processors: List[
            Callable[
                [jnodes.Filter, Dict[str, Any]],
                Dict[str, Any],
            ]
        ],
    ) -> Dict[str, Dict[str, Any]]:
        # For some reason mypy doesn't seem to know about the types within
        # jinja2.nodes. So there will be a lot of ignores here.
        if len(ast.body) > 1:  # type: ignore
            raise Exception("Found a longer body than expected!")
        else:
            output = ast.body[0]  # type: ignore
            if isinstance(output, jnodes.Output):
                nodes = output.nodes  # type: ignore
                # now each node is either a filter or a name or data. We don't care
                # about the names
                variable_info = {}
                for node in nodes:
                    if isinstance(node, jnodes.Name):
                        name = node.name  # type: ignore
                        variable_info[name] = {"type": name}
                    elif isinstance(node, jnodes.Filter):
                        n = node
                        info: Dict[str, Dict[str, str]] = {}
                        while not isinstance(n, jnodes.Name):
                            for f in filter_processors:
                                f(n, info)
                            n = n.node  # type: ignore
                        name = n.name  # type: ignore
                        if "type" not in info:
                            info["type"] = name
                        variable_info[name] = info
                return variable_info
            else:
                raise Exception(f"Expecting output, found {output}")

    def __collect_constraints(self, ast: jnodes.Template) -> Dict[str, Dict[str, Any]]:
        def named_constraint(
            name: str,
        ) -> Callable[[jnodes.Filter, Dict[str, Any]], Dict[str, Any]]:
            def f(filter: jnodes.Filter, info: Dict[str, Any]) -> Dict[str, Any]:
                if filter.name == name:  # type: ignore
                    if name in info:
                        raise Exception(f"Duplicate {name}")
                    info[name] = filter.args[0].value  # type: ignore
                return info

            return f

        def range_processor(
            filter: jnodes.Filter,
            info: Dict[str, Any],
        ) -> Dict[str, Any]:
            if filter.name == "range" and len(filter.args) == 3:  # type: ignore
                start = filter.args[0].value  # type: ignore
                end = filter.args[1].value  # type: ignore
                step = filter.args[2].value  # type: ignore
                info["range"] = (start, end, step)
                info["type"] = "number"
            return info

        filter_processors = [named_constraint("type"), range_processor]

        return self.__walk_ast(ast, filter_processors)

    def render(self, fillers: Dict[str, str]) -> str:
        # At this point, all the constraints have been resolved from the template group
        # So we should safely be able to blindly render the template.
        return self.template.render(**fillers)


class MadLibTemplateGroup:
    templates: Dict[str, MadLibTemplate]
    variables: Set[str]
    constraints: Dict[str, Dict[str, Any]]

    def __init__(self, templates: Dict[str, str]) -> None:
        self.templates = {}
        self.variables = set()
        self.constraints = {}
        for k in templates:
            t = MadLibTemplate(templates[k])
            self.templates[k] = t
            self.variables.update(t.variables)
            self.__merge_constraints(t.variables, t.constraints)

        # every variable should have a constraint
        if len(self.variables) != len(self.constraints):
            raise Exception("Not all variables have constraints")

    def __merge_constraints(
        self,
        variables: Set[str],
        constraints: Dict[str, Dict[str, Any]],
    ) -> None:
        for v in variables:
            if v not in self.constraints:
                self.constraints[v] = {}

        for key in constraints:
            value = constraints[key]
            for item_key in value:
                item_value = value[item_key]
                if item_key not in self.constraints[key]:
                    self.constraints[key][item_key] = item_value
                else:
                    current_value = self.constraints[key][item_key]
                    if current_value != item_value:
                        # It looks like the variable is declared with different types
                        # in different places.
                        raise Exception(f"Type error for {key}")

    def __reconcile_fillers(self, fillers: Dict[str, str]) -> Dict[str, str]:
        # At the end of this function, every variable that is in the template should
        # have a value

        result: Dict[str, str] = {}
        for variable_name in self.variables:
            constraint = self.constraints[variable_name]

            # First the type constraint. If the variable name is its type, then we
            # can just use the filler provided. Otherwise, the variable is associated
            # with the filler of the corresponding type

            variable_type = constraint["type"]
            if variable_type == variable_name:
                result[variable_name] = fillers[variable_name]
            elif variable_type in fillers:
                result[variable_name] = fillers[variable_type]
            elif variable_type == "number" and variable_name in fillers:
                result[variable_name] = fillers[variable_name]

        return result

    def render(
        self, fillers: Dict[str, str]
    ) -> Optional[Tuple[Dict[str, str], Dict[str, str]]]:
        relevant_params: Dict[str, str] = {}
        generated: Dict[str, str] = {}

        reconciled_fillers = self.__reconcile_fillers(fillers)

        # At this point, all variables should be in the reconciled fillers. If not, we
        # need to raise an exception

        for v in self.variables:
            if v not in reconciled_fillers:
                raise Exception(f"Variable {v} assigned any fillers")

        for k in self.templates:
            generated[k] = self.templates[k].render(reconciled_fillers)

        for v in self.variables:
            relevant_params[v] = reconciled_fillers[v]

        return relevant_params, generated
