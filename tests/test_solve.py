from collections.abc import Iterator

import pytest

from crossmill.base.fail import Fail
from crossmill.grid.model import Grid, parse_grid
from crossmill.slots.find import Slot, find_slots
from crossmill.solve import search as search_module
from crossmill.solve.counting import count_fills
from crossmill.solve.domains import initial_domains, propagate
from crossmill.solve.letters import cell_letters
from crossmill.solve.problem import load
from crossmill.solve.search import filled_rows, fills


class FakeIO:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.read_count = 0
        self.stdout: list[str] = []
        self.stderr: list[str] = []

    def read_stdin(self) -> bytes:
        self.read_count += 1
        return self.data

    def out(self, text: str) -> None:
        self.stdout.append(text)

    def err(self, text: str) -> None:
        self.stderr.append(text)


def test_load_normalizes_words_and_returns_slots_in_order() -> None:
    io = FakeIO(b"unused")

    grid, slots, words = load(["A./..", "ba,AB,ba"], io, "domains")

    assert grid.rows == ("A.", "..")
    assert [slot.name for slot in slots] == ["1A", "1D", "2D", "3A"]
    assert words == ["AB", "BA"]
    assert io.read_count == 0


def test_load_returns_no_slots_for_a_blocked_grid() -> None:
    grid, slots, words = load(["##/##", "AB"], FakeIO(b"unused"), "domains")

    assert grid.rows == ("##", "##")
    assert slots == []
    assert words == ["AB"]


def test_load_returns_no_slots_for_isolated_open_cells() -> None:
    grid, slots, words = load([".#/#.", "AB"], FakeIO(b"unused"), "domains")

    assert grid.rows == (".#", "#.")
    assert slots == []
    assert words == ["AB"]


def test_load_literal_words_does_not_read_stdin_or_write_output() -> None:
    io = FakeIO(b"unused")

    grid, slots, words = load(["..", "CAT,DOG"], io, "domains")

    assert grid.rows == ("..",)
    assert [slot.name for slot in slots] == ["1A"]
    assert words == ["CAT", "DOG"]
    assert io.read_count == 0
    assert io.stdout == []
    assert io.stderr == []


def test_load_stdin_skips_bom_and_splits_crlf_and_tabs() -> None:
    io = FakeIO(b"\xef\xbb\xbfba\r\nAB\tba")

    grid, slots, words = load(["../..", "-"], io, "domains")

    assert grid.rows == ("..", "..")
    assert [slot.name for slot in slots] == ["1A", "1D", "2D", "3A"]
    assert words == ["AB", "BA"]
    assert io.read_count == 1
    assert io.stdout == []
    assert io.stderr == []


def test_load_rejects_grid_before_reading_stdin() -> None:
    io = FakeIO(b"\xff")

    with pytest.raises(Fail) as error:
        load(["a", "-"], io, "domains")

    assert str(error.value) == (
        'invalid grid "a" (expected rows of # . and letters A to Z separated by /, '
        "such as ..#../.....)"
    )
    assert io.read_count == 0
    assert io.stdout == []
    assert io.stderr == []


def test_load_rejects_invalid_words_before_grid_size_limit() -> None:
    io = FakeIO(b"unused")

    with pytest.raises(Fail) as error:
        load(["......", "D0G"], io, "domains")

    assert str(error.value) == 'invalid word "D0G" (expected 2 to 15 letters)'
    assert io.read_count == 0
    assert io.stdout == []
    assert io.stderr == []


def test_load_decodes_stdin_before_grid_size_limit() -> None:
    io = FakeIO(b"\xff")

    with pytest.raises(Fail) as error:
        load(["......", "-"], io, "domains")

    assert str(error.value) == "<stdin>: input is not valid UTF-8"
    assert io.read_count == 1
    assert io.stdout == []
    assert io.stderr == []


def test_load_rejects_empty_stdin_before_grid_size_limit() -> None:
    io = FakeIO(b" \r\n\t")

    with pytest.raises(Fail) as error:
        load(["..", "-"], io, "domains")

    assert str(error.value) == "<stdin>: no input"
    assert io.read_count == 1
    assert io.stdout == []
    assert io.stderr == []


