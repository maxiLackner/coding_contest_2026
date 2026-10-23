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

HEX_NEIGHBOR_OFFSETS = ((0, 2), (0, -2), (1, 1), (1, -1), (-1, 1), (-1, -1))


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
    return {2: 0, 3: radius, 4: 2 * radius, 5: 3 * radius, 6: 4 * radius, 1: 5 * radius}


def interior_cells(radius):
    board = build_empty_board(radius)
    return [(row_index, column_index) for row_index, row in enumerate(board)
            for column_index, character in enumerate(row) if character == "O"]


def beam_cells(board_cell_set, emitter_id, emitter_position):
    row_step, column_step = EMITTER_DIRECTION_STEPS[emitter_id]
    beam_row, beam_column = emitter_position[0] + row_step, emitter_position[1] + column_step
    cells = []
    while (beam_row, beam_column) in board_cell_set:
        cells.append((beam_row, beam_column))
        beam_row += row_step
        beam_column += column_step
    return cells


class Pattern:
    def __init__(self, radius, rows, required_count):
        self.radius = radius
        self.rows = rows
        self.required_count = required_count
        self.matter_cells = frozenset((row_index, column_index) for row_index, row in enumerate(rows)
                                      for column_index, character in enumerate(row) if character == "M")
        interior = set(interior_cells(radius))
        self.skirt_cells = frozenset(
            (row_index + row_offset, column_index + column_offset)
            for row_index, column_index in self.matter_cells
            for row_offset, column_offset in HEX_NEIGHBOR_OFFSETS
            if (row_index + row_offset, column_index + column_offset) in interior
        ) - self.matter_cells


def parse_patterns(input_text):
    tokens = input_text.split()
    pattern_count = int(tokens[0])
    token_index = 1
    patterns = []
    for _ in range(pattern_count):
        radius, row_count, _column_count, required_count = map(int, tokens[token_index:token_index + 4])
        rows = tokens[token_index + 4:token_index + 4 + row_count]
        token_index += 4 + row_count
        patterns.append(Pattern(radius, rows, required_count))
    return patterns


def parse_programs(output_text):
    programs = []
    current_program = []
    for line in output_text.split("\n"):
        tokens = line.split()
        if not tokens:
            if current_program:
                programs.append(current_program)
                current_program = []
            continue
        current_program.append(tokens)
    if current_program:
        programs.append(current_program)
    return programs


class Simulation:
    def __init__(self, radius):
        self.radius = radius
        self.matter_cells = set()
        self.board_cell_set = frozenset(interior_cells(radius))
        self.ring = build_clockwise_border_ring(radius)
        self.emitter_ring_indices = corner_ring_indices(radius)
        self.emitter_is_active = {emitter_id: False for emitter_id in EMITTER_DIRECTION_STEPS}
        self.beam_cache = {}

    def beam(self, emitter_id, ring_index):
        key = (emitter_id, ring_index)
        if key not in self.beam_cache:
            self.beam_cache[key] = beam_cells(self.board_cell_set, emitter_id, self.ring[ring_index])
        return self.beam_cache[key]

    def step(self, instruction_line):
        ring_length = len(self.ring)
        for emitter_id, instruction in zip(range(1, 7), instruction_line):
            if instruction == "F":
                self.emitter_ring_indices[emitter_id] = (self.emitter_ring_indices[emitter_id] + 1) % ring_length
            elif instruction == "B":
                self.emitter_ring_indices[emitter_id] = (self.emitter_ring_indices[emitter_id] - 1) % ring_length
            elif instruction == "T":
                self.emitter_is_active[emitter_id] = not self.emitter_is_active[emitter_id]
            elif instruction != "-":
                raise ValueError(f"unknown instruction {instruction!r}")
        beam_hit_counts = {}
        for emitter_id in EMITTER_DIRECTION_STEPS:
            if self.emitter_is_active[emitter_id]:
                for cell in self.beam(emitter_id, self.emitter_ring_indices[emitter_id]):
                    beam_hit_counts[cell] = beam_hit_counts.get(cell, 0) + 1
        for cell, hit_count in beam_hit_counts.items():
            if hit_count == 2:
                self.matter_cells.add(cell)
            elif hit_count >= 3:
                self.matter_cells.discard(cell)

    def submit_if_present(self, pattern):
        if pattern.matter_cells <= self.matter_cells and not (pattern.skirt_cells & self.matter_cells):
            self.matter_cells -= pattern.matter_cells
            return True
        return False


def count_submissions(pattern, program):
    simulation = Simulation(pattern.radius)
    submitted_count = 0
    for instruction_line in program:
        simulation.step(instruction_line)
        if simulation.submit_if_present(pattern):
            submitted_count += 1
    return submitted_count


def validate_output(input_text, output_text):
    patterns = parse_patterns(input_text)
    programs = parse_programs(output_text)
    errors = []
    if len(programs) != len(patterns):
        errors.append(f"expected {len(patterns)} programs, got {len(programs)}")
    for program_index, (pattern, program) in enumerate(zip(patterns, programs)):
        if any(len(instruction_line) != 6 for instruction_line in program):
            errors.append(f"program {program_index}: line without 6 instructions")
            continue
        submitted_count = count_submissions(pattern, program)
        if submitted_count < pattern.required_count:
            errors.append(f"program {program_index}: {submitted_count} of {pattern.required_count} submissions")
    score = sum(len(program) for program in programs)
    return score, errors


def main():
    input_path, output_path = map(Path, sys.argv[1:3])
    score, errors = validate_output(input_path.read_text(), output_path.read_text())
    print(f"{output_path.name}: score {score}, {'VALID' if not errors else 'INVALID'}")
    for error in errors[:20]:
        print("  " + error)


if __name__ == "__main__":
    main()
