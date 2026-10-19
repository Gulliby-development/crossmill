import importlib
import runpy
import sys
from collections.abc import Callable

import pytest

from crossmill.base.fail import Fail
from crossmill.base.inputs import IO, StdIO
from crossmill.cli import cmd_count, cmd_domains, cmd_fill, cmd_forced
from crossmill.cli.cli import run


class FakeIO:
    def __init__(self, stdin: bytes = b"") -> None:
        self.stdin = stdin
        self.out_calls: list[str] = []
        self.err_calls: list[str] = []

    def read_stdin(self) -> bytes:
        return self.stdin

    def out(self, text: str) -> None:
        self.out_calls.append(text)

    def err(self, text: str) -> None:
        self.err_calls.append(text)


def _assert_cli_error(args: list[str], message: str, stdin: bytes = b"") -> None:
    io: IO = FakeIO(stdin)

    assert run(args, io) == 2
    assert io.out_calls == []
    assert io.err_calls == [f"crossmill: {message}\n"]


def _assert_usage_error(args: list[str], usage: str) -> None:
    _assert_cli_error(args, f"usage: {usage}")


def test_missing_command_reports_complete_usage_list() -> None:
    io = FakeIO()

    status = run([], io)

    assert status == 2
    assert io.out_calls == []
    assert io.err_calls == [
        (
            "crossmill: missing command (check, number, render, symmetrize, pattern, stats, "
            "domains, forced, fill or count)\n"
        )
    ]


def test_unknown_command_reports_its_name() -> None:
    io = FakeIO()

    status = run(["frob"], io)

    assert status == 2
    assert io.out_calls == []
    assert io.err_calls == ['crossmill: unknown command "frob"\n']


def test_unknown_command_sanitizes_non_ascii_printable_characters() -> None:
    io = FakeIO()

    status = run(["bad\nname"], io)

    assert status == 2
    assert io.out_calls == []
    assert io.err_calls == ['crossmill: unknown command "bad?name"\n']


def test_check_missing_argument_reports_literal_usage() -> None:
    _assert_usage_error(["check"], "crossmill check GRID [--min-length N] [--checked]")


def test_check_surplus_argument_reports_literal_usage() -> None:
    _assert_usage_error(
        ["check", "...", "extra"], "crossmill check GRID [--min-length N] [--checked]"
    )


def test_number_missing_argument_reports_literal_usage() -> None:
    io = FakeIO()

    status = run(["number"], io)

    assert status == 2
    assert io.out_calls == []
    assert io.err_calls == ["crossmill: usage: crossmill number GRID\n"]


def test_number_surplus_argument_reports_literal_usage() -> None:
    _assert_usage_error(["number", "...", "extra"], "crossmill number GRID")


def test_render_missing_argument_reports_literal_usage() -> None:
    _assert_usage_error(["render"], "crossmill render GRID [--compact]")


def test_render_surplus_argument_reports_literal_usage() -> None:
    _assert_usage_error(["render", "...", "extra"], "crossmill render GRID [--compact]")


def test_symmetrize_missing_argument_reports_literal_usage() -> None:
    _assert_usage_error(["symmetrize"], "crossmill symmetrize GRID")


def test_symmetrize_surplus_argument_reports_literal_usage() -> None:
    _assert_usage_error(["symmetrize", "...", "extra"], "crossmill symmetrize GRID")


def test_pattern_missing_arguments_reports_literal_usage() -> None:
    _assert_usage_error(["pattern"], "crossmill pattern PATTERN WORDS [--limit L]")


def test_pattern_surplus_argument_reports_literal_usage() -> None:
    _assert_usage_error(
        ["pattern", "..", "CAT", "extra"], "crossmill pattern PATTERN WORDS [--limit L]"
    )


def test_stats_missing_argument_reports_literal_usage() -> None:
    _assert_usage_error(["stats"], "crossmill stats WORDS")


def test_stats_surplus_argument_reports_literal_usage() -> None:
    _assert_usage_error(["stats", "CAT", "extra"], "crossmill stats WORDS")


