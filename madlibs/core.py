from typing import Dict, List, Union

FillerType = Union[str, Dict[str, str]]

known_domains: List[str] = ["type", "range"]
known_constraints: List[str] = ["less_than", "greater_than", "equals"]
