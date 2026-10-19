import sys
from dataclasses import FrozenInstanceError
from io import BytesIO

import pytest

from crossmill.base.fail import Fail
from crossmill.base.inputs import StdIO, stdin_words
from crossmill.base.ints import parse_int
from crossmill.base.options import Spec, parse_options
from crossmill.base.text import join, line, show


def test_fail_is_an_exception_with_its_message() -> None:
    error = Fail("bad")

    assert isinstance(error, Exception)
    assert str(error) == "bad"


def test_show_empty_text() -> None:
    assert show("") == '""'


def test_show_sanitizes_each_non_ascii_printable_character() -> None:
    assert show("A B\t\n\ré\x7f") == '"A?B?????"'


def test_show_preserves_printable_boundaries_without_escaping() -> None:
    assert show('!"\\~') == '"!"\\~"'


def test_line_pads_short_keys_and_ends_with_lf() -> None:
    assert line("grid", "5x5") == "grid        5x5\n"


def test_line_does_not_pad_a_ten_character_key() -> None:
    assert line("consistent", "yes") == "consistent  yes\n"


def test_join_formats_positive_zero_and_negative_integers() -> None:
    assert join([3, 0, -2]) == "3 0 -2"


def test_join_empty_list() -> None:
    assert join([]) == ""


def test_parse_int_rejects_minus_sign() -> None:
    with pytest.raises(Fail) as error:
        parse_int("n", "-1", 0, 9)

    assert str(error.value) == 'invalid n "-1" (expected an integer from 0 to 9)'


def test_parse_int_rejects_plus_sign() -> None:
    with pytest.raises(Fail) as error:
        parse_int("n", "+3", 0, 9)

    assert str(error.value) == 'invalid n "+3" (expected an integer from 0 to 9)'


def test_parse_int_rejects_leading_zeroes() -> None:
    with pytest.raises(Fail) as error:
        parse_int("n", "007", 0, 9)

    assert str(error.value) == 'invalid n "007" (expected an integer from 0 to 9)'


def test_parse_int_rejects_decimal_syntax() -> None:
    with pytest.raises(Fail) as error:
        parse_int("n", "1.5", 0, 9)

    assert str(error.value) == 'invalid n "1.5" (expected an integer from 0 to 9)'


def test_parse_int_rejects_empty_text() -> None:
    with pytest.raises(Fail) as error:
        parse_int("n", "", 0, 9)

    assert str(error.value) == 'invalid n "" (expected an integer from 0 to 9)'


def test_parse_int_rejects_non_ascii_digits() -> None:
    with pytest.raises(Fail) as error:
        parse_int("n", "٣", 0, 9)

    assert str(error.value) == 'invalid n "?" (expected an integer from 0 to 9)'


def test_parse_int_rejects_leading_whitespace() -> None:
    with pytest.raises(Fail) as error:
        parse_int("n", " 3", 0, 9)

    assert str(error.value) == 'invalid n "?3" (expected an integer from 0 to 9)'


def test_parse_int_rejects_trailing_newline() -> None:
    with pytest.raises(Fail) as error:
        parse_int("n", "3\n", 0, 9)

    assert str(error.value) == 'invalid n "3?" (expected an integer from 0 to 9)'


def test_parse_int_rejects_more_than_ten_digits() -> None:
    with pytest.raises(Fail) as error:
        parse_int("n", "10000000000", 0, 99999999999)

    assert str(error.value) == (
        'invalid n "10000000000" (expected an integer from 0 to 99999999999)'
    )


def test_parse_int_rejects_value_below_lower_bound() -> None:
    with pytest.raises(Fail) as error:
        parse_int("--min-length", "1", 2, 15)

    assert str(error.value) == 'invalid --min-length "1" (expected an integer from 2 to 15)'


def test_parse_int_rejects_value_above_upper_bound() -> None:
    with pytest.raises(Fail) as error:
        parse_int("n", "16", 2, 15)

    assert str(error.value) == 'invalid n "16" (expected an integer from 2 to 15)'


def test_spec_has_frozen_default_fields() -> None:
    spec = Spec("--x")

    assert spec.name == "--x"
    assert spec.lo == 0
    assert spec.hi == 0
    assert spec.fallback == 0
    assert spec.flag is False
    assert spec == Spec("--x", 0, 0, 0, False)
    with pytest.raises(FrozenInstanceError):
        spec.name = "--changed"


def test_parse_options_uses_numeric_and_flag_fallbacks() -> None:
    specs = [Spec("--limit", 1, 20, 4), Spec("--compact", flag=True)]

    assert parse_options([], specs) == ({"--limit": 4, "--compact": 0}, [])


def test_parse_options_keeps_mixed_ordinary_arguments_in_order() -> None:
    specs = [Spec("--limit", 1, 20, 4), Spec("--compact", flag=True)]

    assert parse_options(["A", "--limit=3", "-", "-x", "--compact", "B"], specs) == (
        {"--limit": 3, "--compact": 1},
        ["A", "-", "-x", "B"],
    )