def test_domains_missing_arguments_reports_literal_usage() -> None:
    _assert_usage_error(["domains"], "crossmill domains GRID WORDS")


def test_domains_surplus_argument_reports_literal_usage() -> None:
    _assert_usage_error(["domains", ".", "CAT", "extra"], "crossmill domains GRID WORDS")


def test_forced_missing_arguments_reports_literal_usage() -> None:
    _assert_usage_error(["forced"], "crossmill forced GRID WORDS")


def test_forced_surplus_argument_reports_literal_usage() -> None:
    _assert_usage_error(["forced", ".", "CAT", "extra"], "crossmill forced GRID WORDS")


def test_fill_missing_arguments_reports_literal_usage() -> None:
    _assert_usage_error(["fill"], "crossmill fill GRID WORDS [--limit L]")


def test_fill_surplus_argument_reports_literal_usage() -> None:
    _assert_usage_error(["fill", ".", "CAT", "extra"], "crossmill fill GRID WORDS [--limit L]")


def test_count_missing_arguments_reports_literal_usage() -> None:
    _assert_usage_error(["count"], "crossmill count GRID WORDS [--max M]")


def test_count_surplus_argument_reports_literal_usage() -> None:
    _assert_usage_error(["count", ".", "CAT", "extra"], "crossmill count GRID WORDS [--max M]")


def test_unknown_option_is_reported_before_number_arity() -> None:
    _assert_cli_error(["number", "--help"], 'unknown option "--help"')


def test_double_dash_is_not_an_end_of_options_marker() -> None:
    _assert_cli_error(["number", "--"], 'unknown option "--"')


def test_missing_option_value_is_reported_before_pattern_arity() -> None:
    _assert_cli_error(["pattern", "--limit"], "--limit needs a value")


def test_flag_option_rejects_equals_value_before_grid_validation() -> None:
    _assert_cli_error(["render", "../..", "--compact=1"], "option --compact takes no value")


def test_invalid_numeric_option_is_reported_before_check_arity() -> None:
    _assert_cli_error(
        ["check", "--min-length", "1"],
        'invalid --min-length "1" (expected an integer from 2 to 15)',
    )


def test_check_arity_error_precedes_invalid_grid_argument() -> None:
    _assert_cli_error(
        ["check", "bad", "extra"], "usage: crossmill check GRID [--min-length N] [--checked]"
    )


def test_invalid_pattern_precedes_invalid_words_argument() -> None:
    _assert_cli_error(
        ["pattern", "A", "D0G"],
        'invalid pattern "A" (expected 2 to 15 characters, letters or .)',
    )


def test_fill_grid_error_precedes_invalid_words_argument() -> None:
    _assert_cli_error(
        ["fill", "bad", "D0G"],
        'invalid grid "bad" (expected rows of # . and letters A to Z separated by /, such as ..#../.....)',
    )


def test_unknown_option_scan_precedes_numeric_option_validation() -> None:
    _assert_cli_error(
        ["pattern", "..", "AB", "--limit", "0", "--unknown"],
        'unknown option "--unknown"',
    )


def test_option_consumes_next_option_looking_argument_as_its_value() -> None:
    _assert_cli_error(
        ["pattern", "..", "AB", "--limit", "--help"],
        'invalid --limit "--help" (expected an integer from 1 to 1000)',
    )


def _assert_cli_report(args: list[str], report: str, status: int = 0, stdin: bytes = b"") -> None:
    io: IO = FakeIO(stdin)

    assert run(args, io) == status
    assert io.out_calls == [report]
    assert io.err_calls == []


def test_pattern_equals_interspersed_and_repeated_limit_uses_last_value() -> None:
    _assert_cli_report(
        [
            "pattern",
            "--limit=0",
            "b.n.",
            "band,bank,BONE,bin,bean,Bind,tank,band",
            "--limit",
            "3",
        ],
        "pattern     B.N.\n"
        "words       7\n"
        "matches     4\n"
        "shown       3\n"
        "word        BAND\n"
        "word        BANK\n"
        "word        BIND\n",
    )


