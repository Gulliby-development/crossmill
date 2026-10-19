def show(text: str) -> str:
    """Quote user text, replacing non-printable ASCII characters with question marks."""
    return '"' + "".join(char if "!" <= char <= "~" else "?" for char in text) + '"'


def line(key: str, value: str) -> str:
    """Format one report row with a fixed-width key and a literal LF."""
    return f"{key:<10}  {value}\n"


def join(nums: list[int]) -> str:
    """Join integers as decimal text separated by single spaces."""
    return " ".join(str(number) for number in nums)
