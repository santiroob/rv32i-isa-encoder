# Codificador educativo de instrucciones RISC-V RV32I

## 1. Descripción general

Este proyecto implementa una herramienta educativa que recibe una única
instrucción de un subconjunto RV32I implementado y produce su codificación de
32 bits. La salida incluye una explicación visual del formato, los campos
codificados, sus rangos de bits, sus valores binarios/decimales y una línea
procesable para validación por scripts:

```text
HEX: 0xXXXXXXXX
```

El punto de entrada principal del proyecto es:

```bash
./run.sh "<instruccion>"
```

Por ejemplo:

```bash
./run.sh "add x7, x20, x6"
```

## 2. Instrucciones soportadas

La herramienta soporta un subconjunto de 12 instrucciones de RISC-V RV32I. Los
campos fijos `opcode`, `funct3` y `funct7` se tomaron del manual oficial de la
ISA RISC-V para RV32I y se corroboraron ensamblando casos con
`riscv64-unknown-elf-gcc` y leyendo la palabra resultante con
`riscv64-unknown-elf-objdump -d`.

| Categoría | Formato | Instrucción | Sintaxis aceptada | opcode | funct3 | funct7 |
|---|---|---|---|---:|---:|---:|
| Aritmética registro-registro | R | `add` | `add rd, rs1, rs2` | `0x33` / `0110011` | `0x0` / `000` | `0x00` / `0000000` |
| Aritmética registro-registro | R | `sub` | `sub rd, rs1, rs2` | `0x33` / `0110011` | `0x0` / `000` | `0x20` / `0100000` |
| Aritmética registro-registro | R | `and` | `and rd, rs1, rs2` | `0x33` / `0110011` | `0x7` / `111` | `0x00` / `0000000` |
| Aritmética registro-registro | R | `or` | `or rd, rs1, rs2` | `0x33` / `0110011` | `0x6` / `110` | `0x00` / `0000000` |
| Aritmética con inmediato | I | `addi` | `addi rd, rs1, imm` | `0x13` / `0010011` | `0x0` / `000` | No aplica |
| Aritmética con inmediato | I | `andi` | `andi rd, rs1, imm` | `0x13` / `0010011` | `0x7` / `111` | No aplica |
| Carga desde memoria | I | `lw` | `lw rd, imm(rs1)` | `0x03` / `0000011` | `0x2` / `010` | No aplica |
| Carga desde memoria | I | `lb` | `lb rd, imm(rs1)` | `0x03` / `0000011` | `0x0` / `000` | No aplica |
| Almacenamiento en memoria | S | `sw` | `sw rs2, imm(rs1)` | `0x23` / `0100011` | `0x2` / `010` | No aplica |
| Almacenamiento en memoria | S | `sb` | `sb rs2, imm(rs1)` | `0x23` / `0100011` | `0x0` / `000` | No aplica |
| Salto condicional | B | `beq` | `beq rs1, rs2, imm` | `0x63` / `1100011` | `0x0` / `000` | No aplica |
| Salto condicional | B | `bne` | `bne rs1, rs2, imm` | `0x63` / `1100011` | `0x1` / `001` | No aplica |

Los registros aceptados van de `x0` a `x31`. Los inmediatos de formatos `I` y
`S` se validan como enteros con signo de 12 bits, en el rango `-2048` a `2047`.
Los saltos de formato `B` aceptan desplazamientos pares en bytes, en el rango
`-4096` a `4094`; el bit menos significativo del desplazamiento es implícito.

## 3. Obtención de campos de codificación

El codificador separa dos tipos de información:

- Campos fijos por instrucción: `opcode`, `funct3` y, cuando aplica, `funct7`.
- Campos variables recibidos en la instrucción: registros e inmediato.

Los campos fijos se almacenan en `INSTRUCTION_MAP`. Los campos variables se
obtienen al analizar la sintaxis de cada formato y convertir `xN` a su valor
numérico `N`. Los inmediatos negativos se codifican en complemento a dos antes
de insertarse en la palabra de 32 bits.

La construcción de la palabra sigue estos formatos:

| Formato | Distribución de bits de 31 a 0 |
|---|---|
| R | `funct7[31:25] rs2[24:20] rs1[19:15] funct3[14:12] rd[11:7] opcode[6:0]` |
| I | `imm[11:0][31:20] rs1[19:15] funct3[14:12] rd[11:7] opcode[6:0]` |
| S | `imm[11:5][31:25] rs2[24:20] rs1[19:15] funct3[14:12] imm[4:0][11:7] opcode[6:0]` |
| B | `imm[12][31] imm[10:5][30:25] rs2[24:20] rs1[19:15] funct3[14:12] imm[4:1][11:8] imm[11][7] opcode[6:0]` |

