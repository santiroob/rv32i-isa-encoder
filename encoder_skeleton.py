#!/usr/bin/env python3
"""
Educational RISC-V Instruction Encoder Skeleton.
CE4301 Computer Architecture I — 2026-IIS

This skeleton implements the command-line and output contract required by
the specification. You must complete the two functions marked with TODO.
"""

import sys
import textwrap
from dataclasses import dataclass
from typing import Literal, TypedDict

EncodingFormat = Literal["R", "I", "S", "B"]
SyntaxFormat = Literal["R", "I", "I_MEM", "S", "B"]
BOX_WIDTH = 78
CONTENT_WIDTH = BOX_WIDTH - 4
BG_BLUE = "\033[44m"
FG_WHITE = "\033[1;37m"
RESET = "\033[0m"


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
    """
    Holds the fully resolved integer values needed to assemble the 32-bit instruction.
    """

    opcode: int
    rd: int | None
    funct3: int
    rs1: int | None
    rs2: int | None
    funct7: int | None
    imm: int | None


@dataclass
class DisplayField:
    """Describes one visible field in the 32-bit instruction word."""

    bit_range: str
    name: str
    value: int
    width: int
    description: str
    decimal_value: int | None = None


def parse_instruction(instruction_str: str) -> ParsedInstruction:
    """
    Parses a raw assembly string, identifies the mnemonic, validates it,
    and extracts the registers and immediate value based on its format.
    """
    instruction_str = instruction_str.strip()
    if not instruction_str:
        raise ValueError("La instrucción no puede estar vacía")

    parts = instruction_str.split(maxsplit=1)
    mnemonic = parts[0]
    operands_str = parts[1] if len(parts) > 1 else ""

    if mnemonic not in INSTRUCTION_MAP:
        raise ValueError(f"Instrucción no soportada: {mnemonic}")

    syntax_format = INSTRUCTION_MAP[mnemonic]["format"]
    operands_str = "".join(operands_str.split())

    rd, rs1, rs2, imm = None, None, None, None
    format_type: EncodingFormat

    if syntax_format == "R":
        operands = operands_str.split(",")
        if len(operands) != 3:
            raise ValueError(
                f"Cantidad inválida de operandos para tipo R: "
                f"se esperaban 3, se recibieron {len(operands)}"
            )
        rd, rs1, rs2 = operands[0], operands[1], operands[2]
        format_type = "R"

    elif syntax_format == "I":
        operands = operands_str.split(",")
        if len(operands) != 3:
            raise ValueError(
                f"Cantidad inválida de operandos para tipo I: "
                f"se esperaban 3, se recibieron {len(operands)}"
            )
        rd, rs1, imm = operands[0], operands[1], operands[2]
        format_type = "I"

    elif syntax_format == "I_MEM":
        operands = operands_str.split(",")
        if len(operands) != 2:
            raise ValueError(
                "Sintaxis inválida para memoria, se esperaba: rd, imm(rs1)"
            )
        rd = operands[0]
        imm, rs1 = parse_memory_operand(operands[1])
        format_type = "I"

    elif syntax_format == "S":
        operands = operands_str.split(",")
        if len(operands) != 2:
            raise ValueError(
                "Sintaxis inválida para memoria, se esperaba: rs2, imm(rs1)"
            )
        rs2 = operands[0]
        imm, rs1 = parse_memory_operand(operands[1])
        format_type = "S"

    elif syntax_format == "B":
        operands = operands_str.split(",")
        if len(operands) != 3:
            raise ValueError(
                f"Cantidad inválida de operandos para tipo B: "
                f"se esperaban 3, se recibieron {len(operands)}"
            )
        rs1, rs2, imm = operands[0], operands[1], operands[2]
        format_type = "B"
    else:
        raise ValueError(f"Formato de instrucción no manejado: {syntax_format}")

    return ParsedInstruction(
        mnemonic=mnemonic, format_type=format_type, rd=rd, rs1=rs1, rs2=rs2, imm=imm
    )


def parse_memory_operand(operand_str: str) -> tuple[str, str]:
    """
    Splits a memory operand of the form imm(rs1) into its immediate and base register.
    """
    if operand_str.count("(") != 1 or not operand_str.endswith(")"):
        raise ValueError(
            "Sintaxis inválida de operando de memoria, se esperaba imm(rs1)"
        )

    imm, rs1 = operand_str[:-1].split("(", 1)
    if not imm or not rs1:
        raise ValueError(
            "Sintaxis inválida de operando de memoria, se esperaba imm(rs1)"
        )

    return imm, rs1


