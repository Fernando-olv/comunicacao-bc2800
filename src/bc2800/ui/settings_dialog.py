from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from bc2800.config import AppConfig
from bc2800.serial_io import available_ports


class SettingsDialog(QDialog):
    def __init__(self, cfg: AppConfig, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Configurações")
        self._cfg = cfg

        self.port = QComboBox()
        self.port.setEditable(True)
        self._reload_ports()
        self.port.setCurrentText(cfg.port)

        refresh = QPushButton("Atualizar")
        refresh.clicked.connect(self._reload_ports)
        port_row = QWidget()
        port_layout = QHBoxLayout(port_row)
        port_layout.setContentsMargins(0, 0, 0, 0)
        port_layout.addWidget(self.port, 1)
        port_layout.addWidget(refresh)

        self.baud = QComboBox()
        for value in (1200, 2400, 4800, 9600, 19200):
            self.baud.addItem(str(value), value)
        self.baud.setCurrentText(str(cfg.baudrate))

        self.bits = QComboBox()
        self.bits.addItem("7", 7)
        self.bits.addItem("8", 8)
        self.bits.setCurrentIndex(0 if cfg.bytesize == 7 else 1)

        self.parity = QComboBox()
        self.parity.addItem("Nenhuma", "N")
        self.parity.addItem("Par (Even)", "E")
        self.parity.addItem("Ímpar (Odd)", "O")
        index = max(0, self.parity.findData(cfg.parity.upper()))
        self.parity.setCurrentIndex(index)

        self.stop = QComboBox()
        self.stop.addItem("1", 1.0)
        self.stop.addItem("2", 2.0)
        self.stop.setCurrentIndex(0 if cfg.stopbits == 1 else 1)

        self.handshake = QCheckBox("Handshake ligado (ENQ/ACK)")
        self.handshake.setChecked(cfg.handshake)

        self.excel = QLineEdit(cfg.excel_path)
        self.excel.setPlaceholderText("data\\exames.xlsx (padrão)")
        browse = QPushButton("Procurar…")
        browse.clicked.connect(self._browse_excel)
        excel_row = QWidget()
        excel_layout = QHBoxLayout(excel_row)
        excel_layout.setContentsMargins(0, 0, 0, 0)
        excel_layout.addWidget(self.excel, 1)
        excel_layout.addWidget(browse)

        self.autostart = QCheckBox("Iniciar com o Windows (bandeja)")
        self.autostart.setChecked(cfg.autostart)

        form = QFormLayout()
        form.addRow("Porta COM", port_row)
        form.addRow("Baud", self.baud)
        form.addRow("Bits de dados", self.bits)
        form.addRow("Paridade", self.parity)
        form.addRow("Stop bits", self.stop)
        form.addRow("", self.handshake)
        form.addRow("Planilha Excel", excel_row)
        form.addRow("", self.autostart)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _reload_ports(self) -> None:
        current = self.port.currentText()
        self.port.clear()
        self.port.addItems(available_ports())
        if current:
            self.port.setCurrentText(current)

    def _browse_excel(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Planilha de exames",
            self.excel.text() or str(Path.cwd() / "data" / "exames.xlsx"),
            "Excel (*.xlsx)",
        )
        if path:
            self.excel.setText(path)

    def result_config(self) -> AppConfig:
        return AppConfig(
            port=self.port.currentText().strip(),
            baudrate=int(self.baud.currentData()),
            bytesize=int(self.bits.currentData()),
            parity=str(self.parity.currentData()),
            stopbits=float(self.stop.currentData()),
            handshake=self.handshake.isChecked(),
            excel_path=self.excel.text().strip(),
            autostart=self.autostart.isChecked(),
        )
