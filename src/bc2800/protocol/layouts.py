from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Field:
    name: str
    width: int
    kind: str = "skip"
    decimals: int = 0


def _f(name: str, width: int, kind: str, decimals: int = 0) -> Field:
    return Field(name, width, kind, decimals)


def _skip(width: int) -> Field:
    return Field("", width, "skip")


# Live BC-2800Vet: ASCII has no decimal point. Widths are digit counts;
# `decimals` is the implied fraction. ID is 8 digits on all species.
# After PCT the firmware sends 10 extra bytes, then the appendix reserved/L-regions.
CDH_FIELDS: tuple[Field, ...] = (
    _f("identifier", 1, "text"),
    _f("sample_id", 8, "text"),
    _f("sample_mode", 1, "int"),
    _f("month", 2, "int"),
    _f("day", 2, "int"),
    _f("year", 4, "int"),
    _f("hour", 2, "int"),
    _f("minute", 2, "int"),
    _f("wbc", 4, "float", 1),
    _f("lymph_abs", 4, "float", 1),
    _f("mid_abs", 4, "float", 1),
    _f("gran_abs", 4, "float", 1),
    _f("lymph_pct", 3, "float", 1),
    _f("mid_pct", 3, "float", 1),
    _f("gran_pct", 3, "float", 1),
    _f("rbc", 4, "float", 2),
    _f("hgb", 3, "float", 0),
    _f("mchc", 4, "float", 0),
    _f("mcv", 4, "float", 1),
    _f("mch", 4, "float", 1),
    _f("rdw", 3, "float", 1),
    _f("hct", 3, "float", 1),
    _f("plt", 4, "float", 0),
    _f("mpv", 3, "float", 1),
    _f("pdw", 3, "float", 1),
    _f("pct", 3, "float", 3),
    _skip(10),
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
    _f("wbc", 4, "float", 1),
    _skip(16),
    _skip(5),
    _f("rbc", 4, "float", 2),
    _f("hgb", 3, "float", 0),
    _f("mchc", 4, "float", 0),
    _f("mcv", 4, "float", 1),
    _f("mch", 4, "float", 1),
    _f("rdw", 3, "float", 1),
    _f("hct", 3, "float", 1),
    _f("plt", 4, "float", 0),
    _f("mpv", 3, "float", 1),
    _f("pdw", 3, "float", 1),
    _f("pct", 3, "float", 3),
    _skip(10),
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
    _f("wbc", 4, "float", 1),
    _skip(16),
    _skip(5),
    _f("rbc", 4, "float", 2),
    _f("hgb", 3, "float", 0),
    _f("mchc", 4, "float", 0),
    _f("mcv", 4, "float", 1),
    _f("mch", 4, "float", 1),
    _f("rdw", 3, "float", 1),
    _f("hct", 3, "float", 1),
    _skip(13),
    _skip(15),
    _skip(10),
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
    _f("wbc", 5, "float", 1),
    _f("rbc", 5, "float", 2),
    _f("hgb", 3, "float", 0),
    _f("plt", 4, "float", 0),
    _skip(14),
    _f("hct", 4, "float", 1),
    _f("mcv", 5, "float", 1),
    _f("mch", 5, "float", 1),
    _f("mchc", 4, "float", 0),
    _f("wbc_limit", 5, "float", 1),
    _f("rbc_limit", 5, "float", 2),
    _f("hgb_limit", 3, "float", 0),
    _f("plt_limit", 4, "float", 0),
    _skip(14),
    _f("hct_limit", 4, "float", 1),
    _f("mcv_limit", 5, "float", 1),
    _f("mch_limit", 5, "float", 1),
    _f("mchc_limit", 4, "float", 0),
)

QC_C_FIELDS: tuple[Field, ...] = (
    _f("identifier", 1, "text"),
    _f("month", 2, "int"),
    _f("day", 2, "int"),
    _f("year", 4, "int"),
    _f("hour", 2, "int"),
    _f("minute", 2, "int"),
    _f("wbc", 5, "float", 1),
    _f("rbc", 5, "float", 2),
    _f("hgb", 3, "float", 0),
    _f("plt", 4, "float", 0),
    _skip(14),
    _f("hct", 4, "float", 1),
    _f("mcv", 5, "float", 1),
    _f("mch", 5, "float", 1),
    _f("mchc", 4, "float", 0),
)

CDH_SPECIES = frozenset({0, 1, 2})
FARM_SPECIES = frozenset({3, 4, 5, 7, 8, 9, 10})
GOAT_SPECIES = frozenset({6})


def prefix_len(fields: tuple[Field, ...]) -> int:
    return sum(item.width for item in fields)
