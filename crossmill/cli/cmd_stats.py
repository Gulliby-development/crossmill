"""Adapter for statistics over a word list."""

from crossmill.base.inputs import IO
from crossmill.base.options import Spec
from crossmill.base.text import line
from crossmill.lexicon.stats import lexicon_stats
from crossmill.lexicon.words import read_lexicon

USAGE = "crossmill stats WORDS"
ARGS = 1
SPECS: list[Spec] = []


def run_stats(args: list[str], options: dict[str, int], io: IO) -> tuple[str, int]:
    """Return a formatted report with word-length and letter-frequency statistics."""
    lexicon = read_lexicon(io, args[0])
    length_counts, ranked_letters = lexicon_stats(lexicon)

    report = [
        line("words", str(len(lexicon))),
        line("shortest", str(min(length_counts))),
        line("longest", str(max(length_counts))),
    ]
    report.extend(
        line("length", f"{length} x {count}") for length, count in sorted(length_counts.items())
    )
    letters = " ".join(f"{letter}={count}" for letter, count in ranked_letters)
    report.append(line("letters", letters))
    return "".join(report), 0
