from __future__ import annotations

from .commands import executable, run_command


def list_ios_devices() -> tuple[list[str], str]:
    if not executable("idevice_id"):
        return [], "libimobiledevice não instalado (comando idevice_id ausente)."
    result = run_command(["idevice_id", "-l"], timeout=5)
    if not result.ok and not result.output:
        return [], result.error or "Não foi possível consultar dispositivos iOS."
    return [line.strip() for line in result.output.splitlines() if line.strip()], result.error


def device_name(udid: str) -> str:
    if not executable("ideviceinfo"):
        return "iPhone/iPad"
    result = run_command(["ideviceinfo", "-u", udid, "-k", "DeviceName"], timeout=4)
    return result.output or "iPhone/iPad"
