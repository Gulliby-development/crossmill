from crossmill.base.fail import Fail
from crossmill.base.text import show


def parse_pattern(text: str) -> str:
    """Validate a crossword pattern and return its ASCII uppercase form."""
    valid = 2 <= len(text) <= 15 and all(
        char == "." or "A" <= char <= "Z" or "a" <= char <= "z" for char in text
    )
    if not valid:
        raise Fail(f"invalid pattern {show(text)} (expected 2 to 15 characters, letters or .)")
    return text.upper()


def matches(pattern: str, word: str) -> bool:
    """Return whether a normalized word satisfies a normalized pattern."""
    return len(pattern) == len(word) and all(
        pattern_char == "." or pattern_char == word_char
        for pattern_char, word_char in zip(pattern, word)
    )


def match_all(lexicon: list[str], pattern: str) -> list[str]:
    """Return all matching lexicon words in ascending order."""
    return sorted(word for word in lexicon if matches(pattern, word))
