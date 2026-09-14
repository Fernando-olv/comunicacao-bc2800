from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from bc2800.paths import config_path, default_excel_path


@dataclass
class AppConfig:
    port: str = ""
    baudrate: int = 9600
    bytesize: int = 7
    parity: str = "N"
    stopbits: float = 1.0
    handshake: bool = True
    excel_path: str = ""
    autostart: bool = True

    def resolved_excel_path(self) -> Path:
        if self.excel_path.strip():
            return Path(self.excel_path)
        return default_excel_path()


def load_config() -> AppConfig:
    path = config_path()
    if not path.exists():
        cfg = AppConfig()
        save_config(cfg)
        return cfg
    raw = json.loads(path.read_text(encoding="utf-8"))
    allowed = {item.name for item in fields(AppConfig)}
    filtered = {key: value for key, value in raw.items() if key in allowed}
    return AppConfig(**filtered)


def save_config(cfg: AppConfig) -> None:
    path = config_path()
    path.write_text(json.dumps(asdict(cfg), indent=2), encoding="utf-8")