W40 = (
    "AA,AB,AC,AD,AE,AF,AG,AH,AI,AJ,AK,AL,AM,AN,AO,AP,AQ,AR,AS,AT,AU,AV,AW,AX,AY,AZ,"
    "BA,BB,BC,BD,BE,BF,BG,BH,BI,BJ,BK,BL,BM,BN"
)
W41 = (
    "AA,AB,AC,AD,AE,AF,AG,AH,AI,AJ,AK,AL,AM,AN,AO,AP,AQ,AR,AS,AT,AU,AV,AW,AX,AY,AZ,"
    "BA,BB,BC,BD,BE,BF,BG,BH,BI,BJ,BK,BL,BM,BN,BO"
)
DUPLICATE_W40 = (
    "AA,AB,AC,AD,AE,AF,AG,AH,AI,AJ,AK,AL,AM,AN,AO,AP,AQ,AR,AS,AT,AU,AV,AW,AX,AY,AZ,"
    "BA,BB,BC,BD,BE,BF,BG,BH,BI,BJ,BK,BL,BM,BN,aa"
)


def test_load_accepts_inclusive_five_by_five_and_forty_word_limits() -> None:
    grid, slots, words = load(["...../...../...../...../.....", W40], FakeIO(b"unused"), "domains")

    assert grid.rows == (".....", ".....", ".....", ".....", ".....")
    assert len(slots) == 10
    assert len(words) == 40
    assert words[0] == "AA"
    assert words[39] == "BN"


def test_load_deduplicates_words_before_applying_the_forty_word_limit() -> None:
    grid, slots, words = load(["..", DUPLICATE_W40], FakeIO(b"unused"), "forced")

    assert grid.rows == ("..",)
    assert [slot.name for slot in slots] == ["1A"]
    assert len(words) == 40
    assert words[0] == "AA"
    assert words[39] == "BN"


def test_load_rejects_forty_one_words_with_the_command_in_the_error() -> None:
    with pytest.raises(Fail) as error:
        load(["..", W41], FakeIO(b"unused"), "forced")

    assert str(error.value) == "41 words (above 40, too large for forced)"


def test_load_checks_grid_limit_before_forty_one_word_limit() -> None:
    with pytest.raises(Fail) as error:
        load(["......", W41], FakeIO(b"unused"), "domains")

    assert str(error.value) == "grid is 1x6 (above 5x5, too large for domains)"


def test_load_rejects_six_rows_with_the_requested_command_in_the_error() -> None:
    with pytest.raises(Fail) as error:
        load(["./././././.", "AB"], FakeIO(b"unused"), "count")

    assert str(error.value) == "grid is 6x1 (above 5x5, too large for count)"


def test_initial_domains_filter_by_pattern_and_length_in_slot_order() -> None:
    grid = parse_grid("A./..")
    slots = find_slots(grid)

    assert initial_domains(grid, slots, ["AB", "AX", "BA", "CAT"]) == [
        ["AB", "AX"],
        ["AB", "AX"],
        ["AB", "AX", "BA"],
        ["AB", "AX", "BA"],
    ]


def test_initial_domains_keep_the_supplied_reversed_slot_order() -> None:
    grid = parse_grid("A./..")
    slots = find_slots(grid)

    assert initial_domains(grid, list(reversed(slots)), ["AB", "AX", "BA", "CAT"]) == [
        ["AB", "AX", "BA"],
        ["AB", "AX", "BA"],
        ["AB", "AX"],
        ["AB", "AX"],
    ]


def test_initial_domains_returns_an_empty_domain_when_nothing_matches() -> None:
    grid = parse_grid("ZZ")
    slots = find_slots(grid)

    assert initial_domains(grid, slots, ["AB"]) == [[]]


def test_initial_domains_supports_an_empty_lexicon() -> None:
    grid = parse_grid("../..")
    slots = find_slots(grid)

    assert initial_domains(grid, slots, []) == [[], [], [], []]


def test_initial_domains_returns_no_domains_for_a_slotless_grid() -> None:
    grid = parse_grid(".#/#.")
    slots = find_slots(grid)

    assert initial_domains(grid, slots, ["AB"]) == []