def parse_register(reg_str: str | None) -> int | None:
    """
    Takes a register string (e.g., "x5") and returns its integer value (5).
    """
    if reg_str is None:
        return None
    if not reg_str.startswith("x") or not reg_str[1:].isdecimal():
        raise ValueError(f"Sintaxis inválida de registro: {reg_str}")

    reg_val = int(reg_str[1:])
    if not (0 <= reg_val <= 31):
        raise ValueError(f"Valor inválido de registro: {reg_str}")
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
    Takes the string-based parsing result and translates all fields into
    their numeric integer equivalents.
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
        raise ValueError(f"Campo requerido faltante: {field_name}")
    return value


def encode_signed_immediate(imm: int, bit_count: int) -> int:
    """
    Validates a signed immediate and returns its two's-complement representation.
    """
    min_value = -(1 << (bit_count - 1))
    max_value = (1 << (bit_count - 1)) - 1

    if not (min_value <= imm <= max_value):
        raise ValueError(
            f"Inmediato fuera de rango para valor con signo de {bit_count} bits: {imm}"
        )

    return imm & ((1 << bit_count) - 1)


def encode_branch_immediate(imm: int) -> int:
    """
    Validates a branch offset and returns its 13-bit two's-complement value.
    """
    if not (-4096 <= imm <= 4094):
        raise ValueError(f"Inmediato de salto fuera de rango: {imm}")
    if imm % 2 != 0:
        raise ValueError(f"El inmediato de salto debe ser par: {imm}")

    return imm & 0x1FFF


def format_bits(value: int, width: int) -> str:
    """
    Formats a field value without a binary prefix.
    """
    return f"{value:0{width}b}"


def group_binary_fields(binary_word: str, field_widths: list[int]) -> str:
    """
    Groups the 32-bit word according to the current instruction format.
    """
    groups: list[str] = []
    start = 0

    for width in field_widths:
        end = start + width
        groups.append(binary_word[start:end])
        start = end

    return " ".join(groups)


def get_format_widths(format_type: EncodingFormat) -> list[int]:
    """
    Returns the visible field widths from bit 31 down to bit 0.
    """
    if format_type == "R":
        return [7, 5, 5, 3, 5, 7]
    if format_type == "I":
        return [12, 5, 3, 5, 7]
    if format_type == "S":
        return [7, 5, 5, 3, 5, 7]
    if format_type == "B":
        return [1, 6, 5, 5, 3, 4, 1, 7]

    raise ValueError(f"Formato visual no soportado: {format_type}")


