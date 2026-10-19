from crossmill.grid.model import Grid
from crossmill.slots.find import Slot
from crossmill.solve.search import fills


def count_fills(grid: Grid, slots: list[Slot], lexicon: list[str], cap: int) -> tuple[int, bool]:
    """Count fills through cap and report whether another fill exists."""
    found = fills(grid, slots, lexicon, cap + 1)
    return min(len(found), cap), len(found) > cap
