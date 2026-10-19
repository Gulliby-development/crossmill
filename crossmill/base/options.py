from dataclasses import dataclass

from crossmill.base.fail import Fail
from crossmill.base.ints import parse_int
from crossmill.base.text import show


@dataclass(frozen=True)
class Spec:
    """Describe one command-line option and its validation defaults."""

    name: str
    lo: int = 0
    hi: int = 0
    fallback: int = 0
    flag: bool = False


def parse_options(argv: list[str], specs: list[Spec]) -> tuple[dict[str, int], list[str]]:
    """Separate options from ordinary arguments, then validate values in spec order."""
    by_name = {spec.name: spec for spec in specs}
    pending: dict[str, str] = {}
    present_flags: set[str] = set()
    ordinary: list[str] = []
    index = 0

    while index < len(argv):
        argument = argv[index]
        if not argument.startswith("--"):
            ordinary.append(argument)
            index += 1
            continue

        name, separator, value = argument.partition("=")
        spec = by_name.get(name)
        if spec is None:
            raise Fail(f"unknown option {show(argument)}")

        if spec.flag:
            if separator:
                raise Fail(f"option {name} takes no value")
            present_flags.add(name)
        else:
            if not separator:
                if index + 1 >= len(argv):
                    raise Fail(f"{name} needs a value")
                index += 1
                value = argv[index]
            pending[name] = value
        index += 1

    values: dict[str, int] = {}
    for spec in specs:
        if spec.flag:
            values[spec.name] = 1 if spec.name in present_flags else spec.fallback
        elif spec.name in pending:
            values[spec.name] = parse_int(spec.name, pending[spec.name], spec.lo, spec.hi)
        else:
            values[spec.name] = spec.fallback

    return values, ordinary
