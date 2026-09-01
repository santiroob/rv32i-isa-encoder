"""
Educational RISC-V Instruction Encoder Skeleton.
CE4301 Computer Architecture I — 2026-IIS

This skeleton implements the command-line and output contract required by
the specification. You must complete the two functions marked with TODO.
"""

import sys
from dataclasses import dataclass
from typing import Literal, TypedDict

EncodingFormat = Literal["R", "I", "S", "B"]
SyntaxFormat = Literal["R", "I", "I_MEM", "S", "B"]


class InstructionInfo(TypedDict):
    """Static encoding metadata for one supported instruction."""

    format: SyntaxFormat
    opcode: int
    funct3: int
    funct7: int | None


# Mapping of supported mnemonics to their respective formats and codes.
INSTRUCTION_MAP: dict[str, InstructionInfo] = {
    "add": {"format": "R", "opcode": 0x33, "funct3": 0x0, "funct7": 0x00},
    "sub": {"format": "R", "opcode": 0x33, "funct3": 0x0, "funct7": 0x20},
    "and": {"format": "R", "opcode": 0x33, "funct3": 0x7, "funct7": 0x00},
    "or": {"format": "R", "opcode": 0x33, "funct3": 0x6, "funct7": 0x00},
    "addi": {"format": "I", "opcode": 0x13, "funct3": 0x0, "funct7": None},
    "andi": {"format": "I", "opcode": 0x13, "funct3": 0x7, "funct7": None},
    "lw": {"format": "I_MEM", "opcode": 0x03, "funct3": 0x2, "funct7": None},
    "lb": {"format": "I_MEM", "opcode": 0x03, "funct3": 0x0, "funct7": None},
    "sw": {"format": "S", "opcode": 0x23, "funct3": 0x2, "funct7": None},
    "sb": {"format": "S", "opcode": 0x23, "funct3": 0x0, "funct7": None},
    "beq": {"format": "B", "opcode": 0x63, "funct3": 0x0, "funct7": None},
    "bne": {"format": "B", "opcode": 0x63, "funct3": 0x1, "funct7": None},
}


@dataclass
class ParsedInstruction:
    """Holds the results of parsing a RISC-V instruction."""

    mnemonic: str
    format_type: EncodingFormat
    rd: str | None
    rs1: str | None
    rs2: str | None
    imm: str | None


@dataclass
class ResolvedFields:
    """Holds the fully resolved integer values needed to assemble the 32-bit instruction."""

    opcode: int
    rd: int | None
    funct3: int
    rs1: int | None
    rs2: int | None
    funct7: int | None
    imm: int | None


def parse_instruction(instruction_str: str) -> ParsedInstruction:
    """
    Parses a raw assembly string, identifies the mnemonic, validates it,
    and extracts the registers and immediate value based on its format.
    """
    instruction_str = instruction_str.strip()
    if not instruction_str:
        raise ValueError("Instruction cannot be empty")

    parts = instruction_str.split(maxsplit=1)
    mnemonic = parts[0]
    operands_str = parts[1] if len(parts) > 1 else ""

    if mnemonic not in INSTRUCTION_MAP:
        raise ValueError(f"Unsupported instruction: {mnemonic}")

    syntax_format = INSTRUCTION_MAP[mnemonic]["format"]
    operands_str = "".join(operands_str.split())

    rd, rs1, rs2, imm = None, None, None, None
    format_type: EncodingFormat

    if syntax_format == "R":
        operands = operands_str.split(",")
        if len(operands) != 3:
            raise ValueError(
                f"Invalid operand count for R-type: expected 3, got {len(operands)}"
            )
        rd, rs1, rs2 = operands[0], operands[1], operands[2]
        format_type = "R"

    elif syntax_format == "I":
        operands = operands_str.split(",")
        if len(operands) != 3:
            raise ValueError(
                f"Invalid operand count for I-type: expected 3, got {len(operands)}"
            )
        rd, rs1, imm = operands[0], operands[1], operands[2]
        format_type = "I"

    elif syntax_format == "I_MEM":
        operands = operands_str.split(",")
        if len(operands) != 2:
            raise ValueError(
                "Invalid syntax for memory instruction, expected format: rd, imm(rs1)"
            )
        rd = operands[0]
        imm, rs1 = parse_memory_operand(operands[1])
        format_type = "I"

    elif syntax_format == "S":
        operands = operands_str.split(",")
        if len(operands) != 2:
            raise ValueError(
                "Invalid syntax for memory instruction, expected format: rs2, imm(rs1)"
            )
        rs2 = operands[0]
        imm, rs1 = parse_memory_operand(operands[1])
        format_type = "S"

    elif syntax_format == "B":
        operands = operands_str.split(",")
        if len(operands) != 3:
            raise ValueError(
                f"Invalid operand count for B-type: expected 3, got {len(operands)}"
            )
        rs1, rs2, imm = operands[0], operands[1], operands[2]
        format_type = "B"
    else:
        raise ValueError(f"Unhandled instruction format: {syntax_format}")

    return ParsedInstruction(
        mnemonic=mnemonic, format_type=format_type, rd=rd, rs1=rs1, rs2=rs2, imm=imm
    )


