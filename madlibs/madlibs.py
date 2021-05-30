import itertools
import json
from typing import Dict, Iterable, List, Tuple

from madlibs.core import FillerType
from madlibs.group import MadLibTemplateGroup


class MadLibs:
    templates: MadLibTemplateGroup

    def __init__(
        self,
        templates: Dict[str, str],
        fillers: Dict[str, List[FillerType]],
    ) -> None:
        self.templates = MadLibTemplateGroup(templates, fillers)

    def __populate_domains(self) -> List[List[Tuple[str, str]]]:
        independent_domains = self.templates.realize_independent_domains()
        fillers = []
        for variable_name in independent_domains:
            variable_fillers = []
            for value in independent_domains[variable_name]:
                variable_fillers.append((variable_name, value))
            fillers.append(variable_fillers)
        return fillers

    def generate(self) -> Iterable[Tuple[Dict[str, str], Dict[str, str]]]:
        fillers = self.__populate_domains()

        all_options = itertools.product(*fillers)
        seen = set()

        for parameters in all_options:
            independent_fillers = {}
            for item in parameters:
                independent_fillers[item[0]] = item[1]

            params_dict = self.templates.realize_dependent_domains(independent_fillers)

            rendered = self.templates.render(params_dict)

            # rendered will be None if a constraint in the template is not satisfied
            # by this filler
            if rendered is not None:
                relevant_params, generated = rendered
                identifier = hash(json.dumps(relevant_params))
                if identifier not in seen:
                    seen.add(identifier)
                    yield relevant_params, generated