def test_propagate_reaches_fixed_point_after_cascading_removals_without_mutating_inputs() -> None:
    slots = find_slots(parse_grid("../.."))
    domains = [["AB", "CD"], ["AX", "CY"], ["BZ"], ["XZ"]]
    original_domains = [["AB", "CD"], ["AX", "CY"], ["BZ"], ["XZ"]]

    result = propagate(slots, domains)

    assert result == [["AB"], ["AX"], ["BZ"], ["XZ"]]
    assert propagate(slots, result) == result
    assert domains == original_domains
    assert result is not domains
    assert all(result[index] is not domains[index] for index in range(len(domains)))


def test_propagate_empties_all_domains_for_contradictory_crossings() -> None:
    slots = find_slots(parse_grid("../.."))

    assert propagate(slots, [["AB"], ["CD"], ["AB"], ["CD"]]) == [[], [], [], []]


def test_propagate_keeps_an_initial_empty_domain_and_propagates_its_consequences() -> None:
    slots = find_slots(parse_grid("../.."))

    assert propagate(slots, [[], ["AA"], ["AA"], ["AA"]]) == [[], [], [], []]


def test_propagate_does_not_apply_a_word_uniqueness_constraint() -> None:
    slots = find_slots(parse_grid("../.."))

    assert propagate(slots, [["AA"], ["AA"], ["AA"], ["AA"]]) == [
        ["AA"],
        ["AA"],
        ["AA"],
        ["AA"],
    ]


def test_propagate_leaves_disconnected_domains_and_slotless_input_unchanged() -> None:
    # AC-006 literals: Grid `..#..`, domains `[[],['AB','BA']]` -> `[[],['AB','BA']]`.
    disconnected_slots = find_slots(parse_grid("..#.."))
    disconnected_domains = [[], ["AB", "BA"]]

    assert propagate(disconnected_slots, disconnected_domains) == [[], ["AB", "BA"]]
    # AC-006 literals: Slots `[]`, domains `[]` -> `[]`.
    assert propagate([], []) == []


def test_propagate_uses_interior_offsets_and_preserves_reversed_slot_order() -> None:
    # AC-006 literals: Grid `.../#.#`, domains `[['ABC','ADC'],['BX']]` -> `[['ABC'],['BX']]`.
    slots = find_slots(parse_grid(".../#.#"))
    domains = [["ABC", "ADC"], ["BX"]]

    assert [slot.name for slot in slots] == ["1A", "2D"]
    assert propagate(slots, domains) == [["ABC"], ["BX"]]
    assert propagate(list(reversed(slots)), list(reversed(domains))) == [["BX"], ["ABC"]]


def test_cell_letters_projects_letters_for_a_singleton_domain() -> None:
    slots = find_slots(parse_grid("AB"))

    assert cell_letters(slots, [["AB"]]) == {(0, 0): {"A"}, (0, 1): {"B"}}


def test_cell_letters_keeps_each_letter_from_an_ambiguous_domain() -> None:
    slots = find_slots(parse_grid(".."))

    assert cell_letters(slots, [["AB", "AC"]]) == {
        (0, 0): {"A"},
        (0, 1): {"B", "C"},
    }


def test_cell_letters_intersects_contributions_at_crossings() -> None:
    slots = find_slots(parse_grid("../.#"))

    assert cell_letters(slots, [["AB", "CB"], ["AX"]]) == {
        (0, 0): {"A"},
        (0, 1): {"B"},
        (1, 0): {"X"},
    }


def test_cell_letters_retains_an_empty_intersection_at_a_conflicting_crossing() -> None:
    slots = find_slots(parse_grid("../.#"))

    assert cell_letters(slots, [["AB"], ["CX"]]) == {
        (0, 0): set(),
        (0, 1): {"B"},
        (1, 0): {"X"},
    }


def test_cell_letters_includes_covered_cells_with_an_empty_domain() -> None:
    slots = find_slots(parse_grid(".."))

    assert cell_letters(slots, [[]]) == {(0, 0): set(), (0, 1): set()}


def test_cell_letters_omits_cells_not_covered_by_any_slot() -> None:
    slots = find_slots(parse_grid(".#/#."))

    assert cell_letters(slots, []) == {}


