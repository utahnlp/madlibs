import json
from typing import Any, Dict

from madlibs.madlibs import MadLibs


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