def build_display_fields(
    parsed: ParsedInstruction, resolved: ResolvedFields
) -> list[DisplayField]:
    """
    Builds the field list used by the visual explanation.
    """
    if parsed.format_type == "R":
        rd = require_field("rd", resolved.rd)
        rs1 = require_field("rs1", resolved.rs1)
        rs2 = require_field("rs2", resolved.rs2)
        funct7 = require_field("funct7", resolved.funct7)

        return [
            DisplayField(
                "[31:25]",
                "funct7",
                funct7,
                7,
                "Distingue operaciones tipo R que comparten opcode y funct3.",
            ),
            DisplayField(
                "[24:20]",
                "rs2",
                rs2,
                5,
                "Identifica el segundo registro leído por la operación.",
            ),
            DisplayField(
                "[19:15]",
                "rs1",
                rs1,
                5,
                "Identifica el primer registro leído por la operación.",
            ),
            DisplayField(
                "[14:12]",
                "funct3",
                resolved.funct3,
                3,
                "Ayuda a seleccionar la operación exacta dentro del opcode.",
            ),
            DisplayField(
                "[11:7]",
                "rd",
                rd,
                5,
                "Identifica el registro donde se escribe el resultado.",
            ),
            DisplayField(
                "[6:0]",
                "opcode",
                resolved.opcode,
                7,
                "Indica al procesador la familia principal de la instrucción.",
            ),
        ]

    if parsed.format_type == "I":
        rd = require_field("rd", resolved.rd)
        rs1 = require_field("rs1", resolved.rs1)
        imm = require_field("imm", resolved.imm)
        encoded_imm = encode_signed_immediate(imm, 12)
        imm_description = (
            "Desplazamiento con signo usado para calcular la dirección de memoria."
            if parsed.mnemonic in {"lb", "lw"}
            else "Constante con signo usada como segundo operando de la operación."
        )
        rs1_description = (
            "Registro base usado para calcular la dirección de memoria."
            if parsed.mnemonic in {"lb", "lw"}
            else "Registro fuente leído por la operación."
        )

        return [
            DisplayField(
                "[31:20]",
                "imm[11:0]",
                encoded_imm,
                12,
                imm_description,
                imm,
            ),
            DisplayField("[19:15]", "rs1", rs1, 5, rs1_description),
            DisplayField(
                "[14:12]",
                "funct3",
                resolved.funct3,
                3,
                "Selecciona la operación aritmética o el tamaño de carga.",
            ),
            DisplayField(
                "[11:7]",
                "rd",
                rd,
                5,
                "Identifica el registro donde se escribe el resultado.",
            ),
            DisplayField(
                "[6:0]",
                "opcode",
                resolved.opcode,
                7,
                "Indica al procesador la familia principal de la instrucción.",
            ),
        ]

    if parsed.format_type == "S":
        rs1 = require_field("rs1", resolved.rs1)
        rs2 = require_field("rs2", resolved.rs2)
        imm = require_field("imm", resolved.imm)
        encoded_imm = encode_signed_immediate(imm, 12)
        imm_11_5 = (encoded_imm >> 5) & 0x7F
        imm_4_0 = encoded_imm & 0x1F

        return [
            DisplayField(
                "[31:25]",
                "imm[11:5]",
                imm_11_5,
                7,
                "Parte alta del desplazamiento con signo usado para la dirección.",
            ),
            DisplayField(
                "[24:20]",
                "rs2",
                rs2,
                5,
                "Identifica el registro cuyo valor se escribe en memoria.",
            ),
            DisplayField(
                "[19:15]",
                "rs1",
                rs1,
                5,
                "Identifica el registro base para calcular la dirección.",
            ),
            DisplayField(
                "[14:12]",
                "funct3",
                resolved.funct3,
                3,
                "Selecciona el tamaño del dato que se almacena.",
            ),
            DisplayField(
                "[11:7]",
                "imm[4:0]",
                imm_4_0,
                5,
                "Parte baja del desplazamiento con signo usado para la dirección.",
            ),
            DisplayField(
                "[6:0]",
                "opcode",
                resolved.opcode,
                7,
                "Indica al procesador la familia principal de la instrucción.",
            ),
        ]

    if parsed.format_type == "B":
        rs1 = require_field("rs1", resolved.rs1)
        rs2 = require_field("rs2", resolved.rs2)
        imm = require_field("imm", resolved.imm)
        encoded_imm = encode_branch_immediate(imm)
        imm_12 = (encoded_imm >> 12) & 0x1
        imm_10_5 = (encoded_imm >> 5) & 0x3F
        imm_4_1 = (encoded_imm >> 1) & 0xF
        imm_11 = (encoded_imm >> 11) & 0x1

        return [
            DisplayField(
                "[31]",
                "imm[12]",
                imm_12,
                1,
                "Contiene el signo del desplazamiento relativo del salto.",
            ),
            DisplayField(
                "[30:25]",
                "imm[10:5]",
                imm_10_5,
                6,
                "Parte media alta del desplazamiento relativo del salto.",
            ),
            DisplayField(
                "[24:20]",
                "rs2",
                rs2,
                5,
                "Identifica el segundo registro usado en la comparación.",
            ),
            DisplayField(
                "[19:15]",
                "rs1",
                rs1,
                5,
                "Identifica el primer registro usado en la comparación.",
            ),
            DisplayField(
                "[14:12]",
                "funct3",
                resolved.funct3,
                3,
                "Selecciona la condición evaluada por el salto.",
            ),
            DisplayField(
                "[11:8]",
                "imm[4:1]",
                imm_4_1,
                4,
                "Parte baja del desplazamiento; el bit menos significativo "
                "es implícito.",
            ),
            DisplayField(
                "[7]",
                "imm[11]",
                imm_11,
                1,
                "Completa el desplazamiento relativo junto con los otros campos imm.",
            ),
            DisplayField(
                "[6:0]",
                "opcode",
                resolved.opcode,
                7,
                "Indica al procesador la familia principal de la instrucción.",
            ),
        ]

    raise ValueError(f"Formato visual no soportado: {parsed.format_type}")