def test_parse_options_last_repeated_numeric_and_flag_values_win() -> None:
    specs = [Spec("--limit", 1, 20, 4), Spec("--compact", flag=True)]

    assert parse_options(["--limit", "bad", "--limit", "2", "--compact", "--compact"], specs) == (
        {"--limit": 2, "--compact": 1},
        [],
    )


def test_parse_options_preserves_nonzero_flag_fallback() -> None:
    specs = [Spec("--x", fallback=7, flag=True)]

    assert parse_options([], specs) == ({"--x": 7}, [])


def test_parse_options_validates_values_in_spec_order() -> None:
    specs = [Spec("--first", 1, 9), Spec("--second", 1, 9)]

    with pytest.raises(Fail) as error:
        parse_options(["--second=bad", "--first=no"], specs)

    assert str(error.value) == 'invalid --first "no" (expected an integer from 1 to 9)'


def test_parse_options_validates_only_the_final_repeated_value() -> None:
    specs = [Spec("--first", 1, 9), Spec("--second", 1, 9)]

    with pytest.raises(Fail) as error:
        parse_options(["--first=2", "--first=bad"], specs)

    assert str(error.value) == 'invalid --first "bad" (expected an integer from 1 to 9)'


def test_parse_options_rejects_unknown_separator() -> None:
    with pytest.raises(Fail) as error:
        parse_options(["--"], [Spec("--limit", 1, 20, 4), Spec("--compact", flag=True)])

    assert str(error.value) == 'unknown option "--"'


def test_parse_options_rejects_unknown_help_option() -> None:
    with pytest.raises(Fail) as error:
        parse_options(["--help"], [Spec("--limit", 1, 20, 4), Spec("--compact", flag=True)])

    assert str(error.value) == 'unknown option "--help"'


def test_parse_options_sanitizes_the_whole_unknown_token() -> None:
    with pytest.raises(Fail) as error:
        parse_options(["--other=a b"], [Spec("--limit", 1, 20, 4), Spec("--compact", flag=True)])

    assert str(error.value) == 'unknown option "--other=a?b"'


def test_parse_options_rejects_flag_with_nonempty_equals_value() -> None:
    with pytest.raises(Fail) as error:
        parse_options(["--compact=1"], [Spec("--limit", 1, 20, 4), Spec("--compact", flag=True)])

    assert str(error.value) == "option --compact takes no value"


def test_parse_options_rejects_flag_with_empty_equals_value() -> None:
    with pytest.raises(Fail) as error:
        parse_options(["--compact="], [Spec("--limit", 1, 20, 4), Spec("--compact", flag=True)])

    assert str(error.value) == "option --compact takes no value"


def test_parse_options_rejects_missing_numeric_value() -> None:
    with pytest.raises(Fail) as error:
        parse_options(["--limit"], [Spec("--limit", 1, 20, 4), Spec("--compact", flag=True)])

    assert str(error.value) == "--limit needs a value"


def test_parse_options_consumes_option_shaped_numeric_value() -> None:
    with pytest.raises(Fail) as error:
        parse_options(
            ["--limit", "--compact"], [Spec("--limit", 1, 20, 4), Spec("--compact", flag=True)]
        )

    assert str(error.value) == ('invalid --limit "--compact" (expected an integer from 1 to 20)')


def test_parse_options_consumes_signed_numeric_value() -> None:
    with pytest.raises(Fail) as error:
        parse_options(["--limit", "-1"], [Spec("--limit", 1, 20, 4), Spec("--compact", flag=True)])

    assert str(error.value) == 'invalid --limit "-1" (expected an integer from 1 to 20)'


def test_parse_options_rejects_empty_numeric_value() -> None:
    with pytest.raises(Fail) as error:
        parse_options(["--limit="], [Spec("--limit", 1, 20, 4), Spec("--compact", flag=True)])

    assert str(error.value) == 'invalid --limit "" (expected an integer from 1 to 20)'


def test_parse_options_splits_numeric_value_at_first_equals() -> None:
    with pytest.raises(Fail) as error:
        parse_options(["--limit=3=4"], [Spec("--limit", 1, 20, 4), Spec("--compact", flag=True)])

    assert str(error.value) == 'invalid --limit "3=4" (expected an integer from 1 to 20)'


def test_parse_options_reports_later_unknown_option_before_invalid_value() -> None:
    with pytest.raises(Fail) as error:
        parse_options(
            ["--limit=bad", "--help"], [Spec("--limit", 1, 20, 4), Spec("--compact", flag=True)]
        )

    assert str(error.value) == 'unknown option "--help"'


def test_parse_options_reports_later_flag_value_before_invalid_value() -> None:
    with pytest.raises(Fail) as error:
        parse_options(
            ["--limit=bad", "--compact=1"],
            [Spec("--limit", 1, 20, 4), Spec("--compact", flag=True)],
        )

    assert str(error.value) == "option --compact takes no value"