def test_frame_domains_propagate_to_expected_domains_and_forced_letters() -> None:
    grid = parse_grid("..../.##./.##./....")
    slots = find_slots(grid)
    lexicon = ["BAND", "BEAD", "BEAR", "DARE", "DATE", "DOOR", "LAKE", "TEAM"]

    initial = initial_domains(grid, slots, lexicon)
    narrowed = propagate(slots, initial)
    letters = cell_letters(slots, narrowed)

    assert [len(domain) for domain in initial] == [8, 8, 8, 8]
    assert narrowed == [
        ["BAND", "BEAD"],
        ["BAND", "BEAD"],
        ["DARE", "DATE", "DOOR"],
        ["DARE", "DATE", "DOOR"],
    ]
    assert {cell: values for cell, values in letters.items() if len(values) == 1} == {
        (0, 0): {"B"},
        (0, 3): {"D"},
        (3, 0): {"D"},
    }


# AC-001 frame case: limit=4, all four ordered fills.
def test_fills_frame_returns_all_four_assignments_in_slot_order() -> None:
    grid = parse_grid("..../.##./.##./....")
    slots = find_slots(grid)
    lexicon = ["BAND", "BEAD", "BEAR", "DARE", "DATE", "DOOR", "LAKE", "TEAM"]

    assert fills(grid, slots, lexicon, 4) == [
        ["BAND", "BEAD", "DARE", "DATE"],
        ["BAND", "BEAD", "DATE", "DARE"],
        ["BEAD", "BAND", "DARE", "DATE"],
        ["BEAD", "BAND", "DATE", "DARE"],
    ]


# AC-001 frame case: limit=1, first fill only.
def test_fills_frame_limit_one_returns_the_first_assignment() -> None:
    grid = parse_grid("..../.##./.##./....")
    slots = find_slots(grid)
    lexicon = ["BAND", "BEAD", "BEAR", "DARE", "DATE", "DOOR", "LAKE", "TEAM"]

    assert fills(grid, slots, lexicon, 1) == [["BAND", "BEAD", "DARE", "DATE"]]


# AC-001 frame case: limit=3, first three fills.
def test_fills_frame_limit_three_returns_the_first_three_assignments() -> None:
    grid = parse_grid("..../.##./.##./....")
    slots = find_slots(grid)
    lexicon = ["BAND", "BEAD", "BEAR", "DARE", "DATE", "DOOR", "LAKE", "TEAM"]

    assert fills(grid, slots, lexicon, 3) == [
        ["BAND", "BEAD", "DARE", "DATE"],
        ["BAND", "BEAD", "DATE", "DARE"],
        ["BEAD", "BAND", "DARE", "DATE"],
    ]


# AC-001 frame case: limit=20, fewer fills than the limit.
def test_fills_frame_limit_twenty_returns_all_four_assignments() -> None:
    grid = parse_grid("..../.##./.##./....")
    slots = find_slots(grid)
    lexicon = ["BAND", "BEAD", "BEAR", "DARE", "DATE", "DOOR", "LAKE", "TEAM"]

    assert fills(grid, slots, lexicon, 20) == [
        ["BAND", "BEAD", "DARE", "DATE"],
        ["BAND", "BEAD", "DATE", "DARE"],
        ["BEAD", "BAND", "DARE", "DATE"],
        ["BEAD", "BAND", "DATE", "DARE"],
    ]


def test_filled_rows_projects_each_ordered_frame_assignment() -> None:
    grid = parse_grid("..../.##./.##./....")
    slots = find_slots(grid)

    assert filled_rows(grid, slots, ["BAND", "BEAD", "DARE", "DATE"]) == ("BAND/E##A/A##R/DATE")
    assert filled_rows(grid, slots, ["BAND", "BEAD", "DATE", "DARE"]) == ("BAND/E##A/A##T/DARE")
    assert filled_rows(grid, slots, ["BEAD", "BAND", "DARE", "DATE"]) == ("BEAD/A##A/N##R/DATE")
    assert filled_rows(grid, slots, ["BEAD", "BAND", "DATE", "DARE"]) == ("BEAD/A##A/N##T/DARE")


def test_fills_assigns_distinct_words_to_disconnected_slots() -> None:
    grid = parse_grid("..#..")
    slots = find_slots(grid)

    assert fills(grid, slots, ["AB", "CD"], 20) == [["AB", "CD"], ["CD", "AB"]]


