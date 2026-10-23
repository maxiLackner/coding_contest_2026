import sys
from collections import deque
from itertools import product
from multiprocessing import Pool
from pathlib import Path

import nanofab_simulator as simulator

AXIS_EMITTER_GROUPS = ((1, 4), (2, 5), (3, 6))


def signed_ring_offset(from_index, to_index, ring_length):
    offset = (to_index - from_index) % ring_length
    return offset if offset <= ring_length // 2 else offset - ring_length


def cell_to_ring_index(simulation, emitter_id):
    mapping = {}
    for ring_index in range(len(simulation.ring)):
        for cell in simulation.beam(emitter_id, ring_index):
            mapping[cell] = ring_index
    return mapping


class PenPlanner:
    def __init__(self, pattern, first_emitter, second_emitter):
        self.pattern = pattern
        self.simulation = simulator.Simulation(pattern.radius)
        self.ring_length = len(self.simulation.ring)
        self.first_emitter = first_emitter
        self.second_emitter = second_emitter
        self.first_ring_index_of = cell_to_ring_index(self.simulation, first_emitter)
        self.second_ring_index_of = cell_to_ring_index(self.simulation, second_emitter)

    def ring_targets(self, cell):
        return self.first_ring_index_of[cell], self.second_ring_index_of[cell]

    def one_tick_reachable(self, from_cell, to_cell):
        from_first, from_second = self.ring_targets(from_cell)
        to_first, to_second = self.ring_targets(to_cell)
        return (abs(signed_ring_offset(from_first, to_first, self.ring_length)) <= 1
                and abs(signed_ring_offset(from_second, to_second, self.ring_length)) <= 1)

    def build_walk(self, start_cell):
        cells = self.pattern.matter_cells
        if not hasattr(self, "neighbors"):
            self.neighbors = {cell: [other for other in cells if other != cell and self.one_tick_reachable(cell, other)]
                              for cell in cells}
        neighbors = self.neighbors
        walk = [start_cell]
        unvisited = set(cells) - {start_cell}
        current = start_cell
        while unvisited:
            parents = {current: None}
            queue = deque([current])
            found = None
            while queue:
                cell = queue.popleft()
                if cell in unvisited:
                    found = cell
                    break
                for neighbor in neighbors[cell]:
                    if neighbor not in parents:
                        parents[neighbor] = cell
                        queue.append(neighbor)
            if found is None:
                return None
            path = []
            cell = found
            while cell != current:
                path.append(cell)
                cell = parents[cell]
            path.reverse()
            walk.extend(path)
            unvisited -= set(path)
            current = found
        return walk

    def instruction_line(self, first_instruction, second_instruction):
        line = ["-"] * 6
        line[self.first_emitter - 1] = first_instruction
        line[self.second_emitter - 1] = second_instruction
        return line

    def move_instruction(self, current_index, target_index):
        offset = signed_ring_offset(current_index, target_index, self.ring_length)
        if offset > 0:
            return "F", (current_index + 1) % self.ring_length
        if offset < 0:
            return "B", (current_index - 1) % self.ring_length
        return "-", current_index

    def build_program(self, walk):
        corners = simulator.corner_ring_indices(self.pattern.radius)
        first_index, second_index = corners[self.first_emitter], corners[self.second_emitter]
        program = []
        first_target, second_target = self.ring_targets(walk[0])
        while first_index != first_target or second_index != second_target:
            first_instruction, first_index = self.move_instruction(first_index, first_target)
            second_instruction, second_index = self.move_instruction(second_index, second_target)
            program.append(self.instruction_line(first_instruction, second_instruction))
        program.append(self.instruction_line("T", "T"))
        forward_steps = []
        for cell in walk[1:]:
            first_target, second_target = self.ring_targets(cell)
            first_instruction, first_index = self.move_instruction(first_index, first_target)
            second_instruction, second_index = self.move_instruction(second_index, second_target)
            forward_steps.append(self.instruction_line(first_instruction, second_instruction))
        program.extend(forward_steps)
        backward_steps = [self.instruction_line(*(invert(instruction) for instruction in (
            step[self.first_emitter - 1], step[self.second_emitter - 1]))) for step in reversed(forward_steps)]
        for repetition_index in range(1, self.pattern.required_count):
            program.append(["-"] * 6)
            program.extend(backward_steps if repetition_index % 2 == 1 else forward_steps)
        return program


def invert(instruction):
    return {"F": "B", "B": "F"}.get(instruction, instruction)


def best_pen_program(pattern):
    best_program = None
    for first_group, second_group in ((0, 1), (0, 2), (1, 2)):
        for first_emitter, second_emitter in product(AXIS_EMITTER_GROUPS[first_group], AXIS_EMITTER_GROUPS[second_group]):
            planner = PenPlanner(pattern, first_emitter, second_emitter)
            for start_cell in sorted(pattern.matter_cells)[::max(1, len(pattern.matter_cells) // 12)]:
                walk = planner.build_walk(start_cell)
                if walk is None:
                    continue
                program = planner.build_program(walk)
                if best_program is None or len(program) < len(best_program):
                    best_program = program
    return best_program


def format_programs(programs):
    return "".join("\n".join(" ".join(line) for line in program) + "\n\n" for program in programs)


def main():
    level_directory = Path(__file__).parent
    output_directory = Path(sys.argv[1]) if len(sys.argv) > 1 else level_directory
    for input_path in sorted(level_directory.glob("in_*.txt")):
        patterns = simulator.parse_patterns(input_path.read_text())
        with Pool() as pool:
            programs = pool.map(best_pen_program, patterns)
        output_path = output_directory / input_path.name.replace("in_", "out_", 1)
        if "example" in output_path.name:
            output_path = output_directory / "out_level-6_0-example-generated.txt"
        output_text = format_programs(programs)
        output_path.write_text(output_text)
        score, errors = simulator.validate_output(input_path.read_text(), output_text)
        print(f"{output_path.name}: score {score}, {'VALID' if not errors else errors[:3]}")


if __name__ == "__main__":
    main()
