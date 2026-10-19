from dataclasses import FrozenInstanceError

import pytest

from crossmill.base.fail import Fail
from crossmill.grid.model import Grid, cell_name, parse_grid


def test_parse_grid_populates_model_properties_and_accessors() -> None:
    # Required literal cases: rows == ('A.#','...'), height == 2, width == 3
    # at(0,0) == 'A', at(0,2) == '#', text() == 'A.#/...', dims() == '2x3'
    grid = parse_grid("A.#/...")

    assert grid.rows == ("A.#", "...")
    assert grid.height == 2
    assert grid.width == 3
    assert grid.at(0, 0) == "A"
    assert grid.at(0, 2) == "#"
    assert grid.text() == "A.#/..."
    assert grid.dims() == "2x3"


def test_parse_grid_accepts_single_block_cell() -> None:
    # Single-cell expectation: dims() == '1x1'
    grid = parse_grid("#")

    assert grid.rows == ("#",)
    assert grid.text() == "#"
    assert grid.dims() == "1x1"


def test_parse_grid_accepts_single_empty_cell() -> None:
    grid = parse_grid(".")

    assert grid.rows == (".",)
    assert grid.text() == "."
    assert grid.dims() == "1x1"


def test_parse_grid_accepts_single_letter_cell() -> None:
    grid = parse_grid("Z")

    assert grid.rows == ("Z",)
    assert grid.text() == "Z"
    assert grid.dims() == "1x1"


def test_parse_grid_accepts_maximum_width() -> None:
    # Boundary expectation: width == 15
    grid = parse_grid("...............")

    assert grid.width == 15


def test_parse_grid_accepts_maximum_height() -> None:
    # Boundary expectation: height == 15
    grid = parse_grid("././././././././././././././.")

    assert grid.height == 15


def test_cell_name_uses_one_based_row_and_column_coordinates() -> None:
    assert cell_name(0, 0) == "r1c1"
    assert cell_name(1, 3) == "r2c4"


def test_grid_rows_cannot_be_reassigned() -> None:
    grid = Grid(("A",))

    with pytest.raises(FrozenInstanceError):
        grid.rows = ("B",)


def test_grid_limit_accepts_dimensions_equal_to_side() -> None:
    # Required literal call: parse_grid('.....').limit(5,'fill')
    assert parse_grid(".....").limit(5, "fill") is None
    assert parse_grid("...../...../...../...../.....").limit(5, "fill") is None


def test_grid_limit_rejects_width_above_side() -> None:
    # Required literal call: parse_grid('......').limit(5,'fill')
    with pytest.raises(Fail) as error:
        parse_grid("......").limit(5, "fill")

    assert str(error.value) == "grid is 1x6 (above 5x5, too large for fill)"


def test_grid_limit_rejects_height_above_side() -> None:
    # Required literal call: parse_grid('./././././.').limit(5,'domains')
    with pytest.raises(Fail) as error:
        parse_grid("./././././.").limit(5, "domains")

    assert str(error.value) == "grid is 6x1 (above 5x5, too large for domains)"


def test_parse_grid_rejects_empty_text() -> None:
    with pytest.raises(Fail) as error:
        parse_grid("")

    assert str(error.value) == (
        'invalid grid "" (expected rows of # . and letters A to Z separated by /, '
        "such as ..#../.....)"
    )


def test_parse_grid_rejects_a_slash_as_an_empty_row() -> None:
    with pytest.raises(Fail) as error:
        parse_grid("/")

    assert str(error.value) == (
        'invalid grid "/" (expected rows of # . and letters A to Z separated by /, '
        "such as ..#../.....)"
    )


def test_parse_grid_rejects_an_empty_first_row() -> None:
    with pytest.raises(Fail) as error:
        parse_grid("/.")

    assert str(error.value) == (
        'invalid grid "/." (expected rows of # . and letters A to Z separated by /, '
        "such as ..#../.....)"
    )


def test_parse_grid_rejects_an_empty_last_row() -> None:
    with pytest.raises(Fail) as error:
        parse_grid("./")

    assert str(error.value) == (
        'invalid grid "./" (expected rows of # . and letters A to Z separated by /, '
        "such as ..#../.....)"
    )


