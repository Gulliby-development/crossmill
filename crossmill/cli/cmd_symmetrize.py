from crossmill.base.inputs import IO
from crossmill.base.options import Spec
from crossmill.base.text import line
from crossmill.grid.mirror import symmetrize
from crossmill.grid.model import parse_grid

USAGE: str = "crossmill symmetrize GRID"
ARGS: int = 1
SPECS: list[Spec] = []


def run_symmetrize(args: list[str], options: dict[str, int], io: IO) -> tuple[str, int]:
    """Return the half-turn-symmetrized grid report and its status."""
    grid = parse_grid(args[0])
    result, added = symmetrize(grid)
    return line("added", str(added)) + line("grid", result.text()), 0
