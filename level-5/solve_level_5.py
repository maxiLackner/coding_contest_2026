import sys
from pathlib import Path

EMITTER_DIRECTION_STEPS = {
    1: (0, 2),
    2: (1, 1),
    3: (1, -1),
    4: (0, -2),
    5: (-1, -1),
    6: (-1, 1),
}

INTERIOR_CHARACTERS = "OM"


def build_empty_board(radius):
    board = []
    for row_index in range(2 * radius + 1):
        leading_dash_count = abs(row_index - radius)
        cell_count = 2 * radius + 1 - leading_dash_count
        is_border_row = row_index in (0, 2 * radius)
        cells = []
        for cell_index in range(cell_count):
            is_border_cell = is_border_row or cell_index in (0, cell_count - 1)
            cells.append("*" if is_border_cell else "O")
        row_text = "-" * leading_dash_count + "-".join(cells) + "-" * leading_dash_count
        board.append(list(row_text))
    return board


def build_clockwise_border_ring(radius):
    ring = []
    for step in range(radius):
        ring.append((0, radius + 2 * step))
    for step in range(radius):
        ring.append((step, 3 * radius + step))
    for step in range(radius):
        ring.append((radius + step, 4 * radius - step))
    for step in range(radius):
        ring.append((2 * radius, 3 * radius - 2 * step))
    for step in range(radius):
        ring.append((2 * radius - step, radius - step))
    for step in range(radius):
        ring.append((radius - step, step))
    return ring


def corner_ring_indices(radius):
    return {
        2: 0,
        3: radius,
        4: 2 * radius,
        5: 3 * radius,
        6: 4 * radius,
        1: 5 * radius,
    }


def fire_active_emitters(board, active_emitter_positions):
    beam_hit_counts = {}
    for emitter_id, (emitter_row, emitter_column) in active_emitter_positions:
        row_step, column_step = EMITTER_DIRECTION_STEPS[emitter_id]
        beam_row, beam_column = emitter_row + row_step, emitter_column + column_step
        while (0 <= beam_row < len(board) and 0 <= beam_column < len(board[beam_row])
               and board[beam_row][beam_column] in INTERIOR_CHARACTERS):
            beam_hit_counts[(beam_row, beam_column)] = beam_hit_counts.get((beam_row, beam_column), 0) + 1
            beam_row += row_step
            beam_column += column_step
    for (hit_row, hit_column), hit_count in beam_hit_counts.items():
        if hit_count == 2:
            board[hit_row][hit_column] = "M"
        elif hit_count >= 3:
            board[hit_row][hit_column] = "O"


def neighbor_positions(row_index, column_index):
    for row_offset, column_offset in ((0, 2), (0, -2), (1, 1), (1, -1), (-1, 1), (-1, -1)):
        yield row_index + row_offset, column_index + column_offset


def submit_pattern_if_present(board, pattern_cells):
    if not all(board[row_index][column_index] == "M" for row_index, column_index in pattern_cells):
        return False
    for row_index, column_index in pattern_cells:
        for neighbor_row, neighbor_column in neighbor_positions(row_index, column_index):
            if (neighbor_row, neighbor_column) in pattern_cells:
                continue
            if (0 <= neighbor_row < len(board) and 0 <= neighbor_column < len(board[neighbor_row])
                    and board[neighbor_row][neighbor_column] == "M"):
                return False
    for row_index, column_index in pattern_cells:
        board[row_index][column_index] = "O"
    return True


def simulate_program(radius, pattern_cells, instruction_lines):
    board = build_empty_board(radius)
    submitted_pattern_count = 0
    ring = build_clockwise_border_ring(radius)
    ring_length = len(ring)
    emitter_ring_indices = corner_ring_indices(radius)
    emitter_is_active = {emitter_id: False for emitter_id in EMITTER_DIRECTION_STEPS}
    for instruction_line in instruction_lines:
        for emitter_id, instruction in zip(range(1, 7), instruction_line):
            if instruction == "F":
                emitter_ring_indices[emitter_id] = (emitter_ring_indices[emitter_id] + 1) % ring_length
            elif instruction == "B":
                emitter_ring_indices[emitter_id] = (emitter_ring_indices[emitter_id] - 1) % ring_length
            elif instruction == "T":
                emitter_is_active[emitter_id] = not emitter_is_active[emitter_id]
            elif instruction != "-":
                raise ValueError(f"unknown instruction {instruction!r}")
        active_emitter_positions = [(emitter_id, ring[emitter_ring_indices[emitter_id]])
                                    for emitter_id in EMITTER_DIRECTION_STEPS if emitter_is_active[emitter_id]]
        fire_active_emitters(board, active_emitter_positions)
        if submit_pattern_if_present(board, pattern_cells):
            submitted_pattern_count += 1
    return submitted_pattern_count


def parse_programs(input_text):
    tokens = input_text.split()
    program_count = int(tokens[0])
    token_index = 1
    programs = []
    for _ in range(program_count):
        radius, row_count, _column_count = map(int, tokens[token_index:token_index + 3])
        pattern_rows = tokens[token_index + 3:token_index + 3 + row_count]
        pattern_cells = {(row_index, column_index)
                         for row_index, row in enumerate(pattern_rows)
                         for column_index, character in enumerate(row) if character == "M"}
        token_index += 3 + row_count
        line_count = int(tokens[token_index])
        token_index += 1
        instruction_lines = []
        for _ in range(line_count):
            instruction_lines.append(tokens[token_index:token_index + 6])
            token_index += 6
        programs.append((radius, pattern_cells, instruction_lines))
    if token_index != len(tokens):
        raise ValueError(f"{len(tokens) - token_index} unparsed tokens")
    return programs


def solve(input_text):
    return "".join(f"{simulate_program(radius, pattern_cells, instruction_lines)}\n"
                   for radius, pattern_cells, instruction_lines in parse_programs(input_text))


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