def test_parse_grid_rejects_an_empty_middle_row() -> None:
    with pytest.raises(Fail) as error:
        parse_grid(".//.")

    assert str(error.value) == (
        'invalid grid ".//." (expected rows of # . and letters A to Z separated by /, '
        "such as ..#../.....)"
    )


def test_parse_grid_rejects_lowercase_letters() -> None:
    with pytest.raises(Fail) as error:
        parse_grid("a../...")

    assert str(error.value) == (
        'invalid grid "a../..." (expected rows of # . and letters A to Z separated by /, '
        "such as ..#../.....)"
    )


def test_parse_grid_sanitizes_space() -> None:
    with pytest.raises(Fail) as error:
        parse_grid("A B")

    assert str(error.value) == (
        'invalid grid "A?B" (expected rows of # . and letters A to Z separated by /, '
        "such as ..#../.....)"
    )


def test_parse_grid_sanitizes_tab() -> None:
    with pytest.raises(Fail) as error:
        parse_grid("A\tB")

    assert str(error.value) == (
        'invalid grid "A?B" (expected rows of # . and letters A to Z separated by /, '
        "such as ..#../.....)"
    )


def test_parse_grid_sanitizes_newline() -> None:
    with pytest.raises(Fail) as error:
        parse_grid("A\nB")

    assert str(error.value) == (
        'invalid grid "A?B" (expected rows of # . and letters A to Z separated by /, '
        "such as ..#../.....)"
    )


def test_parse_grid_sanitizes_non_ascii_character() -> None:
    with pytest.raises(Fail) as error:
        parse_grid("é")

    assert str(error.value) == (
        'invalid grid "?" (expected rows of # . and letters A to Z separated by /, '
        "such as ..#../.....)"
    )


def test_parse_grid_rejects_digit() -> None:
    with pytest.raises(Fail) as error:
        parse_grid("0")

    assert str(error.value) == (
        'invalid grid "0" (expected rows of # . and letters A to Z separated by /, '
        "such as ..#../.....)"
    )


def test_parse_grid_reports_unequal_second_row_width() -> None:
    with pytest.raises(Fail) as error:
        parse_grid("..#/..")

    assert str(error.value) == "row 2 has 2 cells but row 1 has 3"


def test_parse_grid_reports_first_unequal_row() -> None:
    with pytest.raises(Fail) as error:
        parse_grid(".././...")

    assert str(error.value) == "row 2 has 1 cells but row 1 has 2"


def test_parse_grid_checks_grammar_before_rectangularity() -> None:
    with pytest.raises(Fail) as error:
        parse_grid(".././a")

    assert str(error.value) == (
        'invalid grid ".././a" (expected rows of # . and letters A to Z separated by /, '
        "such as ..#../.....)"
    )


def test_parse_grid_checks_rectangularity_before_height() -> None:
    with pytest.raises(Fail) as error:
        parse_grid("./././././././././././././././..")

    assert str(error.value) == "row 16 has 2 cells but row 1 has 1"


def test_parse_grid_rejects_excessive_height() -> None:
    with pytest.raises(Fail) as error:
        parse_grid("./././././././././././././././.")

    assert str(error.value) == "grid has 16 rows (above 15)"


def test_parse_grid_rejects_excessive_width() -> None:
    with pytest.raises(Fail) as error:
        parse_grid("................")

    assert str(error.value) == "grid has 16 columns (above 15)"


def test_parse_grid_checks_height_before_width() -> None:
    with pytest.raises(Fail) as error:
        parse_grid(
            "................"
            "/................"
            "/................"
            "/................"
            "/................"
            "/................"
            "/................"
            "/................"
            "/................"
            "/................"
            "/................"
            "/................"
            "/................"
            "/................"
            "/................"
            "/................"
        )

    assert str(error.value) == "grid has 16 rows (above 15)"


def test_symmetry_problem_accepts_letters_without_blocks() -> None:
    from crossmill.grid.rules import symmetry_problem

    assert symmetry_problem(parse_grid("AB/CD")) is None


