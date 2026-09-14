from __future__ import annotations

from datetime import datetime

from bc2800.domain.models import Exam, QcEvent
from bc2800.protocol.layouts import (
    CDH_FIELDS,
    CDH_SPECIES,
    FARM_FIELDS,
    FARM_SPECIES,
    GOAT_FIELDS,
    GOAT_SPECIES,
    QC_B_FIELDS,
    QC_C_FIELDS,
    Field,
    prefix_len,
)

_ALLOWED = set("0123456789. *")


def _decode(chunk: bytes) -> str:
    return chunk.decode("ascii", errors="replace")


def _star(raw: str) -> bool:
    stripped = raw.strip()
    return not stripped or "*" in stripped


def _plausible(raw: str) -> bool:
    return all(char in _ALLOWED for char in raw)


def _to_int(raw: str) -> int | None:
    if _star(raw):
        return None
    try:
        return int(raw.strip())
    except ValueError:
        return None


def _to_float(raw: str, decimals: int = 0) -> float | None:
    if _star(raw):
        return None
    stripped = raw.strip()
    try:
        if "." in stripped:
            return float(stripped)
        return int(stripped) / (10 ** decimals)
    except ValueError:
        return None


def _to_text(raw: str) -> str | None:
    if _star(raw):
        return None
    return raw.strip()


def _gdl(value: float | None) -> float | None:
    """Cable HGB/MCHC are g/L; the analyzer screen and this app use g/dL."""
    if value is None:
        return None
    return value / 10.0


def _decimals(fields: tuple[Field, ...]) -> dict[str, int]:
    return {item.name: item.decimals for item in fields if item.name}


def walk(body: bytes, fields: tuple[Field, ...]) -> dict[str, str] | None:
    need = prefix_len(fields)
    if len(body) < need:
        return None
    offset = 0
    values: dict[str, str] = {}
    for item in fields:
        chunk = body[offset : offset + item.width]
        offset += item.width
        raw = _decode(chunk)
        if item.kind in ("int", "float") and not _plausible(raw):
            return None
        if item.kind != "skip":
            values[item.name] = raw
    return values


def _num(values: dict[str, str], decimals: dict[str, int], name: str) -> float | None:
    if name not in values:
        return None
    return _to_float(values[name], decimals.get(name, 0))


def _exam_at(values: dict[str, str]) -> datetime | None:
    month = _to_int(values.get("month", ""))
    day = _to_int(values.get("day", ""))
    year = _to_int(values.get("year", ""))
    hour = _to_int(values.get("hour", "0")) or 0
    minute = _to_int(values.get("minute", "0")) or 0
    if month is None or day is None or year is None:
        return None
    try:
        return datetime(year, month, day, hour, minute)
    except ValueError:
        return None


def _qc_at(values: dict[str, str], with_time: bool) -> datetime | None:
    month = _to_int(values.get("month", ""))
    day = _to_int(values.get("day", ""))
    year = _to_int(values.get("year", ""))
    if month is None or day is None or year is None:
        return None
    hour = 0
    minute = 0
    if with_time:
        hour = _to_int(values.get("hour", "0")) or 0
        minute = _to_int(values.get("minute", "0")) or 0
    try:
        return datetime(year, month, day, hour, minute)
    except ValueError:
        return None


def _cdh_diff_ok(exam: Exam) -> bool:
    """Reserved zeros on farm/goat frames look like animal_type 0; DIFF must add up."""
    parts = (exam.lymph_abs, exam.mid_abs, exam.gran_abs)
    if exam.wbc is None or any(part is None for part in parts):
        return True
    return abs(sum(parts) - exam.wbc) <= 0.2


