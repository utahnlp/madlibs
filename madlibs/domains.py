import abc
from numbers import Number
from typing import Any, Dict, List, Optional, Set

from jinja2 import Environment

from madlibs.core import FillerType


class Domain(abc.ABC):
    variable_name: str
    variable_type: str

    def __init__(self, variable_name: str, variable_type: str) -> None:
        self.variable_name = variable_name
        self.variable_type = variable_type

    def __str__(self) -> str:
        return self.__repr__()

    def is_reference_to_type(self) -> bool:
        return self.variable_name != self.variable_type

    @abc.abstractmethod
    def unify_with(self, other: "Domain") -> Optional["Domain"]:
        """Try to unify this domain with another domain

        Raises:
            Exception: If the unification fails

        Returns:
            [type]: A unified type that represents both this domain and the other one.
        """


class IndependentDomain(Domain):
    def __init__(self, variable_name: str, variable_type: str) -> None:
        super().__init__(variable_name, variable_type)

    @abc.abstractmethod
    def generate_domain(self) -> List[str]:
        """Generate a list of fillers that define this type

        Returns:
            List[str]: A list of values that this variable can take
        """


class FillerDomain(IndependentDomain):
    values: List[str]
    # fillers: List[FillerType]
    dependents: Dict[str, Dict[str, str]]
    dependent_variables: Set[str]

    def __init__(
        self, variable_name: str, variable_type: str, fillers: List[FillerType]
    ) -> None:
        super().__init__(variable_name=variable_name, variable_type=variable_type)
        # self.fillers = fillers
        self.values = []
        self.dependents = {}
        self.dependent_variables = set()
        for item in fillers:
            if isinstance(item, str):
                self.values.append(item)
            else:
                value = item[variable_type]
                self.values.append(value)
                self.dependents[value] = {}
                for key in item:
                    if key != variable_type:
                        self.dependents[value][key] = item[key]
                        self.dependent_variables.add(key)

        # if there are dependents, every value should have a dependent
        if len(self.dependents) > 0:
            for v in self.values:
                if v not in self.dependents:
                    raise Exception(f"Missing dependents for value {v}")

    def __repr__(self) -> str:
        values = "[" + ", ".join(self.values) + "]"
        if self.is_reference_to_type():
            return self.variable_name + ": " + self.variable_type + " " + values
        else:
            return self.variable_name + ": " + values

    def generate_domain(self) -> List[str]:
        return self.values

    def lookup_dependent(self, value: str, dependent_name: str) -> str:
        return self.dependents[value][dependent_name]

    def unify_with(self, other: Domain) -> Optional[Domain]:
        self_is_type = self.is_reference_to_type()

        if not isinstance(other, FillerDomain):
            if not self_is_type:
                if self.variable_name == other.variable_name:
                    return other
            return None
        else:
            other_is_type = other.is_reference_to_type()

            # if both domains are references to the same type, then we are in good shape
            if (
                self_is_type
                and other_is_type
                and self.variable_type == other.variable_type
                and self.variable_name == other.variable_name
                and self.values == other.values
            ):
                return self
            elif not self_is_type and not other_is_type:
                if (
                    self.variable_type == other.variable_type
                    and self.values == other.values
                ):
                    return self
            else:
                # if one of these is a reference to a type, and the other one is not a
                # reference, then return the reference to the type.
                if self_is_type and not other_is_type:
                    return self
                elif not self_is_type and other_is_type:
                    return other

            return None


class RangeDomain(IndependentDomain):
    start: Number
    end: Number
    step: Number

    def __init__(
        self,
        variable_name: str,
        start: Number,
        end: Number,
        step: Number = 1,  # type: ignore
    ) -> None:
        super().__init__(variable_name=variable_name, variable_type="numeric")
        self.start = start
        self.end = end
        self.step = step

    def __repr__(self) -> str:
        values = ", ".join([str(self.start), str(self.end), str(self.step)])
        return self.variable_name + f": range({values})"

    def generate_domain(self) -> List[str]:
        numeric_range: List[str] = []
        n = self.start
        while n < self.end:  # type: ignore
            numeric_range.append(str(n))
            n += self.step  # type: ignore

        return numeric_range

    def unify_with(self, other: Domain) -> Optional[Domain]:
        if isinstance(other, RangeDomain):
            # If both domains are numeric, then the ranges should be the same
            if (
                self.variable_name == other.variable_name
                and self.start == other.start
                and self.end == other.end
                and self.step == other.step
            ):
                return self
        elif not other.is_reference_to_type():
            return self
        return None