def test_fills_rejects_disconnected_slots_with_only_one_word() -> None:
    grid = parse_grid("..#..")
    slots = find_slots(grid)

    assert fills(grid, slots, ["AB"], 20) == []


def test_fills_rejects_crossing_contradictions() -> None:
    grid = parse_grid("../..")
    slots = find_slots(grid)

    assert fills(grid, slots, ["AB", "CD"], 20) == []


def test_fills_rejects_an_empty_initial_domain() -> None:
    grid = parse_grid("...")
    slots = find_slots(grid)

    assert fills(grid, slots, ["AB"], 20) == []


def test_fills_rejects_the_unsatisfiable_frame_lexicon() -> None:
    grid = parse_grid("..../.##./.##./....")
    slots = find_slots(grid)

    assert fills(grid, slots, ["BAND", "BEAR", "DOOR"], 20) == []


def test_slotless_all_block_grid_has_one_empty_fill_and_count() -> None:
    grid = parse_grid("##/##")

    assert fills(grid, [], ["AB"], limit=1) == [[]]
    assert filled_rows(grid, [], words=[]) == "##/##"
    assert count_fills(grid, [], ["AB"], cap=1) == (1, False)


def test_slotless_isolated_empty_cells_have_one_empty_fill_and_count() -> None:
    grid = parse_grid(".#/#.")

    assert fills(grid, [], ["AB"], limit=1) == [[]]
    assert filled_rows(grid, [], words=[]) == ".#/#."
    assert count_fills(grid, [], ["AB"], cap=1) == (1, False)


def test_slotless_isolated_fixed_letter_has_one_empty_fill_and_count() -> None:
    grid = parse_grid("A#/#.")

    assert fills(grid, [], ["AB"], limit=1) == [[]]
    assert filled_rows(grid, [], words=[]) == "A#/#."
    assert count_fills(grid, [], ["AB"], cap=1) == (1, False)


def test_fills_project_fixed_letters_and_cells_outside_slots_without_mutation() -> None:
    grid = parse_grid("A.###/#####/Z#.#.")
    slots = find_slots(grid)
    lexicon = ["AB", "AC", "BA"]
    original_grid = grid
    original_slots = slots.copy()
    original_lexicon = lexicon.copy()

    result = fills(grid, slots, lexicon, 20)

    assert result == [["AB"], ["AC"]]
    assert filled_rows(grid, slots, result[0]) == "AB###/#####/Z#.#."
    assert filled_rows(grid, slots, result[1]) == "AC###/#####/Z#.#."
    assert grid == original_grid
    assert slots == original_slots
    assert lexicon == original_lexicon


def test_fills_repeated_calls_return_equal_non_aliased_results() -> None:
    grid = parse_grid("A.###/#####/Z#.#.")
    slots = find_slots(grid)
    lexicon = ["AB", "AC", "BA"]

    first = fills(grid, slots, lexicon, 20)
    second = fills(grid, slots, lexicon, 20)

    assert first == [["AB"], ["AC"]]
    assert second == first
    assert first is not second
    assert first[0] is not first[1]
    assert second[0] is not second[1]
    assert first[0] is not second[0]
    first[0][0] = "XX"
    assert second == [["AB"], ["AC"]]


# AC-005 row: Frame, `cap=3` | overflow | `(3, True)`.
def test_count_fills_frame_cap_three_reports_overflow() -> None:
    grid = parse_grid("..../.##./.##./....")
    slots = find_slots(grid)
    lexicon = ["BAND", "BEAD", "BEAR", "DARE", "DATE", "DOOR", "LAKE", "TEAM"]

    assert count_fills(grid, slots, lexicon, cap=3) == (3, True)


# AC-005 row: Frame, `cap=4` | exactly cap | `(4, False)`.
def test_count_fills_frame_exact_cap_four_is_not_capped() -> None:
    grid = parse_grid("..../.##./.##./....")
    slots = find_slots(grid)
    lexicon = ["BAND", "BEAD", "BEAR", "DARE", "DATE", "DOOR", "LAKE", "TEAM"]

    assert count_fills(grid, slots, lexicon, cap=4) == (4, False)


