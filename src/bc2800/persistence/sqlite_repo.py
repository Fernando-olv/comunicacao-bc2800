from __future__ import annotations

import hashlib
import logging
import sqlite3
from datetime import datetime
from pathlib import Path

from bc2800.domain.models import Exam, QcEvent
from bc2800.paths import sqlite_path
from bc2800.protocol.parser import parse_body

_LOG = logging.getLogger("bc2800.sqlite")

_SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS exams (
    id INTEGER PRIMARY KEY,
    received_at TEXT NOT NULL,
    exam_at TEXT,
    sample_id TEXT,
    sample_mode INTEGER,
    animal_type INTEGER,
    layout TEXT NOT NULL,
    wbc REAL,
    lymph_abs REAL,
    mid_abs REAL,
    gran_abs REAL,
    lymph_pct REAL,
    mid_pct REAL,
    gran_pct REAL,
    rbc REAL,
    hgb REAL,
    mchc REAL,
    mcv REAL,
    mch REAL,
    rdw REAL,
    hct REAL,
    plt REAL,
    mpv REAL,
    pdw REAL,
    pct REAL,
    animal_name TEXT,
    tutor TEXT,
    notes TEXT,
    raw_payload BLOB NOT NULL,
    payload_sha256 TEXT NOT NULL UNIQUE,
    parse_ok INTEGER NOT NULL,
    excel_synced_at TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_exams_natural
    ON exams(sample_id, exam_at, animal_type)
    WHERE sample_id IS NOT NULL AND exam_at IS NOT NULL AND animal_type IS NOT NULL;

CREATE TABLE IF NOT EXISTS qc_events (
    id INTEGER PRIMARY KEY,
    received_at TEXT NOT NULL,
    identifier TEXT NOT NULL,
    file_no TEXT,
    lot_no TEXT,
    qc_at TEXT,
    wbc REAL,
    rbc REAL,
    hgb REAL,
    plt REAL,
    hct REAL,
    mcv REAL,
    mch REAL,
    mchc REAL,
    wbc_limit REAL,
    rbc_limit REAL,
    hgb_limit REAL,
    plt_limit REAL,
    hct_limit REAL,
    mcv_limit REAL,
    mch_limit REAL,
    mchc_limit REAL,
    raw_payload BLOB NOT NULL,
    payload_sha256 TEXT NOT NULL UNIQUE,
    parse_ok INTEGER NOT NULL
);
"""


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat(timespec="seconds")


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def payload_hash(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


class SqliteRepo:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or sqlite_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def insert_exam(self, exam: Exam) -> tuple[Exam, bool]:
        digest = payload_hash(exam.raw_payload)
        existing = self._conn.execute(
            "SELECT id FROM exams WHERE payload_sha256 = ?",
            (digest,),
        ).fetchone()
        if existing:
            stored = self.get_exam(int(existing["id"]))
            if (
                stored is not None
                and not stored.parse_ok
                and exam.parse_ok
                and stored.db_id is not None
            ):
                self._update_parsed_fields(stored.db_id, exam)
                refreshed = self.get_exam(stored.db_id)
                return refreshed or exam, True
            return stored or exam, False
        try:
            cursor = self._conn.execute(
                """
                INSERT INTO exams (
                    received_at, exam_at, sample_id, sample_mode, animal_type, layout,
                    wbc, lymph_abs, mid_abs, gran_abs, lymph_pct, mid_pct, gran_pct,
                    rbc, hgb, mchc, mcv, mch, rdw, hct, plt, mpv, pdw, pct,
                    animal_name, tutor, notes, raw_payload, payload_sha256, parse_ok
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    _iso(exam.received_at),
                    _iso(exam.exam_at),
                    exam.sample_id,
                    exam.sample_mode,
                    exam.animal_type,
                    exam.layout,
                    exam.wbc,
                    exam.lymph_abs,
                    exam.mid_abs,
                    exam.gran_abs,
                    exam.lymph_pct,
                    exam.mid_pct,
                    exam.gran_pct,
                    exam.rbc,
                    exam.hgb,
                    exam.mchc,
                    exam.mcv,
                    exam.mch,
                    exam.rdw,
                    exam.hct,
                    exam.plt,
                    exam.mpv,
                    exam.pdw,
                    exam.pct,
                    exam.animal_name,
                    exam.tutor,
                    exam.notes,
                    exam.raw_payload,
                    digest,
                    int(exam.parse_ok),
                ),
            )
            self._conn.commit()
        except sqlite3.IntegrityError:
            self._conn.rollback()
            row = self._conn.execute(
                """
                SELECT id FROM exams
                WHERE sample_id = ? AND exam_at = ? AND animal_type = ?
                """,
                (exam.sample_id, _iso(exam.exam_at), exam.animal_type),
            ).fetchone()
            if row:
                stored = self.get_exam(int(row["id"]))
                return stored or exam, False
            raise
        exam.db_id = int(cursor.lastrowid)
        return exam, True

    def insert_qc(self, event: QcEvent) -> tuple[QcEvent, bool]:
        digest = payload_hash(event.raw_payload)
        existing = self._conn.execute(
            "SELECT id FROM qc_events WHERE payload_sha256 = ?",
            (digest,),
        ).fetchone()
        if existing:
            event.db_id = int(existing["id"])
            return event, False
        cursor = self._conn.execute(
            """
            INSERT INTO qc_events (
                received_at, identifier, file_no, lot_no, qc_at,
                wbc, rbc, hgb, plt, hct, mcv, mch, mchc,
                wbc_limit, rbc_limit, hgb_limit, plt_limit,
                hct_limit, mcv_limit, mch_limit, mchc_limit,
                raw_payload, payload_sha256, parse_ok
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                _iso(event.received_at),
                event.identifier,
                event.file_no,
                event.lot_no,
                _iso(event.qc_at),
                event.wbc,
                event.rbc,
                event.hgb,
                event.plt,
                event.hct,
                event.mcv,
                event.mch,
                event.mchc,
                event.wbc_limit,
                event.rbc_limit,
                event.hgb_limit,
                event.plt_limit,
                event.hct_limit,
                event.mcv_limit,
                event.mch_limit,
                event.mchc_limit,
                event.raw_payload,
                digest,
                int(event.parse_ok),
            ),
        )
        self._conn.commit()
        event.db_id = int(cursor.lastrowid)
        return event, True

    def _update_parsed_fields(self, exam_id: int, exam: Exam) -> None:
        self._conn.execute(
            """
            UPDATE exams SET
                exam_at = ?, sample_id = ?, sample_mode = ?, animal_type = ?, layout = ?,
                wbc = ?, lymph_abs = ?, mid_abs = ?, gran_abs = ?,
                lymph_pct = ?, mid_pct = ?, gran_pct = ?,
                rbc = ?, hgb = ?, mchc = ?, mcv = ?, mch = ?, rdw = ?, hct = ?,
                plt = ?, mpv = ?, pdw = ?, pct = ?, parse_ok = ?
            WHERE id = ?
            """,
            (
                _iso(exam.exam_at),
                exam.sample_id,
                exam.sample_mode,
                exam.animal_type,
                exam.layout,
                exam.wbc,
                exam.lymph_abs,
                exam.mid_abs,
                exam.gran_abs,
                exam.lymph_pct,
                exam.mid_pct,
                exam.gran_pct,
                exam.rbc,
                exam.hgb,
                exam.mchc,
                exam.mcv,
                exam.mch,
                exam.rdw,
                exam.hct,
                exam.plt,
                exam.mpv,
                exam.pdw,
                exam.pct,
                int(exam.parse_ok),
                exam_id,
            ),
        )
        self._conn.commit()

    def reparse_failed_exams(self) -> list[Exam]:
        rows = self._conn.execute(
            "SELECT id, raw_payload FROM exams WHERE parse_ok = 0"
        ).fetchall()
        updated: list[Exam] = []
        for row in rows:
            parsed = parse_body(bytes(row["raw_payload"]))
            if not isinstance(parsed, Exam) or not parsed.parse_ok:
                continue
            self._update_parsed_fields(int(row["id"]), parsed)
            exam = self.get_exam(int(row["id"]))
            if exam is not None:
                updated.append(exam)
        return updated

    def clear_excel_sync(self, exam_id: int) -> None:
        self._conn.execute(
            "UPDATE exams SET excel_synced_at = NULL WHERE id = ?",
            (exam_id,),
        )
        self._conn.commit()

    def mark_excel_synced(self, exam_id: int) -> None:
        self._conn.execute(
            "UPDATE exams SET excel_synced_at = ? WHERE id = ?",
            (_iso(datetime.now()), exam_id),
        )
        self._conn.commit()

    def pending_excel(self) -> list[Exam]:
        rows = self._conn.execute(
            "SELECT * FROM exams WHERE excel_synced_at IS NULL ORDER BY id"
        ).fetchall()
        return [self._exam_from_row(row) for row in rows]

    def pending_excel_count(self) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) AS n FROM exams WHERE excel_synced_at IS NULL"
        ).fetchone()
        return int(row["n"])

    def list_exams(self, search: str = "") -> list[Exam]:
        if search.strip():
            like = f"%{search.strip()}%"
            rows = self._conn.execute(
                """
                SELECT * FROM exams
                WHERE IFNULL(sample_id, '') LIKE ?
                   OR IFNULL(animal_name, '') LIKE ?
                   OR IFNULL(tutor, '') LIKE ?
                   OR IFNULL(notes, '') LIKE ?
                ORDER BY id DESC
                """,
                (like, like, like, like),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM exams ORDER BY id DESC"
            ).fetchall()
        return [self._exam_from_row(row) for row in rows]

    def get_exam(self, exam_id: int) -> Exam | None:
        row = self._conn.execute(
            "SELECT * FROM exams WHERE id = ?", (exam_id,)
        ).fetchone()
        if row is None:
            return None
        return self._exam_from_row(row)

    def latest_exam(self) -> Exam | None:
        row = self._conn.execute(
            "SELECT * FROM exams ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        return self._exam_from_row(row)

    def update_user_fields(
        self,
        exam_id: int,
        animal_name: str,
        tutor: str,
        notes: str,
    ) -> Exam | None:
        self._conn.execute(
            """
            UPDATE exams
            SET animal_name = ?, tutor = ?, notes = ?
            WHERE id = ?
            """,
            (animal_name or None, tutor or None, notes or None, exam_id),
        )
        self._conn.commit()
        return self.get_exam(exam_id)

    def _exam_from_row(self, row: sqlite3.Row) -> Exam:
        return Exam(
            db_id=int(row["id"]),
            received_at=_parse_dt(row["received_at"]) or datetime.now(),
            exam_at=_parse_dt(row["exam_at"]),
            sample_id=row["sample_id"],
            sample_mode=row["sample_mode"],
            animal_type=row["animal_type"],
            layout=row["layout"],
            wbc=row["wbc"],
            lymph_abs=row["lymph_abs"],
            mid_abs=row["mid_abs"],
            gran_abs=row["gran_abs"],
            lymph_pct=row["lymph_pct"],
            mid_pct=row["mid_pct"],
            gran_pct=row["gran_pct"],
            rbc=row["rbc"],
            hgb=row["hgb"],
            mchc=row["mchc"],
            mcv=row["mcv"],
            mch=row["mch"],
            rdw=row["rdw"],
            hct=row["hct"],
            plt=row["plt"],
            mpv=row["mpv"],
            pdw=row["pdw"],
            pct=row["pct"],
            animal_name=row["animal_name"],
            tutor=row["tutor"],
            notes=row["notes"],
            raw_payload=bytes(row["raw_payload"]),
            parse_ok=bool(row["parse_ok"]),
            excel_synced_at=_parse_dt(row["excel_synced_at"]),
        )
