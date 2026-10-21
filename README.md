<p align="center"><img src="docs/logo.svg" width="96" alt="" /></p>

# crossmill

crossmill is an offline command-line toolkit for people who build small crossword grids by hand. It checks, numbers, draws, and symmetrizes grids; searches and summarizes word lists; and helps narrow and solve small themed grids.

[![CI](https://github.com/Gulliby-development/crossmill/actions/workflows/ci.yml/badge.svg)](https://github.com/Gulliby-development/crossmill/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Install

Python 3.11 or newer is required. No installation step is needed: from the repository root, run the package with `python -m crossmill` followed by a command and its arguments. The usage lines below write `crossmill` as shorthand for that module invocation.

## Usage

Choose one of the ten commands below and provide its required arguments. Optional switches may be placed among ordinary arguments where the command accepts them. Word lists can be supplied directly or read from standard input as described in Grids and words.

## Grids and words

A grid is written as rows separated by `/`; each row contains `#` for a block, `.` for an empty cell, or an uppercase letter from A to Z. Rows must be nonempty and have equal widths, and grids may be at most 15 rows by 15 columns. Lowercase grid letters, empty rows, and any other grid character are rejected.

A WORDS argument is a comma-separated list such as `CAT,dog,Emu`, or a single `-` argument to read words from strict UTF-8 standard input. Each word must contain 2 to 15 ASCII letters; words are normalized to uppercase and duplicates are removed. Empty list entries and entries containing anything other than ASCII letters are rejected. Patterns contain 2 to 15 ASCII letters or dots, such as `b.n.`; letters are case-insensitive and a dot matches any letter. Other pattern characters are rejected. The solving commands accept grids no larger than 5 by 5 and lexicons of at most 40 unique words.

## Commands

### check

crossmill check GRID [--min-length N] [--checked]

Checks construction rules and reports symmetry, disconnected open regions, cells in no slot, short slots, and (when requested) unchecked cells. `--min-length` selects the minimum slot length, while `--checked` asks the report to include unchecked-cell findings.

### number

crossmill number GRID

Reports the grid dimensions and block count, then lists every across and down slot with its number, length, starting cell, and pattern.

### render

crossmill render GRID [--compact]

Draws a bordered grid with slot numbers and letters; `--compact` uses narrower cells and omits the number line. For example, `crossmill render "A.#/.../#.."` prints:

```text
+----+----+----+
|1   |2   |####|
| A  |    |####|
+----+----+----+
|3   |    |4   |
|    |    |    |
+----+----+----+
|####|5   |    |
|####|    |    |
+----+----+----+
```

### symmetrize

crossmill symmetrize GRID

Adds blocks as needed so the grid is symmetric under a half turn, and reports the resulting grid and number of blocks added. It reports an error rather than replacing a letter when a required partner cell contains one.

### pattern

crossmill pattern PATTERN WORDS [--limit L]

Lists the lexicon words matching a pattern in ascending order and reports the total match count. `--limit` caps how many matching words are shown.

### stats

crossmill stats WORDS [--letters N]

Summarizes the number of unique words, shortest and longest word lengths, counts by length, and the five most frequent letters (including repeated occurrences within a word). `--letters` lists the N most frequent letters instead, with N from 1 to 26.

### domains

crossmill domains GRID WORDS

Computes candidates for each slot and removes candidates that cannot agree with candidates in crossing slots, repeating until the domains are arc-consistent. This consistency check does not enforce the distinct-word rule required for a fill.

### forced

crossmill forced GRID WORDS

After domain propagation, reports letters forced in otherwise empty cells, or reports that the domains are inconsistent. For example, `crossmill forced "..../.##./.##./...." "BAND,BEAD,BEAR,DARE,DATE,DOOR,LAKE,TEAM"` prints:

```text
grid        4x4
consistent  yes
forced      3
row         B..D
row         .##.
row         .##.
row         D...
```

### fill

crossmill fill GRID WORDS [--limit L]

Finds fills that agree at every crossing and use each word at most once, ordered by the words in slot order. `--limit` caps the number returned. For example, `crossmill fill "..../.##./.##./...." "BAND,BEAD,BEAR,DARE,DATE,DOOR,LAKE,TEAM" --limit 3` prints:

```text
grid        4x4
slots       4
words       8
found       3
fill        1 BAND/E##A/A##R/DATE
fill        2 BAND/E##A/A##T/DARE
fill        3 BEAD/A##A/N##R/DATE
```

### count

crossmill count GRID WORDS [--max M]

Counts fills up to `--max` and reports whether more fills exist than that cap. It uses the same crossing agreement and distinct-word requirements as fill.

## Exit codes

A command exits with code 0 when it succeeds. Code 1 means it completed a report that found a problem: check found construction problems, domains or forced found inconsistent domains, or fill found no fill. Code 2 means the command could not run because of a usage, argument, or input error.

## Layout

- `crossmill/__main__.py` - provides module execution for the command-line interface.
- `crossmill/base` - holds shared error, text, integer, option, and input utilities.
- `crossmill/grid` - holds grid parsing, construction rules, rendering, and symmetry operations.
- `crossmill/slots` - holds slot numbering, discovery, patterns, and crossings.
- `crossmill/lexicon` - holds word parsing, pattern matching, indexing, and statistics.
- `crossmill/solve` - holds candidate domains, forced-letter projection, search, and fill counting.
- `crossmill/cli` - holds command adapters and command-line dispatch.

## Development

Install the development tools once with `python -m pip install pytest ruff`. From the repository root, run the lint, formatting, and test checks:

- `python -m ruff check .`
- `python -m ruff format --check .`
- `python -m pytest -q`

## License

MIT, see [LICENSE](LICENSE).

---

Built with BAKED
