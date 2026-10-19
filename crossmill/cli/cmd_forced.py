from crossmill.base.inputs import IO
from crossmill.base.options import Spec
from crossmill.base.text import line
from crossmill.solve.domains import initial_domains, propagate
from crossmill.solve.letters import cell_letters
from crossmill.solve.problem import load

USAGE = "crossmill forced GRID WORDS"
ARGS = 2
SPECS: list[Spec] = []


def run_forced(args: list[str], options: dict[str, int], io: IO) -> tuple[str, int]:
    """Report cells whose remaining candidates force a letter."""
    grid, slots, lexicon = load(args, io, "forced")
    domains = propagate(slots, initial_domains(grid, slots, lexicon))
    if not all(domains):
        return line("consistent", "no"), 1

    possible_letters = cell_letters(slots, domains)
    rows = [list(row) for row in grid.rows]
    forced = 0
    for row in range(grid.height):
        for col in range(grid.width):
            letters = possible_letters.get((row, col), set())
            if grid.at(row, col) == "." and len(letters) == 1:
                rows[row][col] = next(iter(letters))
                forced += 1

    report = line("grid", grid.dims())
    report += line("consistent", "yes")
    report += line("forced", str(forced))
    for row in rows:
        report += line("row", "".join(row))

    return report, 0
