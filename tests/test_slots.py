import dataclasses

import pytest

from crossmill.grid.model import parse_grid
from crossmill.slots.crossings import crossings
from crossmill.slots.find import Slot, find_slots, slot_pattern
from crossmill.slots.numbering import number_cells


def test_number_cells_numbers_shared_across_and_down_starts_in_reading_order() -> None:
    assert number_cells(parse_grid("../..")) == {
        (0, 0): 1,
        (0, 1): 2,
        (1, 0): 3,
    }


def test_number_cells_numbers_block_and_letter_grid_starts() -> None:
    assert number_cells(parse_grid("A.#/.../#..")) == {
        (0, 0): 1,
        (0, 1): 2,
        (1, 0): 3,
        (1, 2): 4,
        (2, 1): 5,
    }


def test_number_cells_numbers_a_single_row_start() -> None:
    assert number_cells(parse_grid("...")) == {(0, 0): 1}


def test_number_cells_numbers_a_single_column_start() -> None:
    assert number_cells(parse_grid("././.")) == {(0, 0): 1}


def test_number_cells_returns_empty_for_a_fully_blocked_grid() -> None:
    assert number_cells(parse_grid("###/###")) == {}


def test_number_cells_ignores_isolated_open_cells() -> None:
    assert number_cells(parse_grid(".##/###/##.")) == {}


def test_number_cells_ignores_a_single_open_cell() -> None:
    assert number_cells(parse_grid(".")) == {}


def test_across_slot_retains_fields_name_and_cells() -> None:
    slot = Slot(12, "A", 2, 3, 3)

    assert (slot.number, slot.direction, slot.row, slot.col, slot.length) == (12, "A", 2, 3, 3)
    # AC-002 literals: name == '12A'; cells() == [(2,3), (2,4), (2,5)]
    assert slot.name == "12A"
    assert slot.cells() == [(2, 3), (2, 4), (2, 5)]


def test_down_slot_retains_fields_name_and_cells() -> None:
    slot = Slot(3, "D", 1, 4, 2)

    assert (slot.number, slot.direction, slot.row, slot.col, slot.length) == (3, "D", 1, 4, 2)
    # AC-002 literals: name == '3D'; cells() == [(1,4), (2,4)]
    assert slot.name == "3D"
    assert slot.cells() == [(1, 4), (2, 4)]


def test_slot_fields_cannot_be_assigned() -> None:
    slot = Slot(12, "A", 2, 3, 3)

    with pytest.raises(dataclasses.FrozenInstanceError):
        slot.number = 13


def _slot_fields(slots: list[Slot]) -> list[tuple[int, str, int, int, int]]:
    return [(slot.number, slot.direction, slot.row, slot.col, slot.length) for slot in slots]


def test_find_slots_orders_shared_starts_across_before_down() -> None:
    assert _slot_fields(find_slots(parse_grid("../.."))) == [
        (1, "A", 0, 0, 2),
        (1, "D", 0, 0, 2),
        (2, "D", 0, 1, 2),
        (3, "A", 1, 0, 2),
    ]


def test_find_slots_finds_split_horizontal_runs_with_maximal_lengths() -> None:
    assert _slot_fields(find_slots(parse_grid("..#..."))) == [
        (1, "A", 0, 0, 2),
        (2, "A", 0, 3, 3),
    ]


def test_find_slots_finds_split_vertical_runs_with_maximal_lengths() -> None:
    assert _slot_fields(find_slots(parse_grid("././#/./."))) == [
        (1, "D", 0, 0, 2),
        (2, "D", 3, 0, 2),
    ]


def test_find_slots_omits_isolated_cell_beside_a_horizontal_slot() -> None:
    assert _slot_fields(find_slots(parse_grid("...#."))) == [(1, "A", 0, 0, 3)]


def test_find_slots_matches_the_prescribed_ten_slot_grid() -> None:
    assert _slot_fields(find_slots(parse_grid("#...#/...../...../...../#...#"))) == [
        (1, "A", 0, 1, 3),
        (1, "D", 0, 1, 5),
        (2, "D", 0, 2, 5),
        (3, "D", 0, 3, 5),
        (4, "A", 1, 0, 5),
        (4, "D", 1, 0, 3),
        (5, "D", 1, 4, 3),
        (6, "A", 2, 0, 5),
        (7, "A", 3, 0, 5),
        (8, "A", 4, 1, 3),
    ]


def test_find_slots_returns_no_slots_for_fully_blocked_grid() -> None:
    assert find_slots(parse_grid("###/###")) == []


def test_find_slots_returns_no_slots_for_two_isolated_cells() -> None:
    assert find_slots(parse_grid(".##/###/##.")) == []


def test_find_slots_returns_no_slots_for_single_open_cell() -> None:
    assert find_slots(parse_grid(".")) == []


def test_slot_pattern_reads_mixed_across_letters_and_empty_cells() -> None:
    assert slot_pattern(parse_grid("A.C/.B./D.E"), Slot(1, "A", 0, 0, 3)) == "A.C"


def test_slot_pattern_reads_mixed_down_letters_and_empty_cells() -> None:
    assert slot_pattern(parse_grid("A.C/.B./D.E"), Slot(1, "D", 0, 0, 3)) == "A.D"


def test_slot_pattern_preserves_a_blank_across_slot() -> None:
    assert slot_pattern(parse_grid("..."), Slot(1, "A", 0, 0, 3)) == "..."


def test_slot_pattern_preserves_letters_in_a_slot() -> None:
    assert slot_pattern(parse_grid("ABC"), Slot(1, "A", 0, 0, 3)) == "ABC"


def test_crossings_returns_all_four_intersections_in_input_index_order() -> None:
    slots = find_slots(parse_grid("../.."))

    assert crossings(slots) == [(0, 0, 1, 0), (0, 1, 2, 0), (3, 0, 1, 1), (3, 1, 2, 1)]


def test_crossings_uses_reordered_slot_indices_and_interior_offsets() -> None:
    slots = [Slot(8, "D", 0, 2, 3), Slot(12, "A", 1, 1, 3)]

    assert crossings(slots) == [(1, 1, 0, 1)]


def test_crossings_returns_empty_for_nonintersecting_slots() -> None:
    slots = [Slot(1, "A", 0, 0, 2), Slot(2, "D", 1, 2, 2)]

    assert crossings(slots) == []


def test_crossings_returns_empty_for_parallel_slots() -> None:
    assert crossings(find_slots(parse_grid("..#.."))) == []


def test_crossings_returns_empty_for_no_slots() -> None:
    assert crossings([]) == []
