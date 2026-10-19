from crossmill.grid.model import Grid


def render_box(grid: Grid, numbers: dict[tuple[int, int], int], compact: bool) -> list[str]:
    """Draw a grid as ASCII box lines without line terminators."""
    cell_width = 3 if compact else 4
    border = "+" + ("-" * cell_width + "+") * grid.width
    lines = [border]

    for r, row in enumerate(grid.rows):
        if not compact:
            number_cells = []
            for c, cell in enumerate(row):
                if cell == "#":
                    number_cells.append("#" * cell_width)
                else:
                    number = numbers.get((r, c))
                    number_cells.append("" if number is None else str(number).ljust(cell_width))
                    if number is None:
                        number_cells[-1] = " " * cell_width
            lines.append("|" + "|".join(number_cells) + "|")

        letter_cells = []
        for cell in row:
            if cell == "#":
                letter_cells.append("#" * cell_width)
            elif compact:
                letter_cells.append(f" {cell if cell != '.' else ' '} ")
            else:
                letter_cells.append(f" {cell if cell != '.' else ' '}  ")
        lines.append("|" + "|".join(letter_cells) + "|")
        lines.append(border)

    return lines
