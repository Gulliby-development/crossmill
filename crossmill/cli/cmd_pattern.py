"""Adapter for pattern queries over a word list."""

from crossmill.base.inputs import IO
from crossmill.base.options import Spec
from crossmill.base.text import line
from crossmill.lexicon.pattern import match_all, parse_pattern
from crossmill.lexicon.words import read_lexicon

USAGE = "crossmill pattern PATTERN WORDS [--limit L]"
ARGS = 2
SPECS: list[Spec] = [Spec("--limit", 1, 1000, 20)]


def run_pattern(args: list[str], options: dict[str, int], io: IO) -> tuple[str, int]:
    """Return a formatted report for the words matching a pattern."""
    pattern = parse_pattern(args[0])
    lexicon = read_lexicon(io, args[1])
    matches = match_all(lexicon, pattern)
    shown = min(options["--limit"], len(matches))

    report = [
        line("pattern", pattern),
        line("words", str(len(lexicon))),
        line("matches", str(len(matches))),
        line("shown", str(shown)),
    ]
    report.extend(line("word", word) for word in matches[:shown])
    return "".join(report), 0