## 4. Arquitectura del código

El proyecto se mantiene deliberadamente pequeño para que el flujo sea fácil de
auditar durante la revisión.

| Archivo | Responsabilidad |
|---|---|
| `run.sh` | Punto de entrada fijo. Recibe una instrucción como único argumento e invoca `encoder.py`. |
| `encoder.py` | Implementa el parser, la resolución de campos, la codificación binaria y la salida explicativa. |
| `check_vectors.py` | Ejecuta 36 casos contra el toolchain oficial y compara el `HEX` de `run.sh` contra `objdump`. |

El flujo principal de `encoder.py` es:

1. `parse_instruction` identifica el mnemónico y extrae operandos según la
   sintaxis del formato.
2. `resolve_fields` convierte registros e inmediatos a enteros y agrega los
   campos fijos desde `INSTRUCTION_MAP`.
3. `encode_instruction` arma la palabra de 32 bits con desplazamientos y OR
   bit a bit.
4. `explain_instruction` crea la salida visual: formato, binario agrupado,
   tabla de campos y descripción textual.
5. `main` imprime la explicación y conserva la línea exacta `HEX: 0x........`
   para scripts de validación.

## 5. Instalación del toolchain usado

Para validar este proyecto se usó GNU RISC-V toolchain con los
binarios `riscv64-unknown-elf-gcc` y `riscv64-unknown-elf-objdump` disponibles
en el `PATH`.

En este entorno de macOS se instaló con Homebrew:

```bash
brew install riscv-gnu-toolchain
```

Verificación local del toolchain usado:

```bash
riscv64-unknown-elf-gcc --version
riscv64-unknown-elf-objdump --version
```

Versiones usadas en la validación:

```text
riscv64-unknown-elf-gcc (g6afcc4f6d) 16.1.0
GNU objdump (GNU Binutils) 2.46
```

El script de comparación ensambla cada caso con:

```bash
riscv64-unknown-elf-gcc -march=rv32i -mabi=ilp32 -c case.s -o case.o
riscv64-unknown-elf-objdump -d case.o
```

## 6. Preparación y ejecución de la herramienta

La herramienta no requiere paquetes externos de Python. Solo se necesita:

- Python 3.10 o superior, por el uso de anotaciones como `int | None`.
- Permiso de ejecución sobre `run.sh`.

Preparación mínima:

```bash
python3 --version
chmod +x run.sh
```

La invocación usada por los scripts de prueba es:

```bash
./run.sh "<instruccion>"
```

Ejemplo:

```bash
./run.sh "lw x29, 8(x30)"
```

### 6.1. macOS

En macOS se puede ejecutar directamente desde Terminal, siempre que `python3`
esté instalado y `run.sh` tenga permiso de ejecución:

```bash
cd /ruta/al/proyecto
chmod +x run.sh
./run.sh "add x7, x20, x6"
```

Para ejecutar también la comparación contra el toolchain oficial, el toolchain
usado localmente se instaló con Homebrew:

```bash
brew install riscv-gnu-toolchain
python3 check_vectors.py
```

### 6.2. Ubuntu

En Ubuntu se instala Python, Bash y el toolchain RISC-V desde `apt`. Los
paquetes `gcc-riscv64-unknown-elf` y `binutils-riscv64-unknown-elf` proveen los
comandos `riscv64-unknown-elf-gcc` y `riscv64-unknown-elf-objdump`.

```bash
sudo apt update
sudo apt install python3 bash gcc-riscv64-unknown-elf binutils-riscv64-unknown-elf
cd /ruta/al/proyecto
chmod +x run.sh
./run.sh "add x7, x20, x6"
python3 check_vectors.py
```

Si `apt` no encuentra esos paquetes, se debe habilitar el repositorio `universe`
de Ubuntu y volver a ejecutar `sudo apt update`.

### 6.3. Windows

En Windows se recomienda usar WSL con Ubuntu, porque el proyecto se invoca con
`./run.sh` y depende de Bash. Desde PowerShell como administrador:

```powershell
wsl --install -d Ubuntu
```

Después de reiniciar y abrir Ubuntu en WSL, se prepara igual que en Ubuntu:

```bash
sudo apt update
sudo apt install python3 bash gcc-riscv64-unknown-elf binutils-riscv64-unknown-elf
cd /mnt/c/Users/<usuario>/ruta/al/proyecto
chmod +x run.sh
./run.sh "add x7, x20, x6"
python3 check_vectors.py
```