def build_field_table(fields: list[DisplayField]) -> list[str]:
    """
    Builds a compact table with field names, bits, and bit ranges.
    """
    widths = [
        max(
            len(field.name),
            len(format_bits(field.value, field.width)),
            len(field.bit_range),
        )
        for field in fields
    ]

    def make_border(left: str, separator: str, right: str) -> str:
        return left + separator.join("─" * width for width in widths) + right

    def make_row(values: list[str]) -> str:
        cells = [f"{value:^{widths[index]}}" for index, value in enumerate(values)]
        return "│" + "│".join(cells) + "│"

    return [
        make_border("┌", "┬", "┐"),
        make_row([field.name for field in fields]),
        make_border("├", "┼", "┤"),
        make_row([format_bits(field.value, field.width) for field in fields]),
        make_border("├", "┼", "┤"),
        make_row([field.bit_range for field in fields]),
        make_border("└", "┴", "┘"),
    ]


def field_to_lines(field: DisplayField) -> list[str]:
    """
    Formats one display field and wraps it to the terminal window width.
    """
    decimal_value = field.value if field.decimal_value is None else field.decimal_value
    text = (
        f"{field.name}: {field.description} "
        f"(valor decimal: {decimal_value})"
    )
    return textwrap.wrap(
        text,
        width=CONTENT_WIDTH,
        subsequent_indent=" " * (len(field.name) + 2),
        break_long_words=False,
    )


def render_window(lines: list[str]) -> str:
    """
    Renders the retro terminal window with ANSI colors.
    """
    top_border = "╔" + ("═" * (BOX_WIDTH - 2)) + "╗"
    bottom_border = "╚" + ("═" * (BOX_WIDTH - 2)) + "╝"
    rendered_lines = [top_border]

    for line in lines:
        if not line:
            rendered_lines.append("║" + (" " * (BOX_WIDTH - 2)) + "║")
            continue

        for wrapped_line in textwrap.wrap(
            line, width=CONTENT_WIDTH, break_long_words=False
        ):
            rendered_lines.append(f"║ {wrapped_line:<{CONTENT_WIDTH}} ║")

    rendered_lines.append(bottom_border)
    return "\n".join(f"{BG_BLUE}{FG_WHITE}{line}{RESET}" for line in rendered_lines)


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

    raise ValueError(f"Formato de codificación no soportado: {parsed.format_type}")


def explain_instruction(instruction: str, word: int) -> str:
    """
    Returns text visually showing the 32 bits of 'word' divided into
    fields of the corresponding format (R, I, S, or B).
    """
    parsed = parse_instruction(instruction)
    resolved = resolve_fields(parsed)
    normalized_word = word & 0xFFFFFFFF
    binary_word = f"{normalized_word:032b}"
    grouped_binary = group_binary_fields(
        binary_word, get_format_widths(parsed.format_type)
    )

    lines = [
        "Codificador de instrucciones RISC-V RV32I",
        f"Instrucción : {instruction}",
        f"Formato     : tipo {parsed.format_type}",
        f"Binario     : {grouped_binary}",
        f"Palabra     : 0x{normalized_word:08x}",
        "",
        "Tabla de campos (bit 31 a bit 0):",
    ]

    fields = build_display_fields(parsed, resolved)
    lines.extend(build_field_table(fields))
    lines.extend(["", "Descripción de campos:"])

    for field in fields:
        lines.extend(field_to_lines(field))

    return render_window(lines)


def main():
    if len(sys.argv) != 2:
        print(f'Uso: {sys.argv[0]} "<instrucción>"', file=sys.stderr)
        print(f'Ejemplo: {sys.argv[0]} "add x5, x6, x7"', file=sys.stderr)
        sys.exit(2)

    instruction = sys.argv[1]
    word = encode_instruction(instruction) & 0xFFFFFFFF

    print(explain_instruction(instruction, word))

    # Do not modify the following line format.
    print(f"HEX: 0x{word:08x}")


if __name__ == "__main__":
    main()
