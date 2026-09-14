from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from bc2800.domain.species import format_exam_at, sample_mode_label, species_name


@dataclass
class Exam:
    raw_payload: bytes
    parse_ok: bool
    layout: str
    sample_id: str | None = None
    sample_mode: int | None = None
    exam_at: datetime | None = None
    animal_type: int | None = None
    wbc: float | None = None
    lymph_abs: float | None = None
    mid_abs: float | None = None
    gran_abs: float | None = None
    lymph_pct: float | None = None
    mid_pct: float | None = None
    gran_pct: float | None = None
    rbc: float | None = None
    hgb: float | None = None
    mchc: float | None = None
    mcv: float | None = None
    mch: float | None = None
    rdw: float | None = None
    hct: float | None = None
    plt: float | None = None
    mpv: float | None = None
    pdw: float | None = None
    pct: float | None = None
    animal_name: str | None = None
    tutor: str | None = None
    notes: str | None = None
    received_at: datetime = field(default_factory=datetime.now)
    db_id: int | None = None
    excel_synced_at: datetime | None = None

    @property
    def species_label(self) -> str:
        return species_name(self.animal_type)

    @property
    def sample_mode_label(self) -> str:
        return sample_mode_label(self.sample_mode)

    @property
    def exam_at_label(self) -> str:
        return format_exam_at(self.exam_at)


@dataclass
class QcEvent:
    raw_payload: bytes
    parse_ok: bool
    identifier: str
    file_no: str | None = None
    lot_no: str | None = None
    qc_at: datetime | None = None
    wbc: float | None = None
    rbc: float | None = None
    hgb: float | None = None
    plt: float | None = None
    hct: float | None = None
    mcv: float | None = None
    mch: float | None = None
    mchc: float | None = None
    wbc_limit: float | None = None
    rbc_limit: float | None = None
    hgb_limit: float | None = None
    plt_limit: float | None = None
    hct_limit: float | None = None
    mcv_limit: float | None = None
    mch_limit: float | None = None
    mchc_limit: float | None = None
    received_at: datetime = field(default_factory=datetime.now)
    db_id: int | None = None
