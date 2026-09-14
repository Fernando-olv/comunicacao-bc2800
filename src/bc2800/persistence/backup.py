from __future__ import annotations

import logging
import shutil
from datetime import date

from bc2800.paths import backup_dir, sqlite_path

_LOG = logging.getLogger("bc2800.backup")


def backup_if_needed() -> None:
    source = sqlite_path()
    if not source.exists():
        return
    dest = backup_dir() / f"bc2800-{date.today().isoformat()}.sqlite"
    if dest.exists():
        return
    shutil.copy2(source, dest)
    _LOG.info("Backup criado em %s", dest)