También se puede copiar el proyecto al sistema de archivos de WSL y entrar con
`cd ~/ProyectoIndividual`. Lo importante para ejecutar el proyecto es que el comando
`./run.sh "<instruccion>"` funcione dentro de una terminal con Bash y `python3`
disponibles.

## 7. Ejemplos de salida explicativa

La salida real se presenta en una ventana ANSI azul en la terminal. Los ejemplos
siguientes muestran el mismo contenido en forma compacta para que sea legible en
Markdown.

### 7.1. Formato R: `add x7, x20, x6`

```text
Codificador de instrucciones RISC-V RV32I
Instrucción : add x7, x20, x6
Formato     : tipo R
Binario     : 0000000 00110 10100 000 00111 0110011
Palabra     : 0x006a03b3

Tabla de campos:
funct7  [31:25] = 0000000 = 0   Distingue operaciones tipo R que comparten opcode y funct3.
rs2     [24:20] = 00110   = 6   Segundo registro leído por la operación.
rs1     [19:15] = 10100   = 20  Primer registro leído por la operación.
funct3  [14:12] = 000     = 0   Selecciona la operación exacta dentro del opcode.
rd      [11:7]  = 00111   = 7   Registro donde se escribe el resultado.
opcode  [6:0]   = 0110011 = 51  Familia principal de la instrucción.

HEX: 0x006a03b3
```

### 7.2. Formato I: `addi x5, x25, 2035`

```text
Codificador de instrucciones RISC-V RV32I
Instrucción : addi x5, x25, 2035
Formato     : tipo I
Binario     : 011111110011 11001 000 00101 0010011
Palabra     : 0x7f3c8293

Tabla de campos:
imm[11:0] [31:20] = 011111110011 = 2035 Constante con signo usada como segundo operando.
rs1       [19:15] = 11001        = 25   Registro fuente leído por la operación.
funct3    [14:12] = 000          = 0    Selecciona la operación aritmética o carga.
rd        [11:7]  = 00101        = 5    Registro donde se escribe el resultado.
opcode    [6:0]   = 0010011      = 19   Familia principal de la instrucción.

HEX: 0x7f3c8293
```

### 7.3. Formato S: `sw x31, -411(x23)`

```text
Codificador de instrucciones RISC-V RV32I
Instrucción : sw x31, -411(x23)
Formato     : tipo S
Binario     : 1110011 11111 10111 010 00101 0100011
Palabra     : 0xe7fba2a3

Tabla de campos:
imm[11:5] [31:25] = 1110011 = 115 Parte alta del desplazamiento con signo.
rs2       [24:20] = 11111   = 31  Registro cuyo valor se escribe en memoria.
rs1       [19:15] = 10111   = 23  Registro base para calcular la dirección.
funct3    [14:12] = 010     = 2   Selecciona el tamaño del dato almacenado.
imm[4:0]  [11:7]  = 00101   = 5   Parte baja del desplazamiento con signo.
opcode    [6:0]   = 0100011 = 35  Familia principal de la instrucción.

HEX: 0xe7fba2a3
```

### 7.4. Formato B: `beq x30, x4, -80`

```text
Codificador de instrucciones RISC-V RV32I
Instrucción : beq x30, x4, -80
Formato     : tipo B
Binario     : 1 111101 00100 11110 000 1000 1 1100011
Palabra     : 0xfa4f08e3

Tabla de campos:
imm[12]   [31]    = 1       = 1  Signo del desplazamiento relativo.
imm[10:5] [30:25] = 111101  = 61 Parte media alta del desplazamiento.
rs2       [24:20] = 00100   = 4  Segundo registro usado en la comparación.
rs1       [19:15] = 11110   = 30 Primer registro usado en la comparación.
funct3    [14:12] = 000     = 0  Selecciona la condición evaluada.
imm[4:1]  [11:8]  = 1000    = 8  Parte baja; el bit 0 es implícito.
imm[11]   [7]     = 1       = 1  Completa el desplazamiento relativo.
opcode    [6:0]   = 1100011 = 99 Familia principal de la instrucción.

HEX: 0xfa4f08e3
```

## 8. Evidencia de comparación contra herramienta oficial

La validación se ejecutó con:

```bash
python3 check_vectors.py
```

Resultado:

```text
Summary: 36 passed, 0 failed, 36 total
```

`check_vectors.py` no guarda los valores esperados de forma fija. Para cada
caso genera un archivo assembly temporal, lo ensambla con el toolchain oficial,
extrae la palabra con `objdump -d`, ejecuta `./run.sh "<instruccion>"` y compara
ambas salidas hexadecimales.

