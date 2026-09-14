from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from bc2800.paths import logs_dir

_LOG = logging.getLogger("bc2800")


def setup_logging() -> None:
    logs_dir()
    app_log = logs_dir() / "app.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(app_log, encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )


def dump_frame(body: bytes, kind: str) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    path = logs_dir() / f"{stamp}-{kind}.bin"
    path.write_bytes(body)
    hex_path = logs_dir() / f"{stamp}-{kind}.hex"
    hex_path.write_text(body.hex(" "), encoding="utf-8")
    return path
