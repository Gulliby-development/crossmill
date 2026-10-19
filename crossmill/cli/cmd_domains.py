from crossmill.base.inputs import IO
from crossmill.base.options import Spec
from crossmill.base.text import line
from crossmill.grid.model import cell_name
from crossmill.solve.domains import initial_domains, propagate
from crossmill.solve.problem import load

USAGE = "crossmill domains GRID WORDS"
ARGS = 2
SPECS: list[Spec] = []


def run_domains(args: list[str], options: dict[str, int], io: IO) -> tuple[str, int]:
    """Report the initial and arc-consistent candidate count for every slot."""
    grid, slots, lexicon = load(args, io, "domains")
    before = initial_domains(grid, slots, lexicon)
    after = propagate(slots, before)
    consistent = all(after)

    report = line("grid", grid.dims())
    report += line("slots", str(len(slots)))
    report += line("words", str(len(lexicon)))
    report += line("consistent", "yes" if consistent else "no")
    for slot, initial, narrowed in zip(slots, before, after):
        cell = cell_name(slot.row, slot.col)
        value = f"{slot.name} {slot.length} {cell} {len(initial)} -> {len(narrowed)}"
        report += line("slot", value)

    return report, 0 if consistent else 1
