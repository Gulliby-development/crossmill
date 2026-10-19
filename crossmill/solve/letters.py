from crossmill.slots.find import Slot


def cell_letters(slots: list[Slot], domains: list[list[str]]) -> dict[tuple[int, int], set[str]]:
    """Return the letters still possible at each cell covered by a slot."""
    result: dict[tuple[int, int], set[str]] = {}

    for slot, domain in zip(slots, domains):
        for offset, cell in enumerate(slot.cells()):
            letters = {word[offset] for word in domain}
            if cell in result:
                result[cell].intersection_update(letters)
            else:
                result[cell] = letters

    return result
