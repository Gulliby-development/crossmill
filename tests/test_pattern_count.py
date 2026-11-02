"""Tests for the --count flag of the pattern command."""

import pytest

from crossmill.cli.cli import run

WORDS = "band,bank,BONE,bin,bean,Bind,tank,band"


class FakeIO:
    def __init__(self) -> None:
        self.out_calls: list[str] = []
        self.err_calls: list[str] = []

    def read_stdin(self) -> bytes:
        return b""

    def out(self, text: str) -> None:
        self.out_calls.append(text)

    def err(self, text: str) -> None:
        self.err_calls.append(text)


def test_count_prints_only_the_three_summary_lines() -> None:
    io = FakeIO()

    assert run(["pattern", "b.n.", WORDS, "--count"], io) == 0
    assert io.out_calls == ["pattern     B.N.\nwords       7\nmatches     4\n"]
    assert io.err_calls == []


def test_count_may_stand_before_the_ordinary_arguments() -> None:
    io = FakeIO()

    assert run(["pattern", "--count", "zz", "cat,dog"], io) == 0
    assert io.out_calls == ["pattern     ZZ\nwords       2\nmatches     0\n"]


def test_count_ignores_a_valid_limit_but_still_checks_it() -> None:
    io = FakeIO()
    assert run(["pattern", "b.n.", WORDS, "--count", "--limit", "1"], io) == 0
    assert io.out_calls == ["pattern     B.N.\nwords       7\nmatches     4\n"]

    bad = FakeIO()
    assert run(["pattern", "b.n.", WORDS, "--count", "--limit", "0"], bad) == 2
    assert bad.out_calls == []
    assert len(bad.err_calls) == 1
    assert bad.err_calls[0].startswith("crossmill: ")


def test_count_takes_no_value() -> None:
    io = FakeIO()

    assert run(["pattern", "b.n.", WORDS, "--count=1"], io) == 2
    assert io.out_calls == []
    assert io.err_calls == ["crossmill: option --count takes no value\n"]


def test_without_count_the_report_is_unchanged() -> None:
    io = FakeIO()

    assert run(["pattern", "b.n.", WORDS, "--limit", "2"], io) == 0
    assert io.out_calls == [
        "pattern     B.N.\nwords       7\nmatches     4\nshown       2\nword        BAND\nword        BANK\n"
    ]


@pytest.mark.parametrize("argv", [["pattern"], ["pattern", "b.n.", WORDS, "extra"]])
def test_usage_error_names_the_count_flag(argv: list[str]) -> None:
    io = FakeIO()

    assert run(argv, io) == 2
    assert io.err_calls == [
        "crossmill: usage: crossmill pattern PATTERN WORDS [--limit L] [--count]\n"
    ]
