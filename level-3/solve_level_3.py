import sys
from pathlib import Path

EMITTER_DIRECTION_STEPS = {
    "1": (0, 2),
    "2": (1, 1),
    "3": (1, -1),
    "4": (0, -2),
    "5": (-1, -1),
    "6": (-1, 1),
}


def parse_boards(input_text):
    lines = [line.strip() for line in input_text.splitlines() if line.strip()]
    board_count = int(lines[0])
    boards = []
    line_index = 1
    for _ in range(board_count):
        _radius, row_count, _column_count = map(int, lines[line_index].split())
        rows = lines[line_index + 1:line_index + 1 + row_count]
        boards.append([list(row) for row in rows])
        line_index += 1 + row_count
    return boards


def fire_emitters(board):
    beam_hit_counts = {}
    for row_index, row in enumerate(board):
        for column_index, character in enumerate(row):
            if character not in EMITTER_DIRECTION_STEPS:
                continue
            row_step, column_step = EMITTER_DIRECTION_STEPS[character]
            beam_row, beam_column = row_index + row_step, column_index + column_step
            while (0 <= beam_row < len(board) and 0 <= beam_column < len(board[beam_row])
                   and board[beam_row][beam_column] in "OM"):
                beam_hit_counts[(beam_row, beam_column)] = beam_hit_counts.get((beam_row, beam_column), 0) + 1
                beam_row += row_step
                beam_column += column_step
    for (hit_row, hit_column), hit_count in beam_hit_counts.items():
        if hit_count == 2:
            board[hit_row][hit_column] = "M"
        elif hit_count >= 3:
            board[hit_row][hit_column] = "O"
    return board


def solve(input_text):
    boards = parse_boards(input_text)
    return "".join("\n".join("".join(row) for row in fire_emitters(board)) + "\n\n" for board in boards)


def main():
    level_directory = Path(__file__).parent
    input_paths = sys.argv[1:] or sorted(level_directory.glob("in_*.txt"))
    for input_path in map(Path, input_paths):
        output_path = input_path.with_name(input_path.name.replace("in_", "out_", 1))
        output_text = solve(input_path.read_text())
        if output_path.exists() and "example" in output_path.name:
            expected_text = output_path.read_text()
            status = "OK" if output_text == expected_text else "MISMATCH"
            print(f"{input_path.name}: example check {status}")
            continue
        output_path.write_text(output_text)
        print(f"{input_path.name} -> {output_path.name}")


if __name__ == "__main__":
    main()
