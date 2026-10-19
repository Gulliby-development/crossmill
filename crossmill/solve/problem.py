from crossmill.base.fail import Fail
from crossmill.base.inputs import IO
from crossmill.grid.model import Grid, parse_grid
from crossmill.lexicon.words import read_lexicon
from crossmill.slots.find import Slot, find_slots


def load(args: list[str], io: IO, command: str) -> tuple[Grid, list[Slot], list[str]]:
    """Load and validate a solving problem in the prescribed input order."""
    grid = parse_grid(args[0])
    lexicon = read_lexicon(io, args[1])

    grid.limit(5, command)
    if len(lexicon) > 40:
        raise Fail(f"{len(lexicon)} words (above 40, too large for {command})")

    return grid, find_slots(grid), lexicon
