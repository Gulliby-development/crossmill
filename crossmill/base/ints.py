from crossmill.base.fail import Fail
from crossmill.base.text import show


def parse_int(name: str, text: str, lo: int, hi: int) -> int:
    """Parse a bounded decimal integer in the accepted ASCII syntax."""
    valid = text == "0" or (
        1 <= len(text) <= 10
        and "1" <= text[0] <= "9"
        and all("0" <= char <= "9" for char in text[1:])
    )
    if valid:
        value = int(text)
        if lo <= value <= hi:
            return value
    raise Fail(f"invalid {name} {show(text)} (expected an integer from {lo} to {hi})")
