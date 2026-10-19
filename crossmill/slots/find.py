from dataclasses import dataclass

from crossmill.grid.model import Grid
from crossmill.slots.numbering import number_cells


@dataclass(frozen=True)
class Slot:
    """An immutable maximal across or down run in a grid."""

    number: int
    direction: str
    row: int
    col: int
    length: int

    @property
    def name(self) -> str:
        """Return the slot number followed by its direction."""
        return f"{self.number}{self.direction}"

    def cells(self) -> list[tuple[int, int]]:
        """Return the slot's zero-based cells in reading direction."""
        if self.direction == "A":
            return [(self.row, self.col + offset) for offset in range(self.length)]
        return [(self.row + offset, self.col) for offset in range(self.length)]


def find_slots(grid: Grid) -> list[Slot]:
    """Find maximal runs of at least two open cells in slot order."""
    numbers = number_cells(grid)
    slots: list[Slot] = []

    for (row, col), number in numbers.items():
        if col == 0 or grid.at(row, col - 1) == "#":
            length = 0
            while col + length < grid.width and grid.at(row, col + length) != "#":
                length += 1
            if length >= 2:
                slots.append(Slot(number, "A", row, col, length))

        if row == 0 or grid.at(row - 1, col) == "#":
            length = 0
            while row + length < grid.height and grid.at(row + length, col) != "#":
                length += 1
            if length >= 2:
                slots.append(Slot(number, "D", row, col, length))

    slots.sort(key=lambda slot: (slot.number, slot.direction))
    return slots


def slot_pattern(grid: Grid, slot: Slot) -> str:
    """Return the grid characters in the slot's cell order."""
    return "".join(grid.at(row, col) for row, col in slot.cells())
