import pytest

from crossmill.base.fail import Fail
from crossmill.base.options import Spec
from crossmill.cli import (
    cmd_check,
    cmd_count,
    cmd_domains,
    cmd_fill,
    cmd_forced,
    cmd_number,
    cmd_pattern,
    cmd_render,
    cmd_stats,
    cmd_symmetrize,
)
from crossmill.cli.cli import run


class FakeIO:
    def __init__(self, data: bytes = b"") -> None:
        self.data = data
        self.out_calls: list[str] = []
        self.err_calls: list[str] = []

    def read_stdin(self) -> bytes:
        return self.data

    def out(self, text: str) -> None:
        self.out_calls.append(text)

    def err(self, text: str) -> None:
        self.err_calls.append(text)


def test_six_adapter_metadata_is_literal() -> None:
    assert cmd_check.USAGE == "crossmill check GRID [--min-length N] [--checked]"
    assert cmd_check.ARGS == 1
    assert cmd_check.SPECS == [Spec("--min-length", 2, 15, 3), Spec("--checked", flag=True)]

    assert cmd_number.USAGE == "crossmill number GRID"
    assert cmd_number.ARGS == 1
    assert cmd_number.SPECS == []

    assert cmd_render.USAGE == "crossmill render GRID [--compact]"
    assert cmd_render.ARGS == 1
    assert cmd_render.SPECS == [Spec("--compact", flag=True)]

    assert cmd_symmetrize.USAGE == "crossmill symmetrize GRID"
    assert cmd_symmetrize.ARGS == 1
    assert cmd_symmetrize.SPECS == []

    assert cmd_pattern.USAGE == "crossmill pattern PATTERN WORDS [--limit L]"
    assert cmd_pattern.ARGS == 2
    assert cmd_pattern.SPECS == [Spec("--limit", 1, 1000, 20)]

    assert cmd_stats.USAGE == "crossmill stats WORDS"
    assert cmd_stats.ARGS == 1
    assert cmd_stats.SPECS == []


def test_number_returns_exact_ten_slot_report_without_writing() -> None:
    io = FakeIO()

    result = cmd_number.run_number(["#...#/...../...../...../#...#"], {}, io)

    assert result == (
        (
            "grid        5x5\n"
            "blocks      4\n"
            "across      5\n"
            "down        5\n"
            "slot        1A 3 r1c2 ...\n"
            "slot        1D 5 r1c2 .....\n"
            "slot        2D 5 r1c3 .....\n"
            "slot        3D 5 r1c4 .....\n"
            "slot        4A 5 r2c1 .....\n"
            "slot        4D 3 r2c1 ...\n"
            "slot        5D 3 r2c5 ...\n"
            "slot        6A 5 r3c1 .....\n"
            "slot        7A 5 r4c1 .....\n"
            "slot        8A 3 r5c2 ...\n"
        ),
        0,
    )
    assert io.out_calls == []
    assert io.err_calls == []


def test_number_reports_a_grid_without_slots() -> None:
    io = FakeIO()

    result = cmd_number.run_number(["#"], {}, io)

    assert result == ("grid        1x1\nblocks      1\nacross      0\ndown        0\n", 0)
    assert io.out_calls == []
    assert io.err_calls == []


def test_render_returns_the_exact_standard_drawing_without_writing() -> None:
    io = FakeIO()

    result = cmd_render.run_render(["A.#/.../#.."], {"--compact": 0}, io)

    assert result == (
        (
            "+----+----+----+\n"
            "|1   |2   |####|\n"
            "| A  |    |####|\n"
            "+----+----+----+\n"
            "|3   |    |4   |\n"
            "|    |    |    |\n"
            "+----+----+----+\n"
            "|####|5   |    |\n"
            "|####|    |    |\n"
            "+----+----+----+\n"
        ),
        0,
    )
    assert io.out_calls == []
    assert io.err_calls == []


def test_render_returns_the_exact_compact_drawing_without_writing() -> None:
    io = FakeIO()

    result = cmd_render.run_render(["A.#/.../#.."], {"--compact": 1}, io)

    assert result == (
        (
            "+---+---+---+\n"
            "| A |   |###|\n"
            "+---+---+---+\n"
            "|   |   |   |\n"
            "+---+---+---+\n"
            "|###|   |   |\n"
            "+---+---+---+\n"
        ),
        0,
    )
    assert io.out_calls == []
    assert io.err_calls == []


