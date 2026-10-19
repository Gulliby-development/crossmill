import sys
from typing import Protocol

from crossmill.base.fail import Fail


class IO(Protocol):
    def read_stdin(self) -> bytes:
        """Read the raw bytes supplied on standard input."""

    def out(self, text: str) -> None:
        """Write text to standard output."""

    def err(self, text: str) -> None:
        """Write text to standard error."""


class StdIO:
    """Adapt the process's binary standard streams to the IO protocol."""

    def read_stdin(self) -> bytes:
        return sys.stdin.buffer.read()

    def out(self, text: str) -> None:
        sys.stdout.buffer.write(text.encode("ascii"))

    def err(self, text: str) -> None:
        sys.stderr.buffer.write(text.encode("ascii"))


def stdin_words(io: IO) -> list[str]:
    """Decode standard input strictly and split only the permitted separators."""
    try:
        text = io.read_stdin().decode("utf-8")
    except UnicodeDecodeError:
        raise Fail("<stdin>: input is not valid UTF-8") from None

    text = text.removeprefix("\ufeff")

    words = [
        part
        for part in text.replace("\t", " ").replace("\r", " ").replace("\n", " ").split(" ")
        if part
    ]
    if not words:
        raise Fail("<stdin>: no input")
    return words
