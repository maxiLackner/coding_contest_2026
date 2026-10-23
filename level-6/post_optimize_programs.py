import sys
from multiprocessing import Pool
from pathlib import Path

import nanofab_simulator as simulator
from generate_pen_walk import format_programs


def is_valid(pattern, program):
    return simulator.count_submissions(pattern, program) >= pattern.required_count


def merge_lines(first_line, second_line):
    merged_line = []
    for first_instruction, second_instruction in zip(first_line, second_line):
        if first_instruction != "-" and second_instruction != "-":
            return None
        merged_line.append(first_instruction if first_instruction != "-" else second_instruction)
    return merged_line


def shorten_program(arguments):
    pattern, program = arguments
    program = [list(line) for line in program]
    improved = True
    while improved:
        improved = False
        line_index = len(program) - 1
        while line_index >= 0:
            candidate = program[:line_index] + program[line_index + 1:]
            if is_valid(pattern, candidate):
                program = candidate
                improved = True
            elif line_index + 1 < len(program):
                merged_line = merge_lines(program[line_index], program[line_index + 1])
                if merged_line is not None:
                    candidate = program[:line_index] + [merged_line] + program[line_index + 2:]
                    if is_valid(pattern, candidate):
                        program = candidate
                        improved = True
            line_index = min(line_index - 1, len(program) - 1)
    return program


def main():
    level_directory = Path(__file__).parent
    output_directory = Path(sys.argv[1])
    output_directory.mkdir(parents=True, exist_ok=True)
    for input_path in sorted(level_directory.glob("in_level-6_[2-4]*.txt")):
        output_name = input_path.name.replace("in_", "out_", 1)
        patterns = simulator.parse_patterns(input_path.read_text())
        programs = simulator.parse_programs((level_directory / output_name).read_text())
        with Pool(12) as pool:
            shortened_programs = pool.map(shorten_program, list(zip(patterns, programs)), chunksize=1)
        output_text = format_programs(shortened_programs)
        score, errors = simulator.validate_output(input_path.read_text(), output_text)
        before_score = sum(map(len, programs))
        print(f"{output_name}: {before_score} -> {score}, {'VALID' if not errors else errors[:3]}")
        if not errors:
            (output_directory / output_name).write_text(output_text)


if __name__ == "__main__":
    main()