def test_symmetry_problem_accepts_single_block_and_open_cell() -> None:
    from crossmill.grid.rules import symmetry_problem

    assert symmetry_problem(parse_grid("#")) is None
    assert symmetry_problem(parse_grid(".")) is None


def test_symmetry_problem_accepts_half_turn_symmetric_blocks() -> None:
    from crossmill.grid.rules import symmetry_problem

    assert symmetry_problem(parse_grid("#./.#")) is None


def test_symmetry_problem_reports_first_block_in_reading_order() -> None:
    from crossmill.grid.rules import symmetry_problem

    assert symmetry_problem(parse_grid("..#/#../...")) == (
        "not symmetric: r1c3 is a block but r3c1 is not"
    )


def test_symmetry_problem_ignores_letter_differences() -> None:
    from crossmill.grid.rules import symmetry_problem

    assert symmetry_problem(parse_grid("#A/B#")) is None


def test_symmetry_problem_ignores_earlier_open_partner() -> None:
    from crossmill.grid.rules import symmetry_problem

    assert symmetry_problem(parse_grid("../.#")) == (
        "not symmetric: r2c2 is a block but r1c1 is not"
    )


def test_regions_returns_empty_for_a_grid_without_open_cells() -> None:
    from crossmill.grid.rules import regions

    assert regions(parse_grid("##/##")) == []


def test_regions_separates_diagonally_touching_open_cells() -> None:
    from crossmill.grid.rules import regions

    assert regions(parse_grid(".#/#A")) == [[(0, 0)], [(1, 1)]]


def test_regions_connects_open_cells_through_edges() -> None:
    from crossmill.grid.rules import regions

    assert regions(parse_grid("A./#.")) == [[(0, 0), (0, 1), (1, 1)]]


def test_regions_orders_components_and_members_by_reading_order() -> None:
    from crossmill.grid.rules import regions

    assert regions(parse_grid(".#./.#.")) == [[(0, 0), (1, 0)], [(0, 2), (1, 2)]]


def test_regions_returns_identical_order_on_repeated_calls() -> None:
    from crossmill.grid.rules import regions

    grid = parse_grid(".#./.#.")

    assert regions(grid) == [[(0, 0), (1, 0)], [(0, 2), (1, 2)]]
    assert regions(grid) == [[(0, 0), (1, 0)], [(0, 2), (1, 2)]]


def test_render_box_draws_exact_normal_ascii_lines_without_terminators() -> None:
    from crossmill.grid.render import render_box

    grid = parse_grid("A.#/.../#..")
    numbers = {(0, 0): 1, (0, 1): 2, (1, 0): 3, (1, 2): 4, (2, 1): 5}

    drawing = render_box(grid, numbers, False)

    assert drawing == [
        "+----+----+----+",
        "|1   |2   |####|",
        "| A  |    |####|",
        "+----+----+----+",
        "|3   |    |4   |",
        "|    |    |    |",
        "+----+----+----+",
        "|####|5   |    |",
        "|####|    |    |",
        "+----+----+----+",
    ]
    assert all(line.isascii() and "\r" not in line and "\n" not in line for line in drawing)


def test_render_box_draws_exact_compact_ascii_lines_without_terminators() -> None:
    from crossmill.grid.render import render_box

    grid = parse_grid("A.#/.../#..")
    numbers = {(0, 0): 1, (0, 1): 2, (1, 0): 3, (1, 2): 4, (2, 1): 5}

    drawing = render_box(grid, numbers, True)

    assert drawing == [
        "+---+---+---+",
        "| A |   |###|",
        "+---+---+---+",
        "|   |   |   |",
        "+---+---+---+",
        "|###|   |   |",
        "+---+---+---+",
    ]
    assert all(line.isascii() and "\r" not in line and "\n" not in line for line in drawing)


def test_render_box_pads_supplied_numbers_to_cell_width() -> None:
    from crossmill.grid.render import render_box

    assert render_box(parse_grid(".."), {(0, 0): 12, (0, 1): 100}, False) == [
        "+----+----+",
        "|12  |100 |",
        "|    |    |",
        "+----+----+",
    ]


