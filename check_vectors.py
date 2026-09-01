"""
Runs the example vectors against the project entry point.
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_VECTOR_FILE = PROJECT_ROOT / "vectores_ejemplo.txt"
RUN_SCRIPT = PROJECT_ROOT / "run.sh"


def extract_hex(stdout: str) -> str | None:
    """
    Finds the machine-readable HEX line in the encoder output.
    """
    for line in stdout.splitlines():
        if line.startswith("HEX:"):
            return line.split(":", 1)[1].strip().lower()
    return None


def read_vectors(vector_file: Path) -> list[tuple[int, str, str]]:
    """
    Reads vector lines in the format instruction ; 0xHEX.
    """
    vectors: list[tuple[int, str, str]] = []

    for line_number, raw_line in enumerate(
        vector_file.read_text().splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ";" not in line:
            raise ValueError(f"Invalid vector format at line {line_number}: {raw_line}")

        instruction, expected_hex = line.split(";", 1)
        vectors.append((line_number, instruction.strip(), expected_hex.strip().lower()))

    return vectors


def run_vector(instruction: str) -> tuple[int, str, str]:
    """
    Executes run.sh with one instruction and returns the process result.
    """
    completed = subprocess.run(
        [str(RUN_SCRIPT), instruction],
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.returncode, completed.stdout, completed.stderr


def main() -> int:
    """
    Compares every example vector against the HEX output from run.sh.
    """
    vector_file = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_VECTOR_FILE
    vectors = read_vectors(vector_file)

    passed = 0
    failed = 0

    for line_number, instruction, expected_hex in vectors:
        return_code, stdout, stderr = run_vector(instruction)
        actual_hex = extract_hex(stdout)

        if return_code == 0 and actual_hex == expected_hex:
            print(f"PASS line {line_number}: {instruction} -> {actual_hex}")
            passed += 1
            continue

        print(f"FAIL line {line_number}: {instruction}")
        print(f"  expected: {expected_hex}")
        print(f"  actual:   {actual_hex or '<missing HEX line>'}")
        if stderr.strip():
            print(f"  stderr:   {stderr.strip()}")
        failed += 1

    print(f"\nSummary: {passed} passed, {failed} failed, {len(vectors)} total")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
