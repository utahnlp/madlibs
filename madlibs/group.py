from typing import Dict, List, Optional, Set, Tuple

from madlibs.constraints import Constraint
from madlibs.core import FillerType
from madlibs.domains import DependentDomain, Domain, IndependentDomain, try_unify
from madlibs.template import MadLibTemplate


class MadLibTemplateGroup:
    templates: Dict[str, MadLibTemplate]
    variables: Set[str]
    constraints: Dict[str, List[Constraint]]
    domains: Dict[str, Domain]

    def __init__(
        self,
        templates: Dict[str, str],
        fillers: Dict[str, List[FillerType]],
    ) -> None:
        self.templates = {}
        self.variables = set()
        self.constraints = {}
        self.domains = {}
        collected_dependents: Dict[str, Domain] = {}
        for template_name in templates:
            t = MadLibTemplate(templates[template_name], fillers, collected_dependents)
            self.templates[template_name] = t
            self.variables.update(t.variables)

            for variable_name in t.variables:
                if variable_name not in self.constraints:
                    self.constraints[variable_name] = []
                self.constraints[variable_name].extend(t.constraints[variable_name])
                domain = t.domains[variable_name]
                if variable_name not in self.domains:
                    self.domains[variable_name] = domain
                else:
                    old_domain = self.domains[variable_name]
                    self.domains[variable_name] = try_unify(old_domain, domain)

        # every variable should have a constraint
        if len(self.variables) != len(self.constraints):
            raise Exception("Not all variables have constraints")

        # every variable should have a domain
        if len(self.variables) != len(self.domains):
            raise Exception("Not all variables have domains!")

    def realize_independent_domains(self) -> Dict[str, List[str]]:
        output: Dict[str, List[str]] = {}

        for variable in self.variables:
            domain = self.domains[variable]
            if isinstance(domain, IndependentDomain):
                values = domain.generate_domain()
                output[domain.variable_name] = values
        return output

    def realize_dependent_domains(self, fillers: Dict[str, str]) -> Dict[str, str]:
        output = {}
        for variable in self.variables:
            domain = self.domains[variable]
            if isinstance(domain, DependentDomain):
                output[variable] = domain.value(fillers)
            else:
                output[variable] = fillers[variable]
        return output

    def __check_constraints(self, fillers: Dict[str, str]) -> bool:
        for variable in self.variables:
            for c in self.constraints[variable]:
                if not c.check(fillers):
                    return False
        return True

    def render(
        self, fillers: Dict[str, str]
    ) -> Optional[Tuple[Dict[str, str], Dict[str, str]]]:
        # All variables should be in the reconciled fillers. If not, we
        # need to raise an exception
        for v in self.variables:
            if v not in fillers:
                raise Exception(f"Variable {v} assigned any fillers")

        # Next if any constraint is violated, we need to return None
        if not self.__check_constraints(fillers):
            return None
        else:
            relevant_params: Dict[str, str] = {}
            generated: Dict[str, str] = {}
            for k in self.templates:
                generated[k] = self.templates[k].render(fillers)

            for v in self.variables:
                relevant_params[v] = fillers[v]

            return relevant_params, generated
