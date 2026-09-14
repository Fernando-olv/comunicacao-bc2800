from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap


def status_icon(color: str) -> QIcon:
    pix = QPixmap(64, 64)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(color))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(6, 4, 52, 56)
    painter.setBrush(QColor("#1a3c44"))
    painter.drawEllipse(20, 18, 24, 28)
    painter.end()
    return QIcon(pix)


ICON_OK = "#2e8b57"
ICON_WAIT = "#1f4e5f"
ICON_ERR = "#c0392b"
