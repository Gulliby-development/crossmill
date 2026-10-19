import pytest

from crossmill.base.fail import Fail
from crossmill.lexicon.index import by_length
from crossmill.lexicon.pattern import match_all, matches, parse_pattern
from crossmill.lexicon.stats import lexicon_stats
from crossmill.lexicon.words import build_lexicon, parse_word, read_lexicon


def test_parse_word_accepts_minimum_length_and_uppercases() -> None:
    assert parse_word("aB") == "AB"


def test_parse_word_accepts_maximum_length_and_uppercases() -> None:
    assert parse_word("abcdefghijklmno") == "ABCDEFGHIJKLMNO"


def test_parse_word_rejects_empty_text() -> None:
    with pytest.raises(Fail) as error:
        parse_word("")

    assert str(error.value) == 'invalid word "" (expected 2 to 15 letters)'


def test_parse_word_rejects_one_letter() -> None:
    with pytest.raises(Fail) as error:
        parse_word("A")

    assert str(error.value) == 'invalid word "A" (expected 2 to 15 letters)'


def test_parse_word_rejects_sixteen_letters() -> None:
    with pytest.raises(Fail) as error:
        parse_word("ABCDEFGHIJKLMNOP")

    assert str(error.value) == 'invalid word "ABCDEFGHIJKLMNOP" (expected 2 to 15 letters)'


def test_parse_word_rejects_a_digit() -> None:
    with pytest.raises(Fail) as error:
        parse_word("D0G")

    assert str(error.value) == 'invalid word "D0G" (expected 2 to 15 letters)'


def test_parse_word_rejects_a_hyphen() -> None:
    with pytest.raises(Fail) as error:
        parse_word("A-B")

    assert str(error.value) == 'invalid word "A-B" (expected 2 to 15 letters)'


def test_parse_word_rejects_a_period() -> None:
    with pytest.raises(Fail) as error:
        parse_word("A.B")

    assert str(error.value) == 'invalid word "A.B" (expected 2 to 15 letters)'


def test_parse_word_rejects_accented_letters() -> None:
    with pytest.raises(Fail) as error:
        parse_word("éA")

    assert str(error.value) == 'invalid word "?A" (expected 2 to 15 letters)'


def test_parse_word_rejects_sharp_s_before_case_expansion() -> None:
    with pytest.raises(Fail) as error:
        parse_word("ßA")

    assert str(error.value) == 'invalid word "?A" (expected 2 to 15 letters)'


def test_parse_word_rejects_full_width_letters() -> None:
    with pytest.raises(Fail) as error:
        parse_word("ＡB")

    assert str(error.value) == 'invalid word "?B" (expected 2 to 15 letters)'


def test_parse_word_sanitizes_newline_in_error() -> None:
    with pytest.raises(Fail) as error:
        parse_word("A\n")

    assert str(error.value) == 'invalid word "A?" (expected 2 to 15 letters)'


def test_build_lexicon_uppercases_deduplicates_and_sorts() -> None:
    assert build_lexicon(["CAT", "dog", "Emu", "cat"]) == ["CAT", "DOG", "EMU"]


def test_build_lexicon_reports_the_first_invalid_word() -> None:
    with pytest.raises(Fail) as error:
        build_lexicon(["cat", "D0G", "A"])

    assert str(error.value) == 'invalid word "D0G" (expected 2 to 15 letters)'


def test_build_lexicon_accepts_an_empty_list() -> None:
    assert build_lexicon([]) == []


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


def test_read_lexicon_parses_comma_list_without_reading_stdin() -> None:
    io = FakeIO(b"unused")

    assert read_lexicon(io, "CAT,dog,Emu,CAT") == ["CAT", "DOG", "EMU"]
    assert io.read_count == 0
    assert io.stdout == []
    assert io.stderr == []


def test_read_lexicon_rejects_empty_text_without_reading_stdin() -> None:
    io = FakeIO(b"unused")

    with pytest.raises(Fail) as error:
        read_lexicon(io, "")

    assert str(error.value) == 'invalid word "" (expected 2 to 15 letters)'
    assert io.read_count == 0
    assert io.stdout == []
    assert io.stderr == []


def test_read_lexicon_rejects_leading_empty_field_without_reading_stdin() -> None:
    io = FakeIO(b"unused")

    with pytest.raises(Fail) as error:
        read_lexicon(io, ",CAT")

    assert str(error.value) == 'invalid word "" (expected 2 to 15 letters)'
    assert io.read_count == 0
    assert io.stdout == []
    assert io.stderr == []


def test_read_lexicon_rejects_trailing_empty_field_without_reading_stdin() -> None:
    io = FakeIO(b"unused")

    with pytest.raises(Fail) as error:
        read_lexicon(io, "CAT,")

    assert str(error.value) == 'invalid word "" (expected 2 to 15 letters)'
    assert io.read_count == 0
    assert io.stdout == []
    assert io.stderr == []


