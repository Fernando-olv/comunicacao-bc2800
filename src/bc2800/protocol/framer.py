from __future__ import annotations

from dataclasses import dataclass

from bc2800.protocol.symbols import ACK, BODY_TIMEOUT_S, EOF, ENQ, EOT, ETX, MIN_BODY_LEN, NACK, STX


@dataclass(frozen=True)
class SendByte:
    value: int


@dataclass(frozen=True)
class CompleteFrame:
    body: bytes
    handshake: bool


Action = SendByte | CompleteFrame


class Framer:
    """Acumula o envelope serial (ENQ/ACK/EOT/ETX ou STX/EOF) e devolve o corpo."""

    def __init__(self, idle_timeout_s: float = BODY_TIMEOUT_S) -> None:
        self._timeout = idle_timeout_s
        self._state = "idle"
        self._buf = bytearray()
        self._last = 0.0

    def feed(self, data: bytes, now: float) -> list[Action]:
        actions: list[Action] = []
        if self._state == "body" and self._last and now - self._last > self._timeout:
            self._reset()
        for byte in data:
            actions.extend(self._one(byte, now))
        return actions

    def _one(self, byte: int, now: float) -> list[Action]:
        self._last = now
        if byte == ENQ:
            self._reset(state="body")
            return [SendByte(ACK)]
        if byte == STX:
            self._reset(state="body")
            return []
        if self._state != "body":
            return []
        if byte == EOT:
            return []
        if byte == ETX:
            body = bytes(self._buf)
            self._reset()
            if len(body) < MIN_BODY_LEN:
                return [SendByte(NACK)]
            return [CompleteFrame(body, True), SendByte(ACK)]
        if byte == EOF:
            body = bytes(self._buf)
            self._reset()
            if len(body) < MIN_BODY_LEN:
                return []
            return [CompleteFrame(body, False)]
        self._buf.append(byte)
        return []

    def _reset(self, state: str = "idle") -> None:
        self._state = state
        self._buf = bytearray()