def test_pattern_default_limit_is_twenty() -> None:
    _assert_cli_report(
        ["pattern", "b.n.", "band,bank,BONE,bin,bean,Bind,tank,band"],
        "pattern     B.N.\n"
        "words       7\n"
        "matches     4\n"
        "shown       4\n"
        "word        BAND\n"
        "word        BANK\n"
        "word        BIND\n"
        "word        BONE\n",
    )


def test_pattern_limit_inclusive_lower_endpoint_shows_one_word() -> None:
    _assert_cli_report(
        ["pattern", "b.n.", "band,bank,BONE,bin,bean,Bind,tank,band", "--limit=1"],
        "pattern     B.N.\nwords       7\nmatches     4\nshown       1\nword        BAND\n",
    )


def test_pattern_limit_inclusive_upper_endpoint_is_accepted() -> None:
    _assert_cli_report(
        ["pattern", "b.n.", "band,bank,BONE,bin,bean,Bind,tank,band", "--limit=1000"],
        "pattern     B.N.\n"
        "words       7\n"
        "matches     4\n"
        "shown       4\n"
        "word        BAND\n"
        "word        BANK\n"
        "word        BIND\n"
        "word        BONE\n",
    )


def test_render_accepts_a_repeated_interspersed_flag() -> None:
    _assert_cli_report(
        ["render", "--compact", "A.#/.../#..", "--compact"],
        "+---+---+---+\n"
        "| A |   |###|\n"
        "+---+---+---+\n"
        "|   |   |   |\n"
        "+---+---+---+\n"
        "|###|   |   |\n"
        "+---+---+---+\n",
    )


def test_check_default_minimum_length_is_three() -> None:
    _assert_cli_report(
        ["check", ".."],
        "grid        1x2\n"
        "blocks      0\n"
        "across      1\n"
        "down        0\n"
        "shortest    2\n"
        "longest     2\n"
        "unchecked   2\n"
        "problems    1\n"
        "problem     slot 1A has length 2 (below 3)\n",
        1,
    )


def test_check_minimum_length_inclusive_lower_endpoint_and_checked_flag() -> None:
    _assert_cli_report(
        ["check", "..", "--checked", "--min-length=2"],
        "grid        1x2\n"
        "blocks      0\n"
        "across      1\n"
        "down        0\n"
        "shortest    2\n"
        "longest     2\n"
        "unchecked   2\n"
        "problems    1\n"
        "problem     unchecked cells: 2 (the first is r1c1)\n",
        1,
    )


def test_check_minimum_length_inclusive_upper_endpoint_is_accepted() -> None:
    _assert_cli_report(
        ["check", "..", "--min-length=15"],
        "grid        1x2\n"
        "blocks      0\n"
        "across      1\n"
        "down        0\n"
        "shortest    2\n"
        "longest     2\n"
        "unchecked   2\n"
        "problems    1\n"
        "problem     slot 1A has length 2 (below 15)\n",
        1,
    )


def test_fill_default_limit_is_one() -> None:
    _assert_cli_report(
        ["fill", "..../.##./.##./....", "BAND,BEAD,BEAR,DARE,DATE,DOOR,LAKE,TEAM"],
        "grid        4x4\n"
        "slots       4\n"
        "words       8\n"
        "found       1\n"
        "fill        1 BAND/E##A/A##R/DATE\n",
    )


def test_fill_limit_inclusive_lower_endpoint_is_one() -> None:
    _assert_cli_report(
        [
            "fill",
            "..../.##./.##./....",
            "BAND,BEAD,BEAR,DARE,DATE,DOOR,LAKE,TEAM",
            "--limit=1",
        ],
        "grid        4x4\n"
        "slots       4\n"
        "words       8\n"
        "found       1\n"
        "fill        1 BAND/E##A/A##R/DATE\n",
    )


