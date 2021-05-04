import itertools
import json
from collections import ChainMap
from typing import Dict, List, Tuple, Set

import re


class MadLibs:
    templates: Dict[str, str]
    variables: Set[str]

    def __init__(self, templates: Dict[str, str], fillers):
        self.templates = templates
        self.fillers = self.__reformat_fillers(fillers)
        self.variables = self.__find_variables(templates)

    def __find_variables(self, templates) -> Set[str]:
        regex = re.compile("{{([^}]*)}}")
        variables = set()
        for key in templates:
            template = templates[key]
            variables.update(regex.findall(template))

        return variables

    def __reformat_fillers(self, data):
        fillers = []
        for key in data.keys():
            if isinstance(data[key][0], str):
                new_dict = []
                for item in data[key]:
                    new_dict.append({key: item})
                fillers.append(new_dict)
            else:
                fillers.append(data[key])
        return fillers

    def generate(self):
        all_options = list(itertools.product(*self.fillers))
        seen = set()

        # todo: self.variables can be used to make this more efficient
        for parameters in all_options:
            params_dict: Dict[str, str] = dict(ChainMap(*parameters))
            relevant_params = dict()
            generated = {}
            for key in self.templates:
                template = self.templates[key]
                generated[key], relevant_keys = self.apply(template, params_dict)

                relevant_params.update(
                    dict(
                        map(
                            lambda k: [k, params_dict[k]],
                            relevant_keys,
                        )
                    )
                )

            identifier = hash(json.dumps(relevant_params))
            if identifier not in seen:
                seen.add(identifier)
                yield {"params": relevant_params, "text": generated}

    def apply(self, template: str, parameters: Dict[str, str]) -> Tuple[str, Set[str]]:
        result = template
        relevant_keys = set()
        for key in parameters.keys():
            identifier = "{{" + key + "}}"
            if identifier in template:
                result = result.replace(identifier, parameters[key])
                relevant_keys.add(key)
        return result, relevant_keys


def read_fillers(fillers_file):
    with open(fillers_file, "r") as f:
        data = json.load(f)

    return data


def read_templates(templates_file):
    with open(templates_file, "r") as f:
        data = json.load(f)
    return data


def make_madlibs(fillers_file, templates_file):
    fillers = read_fillers(fillers_file)
    templates = read_templates(templates_file)

    data = {}
    for key in templates:
        data[key] = MadLibs(templates[key], fillers)

    return data
