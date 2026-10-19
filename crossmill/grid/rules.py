from crossmill.grid.model import Grid, cell_name


def symmetry_problem(grid: Grid) -> str | None:
    """Return the first block whose half-turn partner is open or lettered."""
    for r, row in enumerate(grid.rows):
        for c, cell in enumerate(row):
            if cell == "#":
                partner_r = grid.height - 1 - r
                partner_c = grid.width - 1 - c
                if grid.at(partner_r, partner_c) != "#":
                    return (
                        f"not symmetric: {cell_name(r, c)} is a block but "
                        f"{cell_name(partner_r, partner_c)} is not"
                    )
    return None


def regions(grid: Grid) -> list[list[tuple[int, int]]]:
    """Return edge-connected open-cell regions in deterministic reading order."""
    visited: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []

    for r, row in enumerate(grid.rows):
        for c, cell in enumerate(row):
            start = (r, c)
            if cell == "#" or start in visited:
                continue

            visited.add(start)
            pending = [start]
            component: list[tuple[int, int]] = []
            while pending:
                current_r, current_c = pending.pop()
                component.append((current_r, current_c))
                for neighbor in (
                    (current_r - 1, current_c),
                    (current_r, current_c - 1),
                    (current_r, current_c + 1),
                    (current_r + 1, current_c),
                ):
                    neighbor_r, neighbor_c = neighbor
                    if (
                        0 <= neighbor_r < grid.height
                        and 0 <= neighbor_c < grid.width
                        and grid.at(neighbor_r, neighbor_c) != "#"
                        and neighbor not in visited
                    ):
                        visited.add(neighbor)
                        pending.append(neighbor)

            component.sort()
            components.append(component)

    return components
