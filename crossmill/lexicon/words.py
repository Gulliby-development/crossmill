from crossmill.base.fail import Fail
from crossmill.base.inputs import IO, stdin_words
from crossmill.base.text import show


def parse_word(text: str) -> str:
    """Validate a crossword word and return its ASCII uppercase form."""
    valid = 2 <= len(text) <= 15 and all("A" <= char <= "Z" or "a" <= char <= "z" for char in text)
    if not valid:
        raise Fail(f"invalid word {show(text)} (expected 2 to 15 letters)")
    return text.upper()


def build_lexicon(words: list[str]) -> list[str]:
    """Normalize, validate, deduplicate, and sort words in a lexicon."""
    normalized = [parse_word(word) for word in words]
    return sorted(set(normalized))


def read_lexicon(io: IO, text: str) -> list[str]:
    """Read a comma-separated lexicon or delegate a lone dash to standard input."""
    words = stdin_words(io) if text == "-" else text.split(",")
    return build_lexicon(words)
