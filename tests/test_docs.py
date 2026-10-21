import re
from pathlib import Path

import pytest

from crossmill.cli.cli import run


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


def _repository_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _readme_text() -> str:
    return (
        (_repository_root() / "README.md")
        .read_bytes()
        .decode("ascii")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )


def _readme_section(readme: str, heading: str, level: int = 2) -> str:
    marker = "#" * level
    next_heading = r"^## " if level == 2 else r"^(?:##|###) "
    match = re.search(
        rf"(?ms)^{marker} {re.escape(heading)}\s*\n(.*?)(?={next_heading}|\Z)",
        readme,
    )
    assert match is not None
    return match.group(1)


def _output_blocks(readme: str) -> list[str]:
    return re.findall(r"```text\n(.*?)```", readme, flags=re.DOTALL)


@pytest.mark.parametrize(
    ("args", "usage"),
    [
        (["check"], "crossmill check GRID [--min-length N] [--checked]"),
        (["number"], "crossmill number GRID"),
        (["render"], "crossmill render GRID [--compact]"),
        (["symmetrize"], "crossmill symmetrize GRID"),
        (["pattern"], "crossmill pattern PATTERN WORDS [--limit L]"),
        (["stats"], "crossmill stats WORDS [--letters N]"),
        (["domains"], "crossmill domains GRID WORDS"),
        (["forced"], "crossmill forced GRID WORDS"),
        (["fill"], "crossmill fill GRID WORDS [--limit L]"),
        (["count"], "crossmill count GRID WORDS [--max M]"),
    ],
)
def test_documented_usage_matches_cli_usage_error(args: list[str], usage: str) -> None:
    readme = _readme_text()
    io = FakeIO()

    assert usage in readme
    assert run(args, io) == 2
    assert io.out_calls == []
    assert io.err_calls == [f"crossmill: usage: {usage}\n"]


def test_readme_contains_exactly_three_example_output_blocks() -> None:
    assert len(_output_blocks(_readme_text())) == 3


@pytest.mark.parametrize(
    ("args", "command", "output_index", "expected_output"),
    [
        (
            ["render", "A.#/.../#.."],
            'crossmill render "A.#/.../#.."',
            0,
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
        ),
        (
            [
                "forced",
                "..../.##./.##./....",
                "BAND,BEAD,BEAR,DARE,DATE,DOOR,LAKE,TEAM",
            ],
            'crossmill forced "..../.##./.##./...." "BAND,BEAD,BEAR,DARE,DATE,DOOR,LAKE,TEAM"',
            1,
            (
                "grid        4x4\n"
                "consistent  yes\n"
                "forced      3\n"
                "row         B..D\n"
                "row         .##.\n"
                "row         .##.\n"
                "row         D...\n"
            ),
        ),
        (
            [
                "fill",
                "..../.##./.##./....",
                "BAND,BEAD,BEAR,DARE,DATE,DOOR,LAKE,TEAM",
                "--limit",
                "3",
            ],
            (
                'crossmill fill "..../.##./.##./...." '
                '"BAND,BEAD,BEAR,DARE,DATE,DOOR,LAKE,TEAM" --limit 3'
            ),
            2,
            (
                "grid        4x4\n"
                "slots       4\n"
                "words       8\n"
                "found       3\n"
                "fill        1 BAND/E##A/A##R/DATE\n"
                "fill        2 BAND/E##A/A##T/DARE\n"
                "fill        3 BEAD/A##A/N##R/DATE\n"
            ),
        ),
    ],
)
def test_documented_examples_match_cli_output(
    args: list[str],
    command: str,
    output_index: int,
    expected_output: str,
) -> None:
    readme = _readme_text()
    outputs = _output_blocks(readme)
    io = FakeIO()

    assert command in readme
    assert outputs[output_index] == expected_output
    assert run(args, io) == 0
    assert io.out_calls == [outputs[output_index]]
    assert io.err_calls == []