Para `beq` y `bne`, el ensamblador oficial recibe una etiqueta `target` ubicada
a la distancia pedida por el inmediato numérico. Esto permite comparar el
desplazamiento de branch contra la codificación generada por la herramienta.

| # | Caso | Instrucción | Escenario probado | `objdump` | `run.sh` | Coincide |
|---:|---|---|---|---:|---:|:---:|
| 1 | `add/base` | `add x7, x20, x6` | Operación R normal con registros intermedios. | `0x006a03b3` | `0x006a03b3` | Sí |
| 2 | `add/x0` | `add x0, x0, x0` | Uso de `x0` como destino y como ambas fuentes. | `0x00000033` | `0x00000033` | Sí |
| 3 | `add/limit-registers` | `add x31, x31, x30` | Límite superior de registros válidos en `rd`, `rs1` y `rs2`. | `0x01ef8fb3` | `0x01ef8fb3` | Sí |
| 4 | `sub/base` | `sub x5, x7, x18` | Operación R normal con `funct7` específico de resta. | `0x412382b3` | `0x412382b3` | Sí |
| 5 | `sub/x0` | `sub x0, x31, x1` | Destino `x0` con mezcla de registro alto y bajo. | `0x401f8033` | `0x401f8033` | Sí |
| 6 | `sub/limit-registers` | `sub x31, x0, x31` | Registros extremos válidos y codificación de resta. | `0x41f00fb3` | `0x41f00fb3` | Sí |
| 7 | `and/base` | `and x25, x16, x22` | Operación lógica R con registros intermedios-altos. | `0x01687cb3` | `0x01687cb3` | Sí |
| 8 | `and/x0` | `and x0, x1, x2` | Operación lógica con destino `x0`. | `0x0020f033` | `0x0020f033` | Sí |
| 9 | `and/limit-registers` | `and x31, x31, x0` | Registro máximo y registro cero en formato R. | `0x000fffb3` | `0x000fffb3` | Sí |
| 10 | `or/base` | `or x18, x29, x9` | Operación lógica R normal para `or`. | `0x009ee933` | `0x009ee933` | Sí |
| 11 | `or/x0` | `or x0, x0, x31` | `x0` como fuente/destino y `x31` como fuente alta. | `0x01f06033` | `0x01f06033` | Sí |
| 12 | `or/limit-registers` | `or x31, x1, x30` | Registro destino máximo con fuentes válidas mixtas. | `0x01e0efb3` | `0x01e0efb3` | Sí |
| 13 | `addi/positive` | `addi x5, x25, 2035` | Inmediato positivo cercano al límite superior de 12 bits. | `0x7f3c8293` | `0x7f3c8293` | Sí |
| 14 | `addi/negative` | `addi x10, x1, -12` | Inmediato negativo codificado en complemento a dos. | `0xff408513` | `0xff408513` | Sí |
| 15 | `addi/limit` | `addi x31, x0, -2048` | Límite inferior de inmediato con signo de 12 bits. | `0x80000f93` | `0x80000f93` | Sí |
| 16 | `andi/positive` | `andi x8, x3, 127` | Inmediato positivo en operación lógica tipo I. | `0x07f1f413` | `0x07f1f413` | Sí |
| 17 | `andi/negative` | `andi x30, x1, -209` | Inmediato negativo en operación lógica tipo I. | `0xf2f0ff13` | `0xf2f0ff13` | Sí |
| 18 | `andi/limit` | `andi x27, x30, 2047` | Límite superior de inmediato con signo de 12 bits. | `0x7fff7d93` | `0x7fff7d93` | Sí |
| 19 | `lw/positive` | `lw x29, 8(x30)` | Carga con desplazamiento positivo pequeño. | `0x008f2e83` | `0x008f2e83` | Sí |
| 20 | `lw/negative` | `lw x30, -1049(x14)` | Carga con desplazamiento negativo. | `0xbe772f03` | `0xbe772f03` | Sí |
| 21 | `lw/limit` | `lw x31, -2048(x0)` | Límite inferior del offset de memoria tipo I. | `0x80002f83` | `0x80002f83` | Sí |
| 22 | `lb/positive` | `lb x2, 1705(x9)` | Carga de byte con desplazamiento positivo grande. | `0x6a948103` | `0x6a948103` | Sí |
| 23 | `lb/negative` | `lb x25, -389(x27)` | Carga de byte con desplazamiento negativo. | `0xe7bd8c83` | `0xe7bd8c83` | Sí |
| 24 | `lb/limit` | `lb x31, 2047(x0)` | Límite superior del offset de memoria tipo I. | `0x7ff00f83` | `0x7ff00f83` | Sí |
| 25 | `sw/positive` | `sw x16, 1774(x31)` | Store word con inmediato positivo dividido en dos campos. | `0x6f0fa723` | `0x6f0fa723` | Sí |
| 26 | `sw/negative` | `sw x31, -411(x23)` | Store word con inmediato negativo dividido en dos campos. | `0xe7fba2a3` | `0xe7fba2a3` | Sí |
| 27 | `sw/limit` | `sw x31, -2048(x0)` | Límite inferior del inmediato tipo S. | `0x81f02023` | `0x81f02023` | Sí |
| 28 | `sb/positive` | `sb x18, 1701(x20)` | Store byte con desplazamiento positivo grande. | `0x6b2a02a3` | `0x6b2a02a3` | Sí |
| 29 | `sb/negative` | `sb x6, -72(x28)` | Store byte con desplazamiento negativo. | `0xfa6e0c23` | `0xfa6e0c23` | Sí |
| 30 | `sb/limit` | `sb x31, 2047(x0)` | Límite superior del inmediato tipo S. | `0x7ff00fa3` | `0x7ff00fa3` | Sí |
| 31 | `beq/positive` | `beq x31, x23, 16` | Branch positivo con inmediato par. | `0x017f8863` | `0x017f8863` | Sí |
| 32 | `beq/negative` | `beq x30, x4, -80` | Branch negativo con bit de signo activo. | `0xfa4f08e3` | `0xfa4f08e3` | Sí |
| 33 | `beq/zero` | `beq x0, x0, 0` | Desplazamiento cero y comparación entre `x0`. | `0x00000063` | `0x00000063` | Sí |
| 34 | `bne/positive` | `bne x5, x0, 60` | Branch positivo comparando contra `x0`. | `0x02029e63` | `0x02029e63` | Sí |
| 35 | `bne/negative` | `bne x12, x15, -16` | Branch negativo pequeño. | `0xfef618e3` | `0xfef618e3` | Sí |
| 36 | `bne/limit` | `bne x31, x31, 4092` | Valor positivo cercano al límite superior del branch. | `0x7fff9ee3` | `0x7fff9ee3` | Sí |

