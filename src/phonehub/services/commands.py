from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass


@dataclass
class CommandResult:
    ok: bool
    output: str
    error: str = ""


def executable(name: str) -> str | None:
    return shutil.which(name)


def run_command(args: list[str], timeout: float = 5.0) -> CommandResult:
    try:
        result = subprocess.run(
            args, capture_output=True, text=True, timeout=timeout, check=False
        )
        output = (result.stdout or "").strip()
        error = (result.stderr or "").strip()
        return CommandResult(result.returncode == 0, output, error)
    except FileNotFoundError:
        return CommandResult(False, "", f"Comando não encontrado: {args[0]}")
    except subprocess.TimeoutExpired:
        return CommandResult(False, "", f"Tempo limite excedido: {args[0]}")
