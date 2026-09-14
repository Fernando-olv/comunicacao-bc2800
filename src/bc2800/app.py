from __future__ import annotations

import os
import sys

from PySide6.QtCore import QLockFile
from PySide6.QtWidgets import QApplication, QMessageBox

from bc2800.config import load_config
from bc2800.logging_setup import setup_logging
from bc2800.paths import app_root, lock_path
from bc2800.persistence.sqlite_repo import SqliteRepo
from bc2800.ui.icons import ICON_WAIT, status_icon
from bc2800.ui.main_window import MainWindow


def main() -> int:
    os.chdir(app_root())
    setup_logging()

    app = QApplication(sys.argv)
    app.setApplicationName("BC-2800Vet Receptor")
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(status_icon(ICON_WAIT))

    lock = QLockFile(str(lock_path()))
    lock.setStaleLockTime(30_000)
    if not lock.tryLock(100):
        QMessageBox.information(
            None,
            "BC-2800Vet Receptor",
            "O receptor já está em execução (veja o ícone na bandeja).",
        )
        return 0

    cfg = load_config()
    repo = SqliteRepo()
    window = MainWindow(cfg, repo)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
