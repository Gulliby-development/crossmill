from crossmill.base.inputs import IO
from crossmill.base.options import Spec
from crossmill.base.text import line
from crossmill.solve.counting import count_fills
from crossmill.solve.problem import load

USAGE = "crossmill count GRID WORDS [--max M]"
ARGS = 2
SPECS = [Spec("--max", lo=1, hi=1000, fallback=100)]


def run_count(args: list[str], options: dict[str, int], io: IO) -> tuple[str, int]:
    """Report the bounded number of fills for a crossword problem."""
    grid, slots, lexicon = load(args, io, "count")
    count, capped = count_fills(grid, slots, lexicon, options["--max"])

    report = line("grid", grid.dims())
    report += line("slots", str(len(slots)))
    report += line("words", str(len(lexicon)))
    report += line("count", str(count))
    report += line("capped", "yes" if capped else "no")

    return report, 0
