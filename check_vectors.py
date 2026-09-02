#!/usr/bin/env python3
"""
Runs a professor-style validation against the RISC-V toolchain.
"""

import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
RUN_SCRIPT = PROJECT_ROOT / "run.sh"
RISCV_GCC = "riscv64-unknown-elf-gcc"
RISCV_OBJDUMP = "riscv64-unknown-elf-objdump"
INSTRUCTION_PATTERN = re.compile(r"^\s*[0-9a-f]+:\s+([0-9a-f]{8})\b")
START_SYMBOL_PATTERN = re.compile(r"^[0-9a-f]+ <_start>:$")


@dataclass(frozen=True)
class TestCase:
    """Stores one instruction validation case."""

    label: str
    instruction: str


@dataclass(frozen=True)
class CommandResult:
    """Stores command output needed for comparison."""

    return_code: int
    stdout: str
    stderr: str


TEST_CASES: tuple[TestCase, ...] = (
    TestCase("add/base", "add x7, x20, x6"),
    TestCase("add/x0", "add x0, x0, x0"),
    TestCase("add/limit-registers", "add x31, x31, x30"),
    TestCase("sub/base", "sub x5, x7, x18"),
    TestCase("sub/x0", "sub x0, x31, x1"),
    TestCase("sub/limit-registers", "sub x31, x0, x31"),
    TestCase("and/base", "and x25, x16, x22"),
    TestCase("and/x0", "and x0, x1, x2"),
    TestCase("and/limit-registers", "and x31, x31, x0"),
    TestCase("or/base", "or x18, x29, x9"),
    TestCase("or/x0", "or x0, x0, x31"),
    TestCase("or/limit-registers", "or x31, x1, x30"),
    TestCase("addi/positive", "addi x5, x25, 2035"),
    TestCase("addi/negative", "addi x10, x1, -12"),
    TestCase("addi/limit", "addi x31, x0, -2048"),
    TestCase("andi/positive", "andi x8, x3, 127"),
    TestCase("andi/negative", "andi x30, x1, -209"),
    TestCase("andi/limit", "andi x27, x30, 2047"),
    TestCase("lw/positive", "lw x29, 8(x30)"),
    TestCase("lw/negative", "lw x30, -1049(x14)"),
    TestCase("lw/limit", "lw x31, -2048(x0)"),
    TestCase("lb/positive", "lb x2, 1705(x9)"),
    TestCase("lb/negative", "lb x25, -389(x27)"),
    TestCase("lb/limit", "lb x31, 2047(x0)"),
    TestCase("sw/positive", "sw x16, 1774(x31)"),
    TestCase("sw/negative", "sw x31, -411(x23)"),
    TestCase("sw/limit", "sw x31, -2048(x0)"),
    TestCase("sb/positive", "sb x18, 1701(x20)"),
    TestCase("sb/negative", "sb x6, -72(x28)"),
    TestCase("sb/limit", "sb x31, 2047(x0)"),
    TestCase("beq/positive", "beq x31, x23, 16"),
    TestCase("beq/negative", "beq x30, x4, -80"),
    TestCase("beq/zero", "beq x0, x0, 0"),
    TestCase("bne/positive", "bne x5, x0, 60"),
    TestCase("bne/negative", "bne x12, x15, -16"),
    TestCase("bne/limit", "bne x31, x31, 4092"),
)


def extract_encoder_hex(stdout: str) -> str | None:
    """
    Finds the HEX line emitted by run.sh.
    """
    for line in stdout.splitlines():
        if line.startswith("HEX:"):
            return line.split(":", 1)[1].strip().lower()
    return None


def extract_objdump_hex(stdout: str) -> str | None:
    """
    Finds the first 32-bit instruction emitted under the _start symbol.
    """
    in_start_symbol = False

    for line in stdout.splitlines():
        stripped_line = line.strip()
        if START_SYMBOL_PATTERN.match(stripped_line):
            in_start_symbol = True
            continue

        if in_start_symbol and re.match(r"^[0-9a-f]+ <.+>:$", stripped_line):
            break

        if not in_start_symbol:
            continue

        match = INSTRUCTION_PATTERN.match(line)
        if match:
            return f"0x{match.group(1).lower()}"

    return None


def split_branch_instruction(instruction: str) -> tuple[str, str, str, int]:
    """
    Splits a branch instruction into mnemonic, registers, and immediate.
    """
    mnemonic, operands_text = instruction.split(maxsplit=1)
    operands = [operand.strip() for operand in operands_text.split(",")]

    if len(operands) != 3:
        raise ValueError(f"Invalid branch instruction: {instruction}")

    rs1, rs2, immediate_text = operands
    return mnemonic, rs1, rs2, int(immediate_text, 0)


