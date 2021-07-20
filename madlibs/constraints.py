import abc
from typing import Any, Dict, Optional

from jinja2 import Environment

from madlibs.core import known_constraints


def register_known_constraints(env: Environment) -> None:
    def dummy_processor(x: Any, *args: Any) -> str:
        return x

    for name in known_constraints:
        env.filters[name] = dummy_processor


class Constraint(abc.ABC):
    constraint_name: str
    variable_name: str

    def __init__(self, constraint_name: str, variable_name: str) -> None:
        self.constraint_name = constraint_name
        self.variable_name = variable_name

    @abc.abstractmethod
    def check(self, fillers: Dict[str, str]) -> bool:
        """Check if this constraint holds for the given fillers

        Args:
            fillers (Dict[str, str]): The current values to variables

        Returns:
            bool: True if the constraints hold
        """


class EqualityConstraint(Constraint):
    def __init__(self, variable_name: str, other_name: str) -> None:
        super().__init__("equals", variable_name)
        self.other_name = other_name

    def check(self, filler: Dict[str, str]) -> bool:
        a = filler[self.variable_name]
        b = filler[self.other_name]
        # a dirty hack to ensure that numeric equality is checked
        try:
            return float(a) == float(b)
        except Exception:
            return a == b


class InequalityConstraint(Constraint):
    def __init__(self, variable_name: str, other_name: str) -> None:
        super().__init__("not_equals", variable_name)
        self.other_name = other_name

    def check(self, filler: Dict[str, str]) -> bool:
        a = filler[self.variable_name]
        b = filler[self.other_name]
        # a dirty hack to ensure that numeric equality is checked
        try:
            return float(a) != float(b)
        except Exception:
            return a != b


class LessThanConstraint(Constraint):
    def __init__(self, variable_name: str, other_name: str) -> None:
        super().__init__("less_than", variable_name)
        self.other_name = other_name

    def check(self, filler: Dict[str, str]) -> bool:
        a = filler[self.variable_name]
        b = filler[self.other_name]
        return float(a) < float(b)


class GreaterThanConstraint(Constraint):
    def __init__(self, variable_name: str, other_name: str) -> None:
        super().__init__("greater_than", variable_name)
        self.other_name = other_name

    def check(self, filler: Dict[str, str]) -> bool:
        a = filler[self.variable_name]
        b = filler[self.other_name]
        return float(a) > float(b)


binary_constraints = {
    "equals": lambda a, b: EqualityConstraint(a, b),
    "not_equals": lambda a, b: InequalityConstraint(a, b),
    "less_than": lambda a, b: LessThanConstraint(a, b),
    "greater_than": lambda a, b: GreaterThanConstraint(a, b),
}


def make_constraint(
    constraint_name: str,
    variable_name: str,
    *args: str,
) -> Optional[Constraint]:
    if constraint_name in binary_constraints:
        if len(args) == 1:
            arg = args[0]
            return binary_constraints[constraint_name](variable_name, arg)
        else:
            raise Exception(f"Invalid number of arguments for {constraint_name}")

    return None
