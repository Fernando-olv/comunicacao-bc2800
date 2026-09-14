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


def _to_float(raw: str) -> float | None:
    if _star(raw):
        return None
    try:
        return float(raw.strip())
    except ValueError:
        return None


def _to_text(raw: str) -> str | None:
    if _star(raw):
        return None
    return raw.strip()


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
    return Exam(
        raw_payload=body,
        parse_ok=True,
        layout=layout,
        sample_id=_to_text(values["sample_id"]),
        sample_mode=_to_int(values["sample_mode"]),
        exam_at=_exam_at(values),
        animal_type=animal_type,
        wbc=_to_float(values.get("wbc", "")),
        lymph_abs=_to_float(values["lymph_abs"]) if "lymph_abs" in values else None,
        mid_abs=_to_float(values["mid_abs"]) if "mid_abs" in values else None,
        gran_abs=_to_float(values["gran_abs"]) if "gran_abs" in values else None,
        lymph_pct=_to_float(values["lymph_pct"]) if "lymph_pct" in values else None,
        mid_pct=_to_float(values["mid_pct"]) if "mid_pct" in values else None,
        gran_pct=_to_float(values["gran_pct"]) if "gran_pct" in values else None,
        rbc=_to_float(values.get("rbc", "")),
        hgb=_to_float(values.get("hgb", "")),
        mchc=_to_float(values.get("mchc", "")),
        mcv=_to_float(values.get("mcv", "")),
        mch=_to_float(values.get("mch", "")),
        rdw=_to_float(values.get("rdw", "")),
        hct=_to_float(values.get("hct", "")),
        plt=_to_float(values["plt"]) if "plt" in values else None,
        mpv=_to_float(values["mpv"]) if "mpv" in values else None,
        pdw=_to_float(values["pdw"]) if "pdw" in values else None,
        pct=_to_float(values["pct"]) if "pct" in values else None,
    )


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
    return QcEvent(
        raw_payload=body,
        parse_ok=True,
        identifier="B",
        file_no=_to_text(values["file_no"]),
        lot_no=_to_text(values["lot_no"]),
        qc_at=_qc_at(values, with_time=False),
        wbc=_to_float(values["wbc"]),
        rbc=_to_float(values["rbc"]),
        hgb=_to_float(values["hgb"]),
        plt=_to_float(values["plt"]),
        hct=_to_float(values["hct"]),
        mcv=_to_float(values["mcv"]),
        mch=_to_float(values["mch"]),
        mchc=_to_float(values["mchc"]),
        wbc_limit=_to_float(values["wbc_limit"]),
        rbc_limit=_to_float(values["rbc_limit"]),
        hgb_limit=_to_float(values["hgb_limit"]),
        plt_limit=_to_float(values["plt_limit"]),
        hct_limit=_to_float(values["hct_limit"]),
        mcv_limit=_to_float(values["mcv_limit"]),
        mch_limit=_to_float(values["mch_limit"]),
        mchc_limit=_to_float(values["mchc_limit"]),
    )


def parse_qc_c(body: bytes) -> QcEvent:
    values = walk(body, QC_C_FIELDS)
    if values is None or values.get("identifier", "").strip() != "C":
        return QcEvent(raw_payload=body, parse_ok=False, identifier="C")
    return QcEvent(
        raw_payload=body,
        parse_ok=True,
        identifier="C",
        qc_at=_qc_at(values, with_time=True),
        wbc=_to_float(values["wbc"]),
        rbc=_to_float(values["rbc"]),
        hgb=_to_float(values["hgb"]),
        plt=_to_float(values["plt"]),
        hct=_to_float(values["hct"]),
        mcv=_to_float(values["mcv"]),
        mch=_to_float(values["mch"]),
        mchc=_to_float(values["mchc"]),
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
