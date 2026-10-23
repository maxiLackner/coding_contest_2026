import sys
from pathlib import Path

import nanofab_simulator as simulator
from generate_pen_walk import format_programs


def merge_candidates(input_path, candidate_paths):
    patterns = simulator.parse_patterns(input_path.read_text())
    best_programs = [None] * len(patterns)
    best_sources = [None] * len(patterns)
    for candidate_path in candidate_paths:
        programs = simulator.parse_programs(candidate_path.read_text())
        for program_index, (pattern, program) in enumerate(zip(patterns, programs)):
            if best_programs[program_index] is not None and len(program) >= len(best_programs[program_index]):
                continue
            if any(len(line) != 6 or any(token not in "FBT-" for token in line) for line in program):
                continue
            if simulator.count_submissions(pattern, program) >= pattern.required_count:
                best_programs[program_index] = program
                best_sources[program_index] = candidate_path
    return best_programs, best_sources


def main():
    level_directory = Path(__file__).parent
    candidate_root = Path(sys.argv[1])
    for input_path in sorted(level_directory.glob("in_*.txt")):
        output_name = input_path.name.replace("in_", "out_", 1)
        if "example" in output_name:
            continue
        candidate_paths = sorted(candidate_root.glob(f"*/{output_name}")) + [level_directory / output_name]
        best_programs, best_sources = merge_candidates(input_path, [path for path in candidate_paths if path.exists()])
        if any(program is None for program in best_programs):
            print(f"{output_name}: missing valid program, not written")
            continue
        output_text = format_programs(best_programs)
        score, errors = simulator.validate_output(input_path.read_text(), output_text)
        if errors:
            print(f"{output_name}: merged output INVALID {errors[:3]}")
            continue
        (level_directory / output_name).write_text(output_text)
        source_wins = {}
        for source in best_sources:
            source_wins[source.parent.name] = source_wins.get(source.parent.name, 0) + 1
        print(f"{output_name}: score {score}, wins {source_wins}")


if __name__ == "__main__":
    main()
