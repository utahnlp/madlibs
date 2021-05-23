import itertools
import json
from collections import ChainMap
from typing import Any, Dict, Iterable, List, Tuple

from madlibs.template import MadLibTemplateGroup


class MadLibs:

    templates: MadLibTemplateGroup
    fillers: List[List[Dict[str, str]]]

    def __init__(self, templates: Dict[str, str], fillers: Dict[Any, Any]) -> None:
        self.templates = MadLibTemplateGroup(templates)
        self.fillers = self.__reformat_fillers(fillers)

    def __construct_numeric_fillers(self) -> List[List[Dict[str, str]]]:
        relevant_variables = self.templates.variables
        constraints = self.templates.constraints
        result = []

        for variable in relevant_variables:
            c = constraints[variable]
            tpe = c["type"]
            if tpe == "number" and "range" in c:
                start, end, step = c["range"]
                items = list(map(lambda i: {variable: str(i)}, range(start, end, step)))
                result.append(items)
        return result

    def __reformat_fillers(self, data: Dict[Any, Any]) -> List[List[Dict[str, str]]]:
        relevant_variables = self.templates.variables
        constraints = self.templates.constraints
        relevant_types = set(
            map(
                lambda variable: constraints[variable]["type"],
                relevant_variables,
            )
        )

        fillers: List[List[Dict[str, str]]] = []
        for key in data.keys():
            if isinstance(data[key][0], str):
                # Only relevant variables need to be kept
                if key in relevant_variables or key in relevant_types:
                    new_dict: List[Dict[str, str]] = []
                    for item in data[key]:
                        new_dict.append({key: item})
                    fillers.append(new_dict)
            else:
                # This set of fillers is a list of dictionaries. We can prune each
                #  dictionary to only keep relevant variables
                filtered_elements: List[Dict[str, str]] = []
                for item in data[key]:
                    filtered_dict: Dict[str, str] = {}
                    for k in item:
                        if k in relevant_variables or k in relevant_types:
                            filtered_dict[k] = item[k]
                    if len(filtered_dict) > 0:
                        filtered_elements.append(filtered_dict)

                if len(filtered_elements) > 0:
                    fillers.append(filtered_elements)

        # Next we need to add any numeric fillers that have been specified as ranges
        fillers.extend(self.__construct_numeric_fillers())

        return fillers

    def generate(self) -> Iterable[Tuple[Dict[str, str], Dict[str, str]]]:
        all_options = list(itertools.product(*self.fillers))
        seen = set()

        for parameters in all_options:
            params_dict: Dict[str, str] = dict(ChainMap(*parameters))
            rendered = self.templates.render(params_dict)

            # rendered will be None if a constraint in the template is not satisfied
            # by this filler
            if rendered is not None:
                relevant_params, generated = rendered
                identifier = hash(json.dumps(relevant_params))
                if identifier not in seen:
                    seen.add(identifier)
                    yield relevant_params, generated


def read_fillers(fillers_file: str) -> Dict[Any, Any]:
    with open(fillers_file, "r") as f:
        data = json.load(f)

    return data


def read_templates(templates_file: str) -> Dict[str, Dict[str, str]]:
    with open(templates_file, "r") as f:
        data = json.load(f)
    return data


def make_madlibs(fillers_file: str, templates_file: str) -> Dict[str, MadLibs]:
    fillers = read_fillers(fillers_file)
    templates = read_templates(templates_file)

    data = {}
    for key in templates:
        data[key] = MadLibs(templates[key], fillers)

    return data
