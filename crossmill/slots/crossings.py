from crossmill.slots.find import Slot


def crossings(slots: list[Slot]) -> list[tuple[int, int, int, int]]:
    """Return across/down intersections using indices into the supplied list."""
    result: list[tuple[int, int, int, int]] = []

    for across_index, across in enumerate(slots):
        if across.direction != "A":
            continue

        for down_index, down in enumerate(slots):
            if down.direction != "D":
                continue

            down_cells = {cell: offset for offset, cell in enumerate(down.cells())}
            for across_offset, cell in enumerate(across.cells()):
                down_offset = down_cells.get(cell)
                if down_offset is not None:
                    result.append((across_index, across_offset, down_index, down_offset))

    return result
