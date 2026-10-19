def by_length(lexicon: list[str]) -> dict[int, list[str]]:
    """Group words by length with ascending keys and words."""
    grouped: dict[int, list[str]] = {}
    for word in lexicon:
        grouped.setdefault(len(word), []).append(word)
    return {length: sorted(grouped[length]) for length in sorted(grouped)}
