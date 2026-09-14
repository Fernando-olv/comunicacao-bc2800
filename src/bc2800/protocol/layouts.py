from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Field:
    name: str
    width: int
    kind: str = "skip"


def _f(name: str, width: int, kind: str) -> Field:
    return Field(name, width, kind)


def _skip(width: int) -> Field:
    return Field("", width, "skip")


CDH_FIELDS: tuple[Field, ...] = (
    _f("identifier", 1, "text"),
    _f("sample_id", 6, "text"),
    _f("sample_mode", 1, "int"),
    _f("month", 2, "int"),
    _f("day", 2, "int"),
    _f("year", 4, "int"),
    _f("hour", 2, "int"),
    _f("minute", 2, "int"),
    _f("wbc", 5, "float"),
    _f("lymph_abs", 5, "float"),
    _f("mid_abs", 5, "float"),
    _f("gran_abs", 5, "float"),
    _f("lymph_pct", 4, "float"),
    _f("mid_pct", 4, "float"),
    _f("gran_pct", 4, "float"),
    _f("rbc", 5, "float"),
    _f("hgb", 3, "float"),
    _f("mchc", 4, "float"),
    _f("mcv", 5, "float"),
    _f("mch", 5, "float"),
    _f("rdw", 5, "float"),
    _f("hct", 4, "float"),
    _f("plt", 4, "float"),
    _f("mpv", 4, "float"),
    _f("pdw", 4, "float"),
    _f("pct", 4, "float"),
    _skip(11),
    _f("animal_type", 2, "int"),
    _skip(1),
    _skip(3),
    _skip(3),
    _skip(3),
    _skip(3),
    _skip(3),
    _skip(3),
    _skip(3),
    _skip(3),
    _skip(16),
)

FARM_FIELDS: tuple[Field, ...] = (
    _f("identifier", 1, "text"),
    _f("sample_id", 8, "text"),
    _f("sample_mode", 1, "int"),
    _f("month", 2, "int"),
    _f("day", 2, "int"),
    _f("year", 4, "int"),
    _f("hour", 2, "int"),
    _f("minute", 2, "int"),
    _f("wbc", 5, "float"),
    _skip(16),
    _skip(5),
    _f("rbc", 5, "float"),
    _f("hgb", 3, "float"),
    _f("mchc", 4, "float"),
    _f("mcv", 5, "float"),
    _f("mch", 5, "float"),
    _f("rdw", 5, "float"),
    _f("hct", 4, "float"),
    _f("plt", 4, "float"),
    _f("mpv", 4, "float"),
    _f("pdw", 4, "float"),
    _f("pct", 4, "float"),
    _skip(11),
    _f("animal_type", 2, "int"),
    _skip(1),
    _skip(3),
    _skip(6),
    _skip(3),
    _skip(3),
    _skip(3),
    _skip(3),
    _skip(3),
    _skip(16),
)

GOAT_FIELDS: tuple[Field, ...] = (
    _f("identifier", 1, "text"),
    _f("sample_id", 8, "text"),
    _f("sample_mode", 1, "int"),
    _f("month", 2, "int"),
    _f("day", 2, "int"),
    _f("year", 4, "int"),
    _f("hour", 2, "int"),
    _f("minute", 2, "int"),
    _f("wbc", 5, "float"),
    _skip(16),
    _skip(5),
    _f("rbc", 5, "float"),
    _f("hgb", 3, "float"),
    _f("mchc", 4, "float"),
    _f("mcv", 5, "float"),
    _f("mch", 5, "float"),
    _f("rdw", 5, "float"),
    _f("hct", 4, "float"),
    _skip(13),
    _skip(15),
    _f("animal_type", 1, "int"),
    _skip(1),
    _skip(3),
    _skip(6),
    _skip(3),
    _skip(3),
    _skip(3),
    _skip(3),
    _skip(3),
    _skip(16),
)

QC_B_FIELDS: tuple[Field, ...] = (
    _f("identifier", 1, "text"),
    _f("file_no", 1, "text"),
    _f("lot_no", 6, "text"),
    _f("month", 2, "int"),
    _f("day", 2, "int"),
    _f("year", 4, "int"),
    _f("wbc", 5, "float"),
    _f("rbc", 5, "float"),
    _f("hgb", 3, "float"),
    _f("plt", 4, "float"),
    _skip(14),
    _f("hct", 4, "float"),
    _f("mcv", 5, "float"),
    _f("mch", 5, "float"),
    _f("mchc", 4, "float"),
    _f("wbc_limit", 5, "float"),
    _f("rbc_limit", 5, "float"),
    _f("hgb_limit", 3, "float"),
    _f("plt_limit", 4, "float"),
    _skip(14),
    _f("hct_limit", 4, "float"),
    _f("mcv_limit", 5, "float"),
    _f("mch_limit", 5, "float"),
    _f("mchc_limit", 4, "float"),
)

QC_C_FIELDS: tuple[Field, ...] = (
    _f("identifier", 1, "text"),
    _f("month", 2, "int"),
    _f("day", 2, "int"),
    _f("year", 4, "int"),
    _f("hour", 2, "int"),
    _f("minute", 2, "int"),
    _f("wbc", 5, "float"),
    _f("rbc", 5, "float"),
    _f("hgb", 3, "float"),
    _f("plt", 4, "float"),
    _skip(14),
    _f("hct", 4, "float"),
    _f("mcv", 5, "float"),
    _f("mch", 5, "float"),
    _f("mchc", 4, "float"),
)

CDH_SPECIES = frozenset({0, 1, 2})
FARM_SPECIES = frozenset({3, 4, 5, 7, 8, 9, 10})
GOAT_SPECIES = frozenset({6})


def prefix_len(fields: tuple[Field, ...]) -> int:
    return sum(item.width for item in fields)