def test_fill_limit_inclusive_upper_endpoint_returns_all_four_fills() -> None:
    _assert_cli_report(
        [
            "fill",
            "..../.##./.##./....",
            "BAND,BEAD,BEAR,DARE,DATE,DOOR,LAKE,TEAM",
            "--limit=20",
        ],
        "grid        4x4\n"
        "slots       4\n"
        "words       8\n"
        "found       4\n"
        "fill        1 BAND/E##A/A##R/DATE\n"
        "fill        2 BAND/E##A/A##T/DARE\n"
        "fill        3 BEAD/A##A/N##R/DATE\n"
        "fill        4 BEAD/A##A/N##T/DARE\n",
    )


def test_count_default_maximum_is_one_hundred() -> None:
    _assert_cli_report(
        ["count", "..../.##./.##./....", "BAND,BEAD,BEAR,DARE,DATE,DOOR,LAKE,TEAM"],
        "grid        4x4\nslots       4\nwords       8\ncount       4\ncapped      no\n",
    )


def test_count_maximum_inclusive_lower_endpoint_is_accepted() -> None:
    _assert_cli_report(
        [
            "count",
            "..../.##./.##./....",
            "BAND,BEAD,BEAR,DARE,DATE,DOOR,LAKE,TEAM",
            "--max=1",
        ],
        "grid        4x4\nslots       4\nwords       8\ncount       1\ncapped      yes\n",
    )


def test_count_maximum_inclusive_upper_endpoint_is_accepted() -> None:
    _assert_cli_report(
        [
            "count",
            "..../.##./.##./....",
            "BAND,BEAD,BEAR,DARE,DATE,DOOR,LAKE,TEAM",
            "--max=1000",
        ],
        "grid        4x4\nslots       4\nwords       8\ncount       4\ncapped      no\n",
    )


@pytest.mark.parametrize(
    ("args", "message"),
    [
        (
            ["check", "--min-length=-1"],
            'invalid --min-length "-1" (expected an integer from 2 to 15)',
        ),
        (
            ["check", "--min-length=+3"],
            'invalid --min-length "+3" (expected an integer from 2 to 15)',
        ),
        (
            ["check", "--min-length=007"],
            'invalid --min-length "007" (expected an integer from 2 to 15)',
        ),
        (
            ["check", "--min-length=1.5"],
            'invalid --min-length "1.5" (expected an integer from 2 to 15)',
        ),
        (["check", "--min-length="], 'invalid --min-length "" (expected an integer from 2 to 15)'),
        (
            ["check", "--min-length=٣"],
            'invalid --min-length "?" (expected an integer from 2 to 15)',
        ),
        (
            ["check", "--min-length=10000000000"],
            'invalid --min-length "10000000000" (expected an integer from 2 to 15)',
        ),
        (
            ["check", "--min-length=1"],
            'invalid --min-length "1" (expected an integer from 2 to 15)',
        ),
        (
            ["check", "--min-length=16"],
            'invalid --min-length "16" (expected an integer from 2 to 15)',
        ),
        (["pattern", "--limit=-1"], 'invalid --limit "-1" (expected an integer from 1 to 1000)'),
        (["pattern", "--limit=+3"], 'invalid --limit "+3" (expected an integer from 1 to 1000)'),
        (["pattern", "--limit=007"], 'invalid --limit "007" (expected an integer from 1 to 1000)'),
        (["pattern", "--limit=1.5"], 'invalid --limit "1.5" (expected an integer from 1 to 1000)'),
        (["pattern", "--limit="], 'invalid --limit "" (expected an integer from 1 to 1000)'),
        (["pattern", "--limit=٣"], 'invalid --limit "?" (expected an integer from 1 to 1000)'),
        (
            ["pattern", "--limit=10000000000"],
            'invalid --limit "10000000000" (expected an integer from 1 to 1000)',
        ),
        (["pattern", "--limit=0"], 'invalid --limit "0" (expected an integer from 1 to 1000)'),
        (
            ["pattern", "--limit=1001"],
            'invalid --limit "1001" (expected an integer from 1 to 1000)',
        ),
        (["fill", "--limit=-1"], 'invalid --limit "-1" (expected an integer from 1 to 20)'),
        (["fill", "--limit=+3"], 'invalid --limit "+3" (expected an integer from 1 to 20)'),
        (["fill", "--limit=007"], 'invalid --limit "007" (expected an integer from 1 to 20)'),
        (["fill", "--limit=1.5"], 'invalid --limit "1.5" (expected an integer from 1 to 20)'),
        (["fill", "--limit="], 'invalid --limit "" (expected an integer from 1 to 20)'),
        (["fill", "--limit=٣"], 'invalid --limit "?" (expected an integer from 1 to 20)'),
        (
            ["fill", "--limit=10000000000"],
            'invalid --limit "10000000000" (expected an integer from 1 to 20)',
        ),
        (["fill", "--limit=0"], 'invalid --limit "0" (expected an integer from 1 to 20)'),
        (["fill", "--limit=21"], 'invalid --limit "21" (expected an integer from 1 to 20)'),
        (["count", "--max=-1"], 'invalid --max "-1" (expected an integer from 1 to 1000)'),
        (["count", "--max=+3"], 'invalid --max "+3" (expected an integer from 1 to 1000)'),
        (["count", "--max=007"], 'invalid --max "007" (expected an integer from 1 to 1000)'),
        (["count", "--max=1.5"], 'invalid --max "1.5" (expected an integer from 1 to 1000)'),
        (["count", "--max="], 'invalid --max "" (expected an integer from 1 to 1000)'),
        (["count", "--max=٣"], 'invalid --max "?" (expected an integer from 1 to 1000)'),
        (
            ["count", "--max=10000000000"],
            'invalid --max "10000000000" (expected an integer from 1 to 1000)',
        ),
        (["count", "--max=0"], 'invalid --max "0" (expected an integer from 1 to 1000)'),
        (["count", "--max=1001"], 'invalid --max "1001" (expected an integer from 1 to 1000)'),
        (
            ["pattern", "..", "AB", "--limit=2", "--limit=0"],
            'invalid --limit "0" (expected an integer from 1 to 1000)',
        ),
    ],
)
def test_option_numeric_syntax_and_bounds_have_exact_cli_diagnostics(
    args: list[str], message: str
) -> None:
    _assert_cli_error(args, message)


