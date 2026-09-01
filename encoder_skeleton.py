#!/usr/bin/env python3
"""
Educational RISC-V Instruction Encoder Skeleton.
CE4301 Computer Architecture I — 2026-IIS

This skeleton implements the command-line and output contract required by
the specification. You must complete the two functions marked with TODO.
"""

import sys
from dataclasses import dataclass

# Mapping of supported mnemonics to their respective formats.
# Distinguishes I from I_MEM during parsing for syntax differences.
INSTRUCTION_FORMATS = {
    "add": "R",
    "sub": "R",
    "and": "R",
    "or": "R",
    "addi": "I",
    "andi": "I",
    "lw": "I_MEM",
    "lb": "I_MEM",
    "sw": "S",
    "sb": "S",
    "beq": "B",
    "bne": "B",
}


@dataclass
class ParsedInstruction:
    """Holds the results of parsing a RISC-V instruction."""

    mnemonic: str
    format_type: str
    rd: str | None
    rs1: str | None
    rs2: str | None
    imm: str | None


def parse_instruction(instruction_str: str) -> ParsedInstruction:
    """
    Parses a raw assembly string, identifies the mnemonic, validates it,
    and extracts the registers and immediate value based on its format.
    """
    instruction_str = instruction_str.strip()
    parts = instruction_str.split(" ", 1)

    if len(parts) == 1:
        mnemonic = parts[0]
        operands_str = ""
    else:
        mnemonic = parts[0]
        operands_str = parts[1]

    if mnemonic not in INSTRUCTION_FORMATS:
        raise ValueError(f"Unsupported instruction: {mnemonic}")

    format_type = INSTRUCTION_FORMATS[mnemonic]
    operands_str = operands_str.replace(" ", "")

    rd, rs1, rs2, imm = None, None, None, None

    if format_type == "R":
        operands = operands_str.split(",")
        if len(operands) != 3:
            raise ValueError(f"Invalid operand count for R-type: expected 3, got {len(operands)}")
        rd, rs1, rs2 = operands[0], operands[1], operands[2]
        
    elif format_type == "I":
        operands = operands_str.split(",")
        if len(operands) != 3:
            raise ValueError(f"Invalid operand count for I-type: expected 3, got {len(operands)}")
        rd, rs1, imm = operands[0], operands[1], operands[2]
        
    elif format_type == "I_MEM":
        operands = operands_str.split(",")
        if len(operands) != 2 or "(" not in operands[1] or not operands[1].endswith(")"):
            raise ValueError("Invalid syntax for memory instruction, expected format: rd, imm(rs1)")
        rd = operands[0]
        mem_op = operands[1].split("(")
        imm = mem_op[0]
        rs1 = mem_op[1].strip(")")
        format_type = "I"
        
    elif format_type == "S":
        operands = operands_str.split(",")
        if len(operands) != 2 or "(" not in operands[1] or not operands[1].endswith(")"):
            raise ValueError("Invalid syntax for memory instruction, expected format: rs2, imm(rs1)")
        rs2 = operands[0]
        mem_op = operands[1].split("(")
        imm = mem_op[0]
        rs1 = mem_op[1].strip(")")
        
    elif format_type == "B":
        operands = operands_str.split(",")
        if len(operands) != 3:
            raise ValueError(f"Invalid operand count for B-type: expected 3, got {len(operands)}")
        rs1, rs2, imm = operands[0], operands[1], operands[2]

    return ParsedInstruction(
        mnemonic=mnemonic, format_type=format_type, rd=rd, rs1=rs1, rs2=rs2, imm=imm
    )


def encode_instruction(instruction: str) -> int:
    """
    Receives an instruction as text, e.g. "add x5, x6, x7", and returns
    its 32-bit encoding as an integer.
    """
    # TODO: implement.
    raise NotImplementedError("encode_instruction: pending implementation")


def explain_instruction(instruction: str, word: int) -> str:
    """
    Returns text visually showing the 32 bits of 'word' divided into
    fields of the corresponding format (R, I, S, or B).
    """
    # TODO: implement.
    raise NotImplementedError("explain_instruction: pending implementation")


def main():
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} "<instruction>"', file=sys.stderr)
        print(f'Example: {sys.argv[0]} "add x5, x6, x7"', file=sys.stderr)
        sys.exit(2)

    instruction = sys.argv[1]
    word = encode_instruction(instruction) & 0xFFFFFFFF

    print(explain_instruction(instruction, word))

    # Do not modify the following line format.
    print(f"HEX: 0x{word:08x}")


if __name__ == "__main__":
    main()