def test_check_returns_the_exact_valid_construction_report() -> None:
    io = FakeIO()

    result = cmd_check.run_check(
        ["#...#/...../...../...../#...#"], {"--min-length": 3, "--checked": 0}, io
    )

    assert result == (
        (
            "grid        5x5\n"
            "blocks      4\n"
            "across      5\n"
            "down        5\n"
            "shortest    3\n"
            "longest     5\n"
            "unchecked   0\n"
            "problems    0\n"
        ),
        0,
    )
    assert io.out_calls == []
    assert io.err_calls == []


def test_check_reports_disconnected_regions_and_slotless_cells_in_order() -> None:
    io = FakeIO()

    result = cmd_check.run_check([".##/###/##."], {"--min-length": 3, "--checked": 0}, io)

    assert result == (
        (
            "grid        3x3\n"
            "blocks      7\n"
            "across      0\n"
            "down        0\n"
            "shortest    0\n"
            "longest     0\n"
            "unchecked   0\n"
            "problems    3\n"
            "problem     the open cells form 2 regions (the second starts at r3c3)\n"
            "problem     cell r1c1 is in no slot\n"
            "problem     cell r3c3 is in no slot\n"
        ),
        1,
    )
    assert io.out_calls == []
    assert io.err_calls == []


def test_check_reports_short_slots_and_checked_cells_exactly() -> None:
    io = FakeIO()

    result = cmd_check.run_check(["..../.##./.##./...."], {"--min-length": 5, "--checked": 1}, io)

    assert result == (
        (
            "grid        4x4\n"
            "blocks      4\n"
            "across      2\n"
            "down        2\n"
            "shortest    4\n"
            "longest     4\n"
            "unchecked   8\n"
            "problems    5\n"
            "problem     slot 1A has length 4 (below 5)\n"
            "problem     slot 1D has length 4 (below 5)\n"
            "problem     slot 2D has length 4 (below 5)\n"
            "problem     slot 3A has length 4 (below 5)\n"
            "problem     unchecked cells: 8 (the first is r1c2)\n"
        ),
        1,
    )
    assert io.out_calls == []
    assert io.err_calls == []


def test_check_combines_all_five_diagnostic_categories_in_order() -> None:
    io = FakeIO()

    result = cmd_check.run_check(["#.#/###/..."], {"--min-length": 4, "--checked": 1}, io)

    assert result == (
        (
            "grid        3x3\n"
            "blocks      5\n"
            "across      1\n"
            "down        0\n"
            "shortest    3\n"
            "longest     3\n"
            "unchecked   3\n"
            "problems    5\n"
            "problem     not symmetric: r1c1 is a block but r3c3 is not\n"
            "problem     the open cells form 2 regions (the second starts at r3c1)\n"
            "problem     cell r1c2 is in no slot\n"
            "problem     slot 1A has length 3 (below 4)\n"
            "problem     unchecked cells: 3 (the first is r3c1)\n"
        ),
        1,
    )
    assert io.out_calls == []
    assert io.err_calls == []


def test_symmetrize_adds_the_missing_partner_block() -> None:
    io = FakeIO()

    result = cmd_symmetrize.run_symmetrize(["..#../...../...../...../....."], {}, io)

    assert result == ("added       1\ngrid        ..#../...../...../...../..#..\n", 0)
    assert io.out_calls == []
    assert io.err_calls == []


def test_symmetrize_keeps_an_already_symmetric_grid_unchanged() -> None:
    io = FakeIO()

    result = cmd_symmetrize.run_symmetrize(["#./.#"], {}, io)

    assert result == ("added       0\ngrid        #./.#\n", 0)
    assert io.out_calls == []
    assert io.err_calls == []


def test_number_raises_the_exact_invalid_grid_failure() -> None:
    io = FakeIO()

    with pytest.raises(Fail) as error:
        cmd_number.run_number(["a../..."], {}, io)

    assert str(error.value) == (
        'invalid grid "a../..." (expected rows of # . and letters A to Z separated by /, '
        "such as ..#../.....)"
    )
    assert io.out_calls == []
    assert io.err_calls == []


def test_symmetrize_raises_the_exact_letter_collision_failure() -> None:
    io = FakeIO()

    with pytest.raises(Fail) as error:
        cmd_symmetrize.run_symmetrize(["..#/.../A.."], {}, io)

    assert str(error.value) == "cell r3c1 holds a letter but its partner r1c3 is a block"
    assert io.out_calls == []
    assert io.err_calls == []


