from __future__ import annotations

import logging
import time
from datetime import datetime

import serial
from PySide6.QtCore import QThread, Signal
from serial.tools import list_ports

from bc2800.config import AppConfig
from bc2800.domain.models import Exam, QcEvent
from bc2800.logging_setup import dump_frame
from bc2800.protocol.framer import CompleteFrame, Framer, SendByte
from bc2800.protocol.parser import parse_body

_LOG = logging.getLogger("bc2800.serial")

_BYTESIZE = {7: serial.SEVENBITS, 8: serial.EIGHTBITS}
_PARITY = {
    "N": serial.PARITY_NONE,
    "E": serial.PARITY_EVEN,
    "O": serial.PARITY_ODD,
}
_STOP = {1: serial.STOPBITS_ONE, 1.0: serial.STOPBITS_ONE, 2: serial.STOPBITS_TWO}


def available_ports() -> list[str]:
    return [port.device for port in list_ports.comports()]


def resolve_port(cfg: AppConfig) -> str | None:
    if cfg.port.strip():
        return cfg.port.strip()
    ports = available_ports()
    if len(ports) == 1:
        return ports[0]
    return None


class SerialListener(QThread):
    exam_received = Signal(object)
    qc_received = Signal(object)
    status_changed = Signal(str, bool)

    def __init__(self, cfg: AppConfig) -> None:
        super().__init__()
        self._cfg = cfg
        self._stop = False
        self._reopen = False

    def apply_config(self, cfg: AppConfig) -> None:
        self._cfg = cfg
        self._reopen = True

    def stop(self) -> None:
        self._stop = True

    def run(self) -> None:
        while not self._stop:
            port = resolve_port(self._cfg)
            if not port:
                self.status_changed.emit(
                    "Nenhuma porta COM definida. Abra Configurações.",
                    False,
                )
                self._sleep(1.5)
                continue
            try:
                with serial.Serial(
                    port=port,
                    baudrate=self._cfg.baudrate,
                    bytesize=_BYTESIZE.get(self._cfg.bytesize, serial.SEVENBITS),
                    parity=_PARITY.get(self._cfg.parity.upper(), serial.PARITY_NONE),
                    stopbits=_STOP.get(self._cfg.stopbits, serial.STOPBITS_ONE),
                    timeout=0.2,
                    write_timeout=1,
                    rtscts=False,
                    dsrdtr=False,
                ) as ser:
                    self._reopen = False
                    self.status_changed.emit(f"Conectado em {port} — aguardando exame", True)
                    self._pump(ser)
            except serial.SerialException as exc:
                self.status_changed.emit(f"Porta {port}: {exc}", False)
                self._sleep(2)

    def _pump(self, ser: serial.Serial) -> None:
        framer = Framer()
        while not self._stop and not self._reopen:
            try:
                chunk = ser.read(256)
            except serial.SerialException:
                raise
            if not chunk:
                framer.feed(b"", time.monotonic())
                continue
            for action in framer.feed(chunk, time.monotonic()):
                if isinstance(action, SendByte):
                    try:
                        ser.write(bytes([action.value]))
                    except serial.SerialException as exc:
                        _LOG.warning("Falha ao responder handshake: %s", exc)
                elif isinstance(action, CompleteFrame):
                    self._handle_frame(action)

    def _handle_frame(self, frame: CompleteFrame) -> None:
        kind = chr(frame.body[0]) if frame.body else "unk"
        dump_frame(frame.body, kind)
        parsed = parse_body(frame.body)
        parsed.received_at = datetime.now()
        _LOG.info(
            "Frame %s handshake=%s bytes=%s",
            kind,
            frame.handshake,
            len(frame.body),
        )
        if isinstance(parsed, QcEvent):
            self.qc_received.emit(parsed)
        elif isinstance(parsed, Exam):
            self.exam_received.emit(parsed)

    def _sleep(self, seconds: float) -> None:
        end = time.monotonic() + seconds
        while not self._stop and time.monotonic() < end:
            time.sleep(0.2)
