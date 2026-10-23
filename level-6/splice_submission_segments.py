import sys
from multiprocessing import Pool
from pathlib import Path

import nanofab_simulator as simulator
from generate_pen_walk import format_programs


def emitter_state(simulation):
    return (tuple(simulation.emitter_ring_indices[emitter_id] for emitter_id in range(1, 7)),
            tuple(simulation.emitter_is_active[emitter_id] for emitter_id in range(1, 7)))


def harvest_segments(pattern, program, segments):
    simulation = simulator.Simulation(pattern.radius)
    segment_start_state = emitter_state(simulation)
    segment_start_index = 0
    for line_index, instruction_line in enumerate(program):
        simulation.step(instruction_line)
        if simulation.submit_if_present(pattern):
            segment_end_state = emitter_state(simulation)
            segment_lines = program[segment_start_index:line_index + 1]
            key = (segment_start_state, segment_end_state)
            if key not in segments or len(segment_lines) < len(segments[key]):
                segments[key] = segment_lines
            segment_start_state = segment_end_state
            segment_start_index = line_index + 1


MAXIMUM_TRANSIT_LENGTH = 4


def transit_lines(from_state, to_state, ring_length, toggle_first):
    positions, actives = list(from_state[0]), list(from_state[1])
    target_positions, target_actives = to_state
    lines = []
    if toggle_first:
        line = ["-"] * 6
        for emitter_index in range(6):
            if actives[emitter_index] and positions[emitter_index] != target_positions[emitter_index]:
                line[emitter_index] = "T"
                actives[emitter_index] = False
        if line != ["-"] * 6:
            lines.append(line)
    while (positions, actives) != (list(target_positions), list(target_actives)):
        line = ["-"] * 6
        for emitter_index in range(6):
            offset = (target_positions[emitter_index] - positions[emitter_index]) % ring_length
            if offset:
                step = 1 if offset <= ring_length // 2 else -1
                line[emitter_index] = "F" if step == 1 else "B"
                positions[emitter_index] = (positions[emitter_index] + step) % ring_length
            elif actives[emitter_index] != target_actives[emitter_index]:
                line[emitter_index] = "T"
                actives[emitter_index] = target_actives[emitter_index]
        lines.append(line)
        if len(lines) > MAXIMUM_TRANSIT_LENGTH:
            return None
    return lines


def transit_keeps_region_clean(pattern, from_state, lines):
    simulation = simulator.Simulation(pattern.radius)
    for emitter_index in range(6):
        simulation.emitter_ring_indices[emitter_index + 1] = from_state[0][emitter_index]
        simulation.emitter_is_active[emitter_index + 1] = from_state[1][emitter_index]
    relevant_cells = pattern.matter_cells | pattern.skirt_cells
    for instruction_line in lines:
        simulation.step(instruction_line)
        if simulation.matter_cells & relevant_cells:
            return False
    return True


def add_transit_segments(pattern, segments):
    ring_length = 6 * pattern.radius
    start_states = {start_state for start_state, _ in segments}
    end_states = {end_state for _, end_state in segments}
    for end_state in end_states:
        for start_state in start_states:
            if end_state == start_state:
                continue
            for toggle_first in (False, True):
                lines = transit_lines(end_state, start_state, ring_length, toggle_first)
                if lines is None or not transit_keeps_region_clean(pattern, end_state, lines):
                    continue
                for (segment_start, segment_end), segment_lines in list(segments.items()):
                    if segment_start != start_state:
                        continue
                    key = (end_state, segment_end)
                    combined = lines + segment_lines
                    if key not in segments or len(combined) < len(segments[key]):
                        segments[key] = combined
                break


def shortest_spliced_program(arguments):
    pattern, candidate_programs = arguments
    segments = {}
    for program in candidate_programs:
        harvest_segments(pattern, program, segments)
    add_transit_segments(pattern, segments)
    outgoing = {}
    for (start_state, end_state), segment_lines in segments.items():
        outgoing.setdefault(start_state, []).append((end_state, segment_lines))
    initial_state = emitter_state(simulator.Simulation(pattern.radius))
    best_cost = {initial_state: (0, None, None)}
    layers = [best_cost]
    for _ in range(pattern.required_count):
        next_layer = {}
        for state, (cost, _, _) in layers[-1].items():
            for end_state, segment_lines in outgoing.get(state, ()):
                new_cost = cost + len(segment_lines)
                if end_state not in next_layer or new_cost < next_layer[end_state][0]:
                    next_layer[end_state] = (new_cost, state, segment_lines)
        layers.append(next_layer)
    best_reference = min(candidate_programs, key=len)
    if not layers[-1]:
        return best_reference
    end_state = min(layers[-1], key=lambda state: layers[-1][state][0])
    pieces = []
    state = end_state
    for layer in reversed(layers[1:]):
        _, previous_state, segment_lines = layer[state]
        pieces.append(segment_lines)
        state = previous_state
    spliced_program = [list(line) for piece in reversed(pieces) for line in piece]
    if len(spliced_program) < len(best_reference) and \
            simulator.count_submissions(pattern, spliced_program) >= pattern.required_count:
        return spliced_program
    return best_reference


def main():
    level_directory = Path(__file__).parent
    candidate_root = Path(sys.argv[1])
    output_directory = candidate_root / "spliced_segments"
    output_directory.mkdir(parents=True, exist_ok=True)
    for input_path in sorted(level_directory.glob("in_level-6_[2-4]*.txt")):
        output_name = input_path.name.replace("in_", "out_", 1)
        input_text = input_path.read_text()
        patterns = simulator.parse_patterns(input_text)
        candidate_paths = sorted(candidate_root.glob(f"*/{output_name}")) + [level_directory / output_name]
        programs_per_pattern = [[] for _ in patterns]
        for candidate_path in candidate_paths:
            programs = simulator.parse_programs(candidate_path.read_text())
            if len(programs) != len(patterns):
                continue
            for pattern_index, program in enumerate(programs):
                if all(len(line) == 6 for line in program):
                    programs_per_pattern[pattern_index].append(program)
        with Pool(4) as pool:
            spliced_programs = pool.map(shortest_spliced_program, list(zip(patterns, programs_per_pattern)), chunksize=1)
        output_text = format_programs(spliced_programs)
        score, errors = simulator.validate_output(input_text, output_text)
        reference_score = sum(len(program) for program in simulator.parse_programs((level_directory / output_name).read_text()))
        print(f"{output_name}: merged {reference_score} -> spliced {score}, {'VALID' if not errors else errors[:3]}")
        if not errors:
            (output_directory / output_name).write_text(output_text)


if __name__ == "__main__":
    main()