def test_pattern_returns_the_exact_normalized_and_deduplicated_report() -> None:
    # AC-005 shorthand: pattern=B.N. and words=7; the literal report and status follow.
    io = FakeIO()

    result = cmd_pattern.run_pattern(
        ["b.n.", "band,bank,BONE,bin,bean,Bind,tank,band"], {"--limit": 20}, io
    )

    assert result == (
        (
            "pattern     B.N.\n"
            "words       7\n"
            "matches     4\n"
            "shown       4\n"
            "word        BAND\n"
            "word        BANK\n"
            "word        BIND\n"
            "word        BONE\n"
        ),
        0,
    )
    assert io.out_calls == []
    assert io.err_calls == []


def test_pattern_reports_zero_matches_without_word_rows() -> None:
    io = FakeIO()

    result = cmd_pattern.run_pattern(["ZZ", "CAT,DOG"], {"--limit": 20}, io)

    assert result == ("pattern     ZZ\nwords       2\nmatches     0\nshown       0\n", 0)
    assert io.out_calls == []
    assert io.err_calls == []


def test_pattern_validates_pattern_before_words() -> None:
    io = FakeIO()

    with pytest.raises(Fail) as error:
        cmd_pattern.run_pattern(["A", "D0G"], {"--limit": 20}, io)

    assert str(error.value) == 'invalid pattern "A" (expected 2 to 15 characters, letters or .)'
    assert io.out_calls == []
    assert io.err_calls == []


def test_stats_returns_exact_length_and_frequency_tie_report() -> None:
    io = FakeIO()

    result = cmd_stats.run_stats(["bank,BANK,bake,cat,dog,tide,xyz,bat"], {}, io)

    assert result == (
        (
            "words       7\n"
            "shortest    3\n"
            "longest     4\n"
            "length      3 x 4\n"
            "length      4 x 3\n"
            "letters     A=4 B=3 T=3 D=2 E=2\n"
        ),
        0,
    )
    assert io.out_calls == []
    assert io.err_calls == []


def test_stats_raises_the_exact_invalid_word_failure() -> None:
    io = FakeIO()

    with pytest.raises(Fail) as error:
        cmd_stats.run_stats(["CAT,D0G"], {}, io)

    assert str(error.value) == 'invalid word "D0G" (expected 2 to 15 letters)'
    assert io.out_calls == []
    assert io.err_calls == []


def test_dispatch_writes_a_complete_number_report_once() -> None:
    io = FakeIO()

    status = run(["number", "#...#/...../...../...../#...#"], io)

    assert status == 0
    assert io.out_calls == [
        (
            "grid        5x5\n"
            "blocks      4\n"
            "across      5\n"
            "down        5\n"
            "slot        1A 3 r1c2 ...\n"
            "slot        1D 5 r1c2 .....\n"
            "slot        2D 5 r1c3 .....\n"
            "slot        3D 5 r1c4 .....\n"
            "slot        4A 5 r2c1 .....\n"
            "slot        4D 3 r2c1 ...\n"
            "slot        5D 3 r2c5 ...\n"
            "slot        6A 5 r3c1 .....\n"
            "slot        7A 5 r4c1 .....\n"
            "slot        8A 3 r5c2 ...\n"
        )
    ]
    assert io.err_calls == []


def test_dispatch_writes_a_problem_report_once_and_preserves_status_one() -> None:
    io = FakeIO()

    status = run(["check", ".##/###/##."], io)

    assert status == 1
    assert io.out_calls == [
        (
            "grid        3x3\n"
            "blocks      7\n"
            "across      0\n"
            "down        0\n"
            "shortest    0\n"
            "longest     0\n"
            "unchecked   0\n"
            "problems    3\n"
            "problem     the open cells form 2 regions (the second starts at r3c3)\n"
            "problem     cell r1c1 is in no slot\n"
            "problem     cell r3c3 is in no slot\n"
        )
    ]
    assert io.err_calls == []


def test_solving_adapter_metadata_is_literal() -> None:
    assert cmd_domains.USAGE == "crossmill domains GRID WORDS"
    assert cmd_domains.ARGS == 2
    assert cmd_domains.SPECS == []

    assert cmd_forced.USAGE == "crossmill forced GRID WORDS"
    assert cmd_forced.ARGS == 2
    assert cmd_forced.SPECS == []

    assert cmd_fill.USAGE == "crossmill fill GRID WORDS [--limit L]"
    assert cmd_fill.ARGS == 2
    assert cmd_fill.SPECS == [Spec("--limit", 1, 20, 1)]

    assert cmd_count.USAGE == "crossmill count GRID WORDS [--max M]"
    assert cmd_count.ARGS == 2
    assert cmd_count.SPECS == [Spec("--max", 1, 1000, 100)]


