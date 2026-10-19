from crossmill.base.fail import Fail
from crossmill.grid.model import Grid, cell_name


def symmetrize(grid: Grid) -> tuple[Grid, int]:
    """Add blocks at open half-turn partners while preserving original-grid checks."""
    rows = [list(row) for row in grid.rows]
    added = 0

    for r, row in enumerate(grid.rows):
        for c, cell in enumerate(row):
            if cell != "#":
                continue

            partner_r = grid.height - 1 - r
            partner_c = grid.width - 1 - c
            partner = grid.at(partner_r, partner_c)
            if partner == "#":
                continue
            if partner != ".":
                raise Fail(
                    f"cell {cell_name(partner_r, partner_c)} holds a letter but its partner "
                    f"{cell_name(r, c)} is a block"
                )

            rows[partner_r][partner_c] = "#"
            added += 1

    return Grid(tuple("".join(row) for row in rows)), added