# AC-005 row: Frame, `cap=5` | below cap | `(4, False)`.
def test_count_fills_frame_cap_five_returns_all_four_uncapped() -> None:
    grid = parse_grid("..../.##./.##./....")
    slots = find_slots(grid)
    lexicon = ["BAND", "BEAD", "BEAR", "DARE", "DATE", "DOOR", "LAKE", "TEAM"]

    assert count_fills(grid, slots, lexicon, cap=5) == (4, False)


def test_count_fills_disconnected_slots_with_one_word_has_no_fill() -> None:
    grid = parse_grid("..#..")
    slots = find_slots(grid)

    assert count_fills(grid, slots, ["AB"], cap=1) == (0, False)


def test_count_fills_counts_more_than_twenty_with_overflow() -> None:
    grid = parse_grid("..#../#####/..###")
    slots = find_slots(grid)
    lexicon = ["AB", "CD", "EF", "GH"]

    assert count_fills(grid, slots, lexicon, cap=23) == (23, True)


def test_count_fills_counts_more_than_twenty_at_exact_boundary() -> None:
    grid = parse_grid("..#../#####/..###")
    slots = find_slots(grid)
    lexicon = ["AB", "CD", "EF", "GH"]

    assert count_fills(grid, slots, lexicon, cap=24) == (24, False)


def test_count_fills_caps_the_specified_three_by_three_fixture() -> None:
    grid = parse_grid(".../.../...")
    slots = find_slots(grid)
    lexicon = [
        "APE",
        "ASH",
        "ASP",
        "ATE",
        "EAR",
        "EAT",
        "HAT",
        "PAR",
        "PAT",
        "PEA",
        "SEA",
        "TAR",
        "TEA",
    ]

    assert count_fills(grid, slots, lexicon, cap=4) == (4, True)


def _observe_solutions(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[list[list[str]], list[bool]]:
    discovered: list[list[str]] = []
    exhausted: list[bool] = []
    original_solutions = search_module._solutions

    def observe(grid: Grid, slots: list[Slot], lexicon: list[str]) -> Iterator[list[str]]:
        for solution in original_solutions(grid, slots, lexicon):
            discovered.append(solution)
            yield solution
        exhausted.append(True)

    monkeypatch.setattr(search_module, "_solutions", observe)
    return discovered, exhausted


# AC-006 row: Frame, `limit=1` stops after the first discovered fill.
def test_fills_limit_one_stops_without_exhausting_search(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    grid = parse_grid("..../.##./.##./....")
    slots = find_slots(grid)
    lexicon = ["BAND", "BEAD", "BEAR", "DARE", "DATE", "DOOR", "LAKE", "TEAM"]
    discovered, exhausted = _observe_solutions(monkeypatch)

    assert fills(grid, slots, lexicon, limit=1) == [["BAND", "BEAD", "DARE", "DATE"]]
    assert discovered == [["BAND", "BEAD", "DARE", "DATE"]]
    assert exhausted == []


# AC-006 row: Frame, `cap=1` stops after discovering the second fill.
def test_count_fills_cap_one_stops_after_overflow_is_discovered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    grid = parse_grid("..../.##./.##./....")
    slots = find_slots(grid)
    lexicon = ["BAND", "BEAD", "BEAR", "DARE", "DATE", "DOOR", "LAKE", "TEAM"]
    discovered, exhausted = _observe_solutions(monkeypatch)

    assert count_fills(grid, slots, lexicon, cap=1) == (1, True)
    assert discovered == [
        ["BAND", "BEAD", "DARE", "DATE"],
        ["BAND", "BEAD", "DATE", "DARE"],
    ]
    assert exhausted == []


# AC-006 row: Frame, `cap=4` must exhaust search to establish the exact boundary.
def test_count_fills_exact_cap_exhausts_after_four_discoveries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    grid = parse_grid("..../.##./.##./....")
    slots = find_slots(grid)
    lexicon = ["BAND", "BEAD", "BEAR", "DARE", "DATE", "DOOR", "LAKE", "TEAM"]
    discovered, exhausted = _observe_solutions(monkeypatch)

    assert count_fills(grid, slots, lexicon, cap=4) == (4, False)
    assert discovered == [
        ["BAND", "BEAD", "DARE", "DATE"],
        ["BAND", "BEAD", "DATE", "DARE"],
        ["BEAD", "BAND", "DARE", "DATE"],
        ["BEAD", "BAND", "DATE", "DARE"],
    ]
    assert exhausted == [True]