def test_read_lexicon_rejects_inner_empty_field_without_reading_stdin() -> None:
    io = FakeIO(b"unused")

    with pytest.raises(Fail) as error:
        read_lexicon(io, "CAT,,DOG")

    assert str(error.value) == 'invalid word "" (expected 2 to 15 letters)'
    assert io.read_count == 0
    assert io.stdout == []
    assert io.stderr == []


def test_read_lexicon_rejects_embedded_dash_without_reading_stdin() -> None:
    io = FakeIO(b"unused")

    with pytest.raises(Fail) as error:
        read_lexicon(io, "CAT,-")

    assert str(error.value) == 'invalid word "-" (expected 2 to 15 letters)'
    assert io.read_count == 0
    assert io.stdout == []
    assert io.stderr == []


def test_read_lexicon_does_not_trim_comma_fields() -> None:
    io = FakeIO(b"unused")

    with pytest.raises(Fail) as error:
        read_lexicon(io, " CAT,DOG")

    assert str(error.value) == 'invalid word "?CAT" (expected 2 to 15 letters)'
    assert io.read_count == 0
    assert io.stdout == []
    assert io.stderr == []


def test_read_lexicon_uses_stdin_once_for_lone_dash_with_bom_and_separators() -> None:
    io = FakeIO(b"\xef\xbb\xbfcat\tDOG\r\ncat emu\n")

    assert read_lexicon(io, "-") == ["CAT", "DOG", "EMU"]
    assert io.read_count == 1
    assert io.stdout == []
    assert io.stderr == []


def test_read_lexicon_rejects_empty_stdin_once() -> None:
    io = FakeIO(b" \t\r\n")

    with pytest.raises(Fail) as error:
        read_lexicon(io, "-")

    assert str(error.value) == "<stdin>: no input"
    assert io.read_count == 1
    assert io.stdout == []
    assert io.stderr == []


def test_read_lexicon_rejects_malformed_stdin_utf8_once() -> None:
    io = FakeIO(b"AB\xff\n")

    with pytest.raises(Fail) as error:
        read_lexicon(io, "-")

    assert str(error.value) == "<stdin>: input is not valid UTF-8"
    assert io.read_count == 1
    assert io.stdout == []
    assert io.stderr == []


def test_read_lexicon_reports_first_invalid_stdin_word_once() -> None:
    io = FakeIO(b"CAT D0G A")

    with pytest.raises(Fail) as error:
        read_lexicon(io, "-")

    assert str(error.value) == 'invalid word "D0G" (expected 2 to 15 letters)'
    assert io.read_count == 1
    assert io.stdout == []
    assert io.stderr == []


def test_read_lexicon_does_not_split_vertical_tab_from_stdin() -> None:
    io = FakeIO(b"AB\vCD")

    with pytest.raises(Fail) as error:
        read_lexicon(io, "-")

    assert str(error.value) == 'invalid word "AB?CD" (expected 2 to 15 letters)'
    assert io.read_count == 1
    assert io.stdout == []
    assert io.stderr == []


def test_parse_pattern_accepts_minimum_length_and_uppercases() -> None:
    assert parse_pattern("a.") == "A."


def test_parse_pattern_accepts_maximum_length_and_uppercases() -> None:
    assert parse_pattern("abcdefghijklmno") == "ABCDEFGHIJKLMNO"


def test_parse_pattern_accepts_letters_and_wildcards() -> None:
    assert parse_pattern("b.n.") == "B.N."
    assert parse_pattern("..") == ".."


@pytest.mark.parametrize(
    ("text", "shown"),
    [
        ("", '""'),
        ("A", '"A"'),
        ("................", '"................"'),
        ("A*", '"A*"'),
        ("A1", '"A1"'),
        ("A-", '"A-"'),
        ("é.", '"?."'),
        ("ß.", '"?."'),
        ("Ａ.", '"?."'),
    ],
)
def test_parse_pattern_rejects_invalid_forms(text: str, shown: str) -> None:
    with pytest.raises(Fail) as error:
        parse_pattern(text)

    assert str(error.value) == (
        f"invalid pattern {shown} (expected 2 to 15 characters, letters or .)"
    )


def test_parse_pattern_sanitizes_newline_in_error() -> None:
    with pytest.raises(Fail) as error:
        parse_pattern("A\n")

    assert str(error.value) == 'invalid pattern "A?" (expected 2 to 15 characters, letters or .)'


@pytest.mark.parametrize(
    ("pattern", "word"),
    [("B.N.", "BAND"), ("CAT", "CAT"), ("...", "DOG")],
)
def test_matches_exact_and_wildcard_patterns(pattern: str, word: str) -> None:
    assert matches(pattern, word) is True


