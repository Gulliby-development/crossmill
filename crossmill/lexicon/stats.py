from collections import Counter

from crossmill.lexicon.index import by_length


def lexicon_stats(
    lexicon: list[str], letters: int = 5
) -> tuple[dict[int, int], list[tuple[str, int]]]:
    """Count word lengths and rank the `letters` most frequent letters (default five)."""
    length_counts = {length: len(words) for length, words in by_length(lexicon).items()}
    letter_counts = Counter(letter for word in lexicon for letter in word)
    ranked_letters = sorted(letter_counts.items(), key=lambda item: (-item[1], item[0]))[:letters]
    return length_counts, ranked_letters
