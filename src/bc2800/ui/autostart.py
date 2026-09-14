from __future__ import annotations

import sys
from pathlib import Path

if sys.platform != "win32":
    def launch_command() -> str:
        return f'"{sys.executable}" -m bc2800'

    def is_enabled() -> bool:
        return False

    def set_enabled(_enabled: bool) -> None:
        return
else:
    import winreg

    _NAME = "BC2800Receptor"
    _KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

    def launch_command() -> str:
        if getattr(sys, "frozen", False):
            return f'"{sys.executable}"'
        python = Path(sys.executable)
        pythonw = python.with_name("pythonw.exe")
        if python.name.lower() == "python.exe" and pythonw.exists():
            python = pythonw
        return f'"{python}" -m bc2800'

    def is_enabled() -> bool:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _KEY) as key:
                value, _ = winreg.QueryValueEx(key, _NAME)
            return bool(value)
        except OSError:
            return False

    def set_enabled(enabled: bool) -> None:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _KEY) as key:
            if enabled:
                winreg.SetValueEx(key, _NAME, 0, winreg.REG_SZ, launch_command())
            else:
                try:
                    winreg.DeleteValue(key, _NAME)
                except FileNotFoundError:
                    pass
