from collections.abc import Iterator

from crossmill.grid.model import Grid
from crossmill.slots.find import Slot
from crossmill.solve.domains import initial_domains, propagate


def fills(grid: Grid, slots: list[Slot], lexicon: list[str], limit: int) -> list[list[str]]:
    """Return up to limit distinct fills in lexicographic slot order."""
    if limit <= 0:
        return []

    solutions: list[list[str]] = []
    for words in _solutions(grid, slots, lexicon):
        solutions.append(words)
        if len(solutions) == limit:
            break
    return solutions


def filled_rows(grid: Grid, slots: list[Slot], words: list[str]) -> str:
    """Project the words of a fill into a copy of the grid rows."""
    rows = [list(row) for row in grid.rows]
    for slot, word in zip(slots, words):
        for (row, col), letter in zip(slot.cells(), word):
            rows[row][col] = letter
    return "/".join("".join(row) for row in rows)


def _solutions(grid: Grid, slots: list[Slot], lexicon: list[str]) -> Iterator[list[str]]:
    """Lazily enumerate globally distinct, crossing-consistent assignments."""
    domains = propagate(slots, initial_domains(grid, slots, lexicon))
    if any(not domain for domain in domains):
        return

    def visit(
        index: int,
        current: list[list[str]],
        chosen: list[str],
        used: set[str],
    ) -> Iterator[list[str]]:
        if index == len(slots):
            yield list(chosen)
            return

        for word in sorted(current[index]):
            if word in used:
                continue

            branch = [list(domain) for domain in current]
            branch[index] = [word]
            for remaining in range(index + 1, len(slots)):
                branch[remaining] = [
                    candidate for candidate in branch[remaining] if candidate != word
                ]

            branch = propagate(slots, branch)
            if any(not domain for domain in branch):
                continue

            chosen.append(word)
            yield from visit(index + 1, branch, chosen, used | {word})
            chosen.pop()

    yield from visit(0, domains, [], set())