def test_render_box_handles_blank_numbers_and_ignores_numbers_in_compact_mode() -> None:
    from crossmill.grid.render import render_box

    assert render_box(parse_grid("."), {}, False) == [
        "+----+",
        "|    |",
        "|    |",
        "+----+",
    ]
    assert render_box(parse_grid("."), {(0, 0): 12}, True) == [
        "+---+",
        "|   |",
        "+---+",
    ]


def test_symmetrize_adds_one_block_and_preserves_the_original_grid() -> None:
    from crossmill.grid.mirror import symmetrize

    grid = parse_grid("..#../...../...../...../.....")

    mirrored, added = symmetrize(grid)

    assert (mirrored.text(), added) == ("..#../...../...../...../..#..", 1)
    assert grid.text() == "..#../...../...../...../....."
    mirrored_again, added_again = symmetrize(mirrored)
    assert (mirrored_again.text(), added_again) == ("..#../...../...../...../..#..", 0)


def test_symmetrize_adds_each_missing_partner_block() -> None:
    from crossmill.grid.mirror import symmetrize

    grid = parse_grid("##./.../...")

    mirrored, added = symmetrize(grid)

    assert (mirrored.text(), added) == ("##./.../.##", 2)
    assert grid.text() == "##./.../..."
    mirrored_again, added_again = symmetrize(mirrored)
    assert (mirrored_again.text(), added_again) == ("##./.../.##", 0)


def test_symmetrize_leaves_already_symmetric_and_unblocked_grids_unchanged() -> None:
    from crossmill.grid.mirror import symmetrize

    paired_grid = parse_grid("#./.#")
    center_grid = parse_grid(".../.#./...")
    letters_grid = parse_grid("AB/CD")
    all_blocks_grid = parse_grid("#")
    paired, paired_added = symmetrize(paired_grid)
    center, center_added = symmetrize(center_grid)
    letters, letters_added = symmetrize(letters_grid)
    all_blocks, all_blocks_added = symmetrize(all_blocks_grid)

    assert (paired.text(), paired_added) == ("#./.#", 0)
    assert (center.text(), center_added) == (".../.#./...", 0)
    assert (letters.text(), letters_added) == ("AB/CD", 0)
    assert (all_blocks.text(), all_blocks_added) == ("#", 0)
    assert paired_grid.text() == "#./.#"
    assert center_grid.text() == ".../.#./..."
    assert letters_grid.text() == "AB/CD"
    assert all_blocks_grid.text() == "#"
    paired_again, paired_again_added = symmetrize(paired)
    center_again, center_again_added = symmetrize(center)
    letters_again, letters_again_added = symmetrize(letters)
    all_blocks_again, all_blocks_again_added = symmetrize(all_blocks)
    assert (paired_again.text(), paired_again_added) == ("#./.#", 0)
    assert (center_again.text(), center_again_added) == (".../.#./...", 0)
    assert (letters_again.text(), letters_again_added) == ("AB/CD", 0)
    assert (all_blocks_again.text(), all_blocks_again_added) == ("#", 0)


def test_symmetrize_reports_the_first_letter_conflict_without_mutating_input() -> None:
    from crossmill.grid.mirror import symmetrize

    grid = parse_grid("..#/.../A..")

    with pytest.raises(Fail) as error:
        symmetrize(grid)

    assert str(error.value) == "cell r3c1 holds a letter but its partner r1c3 is a block"
    assert grid.text() == "..#/.../A.."


def test_symmetrize_reports_the_first_conflict_among_multiple_blocks() -> None:
    from crossmill.grid.mirror import symmetrize

    grid = parse_grid("##./.../.AB")

    with pytest.raises(Fail) as error:
        symmetrize(grid)

    assert str(error.value) == "cell r3c3 holds a letter but its partner r1c1 is a block"
    assert grid.text() == "##./.../.AB"


def test_symmetrize_reports_a_letter_after_a_tentative_addition() -> None:
    from crossmill.grid.mirror import symmetrize

    grid = parse_grid("##./.../.A.")

    with pytest.raises(Fail) as error:
        symmetrize(grid)

    assert str(error.value) == "cell r3c2 holds a letter but its partner r1c2 is a block"
    assert grid.text() == "##./.../.A."