def test_domains_returns_exact_frame_propagation_report_without_writing() -> None:
    io = FakeIO()

    result = cmd_domains.run_domains(
        ["..../.##./.##./....", "BAND,BEAD,BEAR,DARE,DATE,DOOR,LAKE,TEAM"], {}, io
    )

    assert result == (
        (
            "grid        4x4\n"
            "slots       4\n"
            "words       8\n"
            "consistent  yes\n"
            "slot        1A 4 r1c1 8 -> 2\n"
            "slot        1D 4 r1c1 8 -> 2\n"
            "slot        2D 4 r1c4 8 -> 3\n"
            "slot        3A 4 r4c1 8 -> 3\n"
        ),
        0,
    )
    assert io.out_calls == []
    assert io.err_calls == []


def test_forced_returns_exact_frame_projection_without_writing() -> None:
    io = FakeIO()

    result = cmd_forced.run_forced(
        ["..../.##./.##./....", "BAND,BEAD,BEAR,DARE,DATE,DOOR,LAKE,TEAM"], {}, io
    )

    assert result == (
        (
            "grid        4x4\n"
            "consistent  yes\n"
            "forced      3\n"
            "row         B..D\n"
            "row         .##.\n"
            "row         .##.\n"
            "row         D...\n"
        ),
        0,
    )
    assert io.out_calls == []
    assert io.err_calls == []


def test_fill_limit_three_returns_the_exact_first_three_frame_fills() -> None:
    io = FakeIO()

    result = cmd_fill.run_fill(
        ["..../.##./.##./....", "BAND,BEAD,BEAR,DARE,DATE,DOOR,LAKE,TEAM"],
        {"--limit": 3},
        io,
    )

    assert result == (
        (
            "grid        4x4\n"
            "slots       4\n"
            "words       8\n"
            "found       3\n"
            "fill        1 BAND/E##A/A##R/DATE\n"
            "fill        2 BAND/E##A/A##T/DARE\n"
            "fill        3 BEAD/A##A/N##R/DATE\n"
        ),
        0,
    )
    assert io.out_calls == []
    assert io.err_calls == []


def test_fill_limit_four_returns_the_corrected_ordered_frame_fills() -> None:
    io = FakeIO()

    result = cmd_fill.run_fill(
        ["..../.##./.##./....", "BAND,BEAD,BEAR,DARE,DATE,DOOR,LAKE,TEAM"],
        {"--limit": 4},
        io,
    )

    assert result == (
        (
            "grid        4x4\n"
            "slots       4\n"
            "words       8\n"
            "found       4\n"
            "fill        1 BAND/E##A/A##R/DATE\n"
            "fill        2 BAND/E##A/A##T/DARE\n"
            "fill        3 BEAD/A##A/N##R/DATE\n"
            "fill        4 BEAD/A##A/N##T/DARE\n"
        ),
        0,
    )
    assert io.out_calls == []
    assert io.err_calls == []


def test_fill_reports_no_distinct_frame_fill_with_status_one() -> None:
    io = FakeIO()

    result = cmd_fill.run_fill(["..../.##./.##./....", "BAND,BEAR,DOOR"], {"--limit": 1}, io)

    assert result == ("grid        4x4\nslots       4\nwords       3\nfound       0\n", 1)
    assert io.out_calls == []
    assert io.err_calls == []


def test_domains_reports_each_empty_frame_domain_and_status_one() -> None:
    io = FakeIO()

    result = cmd_domains.run_domains(["../..", "CAT"], {}, io)

    assert result == (
        (
            "grid        2x2\n"
            "slots       4\n"
            "words       1\n"
            "consistent  no\n"
            "slot        1A 2 r1c1 0 -> 0\n"
            "slot        1D 2 r1c1 0 -> 0\n"
            "slot        2D 2 r1c2 0 -> 0\n"
            "slot        3A 2 r2c1 0 -> 0\n"
        ),
        1,
    )
    assert io.out_calls == []
    assert io.err_calls == []


def test_forced_returns_only_the_inconsistent_status_report() -> None:
    io = FakeIO()

    result = cmd_forced.run_forced(["../..", "CAT"], {}, io)

    assert result == ("consistent  no\n", 1)
    assert io.out_calls == []
    assert io.err_calls == []


def test_forced_replaces_only_the_unfilled_forced_cell() -> None:
    io = FakeIO()

    result = cmd_forced.run_forced(["A.", "AB"], {}, io)

    assert result == (
        "grid        1x2\nconsistent  yes\nforced      1\nrow         AB\n",
        0,
    )
    assert io.out_calls == []
    assert io.err_calls == []


