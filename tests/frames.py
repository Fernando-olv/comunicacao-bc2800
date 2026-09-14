from __future__ import annotations

from bc2800.protocol.layouts import (
    CDH_FIELDS,
    FARM_FIELDS,
    Field,
    GOAT_FIELDS,
    QC_B_FIELDS,
    QC_C_FIELDS,
)
from bc2800.protocol.symbols import HISTO_BYTES


def _skip_fill(width: int) -> bytes:
    return b" " * width


def _i(value: int, width: int) -> bytes:
    return f"{value:0{width}d}".encode("ascii")


def _f(value: float | None, width: int, decimals: int) -> bytes:
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
        return b"****"
    return f".{int(round(value * 1000)):03d}".encode("ascii")


def _text(value: str, width: int) -> bytes:
    return value.encode("ascii").rjust(width)[:width]


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
    sample_id: str = "000123",
    animal_type: int = 0,
    histo: bool = True,
    wbc: float = 12.3,
    lymph_abs: float | None = 4.1,
    plt: float | None = 250,
) -> bytes:
    values = {
        "identifier": _text("A", 1),
        "sample_id": _text(sample_id, 6),
        "sample_mode": _i(0, 1),
        "month": _i(8, 2),
        "day": _i(28, 2),
        "year": _i(2026, 4),
        "hour": _i(14, 2),
        "minute": _i(30, 2),
        "wbc": _f(wbc, 5, 1),
        "lymph_abs": _f(lymph_abs, 5, 1),
        "mid_abs": _f(0.8, 5, 1),
        "gran_abs": _f(7.4, 5, 1),
        "lymph_pct": _f(33.3, 4, 1),
        "mid_pct": _f(6.5, 4, 1),
        "gran_pct": _f(60.2, 4, 1),
        "rbc": _f(6.45, 5, 2),
        "hgb": _f(142, 3, 0),
        "mchc": _f(340, 4, 0),
        "mcv": _f(68.2, 5, 1),
        "mch": _f(22.1, 5, 1),
        "rdw": _f(14.20, 5, 2),
        "hct": _f(43.1, 4, 1),
        "plt": _f(plt, 4, 0),
        "mpv": _f(8.2, 4, 1),
        "pdw": _f(12.1, 4, 1),
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
        "wbc": _f(wbc, 5, 1),
        "rbc": _f(5.12, 5, 2),
        "hgb": _f(110, 3, 0),
        "mchc": _f(330, 4, 0),
        "mcv": _f(50.0, 5, 1),
        "mch": _f(18.0, 5, 1),
        "rdw": _f(16.00, 5, 2),
        "hct": _f(32.5, 4, 1),
        "plt": _f(plt, 4, 0),
        "mpv": _f(7.5, 4, 1),
        "pdw": _f(11.0, 4, 1),
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
        "wbc": _f(wbc, 5, 1),
        "rbc": _f(12.00, 5, 2),
        "hgb": _f(98, 3, 0),
        "mchc": _f(320, 4, 0),
        "mcv": _f(28.0, 5, 1),
        "mch": _f(9.0, 5, 1),
        "rdw": _f(18.50, 5, 2),
        "hct": _f(30.0, 4, 1),
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
        "lot_no": _text("LOT001", 6),
        "month": _i(8, 2),
        "day": _i(1, 2),
        "year": _i(2026, 4),
        "wbc": _f(10.0, 5, 1),
        "rbc": _f(5.00, 5, 2),
        "hgb": _f(120, 3, 0),
        "plt": _f(300, 4, 0),
        "hct": _f(40.0, 4, 1),
        "mcv": _f(80.0, 5, 1),
        "mch": _f(27.0, 5, 1),
        "mchc": _f(330, 4, 0),
        "wbc_limit": _f(2.0, 5, 1),
        "rbc_limit": _f(0.50, 5, 2),
        "hgb_limit": _f(15, 3, 0),
        "plt_limit": _f(50, 4, 0),
        "hct_limit": _f(5.0, 4, 1),
        "mcv_limit": _f(5.0, 5, 1),
        "mch_limit": _f(3.0, 5, 1),
        "mchc_limit": _f(20, 4, 0),
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
        "wbc": _f(9.8, 5, 1),
        "rbc": _f(4.90, 5, 2),
        "hgb": _f(118, 3, 0),
        "plt": _f(280, 4, 0),
        "hct": _f(39.0, 4, 1),
        "mcv": _f(79.0, 5, 1),
        "mch": _f(26.5, 5, 1),
        "mchc": _f(328, 4, 0),
    }
    return pack(QC_C_FIELDS, values)