def build_branch_source(instruction: str) -> str:
    """
    Builds branch assembly using a label at the requested offset.
    """
    mnemonic, rs1, rs2, immediate = split_branch_instruction(instruction)
    branch_instruction = f"{mnemonic} {rs1}, {rs2}, target"

    if immediate > 0:
        return (
            ".option norvc\n"
            ".text\n"
            ".globl _start\n"
            "_start:\n"
            f"    {branch_instruction}\n"
            f"    .org {immediate}\n"
            "target:\n"
        )

    if immediate == 0:
        return (
            ".option norvc\n"
            ".text\n"
            ".globl _start\n"
            "_start:\n"
            "target:\n"
            f"    {branch_instruction}\n"
        )

    branch_address = -immediate
    return (
        ".option norvc\n"
        ".text\n"
        ".globl _start\n"
        "target:\n"
        f"    .org {branch_address}\n"
        "_start:\n"
        f"    {branch_instruction}\n"
    )


def build_assembly_source(instruction: str) -> str:
    """
    Builds an assembly file for one instruction.
    """
    mnemonic = instruction.split(maxsplit=1)[0]
    if mnemonic in {"beq", "bne"}:
        return build_branch_source(instruction)

    return (
        ".option norvc\n"
        ".text\n"
        ".globl _start\n"
        "_start:\n"
        f"    {instruction}\n"
    )


def run_command(command: list[str], cwd: Path | None = None) -> CommandResult:
    """
    Runs one subprocess and captures its output.
    """
    completed = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def run_encoder(instruction: str) -> CommandResult:
    """
    Runs the student encoder through the required entry point.
    """
    return run_command([str(RUN_SCRIPT), instruction], cwd=PROJECT_ROOT)


def run_toolchain(instruction: str) -> CommandResult:
    """
    Assembles one instruction with the official RISC-V toolchain.
    """
    with tempfile.TemporaryDirectory() as temporary_directory:
        work_dir = Path(temporary_directory)
        source_path = work_dir / "case.s"
        object_path = work_dir / "case.o"
        source_path.write_text(build_assembly_source(instruction))

        assemble_result = run_command(
            [
                RISCV_GCC,
                "-march=rv32i",
                "-mabi=ilp32",
                "-c",
                str(source_path),
                "-o",
                str(object_path),
            ],
            cwd=work_dir,
        )
        if assemble_result.return_code != 0:
            return assemble_result

        return run_command([RISCV_OBJDUMP, "-d", str(object_path)], cwd=work_dir)


def check_toolchain() -> bool:
    """
    Checks whether the expected RISC-V commands are available.
    """
    missing_tools = [
        tool for tool in (RISCV_GCC, RISCV_OBJDUMP) if shutil.which(tool) is None
    ]
    if not missing_tools:
        return True

    print("Missing RISC-V toolchain commands:")
    for tool in missing_tools:
        print(f"  - {tool}")
    print("Install them before running this validation script.")
    return False


def main() -> int:
    """
    Compares the encoder output against toolchain output for 36 cases.
    """
    if not check_toolchain():
        return 2

    passed = 0
    failed = 0
    total = len(TEST_CASES)

    for index, test_case in enumerate(TEST_CASES, start=1):
        toolchain_result = run_toolchain(test_case.instruction)
        encoder_result = run_encoder(test_case.instruction)

        expected_hex = extract_objdump_hex(toolchain_result.stdout)
        actual_hex = extract_encoder_hex(encoder_result.stdout)

        if (
            toolchain_result.return_code == 0
            and encoder_result.return_code == 0
            and expected_hex == actual_hex
        ):
            print(
                f"PASS {index:02d}/{total} {test_case.label}: "
                f"{test_case.instruction} -> {actual_hex}"
            )
            passed += 1
            continue

        print(f"FAIL {index:02d}/{total} {test_case.label}: {test_case.instruction}")
        print(f"  toolchain: {expected_hex or '<missing objdump word>'}")
        print(f"  encoder:   {actual_hex or '<missing HEX line>'}")

        if toolchain_result.stderr.strip():
            print(f"  toolchain stderr: {toolchain_result.stderr.strip()}")
        if encoder_result.stderr.strip():
            print(f"  encoder stderr:   {encoder_result.stderr.strip()}")

        failed += 1

    print(f"\nSummary: {passed} passed, {failed} failed, {total} total")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