def test_count_returns_the_exact_capped_three_by_three_report() -> None:
    io = FakeIO()

    result = cmd_count.run_count(
        [".../.../...", "APE,ASP,EAT,PAR,PAT,PEA,SEA,TEA,ATE,HAT,ASH,EAR,TAR"],
        {"--max": 4},
        io,
    )

    assert result == (
        "grid        3x3\nslots       6\nwords       13\ncount       4\ncapped      yes\n",
        0,
    )
    assert io.out_calls == []
    assert io.err_calls == []


def test_count_at_the_exact_frame_cap_is_not_capped() -> None:
    io = FakeIO()

    result = cmd_count.run_count(
        ["..../.##./.##./....", "BAND,BEAD,BEAR,DARE,DATE,DOOR,LAKE,TEAM"],
        {"--max": 4},
        io,
    )

    assert result == (
        "grid        4x4\nslots       4\nwords       8\ncount       4\ncapped      no\n",
        0,
    )
    assert io.out_calls == []
    assert io.err_calls == []


def test_count_above_the_frame_cap_reports_capped_count() -> None:
    io = FakeIO()

    result = cmd_count.run_count(
        ["..../.##./.##./....", "BAND,BEAD,BEAR,DARE,DATE,DOOR,LAKE,TEAM"],
        {"--max": 3},
        io,
    )

    assert result == (
        "grid        4x4\nslots       4\nwords       8\ncount       3\ncapped      yes\n",
        0,
    )
    assert io.out_calls == []
    assert io.err_calls == []


def test_count_reports_zero_fills_without_capping() -> None:
    io = FakeIO()

    result = cmd_count.run_count(["../..", "CAT"], {"--max": 100}, io)

    assert result == (
        "grid        2x2\nslots       4\nwords       1\ncount       0\ncapped      no\n",
        0,
    )
    assert io.out_calls == []
    assert io.err_calls == []


def test_all_solving_commands_report_their_slotless_grid_results_without_writing() -> None:
    io = FakeIO()

    assert cmd_domains.run_domains([".", "CAT"], {}, io) == (
        "grid        1x1\nslots       0\nwords       1\nconsistent  yes\n",
        0,
    )
    assert cmd_forced.run_forced([".", "CAT"], {}, io) == (
        "grid        1x1\nconsistent  yes\nforced      0\nrow         .\n",
        0,
    )
    assert cmd_fill.run_fill([".", "CAT"], {"--limit": 1}, io) == (
        "grid        1x1\nslots       0\nwords       1\nfound       1\nfill        1 .\n",
        0,
    )
    assert cmd_count.run_count([".", "CAT"], {"--max": 100}, io) == (
        "grid        1x1\nslots       0\nwords       1\ncount       1\ncapped      no\n",
        0,
    )
    assert io.out_calls == []
    assert io.err_calls == []


def test_dispatch_writes_domains_report_once_and_preserves_status_one() -> None:
    io = FakeIO()

    status = run(["domains", "../..", "CAT"], io)

    assert status == 1
    assert io.out_calls == [
        (
            "grid        2x2\n"
            "slots       4\n"
            "words       1\n"
            "consistent  no\n"
            "slot        1A 2 r1c1 0 -> 0\n"
            "slot        1D 2 r1c1 0 -> 0\n"
            "slot        2D 2 r1c2 0 -> 0\n"
            "slot        3A 2 r2c1 0 -> 0\n"
        )
    ]
    assert io.err_calls == []


def test_dispatch_writes_forced_report_once_and_preserves_status_zero() -> None:
    io = FakeIO()

    status = run(["forced", "A.", "AB"], io)

    assert status == 0
    assert io.out_calls == ["grid        1x2\nconsistent  yes\nforced      1\nrow         AB\n"]
    assert io.err_calls == []


def test_dispatch_writes_fill_report_once_and_preserves_status_zero() -> None:
    io = FakeIO()

    status = run(["fill", ".", "CAT"], io)

    assert status == 0
    assert io.out_calls == [
        "grid        1x1\nslots       0\nwords       1\nfound       1\nfill        1 .\n"
    ]
    assert io.err_calls == []


def test_dispatch_writes_count_report_once_and_preserves_status_zero() -> None:
    io = FakeIO()

    status = run(["count", "../..", "CAT"], io)

    assert status == 0
    assert io.out_calls == [
        "grid        2x2\nslots       4\nwords       1\ncount       0\ncapped      no\n"
    ]
    assert io.err_calls == []
