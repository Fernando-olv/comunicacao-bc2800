from __future__ import annotations

from pathlib import Path

from bc2800.protocol.layouts import (
    CDH_FIELDS,
    FARM_FIELDS,
    Field,
    GOAT_FIELDS,
    QC_B_FIELDS,
    QC_C_FIELDS,
)
from bc2800.protocol.symbols import HISTO_BYTES

_LIVE_DOG = Path(__file__).parent / "fixtures" / "20260914-101927-917617-A.bin"


def _skip_fill(width: int) -> bytes:
    return b"0" * width


def _i(value: int, width: int) -> bytes:
    return f"{value:0{width}d}".encode("ascii")


def _n(value: float | None, width: int, decimals: int) -> bytes:
    """Pack a number as zero-padded digits with implied decimal places (live wire)."""
    if value is None:
        return b"*" * width
    scaled = int(round(value * (10 ** decimals)))
    text = f"{scaled:0{width}d}"
    if len(text) > width:
        text = text[-width:]
    return text.encode("ascii")


def _dotted(value: float | None, width: int, decimals: int) -> bytes:
    """QC appendix still uses an ASCII decimal point in tests."""
    if value is None:
        return b"*" * width
    if decimals == 0:
        text = f"{int(round(value)):{width}d}"
    else:
        text = f"{value:{width}.{decimals}f}"
    if len(text) != width:
        text = text.rjust(width)[:width]
    return text.encode("ascii")


def _pct(value: float | None) -> bytes:
    if value is None:
        return b"***"
    return f"{int(round(value * 1000)):03d}".encode("ascii")


def _text(value: str, width: int) -> bytes:
    return value.encode("ascii").rjust(width, b"0")[:width]


def pack(fields: tuple[Field, ...], values: dict[str, bytes]) -> bytes:
    parts: list[bytes] = []
    for field in fields:
        if field.kind == "skip":
            parts.append(_skip_fill(field.width))
        else:
            chunk = values[field.name]
            if len(chunk) != field.width:
                raise AssertionError(f"{field.name}: {len(chunk)} != {field.width}")
            parts.append(chunk)
    return b"".join(parts)


def make_cdh(
    *,
    sample_id: str = "00000123",
    animal_type: int = 0,
    histo: bool = True,
    wbc: float = 12.3,
    lymph_abs: float | None = 4.1,
    plt: float | None = 250,
) -> bytes:
    values = {
        "identifier": _text("A", 1),
        "sample_id": _text(sample_id, 8),
        "sample_mode": _i(0, 1),
        "month": _i(8, 2),
        "day": _i(28, 2),
        "year": _i(2026, 4),
        "hour": _i(14, 2),
        "minute": _i(30, 2),
        "wbc": _n(wbc, 4, 1),
        "lymph_abs": _n(lymph_abs, 4, 1),
        "mid_abs": _n(0.8, 4, 1),
        "gran_abs": _n(7.4, 4, 1),
        "lymph_pct": _n(33.3, 3, 1),
        "mid_pct": _n(6.5, 3, 1),
        "gran_pct": _n(60.2, 3, 1),
        "rbc": _n(6.45, 4, 2),
        "hgb": _n(142, 3, 0),
        "mchc": _n(340, 4, 0),
        "mcv": _n(68.2, 4, 1),
        "mch": _n(22.1, 4, 1),
        "rdw": _n(14.2, 3, 1),
        "hct": _n(43.1, 3, 1),
        "plt": _n(plt, 4, 0),
        "mpv": _n(8.2, 3, 1),
        "pdw": _n(12.1, 3, 1),
        "pct": _pct(0.205),
        "animal_type": _i(animal_type, 2),
    }
    body = pack(CDH_FIELDS, values)
    if histo:
        body += b"0" * HISTO_BYTES
    return body


