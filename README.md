# Codificador educativo RISC-V RV32I

Herramienta educativa que codifica una instrucción individual de un subconjunto
de 12 instrucciones RISC-V RV32I. El programa muestra la palabra de 32 bits, sus
campos y una línea `HEX: 0xXXXXXXXX` para comparaciones automatizadas.

La documentación técnica completa está en [documentation.md](documentation.md).

## Cómo correr el proyecto

El comando principal es el mismo en todos los entornos:

```bash
./run.sh "<instruccion>"
```

Ejemplo:

```bash
./run.sh "add x7, x20, x6"
```

## macOS

```bash
cd /ruta/al/proyecto
python3 --version
chmod +x run.sh
./run.sh "add x7, x20, x6"
```

Para correr la comparación contra el toolchain RISC-V:

```bash
brew install riscv-gnu-toolchain
python3 check_vectors.py
```

## Ubuntu

```bash
sudo apt update
sudo apt install python3 bash gcc-riscv64-unknown-elf binutils-riscv64-unknown-elf
cd /ruta/al/proyecto
chmod +x run.sh
./run.sh "add x7, x20, x6"
```

Para correr la comparación contra el toolchain RISC-V:

```bash
python3 check_vectors.py
```

Si Ubuntu no encuentra los paquetes del toolchain, habilite el repositorio
`universe` y vuelva a ejecutar `sudo apt update`.

## Windows

En Windows se recomienda usar WSL con Ubuntu, porque `run.sh` depende de Bash.
Desde PowerShell como administrador:

```powershell
wsl --install -d Ubuntu
```

Luego, dentro de Ubuntu en WSL:

```bash
sudo apt update
sudo apt install python3 bash gcc-riscv64-unknown-elf binutils-riscv64-unknown-elf
cd /mnt/c/Users/<usuario>/ruta/al/proyecto
chmod +x run.sh
./run.sh "add x7, x20, x6"
```

Para correr la comparación contra el toolchain RISC-V:

```bash
python3 check_vectors.py
```