class DependentDomain(Domain):
    args: List[str]

    def __init__(
        self,
        parent_name: str,
        variable_name: str,
        *args: str,
    ) -> None:
        a = [parent_name]
        a.extend(args)
        args_string = ",".join(a)
        super().__init__(variable_name, f"{variable_name}({args_string})")
        self.args = list(args)

    def __repr__(self) -> str:
        return self.variable_type

    @abc.abstractmethod
    def value(self, context: Dict[str, str]) -> str:
        """The actual implementation of the dependency that this constraint realizes

        Args:
            context (Dict[str, str]): The context for this constraint that contains
            instances for the arguments

        Returns:
            str: The value of this variable given the context
        """

    def unify_with(self, other: Domain) -> Optional[Domain]:
        if isinstance(other, DependentDomain):
            if self.variable_type == other.variable_type:
                return self
        elif not other.is_reference_to_type():
            if self.variable_name == other.variable_type:
                return self
        return None


class FillerDependentDomain(DependentDomain):
    parent: FillerDomain

    def __init__(self, variable_type: str, parent: FillerDomain) -> None:
        super().__init__(parent_name=parent.variable_name, variable_name=variable_type)
        self.parent = parent

    def value(self, context: Dict[str, str]) -> str:
        return self.parent.lookup_dependent(
            context[self.parent.variable_name],
            self.variable_name,
        )


def make_filler_domain(
    variable_name: str,
    fillers: Dict[str, List[FillerType]],
    *args: str,
) -> List[Domain]:
    if len(args) != 1:
        raise Exception(f"Invalid type specification for {variable_name}")

    variable_type = args[0]
    if variable_type in fillers:
        items = fillers[variable_type]
        return [FillerDomain(variable_name, variable_type, items)]
    else:
        domains: List[Domain] = []
        for key in fillers:
            sample = fillers[key][0]
            if not (isinstance(sample, dict) and variable_type in sample):
                continue

            parent = FillerDomain(variable_name, variable_type, fillers[key])
            domains.append(parent)
            for child_variable_type in parent.dependent_variables:
                child = FillerDependentDomain(child_variable_type, parent)
                domains.append(child)
            break
        if len(domains) == 0:
            raise Exception(f"Unknown domain for {variable_name}")
        return domains


def make_range_domain(variable_name: str, *args: str) -> Domain:
    def make_number(s: str) -> Number:
        # a pretty terrible hack
        f = float(s)
        v = int(f)
        if v != f:
            return f  # type: ignore
        else:
            return v  # type: ignore

    start = make_number(args[0])
    end = make_number(args[1])
    step: Number = 1  # type: ignore
    if len(args) == 3:
        step = make_number(args[2])
    elif len(args) != 2:
        raise Exception("Invalid number of arguments for range")

    return RangeDomain(
        variable_name=variable_name,
        start=start,
        end=end,
        step=step,
    )


def make_domain(
    domain_type: str,
    variable_name: str,
    fillers: Dict[str, List[FillerType]],
    *args: str,
) -> List[Domain]:
    if domain_type == "type":
        return make_filler_domain(variable_name, fillers, *args)
    elif domain_type == "range":
        return [make_range_domain(variable_name, *args)]
    else:
        return []


known_domains = ["type", "range"]


def register_known_domains(env: Environment) -> None:
    def dummy_processor(x: Any, *args: Any) -> str:
        return x

    for name in known_domains:
        env.filters[name] = dummy_processor


def try_unify(old_domain: Domain, new_domain: Domain) -> Domain:
    unified = old_domain.unify_with(new_domain)
    if unified is None:
        old_type = old_domain.variable_type
        new_type = new_domain.variable_type
        raise Exception(f"Cannot unify {old_type} with {new_type}")
    else:
        return unified