def make_farm(
    *,
    sample_id: str = "00000123",
    animal_type: int = 3,
    histo: bool = True,
    wbc: float = 9.1,
    plt: float | None = 180,
) -> bytes:
    values = {
        "identifier": _text("A", 1),
        "sample_id": _text(sample_id, 8),
        "sample_mode": _i(1, 1),
        "month": _i(8, 2),
        "day": _i(28, 2),
        "year": _i(2026, 4),
        "hour": _i(9, 2),
        "minute": _i(5, 2),
        "wbc": _n(wbc, 4, 1),
        "rbc": _n(5.12, 4, 2),
        "hgb": _n(110, 3, 0),
        "mchc": _n(330, 4, 0),
        "mcv": _n(50.0, 4, 1),
        "mch": _n(18.0, 4, 1),
        "rdw": _n(16.0, 3, 1),
        "hct": _n(32.5, 3, 1),
        "plt": _n(plt, 4, 0),
        "mpv": _n(7.5, 3, 1),
        "pdw": _n(11.0, 3, 1),
        "pct": _pct(0.132),
        "animal_type": _i(animal_type, 2),
    }
    body = pack(FARM_FIELDS, values)
    if histo:
        body += b"0" * HISTO_BYTES
    return body


def make_goat(
    *,
    sample_id: str = "00000999",
    histo: bool = True,
    wbc: float = 8.0,
) -> bytes:
    values = {
        "identifier": _text("A", 1),
        "sample_id": _text(sample_id, 8),
        "sample_mode": _i(0, 1),
        "month": _i(1, 2),
        "day": _i(15, 2),
        "year": _i(2026, 4),
        "hour": _i(11, 2),
        "minute": _i(0, 2),
        "wbc": _n(wbc, 4, 1),
        "rbc": _n(12.00, 4, 2),
        "hgb": _n(98, 3, 0),
        "mchc": _n(320, 4, 0),
        "mcv": _n(28.0, 4, 1),
        "mch": _n(9.0, 4, 1),
        "rdw": _n(18.5, 3, 1),
        "hct": _n(30.0, 3, 1),
        "animal_type": _i(6, 1),
    }
    body = pack(GOAT_FIELDS, values)
    if histo:
        body += b"0" * HISTO_BYTES
    return body


def make_qc_b() -> bytes:
    values = {
        "identifier": _text("B", 1),
        "file_no": _text("1", 1),
        "lot_no": b"LOT001",
        "month": _i(8, 2),
        "day": _i(1, 2),
        "year": _i(2026, 4),
        "wbc": _dotted(10.0, 5, 1),
        "rbc": _dotted(5.00, 5, 2),
        "hgb": _dotted(120, 3, 0),
        "plt": _dotted(300, 4, 0),
        "hct": _dotted(40.0, 4, 1),
        "mcv": _dotted(80.0, 5, 1),
        "mch": _dotted(27.0, 5, 1),
        "mchc": _dotted(330, 4, 0),
        "wbc_limit": _dotted(2.0, 5, 1),
        "rbc_limit": _dotted(0.50, 5, 2),
        "hgb_limit": _dotted(15, 3, 0),
        "plt_limit": _dotted(50, 4, 0),
        "hct_limit": _dotted(5.0, 4, 1),
        "mcv_limit": _dotted(5.0, 5, 1),
        "mch_limit": _dotted(3.0, 5, 1),
        "mchc_limit": _dotted(20, 4, 0),
    }
    return pack(QC_B_FIELDS, values)


def make_qc_c() -> bytes:
    values = {
        "identifier": _text("C", 1),
        "month": _i(8, 2),
        "day": _i(28, 2),
        "year": _i(2026, 4),
        "hour": _i(8, 2),
        "minute": _i(0, 2),
        "wbc": _dotted(9.8, 5, 1),
        "rbc": _dotted(4.90, 5, 2),
        "hgb": _dotted(118, 3, 0),
        "plt": _dotted(280, 4, 0),
        "hct": _dotted(39.0, 4, 1),
        "mcv": _dotted(79.0, 5, 1),
        "mch": _dotted(26.5, 5, 1),
        "mchc": _dotted(328, 4, 0),
    }
    return pack(QC_C_FIELDS, values)


def live_cdh_dog() -> bytes:
    return _LIVE_DOG.read_bytes()
