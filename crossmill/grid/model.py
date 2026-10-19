from dataclasses import dataclass

from crossmill.base.fail import Fail
from crossmill.base.text import show


@dataclass(frozen=True)
class Grid:
    """An immutable rectangular crossword grid."""

    rows: tuple[str, ...]

    @property
    def height(self) -> int:
        return len(self.rows)

    @property
    def width(self) -> int:
        return len(self.rows[0])

    def at(self, r: int, c: int) -> str:
        """Return the cell at zero-based row and column coordinates."""
        return self.rows[r][c]

    def text(self) -> str:
        """Return the rows joined with the grid separator."""
        return "/".join(self.rows)

    def dims(self) -> str:
        """Return the dimensions in HxW form."""
        return f"{self.height}x{self.width}"

    def limit(self, side: int, command: str) -> None:
        """Reject grids wider or taller than the command's supported limit."""
        if self.height > side or self.width > side:
            raise Fail(f"grid is {self.dims()} (above {side}x{side}, too large for {command})")


def parse_grid(text: str) -> Grid:
    """Parse and validate a slash-separated crossword grid."""
    rows = text.split("/")
    if any(not row or any(not _is_cell(char) for char in row) for row in rows):
        raise Fail(
            f"invalid grid {show(text)} (expected rows of # . and letters A to Z "
            "separated by /, such as ..#../.....)"
        )

    first_width = len(rows[0])
    for row_number, row in enumerate(rows[1:], start=2):
        if len(row) != first_width:
            raise Fail(f"row {row_number} has {len(row)} cells but row 1 has {first_width}")

    if len(rows) > 15:
        raise Fail(f"grid has {len(rows)} rows (above 15)")
    if first_width > 15:
        raise Fail(f"grid has {first_width} columns (above 15)")

    return Grid(tuple(rows))


def cell_name(r: int, c: int) -> str:
    """Return a one-based row-first cell name from zero-based coordinates."""
    return f"r{r + 1}c{c + 1}"


def _is_cell(char: str) -> bool:
    return char in "#." or "A" <= char <= "Z"