## 9. Validaciones de entradas inválidas

Además de comparar instrucciones válidas contra el toolchain oficial, se
probaron entradas inválidas para confirmar que el parser rechaza instrucciones
fuera del subconjunto, operandos mal formados y valores que no caben en los
campos de codificación.

| # | Entrada | Escenario probado | Resultado esperado |
|---:|---|---|---|
| 1 | `add x32, x1, x2` | Registro fuera del rango válido: `x32` es uno mayor que `x31`. | Error: `Valor inválido de registro: x32` |
| 2 | `addi x1, x2, 2048` | Inmediato tipo I por encima del máximo de 12 bits con signo. | Error: `Inmediato fuera de rango para valor con signo de 12 bits: 2048` |
| 3 | `sw x1, 2048(x2)` | Offset tipo S por encima del máximo representable. | Error: `Inmediato fuera de rango para valor con signo de 12 bits: 2048` |
| 4 | `beq x1, x2, 3` | Branch con desplazamiento impar; el bit 0 debe ser implícito. | Error: `El inmediato de salto debe ser par: 3` |
| 5 | `beq x1, x2, 4096` | Branch por encima del rango soportado. | Error: `Inmediato de salto fuera de rango: 4096` |
| 6 | `mul x1, x2, x3` | Instrucción inexistente en el subconjunto implementado. | Error: `Instrucción no soportada: mul` |
| 7 | `add x1, x2` | Formato R incorrecto, faltan operandos. | Error: `Cantidad inválida de operandos para tipo R: se esperaban 3, se recibieron 2` |
| 8 | `lw x1, 4x2` | Operando de memoria sin la forma `imm(rs1)`. | Error: `Sintaxis inválida de operando de memoria, se esperaba imm(rs1)` |

## 10. Referencias

- Andrew Waterman y Krste Asanović. *The RISC-V Instruction Set Manual,
  Volume I: User-Level ISA, Document Version 20191213*. RISC-V Foundation,
  2019.
- GNU RISC-V toolchain usado localmente:
  `riscv64-unknown-elf-gcc` y `riscv64-unknown-elf-objdump`.
- Documentación de WSL de Microsoft:
  <https://learn.microsoft.com/windows/wsl/install>.
- Paquetes de Ubuntu:
  <https://packages.ubuntu.com/search?keywords=gcc-riscv64-unknown-elf> y
  <https://packages.ubuntu.com/search?keywords=binutils-riscv64-unknown-elf>.