def test_parse_options_reports_later_missing_value_before_invalid_value() -> None:
    with pytest.raises(Fail) as error:
        parse_options(
            ["--limit=bad", "--limit"], [Spec("--limit", 1, 20, 4), Spec("--compact", flag=True)]
        )

    assert str(error.value) == "--limit needs a value"


class FakeIO:
    def __init__(self, data: bytes) -> None:
        self.data = data

    def read_stdin(self) -> bytes:
        return self.data


def test_stdin_words_removes_one_bom_and_splits_permitted_delimiters() -> None:
    assert stdin_words(FakeIO(b"\xef\xbb\xbfCAT\r\nDOG\tEMU  ")) == ["CAT", "DOG", "EMU"]


def test_stdin_words_splits_each_permitted_delimiter() -> None:
    assert stdin_words(FakeIO(b" A\rB\nC\tD ")) == ["A", "B", "C", "D"]


def test_stdin_words_retains_other_whitespace_characters() -> None:
    assert stdin_words(FakeIO(b"A\xc2\xa0B\vC\fD")) == ["A\u00a0B\vC\fD"]


def test_stdin_words_removes_only_one_initial_bom() -> None:
    assert stdin_words(FakeIO(b"\xef\xbb\xbf\xef\xbb\xbfAB")) == ["\ufeffAB"]


def test_stdin_words_retains_embedded_bom() -> None:
    assert stdin_words(FakeIO(b"AB\xef\xbb\xbfCD")) == ["AB\ufeffCD"]


def test_stdin_words_decodes_valid_unicode_utf8() -> None:
    assert stdin_words(FakeIO(b"\xc3\xa9")) == ["é"]


@pytest.mark.parametrize("data", [b"AB\xff\n", b"\xc3"])
def test_stdin_words_rejects_malformed_utf8(data: bytes) -> None:
    with pytest.raises(Fail) as error:
        stdin_words(FakeIO(data))

    assert str(error.value) == "<stdin>: input is not valid UTF-8"


def test_stdin_words_rejects_empty_input() -> None:
    with pytest.raises(Fail) as error:
        stdin_words(FakeIO(b""))

    assert str(error.value) == "<stdin>: no input"


def test_stdin_words_rejects_only_permitted_delimiters() -> None:
    with pytest.raises(Fail) as error:
        stdin_words(FakeIO(b" \t\r\n"))

    assert str(error.value) == "<stdin>: no input"


def test_stdin_words_rejects_a_single_initial_bom_without_words() -> None:
    with pytest.raises(Fail) as error:
        stdin_words(FakeIO(b"\xef\xbb\xbf"))

    assert str(error.value) == "<stdin>: no input"


def test_stdio_and_stdin_words_reject_invalid_bytes_from_binary_buffer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class BinaryStdin:
        def __init__(self) -> None:
            self.buffer = BytesIO(b"AB\xff\n")

    monkeypatch.setattr(sys, "stdin", BinaryStdin())

    with pytest.raises(Fail) as error:
        stdin_words(StdIO())

    assert str(error.value) == "<stdin>: input is not valid UTF-8"


def test_parse_int_accepts_zero() -> None:
    assert parse_int("n", "0", 0, 9) == 0


def test_parse_int_accepts_inclusive_lower_bound() -> None:
    assert parse_int("n", "2", 2, 15) == 2


def test_parse_int_accepts_inclusive_upper_bound() -> None:
    assert parse_int("n", "15", 2, 15) == 15


def test_parse_int_accepts_ten_digit_maximum() -> None:
    assert parse_int("n", "9999999999", 0, 9999999999) == 9999999999


class BinaryStream:
    def __init__(self, data: bytes = b"") -> None:
        self.buffer = BytesIO(data)

    def write(self, text: str) -> None:
        raise AssertionError("StdIO must use the binary buffer")


def test_stdio_reads_raw_stdin_bytes(monkeypatch: pytest.MonkeyPatch) -> None:
    stream = BinaryStream(b"AB\xff\n")
    monkeypatch.setattr(sys, "stdin", stream)

    assert StdIO().read_stdin() == b"AB\xff\n"


def test_stdio_writes_exact_ascii_bytes_to_stdout(monkeypatch: pytest.MonkeyPatch) -> None:
    stream = BinaryStream()
    monkeypatch.setattr(sys, "stdout", stream)

    StdIO().out("grid        5x5\n")

    assert stream.buffer.getvalue() == b"grid        5x5\n"


def test_stdio_writes_exact_ascii_bytes_to_stderr(monkeypatch: pytest.MonkeyPatch) -> None:
    stream = BinaryStream()
    monkeypatch.setattr(sys, "stderr", stream)

    StdIO().err("crossmill: bad\n")

    assert stream.buffer.getvalue() == b"crossmill: bad\n"