def test_pattern_limit_equals_syntax_at_end_of_arguments() -> None:
    _assert_cli_report(
        ["pattern", "b.n.", "band,bank,BONE,bin,bean,Bind,tank,band", "--limit=3"],
        "pattern     B.N.\n"
        "words       7\n"
        "matches     4\n"
        "shown       3\n"
        "word        BAND\n"
        "word        BANK\n"
        "word        BIND\n",
    )


def test_pattern_repeated_limit_overwrites_invalid_value() -> None:
    _assert_cli_report(
        [
            "pattern",
            "b.n.",
            "band,bank,BONE,bin,bean,Bind,tank,band",
            "--limit",
            "0",
            "--limit",
            "3",
        ],
        "pattern     B.N.\n"
        "words       7\n"
        "matches     4\n"
        "shown       3\n"
        "word        BAND\n"
        "word        BANK\n"
        "word        BIND\n",
    )


def test_count_accepts_maximum_of_one_hundred() -> None:
    _assert_cli_report(
        [
            "count",
            "..../.##./.##./....",
            "BAND,BEAD,BEAR,DARE,DATE,DOOR,LAKE,TEAM",
            "--max=100",
        ],
        "grid        4x4\nslots       4\nwords       8\ncount       4\ncapped      no\n",
    )


def test_number_dispatch_emits_one_complete_report() -> None:
    _assert_cli_report(
        ["number", "#"],
        "grid        1x1\nblocks      1\nacross      0\ndown        0\n",
    )


def test_symmetrize_dispatch_emits_one_complete_report() -> None:
    _assert_cli_report(
        ["symmetrize", "..#/..."],
        "added       1\ngrid        ..#/#..\n",
    )


def test_stats_dispatch_emits_one_complete_report() -> None:
    _assert_cli_report(
        ["stats", "CAT,DOG"],
        "words       2\n"
        "shortest    3\n"
        "longest     3\n"
        "length      3 x 2\n"
        "letters     A=1 C=1 D=1 G=1 O=1\n",
    )