@pytest.mark.parametrize(
    ("pattern", "word"),
    [("B.N.", "BEAN"), ("B.N.", "BIN"), ("..", "CAT")],
)
def test_matches_rejects_letter_and_length_mismatches(pattern: str, word: str) -> None:
    assert matches(pattern, word) is False


def test_match_all_sorts_matching_words_from_unsorted_lexicon() -> None:
    assert match_all(["TANK", "BONE", "BIND", "BIN", "BEAN", "BANK", "BAND"], "B.N.") == [
        "BAND",
        "BANK",
        "BIND",
        "BONE",
    ]


def test_match_all_returns_empty_for_no_matches() -> None:
    assert match_all(["CAT", "DOG"], "Z..") == []


def test_match_all_returns_empty_for_empty_lexicon() -> None:
    assert match_all([], "..") == []


def test_parse_pattern_rejects_empty_text() -> None:
    with pytest.raises(Fail) as error:
        parse_pattern("")

    assert str(error.value) == 'invalid pattern "" (expected 2 to 15 characters, letters or .)'


def test_parse_pattern_rejects_one_character() -> None:
    with pytest.raises(Fail) as error:
        parse_pattern("A")

    assert str(error.value) == 'invalid pattern "A" (expected 2 to 15 characters, letters or .)'


def test_parse_pattern_rejects_sixteen_characters() -> None:
    with pytest.raises(Fail) as error:
        parse_pattern("................")

    assert str(error.value) == (
        'invalid pattern "................" (expected 2 to 15 characters, letters or .)'
    )


def test_parse_pattern_rejects_an_asterisk() -> None:
    with pytest.raises(Fail) as error:
        parse_pattern("A*")

    assert str(error.value) == 'invalid pattern "A*" (expected 2 to 15 characters, letters or .)'


def test_parse_pattern_rejects_a_digit() -> None:
    with pytest.raises(Fail) as error:
        parse_pattern("A1")

    assert str(error.value) == 'invalid pattern "A1" (expected 2 to 15 characters, letters or .)'


def test_parse_pattern_rejects_a_hyphen() -> None:
    with pytest.raises(Fail) as error:
        parse_pattern("A-")

    assert str(error.value) == 'invalid pattern "A-" (expected 2 to 15 characters, letters or .)'


def test_parse_pattern_rejects_accented_letter() -> None:
    with pytest.raises(Fail) as error:
        parse_pattern("é.")

    assert str(error.value) == 'invalid pattern "?." (expected 2 to 15 characters, letters or .)'


def test_parse_pattern_rejects_sharp_s_before_case_expansion() -> None:
    with pytest.raises(Fail) as error:
        parse_pattern("ß.")

    assert str(error.value) == 'invalid pattern "?." (expected 2 to 15 characters, letters or .)'


def test_parse_pattern_rejects_full_width_letter() -> None:
    with pytest.raises(Fail) as error:
        parse_pattern("Ａ.")

    assert str(error.value) == 'invalid pattern "?." (expected 2 to 15 characters, letters or .)'


def test_match_all_returns_empty_when_words_do_not_match() -> None:
    assert match_all(["CAT", "DOG"], "Z..") == []


def test_match_all_returns_empty_for_an_empty_lexicon() -> None:
    assert match_all([], "..") == []


def test_by_length_groups_unsorted_words_with_ascending_keys_and_buckets() -> None:
    grouped = by_length(["DOG", "BANK", "AN", "CAT", "BAKE"])

    assert list(grouped) == [2, 3, 4]
    assert grouped == {2: ["AN"], 3: ["CAT", "DOG"], 4: ["BAKE", "BANK"]}


def test_by_length_returns_an_empty_mapping_for_an_empty_lexicon() -> None:
    assert by_length([]) == {}


def test_lexicon_stats_deduplicated_words_rank_letters_by_frequency() -> None:
    lexicon = build_lexicon(["bank", "BANK", "bake", "cat", "dog", "tide", "xyz", "bat"])

    assert lexicon_stats(lexicon) == (
        {3: 4, 4: 3},
        [("A", 4), ("B", 3), ("T", 3), ("D", 2), ("E", 2)],
    )


def test_lexicon_stats_counts_repeated_letters_and_returns_fewer_than_five() -> None:
    assert lexicon_stats(["AAA", "AB"]) == ({2: 1, 3: 1}, [("A", 4), ("B", 1)])


def test_lexicon_stats_breaks_a_tie_at_fifth_place_alphabetically() -> None:
    assert lexicon_stats(["AB", "CD", "EF"]) == (
        {2: 3},
        [("A", 1), ("B", 1), ("C", 1), ("D", 1), ("E", 1)],
    )


def test_lexicon_stats_returns_empty_results_for_an_empty_lexicon() -> None:
    assert lexicon_stats([]) == ({}, [])
