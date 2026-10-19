from crossmill.base.inputs import IO
from crossmill.base.options import Spec
from crossmill.base.text import line
from crossmill.grid.model import cell_name, parse_grid
from crossmill.slots.find import find_slots, slot_pattern

USAGE: str = "crossmill number GRID"
ARGS: int = 1
SPECS: list[Spec] = []


def run_number(args: list[str], options: dict[str, int], io: IO) -> tuple[str, int]:
    """Return the numbered grid report and its status."""
    grid = parse_grid(args[0])
    slots = find_slots(grid)

    blocks = sum(cell == "#" for row in grid.rows for cell in row)
    across = sum(slot.direction == "A" for slot in slots)
    down = sum(slot.direction == "D" for slot in slots)

    report = [
        line("grid", grid.dims()),
        line("blocks", str(blocks)),
        line("across", str(across)),
        line("down", str(down)),
    ]
    for slot in slots:
        cell = cell_name(slot.row, slot.col)
        value = f"{slot.name} {slot.length} {cell} {slot_pattern(grid, slot)}"
        report.append(line("slot", value))

    return "".join(report), 0