def test_domains_dispatch_emits_one_complete_report_without_slots() -> None:
    _assert_cli_report(
        ["domains", ".", "CAT"],
        "grid        1x1\nslots       0\nwords       1\nconsistent  yes\n",
    )


def test_forced_dispatch_emits_one_complete_report_without_slots() -> None:
    _assert_cli_report(
        ["forced", ".", "CAT"],
        "grid        1x1\nconsistent  yes\nforced      0\nrow         .\n",
    )


_FORTY_ONE_WORDS = (
    "AA,AB,AC,AD,AE,AF,AG,AH,AI,AJ,AK,AL,AM,AN,AO,"
    "AP,AQ,AR,AS,AT,AU,AV,AW,AX,AY,AZ,BA,BB,BC,BD,"
    "BE,BF,BG,BH,BI,BJ,BK,BL,BM,BN,BO"
)


_WORD_LIMIT_TEMPLATE = "41 words (above 40, too large for COMMAND)"


_SOLVER_ADAPTERS: list[
    tuple[Callable[[list[str], dict[str, int], IO], tuple[str, int]], str, dict[str, int], str, str]
] = [
    (
        cmd_domains.run_domains,
        "domains",
        {},
        "grid is 6x6 (above 5x5, too large for domains)",
        "41 words (above 40, too large for domains)",
    ),
    (
        cmd_forced.run_forced,
        "forced",
        {},
        "grid is 6x6 (above 5x5, too large for forced)",
        "41 words (above 40, too large for forced)",
    ),
    (
        cmd_fill.run_fill,
        "fill",
        {"--limit": 1},
        "grid is 6x6 (above 5x5, too large for fill)",
        "41 words (above 40, too large for fill)",
    ),
    (
        cmd_count.run_count,
        "count",
        {"--max": 100},
        "grid is 6x6 (above 5x5, too large for count)",
        "41 words (above 40, too large for count)",
    ),
]


@pytest.mark.parametrize(
    ("adapter", "command", "options", "grid_message", "words_message"),
    _SOLVER_ADAPTERS,
)
def test_solver_adapters_raise_unprefixed_size_limit_failures(
    adapter: Callable[[list[str], dict[str, int], IO], tuple[str, int]],
    command: str,
    options: dict[str, int],
    grid_message: str,
    words_message: str,
) -> None:
    with pytest.raises(Fail) as grid_error:
        adapter(["....../....../....../....../....../......", "CAT"], options, FakeIO())

    assert str(grid_error.value) == grid_message

    with pytest.raises(Fail) as words_error:
        adapter([".", _FORTY_ONE_WORDS], options, FakeIO())

    assert str(words_error.value) == words_message
    assert words_message == _WORD_LIMIT_TEMPLATE.replace("COMMAND", command)


@pytest.mark.parametrize(
    ("command", "args", "message"),
    [
        (
            "domains",
            ["....../....../....../....../....../......", "D0G"],
            'invalid word "D0G" (expected 2 to 15 letters)',
        ),
        (
            "forced",
            ["....../....../....../....../....../......", "D0G"],
            'invalid word "D0G" (expected 2 to 15 letters)',
        ),
        (
            "fill",
            ["....../....../....../....../....../......", "D0G"],
            'invalid word "D0G" (expected 2 to 15 letters)',
        ),
        (
            "count",
            ["....../....../....../....../....../......", "D0G"],
            'invalid word "D0G" (expected 2 to 15 letters)',
        ),
        (
            "domains",
            ["....../....../....../....../....../......", _FORTY_ONE_WORDS],
            "grid is 6x6 (above 5x5, too large for domains)",
        ),
        (
            "forced",
            ["....../....../....../....../....../......", _FORTY_ONE_WORDS],
            "grid is 6x6 (above 5x5, too large for forced)",
        ),
        (
            "fill",
            ["....../....../....../....../....../......", _FORTY_ONE_WORDS],
            "grid is 6x6 (above 5x5, too large for fill)",
        ),
        (
            "count",
            ["....../....../....../....../....../......", _FORTY_ONE_WORDS],
            "grid is 6x6 (above 5x5, too large for count)",
        ),
        ("domains", [".", _FORTY_ONE_WORDS], "41 words (above 40, too large for domains)"),
        ("forced", [".", _FORTY_ONE_WORDS], "41 words (above 40, too large for forced)"),
        ("fill", [".", _FORTY_ONE_WORDS], "41 words (above 40, too large for fill)"),
        ("count", [".", _FORTY_ONE_WORDS], "41 words (above 40, too large for count)"),
    ],
)
def test_solving_cli_reports_argument_and_size_errors_in_order(
    command: str, args: list[str], message: str
) -> None:
    _assert_cli_error([command, *args], message)