def test_readme_has_required_sections_and_product_guidance() -> None:
    readme = _readme_text()

    assert "## Install" in readme
    assert "## Usage" in readme
    assert "## Grids and words" in readme
    assert "## Commands" in readme
    assert "## Exit codes" in readme
    assert "## Layout" in readme
    assert "## Development" in readme

    assert "offline command-line toolkit" in readme
    assert "people who build small crossword grids by hand" in readme
    assert "Python 3.11 or newer" in readme
    assert "No installation step is needed" in readme
    assert "`python -m crossmill`" in readme

    grid_words = _readme_section(readme, "Grids and words")
    assert "rows separated by `/`" in grid_words
    assert "`#` for a block, `.` for an empty cell" in grid_words
    assert "uppercase letter from A to Z" in grid_words
    assert "equal widths" in grid_words
    assert "at most 15 rows by 15 columns" in grid_words
    assert "Lowercase grid letters, empty rows" in grid_words
    assert "comma-separated list such as `CAT,dog,Emu`" in grid_words
    assert "a single `-` argument to read words from strict UTF-8 standard input" in grid_words
    assert "2 to 15 ASCII letters" in grid_words
    assert "normalized to uppercase and duplicates are removed" in grid_words
    assert "Empty list entries" in grid_words
    assert "Patterns contain 2 to 15 ASCII letters or dots, such as `b.n.`" in grid_words
    assert "Other pattern characters are rejected" in grid_words
    assert "5 by 5" in grid_words
    assert "at most 40 unique words" in grid_words

    assert "construction rules" in _readme_section(readme, "check", level=3)
    assert "across and down slot" in _readme_section(readme, "number", level=3)
    assert "bordered grid" in _readme_section(readme, "render", level=3)
    assert "half turn" in _readme_section(readme, "symmetrize", level=3)
    assert "matching" in _readme_section(readme, "pattern", level=3)
    assert "five most frequent letters" in _readme_section(readme, "stats", level=3)
    domains = _readme_section(readme, "domains", level=3)
    assert "arc-consistent" in domains
    assert "distinct-word rule required for a fill" in domains
    assert "forced in otherwise empty cells" in _readme_section(readme, "forced", level=3)
    assert "use each word at most once" in _readme_section(readme, "fill", level=3)
    assert "whether more fills exist" in _readme_section(readme, "count", level=3)

    exit_codes = _readme_section(readme, "Exit codes")
    assert "code 0 when it succeeds" in exit_codes
    assert "Code 1 means it completed a report that found a problem" in exit_codes
    assert "check found construction problems" in exit_codes
    assert "domains or forced found inconsistent domains" in exit_codes
    assert "fill found no fill" in exit_codes
    assert "Code 2 means" in exit_codes
    assert "usage, argument, or input error" in exit_codes


def test_readme_documents_required_development_commands() -> None:
    development = _readme_section(_readme_text(), "Development")

    assert "`python -m ruff check .`" in development
    assert "`python -m ruff format --check .`" in development
    assert "`python -m pytest -q`" in development


def test_readme_layout_lists_exact_paths_and_all_layer_folders() -> None:
    readme = _readme_text()
    layout = _readme_section(readme, "Layout")
    layout_lines = [line for line in layout.splitlines() if line]
    assert len(layout_lines) == 7
    assert all(re.fullmatch(r"- `[^\n`]+` - [^.!?]+[.]", line) for line in layout_lines)

    bullets = re.findall(r"^- `([^\n`]+)` - ([^.!?]+[.])$", layout, flags=re.MULTILINE)
    paths = [path for path, _ in bullets]
    assert paths == [
        "crossmill/__main__.py",
        "crossmill/base",
        "crossmill/grid",
        "crossmill/slots",
        "crossmill/lexicon",
        "crossmill/solve",
        "crossmill/cli",
    ]
    assert len(bullets) == 7

    repository_root = _repository_root()
    assert (repository_root / paths[0]).is_file()
    assert (repository_root / paths[1]).is_dir()
    assert (repository_root / paths[2]).is_dir()
    assert (repository_root / paths[3]).is_dir()
    assert (repository_root / paths[4]).is_dir()
    assert (repository_root / paths[5]).is_dir()
    assert (repository_root / paths[6]).is_dir()

    package_root = repository_root / "crossmill"
    module_folders = {
        path.parent.relative_to(package_root).as_posix()
        for path in package_root.rglob("*.py")
        if path.name != "__init__.py" and path.parent != package_root
    }
    assert module_folders == {"base", "grid", "slots", "lexicon", "solve", "cli"}
    assert set(paths[1:]) == {f"crossmill/{folder}" for folder in module_folders}
