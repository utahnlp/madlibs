from typing import Dict, List, Optional, Set, Tuple

import jinja2.nodes as jnodes
from jinja2 import Environment, Template, meta

from madlibs.constraints import Constraint, make_constraint, register_known_constraints
from madlibs.core import FillerType
from madlibs.domains import (
    Domain,
    FillerDependentDomain,
    make_domain,
    make_filler_domain,
    register_known_domains,
    try_unify,
)


class MadLibTemplate:
    template: Template
    variables: Set[str]
    constraints: Dict[str, List[Constraint]]
    domains: Dict[str, Domain]

    def __init__(
        self,
        template: str,
        fillers: Dict[str, List[FillerType]],
        collected_dependents: Dict[str, Domain] = None,
    ) -> None:
        env = Environment(autoescape=True)
        register_known_domains(env)
        register_known_constraints(env)

        self.template = env.from_string(template)
        self.domains = {}
        self.constraints = {}

        ast = env.parse(template)
        self.variables = meta.find_undeclared_variables(ast)

        if collected_dependents is None:
            collected_dependents = {}
        self.__collect_constraints(ast, fillers, collected_dependents)

        # At this point, every variable should have a domain
        for v in self.variables:
            if v not in self.domains:
                raise Exception(f"Missing domain for {v}")

    def __walk_filter_node(
        self,
        node: jnodes.Filter,
        fillers: Dict[str, List[FillerType]],
        collected_dependents: Dict[str, Domain],
    ) -> Tuple[str, List[Constraint], Domain, List[Domain]]:
        n = node
        filters = []

        while not isinstance(n, jnodes.Name):
            filters.append((n.name, n.args))  # type: ignore
            n = n.node  # type: ignore

        # at this point, we are on a Name node.
        variable_name: str = n.name  # type: ignore

        node_constraints: List[Constraint] = []
        domain: Optional[Domain] = None
        dependent_domains: List[Domain] = []

        for constraint_name, raw_args in filters:
            args = list(map(lambda a: a.value, raw_args))
            domains = make_domain(constraint_name, variable_name, fillers, *args)

            if len(domains) >= 1:
                if domain is not None:
                    raise Exception(f"Multiple types assigned for {variable_name}")
                domain = domains[0]
                domain = self.__try_reconcile_with_collected_dependent(
                    variable_name, domains[0], collected_dependents
                )

                dependent_domains.extend(domains[1:])

            constraint = make_constraint(constraint_name, variable_name, *args)
            if constraint is not None:
                node_constraints.append(constraint)

        if domain is None:
            if variable_name in collected_dependents:
                domain = collected_dependents[variable_name]
            else:
                domains = make_filler_domain(variable_name, fillers, variable_name)
                domain = domains[0]
                dependent_domains.extend(domains[1:])

        return variable_name, node_constraints, domain, dependent_domains

    def __collect_constraints(
        self,
        ast: jnodes.Template,
        fillers: Dict[str, List[FillerType]],
        collected_dependents: Dict[str, Domain],
    ) -> None:
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
                for node in nodes:
                    if isinstance(node, jnodes.Name):
                        name = node.name  # type: ignore

                        domains = make_filler_domain(name, fillers, name)
                        domain = self.__try_reconcile_with_collected_dependent(
                            name, domains[0], collected_dependents
                        )
                        self.domains[name] = domain

                        self.__update_dependents(collected_dependents, domains[1:])
                        self.constraints[name] = []
                    elif isinstance(node, jnodes.Filter):
                        name = node.name  # type: ignore

                        name, constraints, domain, dependents = self.__walk_filter_node(
                            node,
                            fillers,
                            collected_dependents,
                        )
                        if name not in self.domains:
                            if name in collected_dependents:
                                self.domains[name] = try_unify(
                                    collected_dependents[name], domain
                                )
                            else:
                                self.domains[name] = domain
                        else:
                            self.domains[name] = try_unify(self.domains[name], domain)
                        self.__update_dependents(collected_dependents, dependents)
                        self.constraints[name] = constraints
            else:
                raise Exception(f"Expecting output, found {output}")

    def __update_dependents(
        self, collected_dependents: Dict[str, Domain], dependents: List[Domain]
    ) -> None:
        for d in dependents:
            v = d.variable_name
            if v not in collected_dependents:
                # only add something as a dependent if it is not a parent already
                is_parent = False
                for name in collected_dependents:
                    dep = collected_dependents[name]
                    if isinstance(dep, FillerDependentDomain):
                        if v == dep.parent.variable_name:
                            is_parent = True
                            break

                if not is_parent:
                    collected_dependents[v] = d
            else:
                unified = collected_dependents[v].unify_with(d)
                if unified is None:
                    other_type = collected_dependents[v].variable_type
                    raise Exception(
                        f"{other_type} cannot be unified with {d.variable_type}"
                    )

    def __try_reconcile_with_collected_dependent(
        self,
        variable_name: str,
        domain: Domain,
        collected_dependents: Dict[str, Domain],
    ) -> Domain:
        if variable_name in collected_dependents:
            return try_unify(collected_dependents[variable_name], domain)
        else:
            return domain

    def render(self, fillers: Dict[str, str]) -> str:
        # At this point, all the constraints have been resolved from the template group
        # So we should safely be able to blindly render the template. But to be safe,
        # let us ensure that all the variables have a filler.

        for v in self.variables:
            if v not in fillers:
                raise Exception(f"Missing filler for variable {v}")
        return self.template.render(**fillers)
