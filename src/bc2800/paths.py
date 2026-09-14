from __future__ import annotations

import sys
from pathlib import Path


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def data_dir() -> Path:
    path = app_root() / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def logs_dir() -> Path:
    path = app_root() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def backup_dir() -> Path:
    path = data_dir() / "backup"
    path.mkdir(parents=True, exist_ok=True)
    return path


def sqlite_path() -> Path:
    return data_dir() / "bc2800.sqlite"


def default_excel_path() -> Path:
    return data_dir() / "exames.xlsx"


def config_path() -> Path:
    return data_dir() / "config.json"


def lock_path() -> Path:
    return data_dir() / "bc2800.lock"
