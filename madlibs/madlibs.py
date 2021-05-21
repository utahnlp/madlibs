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
        self.fillers = self.__reformat_fillers(fillers)  # noqa: ANN001

    def __reformat_fillers(self, data: Dict[Any, Any]) -> List[List[Dict[str, str]]]:
        fillers: List[List[Dict[str, str]]] = []
        for key in data.keys():
            if isinstance(data[key][0], str):
                new_dict: List[Dict[str, str]] = []
                for item in data[key]:
                    new_dict.append({key: item})
                fillers.append(new_dict)
            else:
                fillers.append(data[key])
        return fillers

    def generate(self) -> Iterable[Tuple[Dict[str, str], Dict[str, str]]]:
        all_options = list(itertools.product(*self.fillers))
        seen = set()

        # todo: self.variables can be used to make this more efficient
        for parameters in all_options:
            params_dict: Dict[str, str] = dict(ChainMap(*parameters))
            relevant_params, generated = self.templates.render(params_dict)

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
