from crossmill.base.inputs import IO
from crossmill.base.options import Spec
from crossmill.base.text import line
from crossmill.grid.model import cell_name, parse_grid
from crossmill.grid.rules import regions, symmetry_problem
from crossmill.slots.find import find_slots

USAGE = "crossmill check GRID [--min-length N] [--checked]"
ARGS = 1
SPECS = [Spec("--min-length", 2, 15, 3), Spec("--checked", flag=True)]


def run_check(args: list[str], options: dict[str, int], io: IO) -> tuple[str, int]:
    """Return a complete grid construction report and its status."""
    grid = parse_grid(args[0])
    slots = find_slots(grid)

    membership: dict[tuple[int, int], int] = {}
    for slot in slots:
        for cell in slot.cells():
            membership[cell] = membership.get(cell, 0) + 1

    unchecked = 0
    first_unchecked: tuple[int, int] | None = None
    slotless_cells: list[tuple[int, int]] = []
    for row, cells in enumerate(grid.rows):
        for col, cell in enumerate(cells):
            if cell == "#":
                continue
            count = membership.get((row, col), 0)
            if count == 0:
                slotless_cells.append((row, col))
            elif count == 1:
                unchecked += 1
                if first_unchecked is None:
                    first_unchecked = (row, col)

    problems: list[str] = []
    symmetry = symmetry_problem(grid)
    if symmetry is not None:
        problems.append(symmetry)

    open_regions = regions(grid)
    if len(open_regions) > 1:
        second_start = cell_name(*open_regions[1][0])
        problems.append(
            f"the open cells form {len(open_regions)} regions (the second starts at {second_start})"
        )

    for row, col in slotless_cells:
        problems.append(f"cell {cell_name(row, col)} is in no slot")

    minimum = options["--min-length"]
    for slot in slots:
        if slot.length < minimum:
            problems.append(f"slot {slot.name} has length {slot.length} (below {minimum})")

    if options["--checked"] and unchecked:
        assert first_unchecked is not None
        problems.append(
            f"unchecked cells: {unchecked} (the first is {cell_name(*first_unchecked)})"
        )

    blocks = sum(cell == "#" for row in grid.rows for cell in row)
    across = sum(slot.direction == "A" for slot in slots)
    down = sum(slot.direction == "D" for slot in slots)
    shortest = min((slot.length for slot in slots), default=0)
    longest = max((slot.length for slot in slots), default=0)

    report = [
        line("grid", grid.dims()),
        line("blocks", str(blocks)),
        line("across", str(across)),
        line("down", str(down)),
        line("shortest", str(shortest)),
        line("longest", str(longest)),
        line("unchecked", str(unchecked)),
        line("problems", str(len(problems))),
    ]
    report.extend(line("problem", problem) for problem in problems)
    return "".join(report), 1 if problems else 0
