from crossmill.grid.model import Grid
from crossmill.lexicon.pattern import match_all
from crossmill.slots.crossings import crossings
from crossmill.slots.find import Slot, slot_pattern


def initial_domains(grid: Grid, slots: list[Slot], lexicon: list[str]) -> list[list[str]]:
    """Return each slot's matching lexicon words in the supplied slot order."""
    return [match_all(lexicon, slot_pattern(grid, slot)) for slot in slots]


def propagate(slots: list[Slot], domains: list[list[str]]) -> list[list[str]]:
    """Narrow domains to crossing arc consistency without mutating the inputs."""
    current = [list(domain) for domain in domains]
    neighbors: list[list[tuple[int, int, int]]] = [[] for _ in slots]

    for across, across_offset, down, down_offset in crossings(slots):
        neighbors[across].append((across_offset, down, down_offset))
        neighbors[down].append((down_offset, across, across_offset))

    while True:
        narrowed = [
            [
                word
                for word in domain
                if all(
                    any(word[offset] == other[other_offset] for other in current[neighbor])
                    for offset, neighbor, other_offset in neighbors[index]
                )
            ]
            for index, domain in enumerate(current)
        ]
        if narrowed == current:
            return narrowed
        current = narrowed
