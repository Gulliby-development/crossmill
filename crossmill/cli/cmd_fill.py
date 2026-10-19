from crossmill.base.inputs import IO
from crossmill.base.options import Spec
from crossmill.base.text import line
from crossmill.solve.problem import load
from crossmill.solve.search import filled_rows, fills

USAGE = "crossmill fill GRID WORDS [--limit L]"
ARGS = 2
SPECS = [Spec("--limit", lo=1, hi=20, fallback=1)]


def run_fill(args: list[str], options: dict[str, int], io: IO) -> tuple[str, int]:
    """Report the first requested crossword fills in search order."""
    grid, slots, lexicon = load(args, io, "fill")
    assignments = fills(grid, slots, lexicon, options["--limit"])

    report = line("grid", grid.dims())
    report += line("slots", str(len(slots)))
    report += line("words", str(len(lexicon)))
    report += line("found", str(len(assignments)))
    for number, words in enumerate(assignments, start=1):
        report += line("fill", f"{number} {filled_rows(grid, slots, words)}")

    return report, 0 if assignments else 1
