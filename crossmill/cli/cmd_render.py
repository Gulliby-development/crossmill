from crossmill.base.inputs import IO
from crossmill.base.options import Spec
from crossmill.grid.model import parse_grid
from crossmill.grid.render import render_box
from crossmill.slots.numbering import number_cells

USAGE: str = "crossmill render GRID [--compact]"
ARGS: int = 1
SPECS: list[Spec] = [Spec("--compact", flag=True)]


def run_render(args: list[str], options: dict[str, int], io: IO) -> tuple[str, int]:
    """Return a rendered grid drawing and its status."""
    grid = parse_grid(args[0])
    lines = render_box(grid, number_cells(grid), bool(options["--compact"]))
    return "\n".join(lines) + "\n", 0
