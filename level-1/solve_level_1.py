import sys
from pathlib import Path


def render_board(radius):
    rows = []
    for row_index in range(2 * radius + 1):
        distance_from_center = abs(row_index - radius)
        cell_count = 2 * radius + 1 - distance_from_center
        if distance_from_center == radius:
            cells = ["*"] * cell_count
        else:
            cells = ["*"] + ["O"] * (cell_count - 2) + ["*"]
        indentation = "-" * distance_from_center
        rows.append(indentation + "-".join(cells) + indentation)
    return "\n".join(rows)


def solve(input_text):
    numbers = [int(token) for token in input_text.split()]
    radius_count = numbers[0]
    radii = numbers[1:1 + radius_count]
    return "".join(render_board(radius) + "\n\n" for radius in radii)


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