def parse_memory_operand(operand_str: str) -> tuple[str, str]:
    """
    Splits a memory operand of the form imm(rs1) into its immediate and base register.
    """
    if operand_str.count("(") != 1 or not operand_str.endswith(")"):
        raise ValueError("Invalid memory operand syntax, expected imm(rs1)")

    imm, rs1 = operand_str[:-1].split("(", 1)
    if not imm or not rs1:
        raise ValueError("Invalid memory operand syntax, expected imm(rs1)")

    return imm, rs1


def parse_register(reg_str: str | None) -> int | None:
    """
    Takes a register string (e.g., "x5") and returns its integer value (5).
    """
    if reg_str is None:
        return None
    if not reg_str.startswith("x") or not reg_str[1:].isdecimal():
        raise ValueError(f"Invalid register syntax: {reg_str}")

    reg_val = int(reg_str[1:])
    if not (0 <= reg_val <= 31):
        raise ValueError(f"Invalid register value: {reg_str}")
    return reg_val


def parse_immediate(imm_str: str | None) -> int | None:
    """
    Converts an immediate string to an integer.
    """
    if imm_str is None:
        return None
    return int(imm_str, 0)


def resolve_fields(parsed: ParsedInstruction) -> ResolvedFields:
    """
    Takes the string-based parsing result and translates all fields into their numeric integer equivalents.
    """
    inst_info = INSTRUCTION_MAP[parsed.mnemonic]

    return ResolvedFields(
        opcode=inst_info["opcode"],
        rd=parse_register(parsed.rd),
        funct3=inst_info["funct3"],
        rs1=parse_register(parsed.rs1),
        rs2=parse_register(parsed.rs2),
        funct7=inst_info["funct7"],
        imm=parse_immediate(parsed.imm),
    )


def require_field(field_name: str, value: int | None) -> int:
    """
    Returns a required numeric field or raises an error if it is missing.
    """
    if value is None:
        raise ValueError(f"Missing required field: {field_name}")
    return value


def encode_signed_immediate(imm: int, bit_count: int) -> int:
    """
    Validates a signed immediate and returns its two's-complement representation.
    """
    min_value = -(1 << (bit_count - 1))
    max_value = (1 << (bit_count - 1)) - 1

    if not (min_value <= imm <= max_value):
        raise ValueError(
            f"Immediate out of range for {bit_count}-bit signed value: {imm}"
        )

    return imm & ((1 << bit_count) - 1)


def encode_branch_immediate(imm: int) -> int:
    """
    Validates a branch offset and returns its 13-bit two's-complement value.
    """
    if not (-4096 <= imm <= 4094):
        raise ValueError(f"Branch immediate out of range: {imm}")
    if imm % 2 != 0:
        raise ValueError(f"Branch immediate must be even: {imm}")

    return imm & 0x1FFF


def encode_instruction(instruction: str) -> int:
    """
    Receives an instruction as text, e.g. "add x5, x6, x7", and returns
    its 32-bit encoding as an integer.
    """
    parsed = parse_instruction(instruction)
    resolved = resolve_fields(parsed)

    if parsed.format_type == "R":
        rd = require_field("rd", resolved.rd)
        rs1 = require_field("rs1", resolved.rs1)
        rs2 = require_field("rs2", resolved.rs2)
        funct7 = require_field("funct7", resolved.funct7)

        return (
            (funct7 << 25)
            | (rs2 << 20)
            | (rs1 << 15)
            | (resolved.funct3 << 12)
            | (rd << 7)
            | resolved.opcode
        )

    if parsed.format_type == "I":
        rd = require_field("rd", resolved.rd)
        rs1 = require_field("rs1", resolved.rs1)
        imm = encode_signed_immediate(require_field("imm", resolved.imm), 12)

        return (
            (imm << 20)
            | (rs1 << 15)
            | (resolved.funct3 << 12)
            | (rd << 7)
            | resolved.opcode
        )

    if parsed.format_type == "S":
        rs1 = require_field("rs1", resolved.rs1)
        rs2 = require_field("rs2", resolved.rs2)
        imm = encode_signed_immediate(require_field("imm", resolved.imm), 12)
        imm_11_5 = (imm >> 5) & 0x7F
        imm_4_0 = imm & 0x1F

        return (
            (imm_11_5 << 25)
            | (rs2 << 20)
            | (rs1 << 15)
            | (resolved.funct3 << 12)
            | (imm_4_0 << 7)
            | resolved.opcode
        )

    if parsed.format_type == "B":
        rs1 = require_field("rs1", resolved.rs1)
        rs2 = require_field("rs2", resolved.rs2)
        imm = encode_branch_immediate(require_field("imm", resolved.imm))
        imm_12 = (imm >> 12) & 0x1
        imm_10_5 = (imm >> 5) & 0x3F
        imm_4_1 = (imm >> 1) & 0xF
        imm_11 = (imm >> 11) & 0x1

        return (
            (imm_12 << 31)
            | (imm_10_5 << 25)
            | (rs2 << 20)
            | (rs1 << 15)
            | (resolved.funct3 << 12)
            | (imm_4_1 << 8)
            | (imm_11 << 7)
            | resolved.opcode
        )

    raise ValueError(f"Unsupported encoding format: {parsed.format_type}")


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

    # print(explain_instruction(instruction, word))

    # Do not modify the following line format.
    print(f"HEX: 0x{word:08x}")


if __name__ == "__main__":
    main()