@pytest.mark.parametrize(
    ("args", "stdin", "status", "out_calls", "err_calls"),
    [
        (
            ["stats", "-"],
            b"\xef\xbb\xbfAB\r\nBA\tAB\n",
            0,
            [
                "words       2\nshortest    2\nlongest     2\nlength      2 x 2\nletters     A=2 B=2\n"
            ],
            [],
        ),
        (["stats", "-"], b" \t\r\n", 2, [], ["crossmill: <stdin>: no input\n"]),
        (
            ["stats", "-"],
            b"AB\xff\n",
            2,
            [],
            ["crossmill: <stdin>: input is not valid UTF-8\n"],
        ),
    ],
)
def test_stats_stdin_binary_inputs_have_exact_reports(
    args: list[str],
    stdin: bytes,
    status: int,
    out_calls: list[str],
    err_calls: list[str],
) -> None:
    io = FakeIO(stdin)

    assert run(args, io) == status
    assert io.out_calls == out_calls
    assert io.err_calls == err_calls


def test_number_cli_reports_mismatched_row_width() -> None:
    _assert_cli_error(["number", "..#/.."], "row 2 has 2 cells but row 1 has 3")


def test_number_cli_rejects_sixteen_columns() -> None:
    _assert_cli_error(["number", "................"], "grid has 16 columns (above 15)")


def test_number_cli_reports_invalid_grid_diagnostic() -> None:
    _assert_cli_error(
        ["number", "a../..."],
        'invalid grid "a../..." (expected rows of # . and letters A to Z separated by /, '
        "such as ..#../.....)",
    )


def test_number_cli_rejects_sixteen_rows() -> None:
    _assert_cli_error(
        ["number", "./././././././././././././././."],
        "grid has 16 rows (above 15)",
    )


def test_stats_cli_reports_invalid_word_diagnostic() -> None:
    _assert_cli_error(["stats", "CAT,D0G"], 'invalid word "D0G" (expected 2 to 15 letters)')


def test_symmetrize_cli_reports_letter_collision() -> None:
    _assert_cli_error(
        ["symmetrize", "..#/.../A.."],
        "cell r3c1 holds a letter but its partner r1c3 is a block",
    )


def test_main_guard_dispatches_with_std_io_and_exits_with_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exercise `sys.exit(run(sys.argv[1:], StdIO()))` in memory."""
    fake_io = FakeIO()
    calls: list[tuple[list[str], IO]] = []

    def fake_run(args: list[str], io: IO) -> int:
        calls.append((args, io))
        return 7

    monkeypatch.setattr("crossmill.base.inputs.StdIO", lambda: fake_io)
    monkeypatch.setattr("crossmill.cli.cli.run", fake_run)
    monkeypatch.setattr(sys, "argv", ["crossmill", "stats", "CAT"])

    with pytest.raises(SystemExit) as exit_info:
        runpy.run_module("crossmill.__main__", run_name="__main__")

    assert exit_info.value.code == 7
    assert calls == [(["stats", "CAT"], fake_io)]
    assert fake_io.out_calls == []
    assert fake_io.err_calls == []


def test_importing_module_entry_point_has_no_output_or_exit(
    capfd: pytest.CaptureFixture[str],
) -> None:
    entry_point = importlib.import_module("crossmill.__main__")

    assert entry_point.run is run
    assert entry_point.StdIO is StdIO

    captured = capfd.readouterr()
    assert captured.out == ""
    assert captured.err == ""
