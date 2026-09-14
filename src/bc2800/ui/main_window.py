from __future__ import annotations

import logging
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QCloseEvent, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QPushButton,
    QSystemTrayIcon,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from bc2800.config import AppConfig, save_config
from bc2800.domain.models import Exam, QcEvent
from bc2800.persistence.backup import backup_if_needed
from bc2800.persistence.excel_writer import ExcelLockedError, ExcelWriter
from bc2800.persistence.sqlite_repo import SqliteRepo
from bc2800.serial_io import SerialListener
from bc2800.ui import autostart
from bc2800.ui.icons import ICON_ERR, ICON_OK, ICON_WAIT, status_icon
from bc2800.ui.settings_dialog import SettingsDialog

_LOG = logging.getLogger("bc2800.ui")

_TABLE_HEADERS = [
    "Recebido",
    "Exame",
    "ID",
    "Espécie",
    "WBC",
    "RBC",
    "HGB",
    "PLT",
    "Nome do animal",
    "Tutor",
    "Observações",
]


def _fmt(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def _beep() -> None:
    try:
        import winsound

        winsound.Beep(880, 180)
    except Exception:
        QApplication.beep()


class CompletarDialog(QDialog):
    def __init__(self, exam: Exam, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Completar dados do exame")
        self.name = QLineEdit(exam.animal_name or "")
        self.tutor = QLineEdit(exam.tutor or "")
        self.notes = QTextEdit()
        self.notes.setPlainText(exam.notes or "")
        self.notes.setFixedHeight(90)
        form = QFormLayout()
        form.addRow("Nome do animal", self.name)
        form.addRow("Tutor", self.tutor)
        form.addRow("Observações", self.notes)
        save = QPushButton("Salvar")
        cancel = QPushButton("Cancelar")
        save.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(buttons)


class MainWindow(QMainWindow):
    def __init__(self, cfg: AppConfig, repo: SqliteRepo) -> None:
        super().__init__()
        self.cfg = cfg
        self.repo = repo
        self.excel = ExcelWriter(cfg.resolved_excel_path())
        self.listener = SerialListener(cfg)
        self._tray_hint_shown = False

        self.setWindowTitle("BC-2800Vet Receptor")
        self.setMinimumSize(1080, 680)
        self.setWindowIcon(status_icon(ICON_WAIT))

        self.status = QLabel("Iniciando…")
        self.status.setObjectName("statusLine")
        self.pending = QLabel("")
        self.pending.setObjectName("pendingBadge")

        self.last_id = QLabel("—")
        self.last_species = QLabel("—")
        self.last_when = QLabel("—")
        self.last_wbc = QLabel("—")
        self.last_rbc = QLabel("—")
        self.last_hgb = QLabel("—")
        self.last_plt = QLabel("—")
        for label in (
            self.last_id,
            self.last_species,
            self.last_when,
            self.last_wbc,
            self.last_rbc,
            self.last_hgb,
            self.last_plt,
        ):
            label.setProperty("class", "metric")
            font = QFont()
            font.setPointSize(14)
            font.setBold(True)
            label.setFont(font)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Filtrar por ID, nome, tutor…")
        self.search.textChanged.connect(self.refresh_table)

        sync = QPushButton("Sincronizar planilha")
        sync.clicked.connect(self.flush_excel)
        settings = QPushButton("Configurações")
        settings.clicked.connect(self.open_settings)

        header = QHBoxLayout()
        header.addWidget(self.status, 1)
        header.addWidget(self.pending)
        header.addWidget(sync)
        header.addWidget(settings)

        cards = QHBoxLayout()
        for title, widget in (
            ("ID", self.last_id),
            ("Espécie", self.last_species),
            ("Data/hora", self.last_when),
            ("WBC", self.last_wbc),
            ("RBC", self.last_rbc),
            ("HGB", self.last_hgb),
            ("PLT", self.last_plt),
        ):
            cards.addWidget(self._card(title, widget))

        self.table = QTableWidget(0, len(_TABLE_HEADERS))
        self.table.setHorizontalHeaderLabels(_TABLE_HEADERS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.doubleClicked.connect(lambda *_: self._edit_selected())

        hint = QLabel("Dê um duplo clique numa linha para preencher nome, tutor e observações.")
        hint.setObjectName("hint")

        root = QVBoxLayout()
        root.addLayout(header)
        root.addLayout(cards)
        root.addWidget(self.search)
        root.addWidget(self.table, 1)
        root.addWidget(hint)
        container = QWidget()
        container.setLayout(root)
        self.setCentralWidget(container)

        self._setup_tray()
        self._apply_style()

        self.listener.exam_received.connect(self.on_exam)
        self.listener.qc_received.connect(self.on_qc)
        self.listener.status_changed.connect(self.on_status)
        self.listener.start()

        self.excel_timer = QTimer(self)
        self.excel_timer.timeout.connect(self.flush_excel)
        self.excel_timer.start(15_000)

        self.backup_timer = QTimer(self)
        self.backup_timer.timeout.connect(backup_if_needed)
        self.backup_timer.start(60 * 60 * 1000)
        backup_if_needed()

        if self.cfg.autostart:
            autostart.set_enabled(True)

        self._reparse_failed()
        self.refresh_table()
        self._show_latest()
        self._update_pending()

    def _card(self, title: str, value: QLabel) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        caption = QLabel(title)
        caption.setObjectName("cardTitle")
        layout.addWidget(caption)
        layout.addWidget(value)
        return frame

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow { background: #eef3f4; }
            QLabel#statusLine { font-size: 15px; color: #1f4e5f; }
            QLabel#pendingBadge { color: #9a4d0a; font-weight: 600; }
            QLabel#cardTitle { color: #5b6e75; font-size: 12px; }
            QFrame#card {
                background: white;
                border: 1px solid #d5e2e6;
                border-radius: 10px;
                padding: 8px 12px;
            }
            QLabel#hint { color: #5b6e75; }
            QPushButton {
                background: #1f4e5f;
                color: white;
                border: none;
                padding: 8px 14px;
                border-radius: 6px;
            }
            QPushButton:hover { background: #2b6a7a; }
            QLineEdit, QTableWidget { background: white; }
            """
        )

    def _setup_tray(self) -> None:
        self.tray = QSystemTrayIcon(status_icon(ICON_WAIT), self)
        menu = QMenu()
        menu.addAction("Abrir", self.showNormal)
        menu.addAction("Sincronizar planilha", self.flush_excel)
        menu.addSeparator()
        menu.addAction("Sair", self.quit_app)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.setToolTip("BC-2800Vet Receptor")
        self.tray.show()

    def _tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.showNormal()
            self.raise_()
            self.activateWindow()

    def closeEvent(self, event: QCloseEvent) -> None:
        event.ignore()
        self.hide()
        if not self._tray_hint_shown:
            self.tray.showMessage(
                "BC-2800Vet Receptor",
                "O programa continua recebendo exames na bandeja. Use Sair para encerrar.",
                QSystemTrayIcon.MessageIcon.Information,
                4000,
            )
            self._tray_hint_shown = True

    def quit_app(self) -> None:
        self.listener.stop()
        self.listener.wait(2000)
        self.repo.close()
        self.tray.hide()
        QApplication.quit()

    @Slot(str, bool)
    def on_status(self, message: str, connected: bool) -> None:
        self.status.setText(message)
        color = ICON_OK if connected else ICON_ERR
        icon = status_icon(color)
        self.setWindowIcon(icon)
        self.tray.setIcon(icon)
        self.tray.setToolTip(message)

    @Slot(object)
    def on_exam(self, exam: object) -> None:
        if not isinstance(exam, Exam):
            return
        stored, inserted = self.repo.insert_exam(exam)
        if inserted:
            self._sync_excel(stored)
            _beep()
        self.refresh_table()
        self._show_latest(stored)
        self._update_pending()
        self.tray.showMessage(
            "Exame recebido",
            f"ID {stored.sample_id or '—'} · {stored.species_label or 'espécie ?'}",
            QSystemTrayIcon.MessageIcon.Information,
            2500,
        )

    @Slot(object)
    def on_qc(self, event: object) -> None:
        if not isinstance(event, QcEvent):
            return
        self.repo.insert_qc(event)
        self.status.setText("QC recebido — gravado no banco (não vai para a planilha)")
        self.tray.showMessage(
            "QC recebido",
            f"Controle {event.identifier} gravado no SQLite.",
            QSystemTrayIcon.MessageIcon.Information,
            2500,
        )

    def _reparse_failed(self) -> None:
        updated = self.repo.reparse_failed_exams()
        for exam in updated:
            self._sync_excel(exam)
        if updated:
            _LOG.info("Reinterpretados %s exame(s) gravados com parse_ok=0", len(updated))

    def _sync_excel(self, exam: Exam) -> None:
        if exam.db_id is None:
            return
        if exam.excel_synced_at is not None:
            try:
                if self.excel.fill_exam_row(exam):
                    return
            except ExcelLockedError:
                self.repo.clear_excel_sync(exam.db_id)
                return
            self.repo.clear_excel_sync(exam.db_id)
        self._try_excel(exam)

    def _try_excel(self, exam: Exam) -> None:
        if exam.db_id is None:
            return
        try:
            self.excel.append_exam(exam)
            self.repo.mark_excel_synced(exam.db_id)
        except ExcelLockedError:
            _LOG.info("Planilha aberta; exame %s fica na fila", exam.db_id)

    def flush_excel(self) -> None:
        pending = self.repo.pending_excel()
        for exam in pending:
            try:
                self.excel.append_exam(exam)
                if exam.db_id is not None:
                    self.repo.mark_excel_synced(exam.db_id)
            except ExcelLockedError:
                break
        self._update_pending()

    def _update_pending(self) -> None:
        count = self.repo.pending_excel_count()
        if count:
            self.pending.setText(f"{count} exame(s) aguardando a planilha")
        else:
            self.pending.setText("")

    def refresh_table(self) -> None:
        exams = self.repo.list_exams(self.search.text())
        self.table.setRowCount(len(exams))
        for row, exam in enumerate(exams):
            values = [
                exam.received_at.strftime("%d/%m/%Y %H:%M:%S"),
                exam.exam_at_label,
                exam.sample_id or "",
                exam.species_label,
                _fmt(exam.wbc),
                _fmt(exam.rbc),
                _fmt(exam.hgb),
                _fmt(exam.plt),
                exam.animal_name or "",
                exam.tutor or "",
                exam.notes or "",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if exam.db_id is not None and col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, exam.db_id)
                if not exam.parse_ok:
                    item.setForeground(Qt.GlobalColor.darkRed)
                self.table.setItem(row, col, item)

    def _show_latest(self, exam: Exam | None = None) -> None:
        latest = exam or self.repo.latest_exam()
        if latest is None:
            return
        self.last_id.setText(latest.sample_id or "—")
        self.last_species.setText(latest.species_label or "—")
        self.last_when.setText(latest.exam_at_label or "—")
        self.last_wbc.setText(_fmt(latest.wbc) or "—")
        self.last_rbc.setText(_fmt(latest.rbc) or "—")
        self.last_hgb.setText(_fmt(latest.hgb) or "—")
        self.last_plt.setText(_fmt(latest.plt) or "—")

    def _edit_selected(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        item = self.table.item(row, 0)
        if item is None:
            return
        exam_id = item.data(Qt.ItemDataRole.UserRole)
        if exam_id is None:
            return
        exam = self.repo.get_exam(int(exam_id))
        if exam is None:
            return
        dialog = CompletarDialog(exam, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        updated = self.repo.update_user_fields(
            int(exam_id),
            dialog.name.text().strip(),
            dialog.tutor.text().strip(),
            dialog.notes.toPlainText().strip(),
        )
        if updated:
            self.excel.update_user_fields(updated)
        self.refresh_table()

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.cfg, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self.cfg = dialog.result_config()
        save_config(self.cfg)
        autostart.set_enabled(self.cfg.autostart)
        self.excel = ExcelWriter(self.cfg.resolved_excel_path())
        self.listener.apply_config(self.cfg)
        self.status.setText("Configuração salva. Reconectando…")