def _try_exam_layout(
    body: bytes,
    layout: str,
    fields: tuple[Field, ...],
    species: frozenset[int],
) -> Exam | None:
    values = walk(body, fields)
    if values is None:
        return None
    if values.get("identifier", "").strip() != "A":
        return None
    animal_type = _to_int(values.get("animal_type", ""))
    if animal_type not in species:
        return None
    dec = _decimals(fields)
    exam = Exam(
        raw_payload=body,
        parse_ok=True,
        layout=layout,
        sample_id=_to_text(values["sample_id"]),
        sample_mode=_to_int(values["sample_mode"]),
        exam_at=_exam_at(values),
        animal_type=animal_type,
        wbc=_num(values, dec, "wbc"),
        lymph_abs=_num(values, dec, "lymph_abs"),
        mid_abs=_num(values, dec, "mid_abs"),
        gran_abs=_num(values, dec, "gran_abs"),
        lymph_pct=_num(values, dec, "lymph_pct"),
        mid_pct=_num(values, dec, "mid_pct"),
        gran_pct=_num(values, dec, "gran_pct"),
        rbc=_num(values, dec, "rbc"),
        hgb=_gdl(_num(values, dec, "hgb")),
        mchc=_gdl(_num(values, dec, "mchc")),
        mcv=_num(values, dec, "mcv"),
        mch=_num(values, dec, "mch"),
        rdw=_num(values, dec, "rdw"),
        hct=_num(values, dec, "hct"),
        plt=_num(values, dec, "plt"),
        mpv=_num(values, dec, "mpv"),
        pdw=_num(values, dec, "pdw"),
        pct=_num(values, dec, "pct"),
    )
    if layout == "cdh" and not _cdh_diff_ok(exam):
        return None
    return exam


def parse_exam(body: bytes) -> Exam:
    matches = [
        candidate
        for candidate in (
            _try_exam_layout(body, "cdh", CDH_FIELDS, CDH_SPECIES),
            _try_exam_layout(body, "farm", FARM_FIELDS, FARM_SPECIES),
            _try_exam_layout(body, "goat", GOAT_FIELDS, GOAT_SPECIES),
        )
        if candidate is not None
    ]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        return matches[0]
    return Exam(raw_payload=body, parse_ok=False, layout="unknown")


def parse_qc_b(body: bytes) -> QcEvent:
    values = walk(body, QC_B_FIELDS)
    if values is None or values.get("identifier", "").strip() != "B":
        return QcEvent(raw_payload=body, parse_ok=False, identifier="B")
    dec = _decimals(QC_B_FIELDS)
    return QcEvent(
        raw_payload=body,
        parse_ok=True,
        identifier="B",
        file_no=_to_text(values["file_no"]),
        lot_no=_to_text(values["lot_no"]),
        qc_at=_qc_at(values, with_time=False),
        wbc=_num(values, dec, "wbc"),
        rbc=_num(values, dec, "rbc"),
        hgb=_gdl(_num(values, dec, "hgb")),
        plt=_num(values, dec, "plt"),
        hct=_num(values, dec, "hct"),
        mcv=_num(values, dec, "mcv"),
        mch=_num(values, dec, "mch"),
        mchc=_gdl(_num(values, dec, "mchc")),
        wbc_limit=_num(values, dec, "wbc_limit"),
        rbc_limit=_num(values, dec, "rbc_limit"),
        hgb_limit=_gdl(_num(values, dec, "hgb_limit")),
        plt_limit=_num(values, dec, "plt_limit"),
        hct_limit=_num(values, dec, "hct_limit"),
        mcv_limit=_num(values, dec, "mcv_limit"),
        mch_limit=_num(values, dec, "mch_limit"),
        mchc_limit=_gdl(_num(values, dec, "mchc_limit")),
    )


def parse_qc_c(body: bytes) -> QcEvent:
    values = walk(body, QC_C_FIELDS)
    if values is None or values.get("identifier", "").strip() != "C":
        return QcEvent(raw_payload=body, parse_ok=False, identifier="C")
    dec = _decimals(QC_C_FIELDS)
    return QcEvent(
        raw_payload=body,
        parse_ok=True,
        identifier="C",
        qc_at=_qc_at(values, with_time=True),
        wbc=_num(values, dec, "wbc"),
        rbc=_num(values, dec, "rbc"),
        hgb=_gdl(_num(values, dec, "hgb")),
        plt=_num(values, dec, "plt"),
        hct=_num(values, dec, "hct"),
        mcv=_num(values, dec, "mcv"),
        mch=_num(values, dec, "mch"),
        mchc=_gdl(_num(values, dec, "mchc")),
    )


def parse_body(body: bytes) -> Exam | QcEvent:
    if not body:
        return Exam(raw_payload=body, parse_ok=False, layout="unknown")
    marker = chr(body[0]) if body[0] < 128 else "?"
    if marker == "A":
        return parse_exam(body)
    if marker == "B":
        return parse_qc_b(body)
    if marker == "C":
        return parse_qc_c(body)
    return Exam(raw_payload=body, parse_ok=False, layout="unknown")
