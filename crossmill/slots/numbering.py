from crossmill.grid.model import Grid


def number_cells(grid: Grid) -> dict[tuple[int, int], int]:
    """Number the starts of maximal across and down runs in reading order."""
    numbers: dict[tuple[int, int], int] = {}
    next_number = 1

    for row in range(grid.height):
        for col in range(grid.width):
            if grid.at(row, col) == "#":
                continue

            starts_across = (
                (col == 0 or grid.at(row, col - 1) == "#")
                and col + 1 < grid.width
                and grid.at(row, col + 1) != "#"
            )
            starts_down = (
                (row == 0 or grid.at(row - 1, col) == "#")
                and row + 1 < grid.height
                and grid.at(row + 1, col) != "#"
            )

            if starts_across or starts_down:
                numbers[(row, col)] = next_number
                next_number += 1

    return numbers
