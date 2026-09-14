from datetime import datetime

from bc2800.protocol.layouts import (
    CDH_FIELDS,
    FARM_FIELDS,
    GOAT_FIELDS,
    QC_B_FIELDS,
    QC_C_FIELDS,
    prefix_len,
)
from bc2800.protocol.symbols import ACK, EOF, ENQ, EOT, ETX, NACK, STX
from bc2800.protocol.framer import CompleteFrame, Framer, SendByte
from bc2800.protocol.parser import parse_body, parse_exam
from bc2800.domain.models import Exam, QcEvent

from frames import live_cdh_dog, make_cdh, make_farm, make_goat, make_qc_b, make_qc_c


def test_prefix_lengths() -> None:
    assert prefix_len(CDH_FIELDS) == 149
    assert prefix_len(FARM_FIELDS) == 149
    assert prefix_len(GOAT_FIELDS) == 152
    assert prefix_len(QC_B_FIELDS) == 114
    assert prefix_len(QC_C_FIELDS) == 62


def test_parse_cdh_dog() -> None:
    exam = parse_exam(make_cdh(animal_type=0))
    assert exam.parse_ok
    assert exam.layout == "cdh"
    assert exam.sample_id == "00000123"
    assert exam.animal_type == 0
    assert exam.species_label == "Cão"
    assert exam.wbc == 12.3
    assert exam.lymph_abs == 4.1
    assert exam.plt == 250
    assert exam.hgb == 14.2
    assert exam.mchc == 34.0
    assert exam.exam_at is not None
    assert exam.exam_at.year == 2026


def test_parse_farm_pig_has_no_diff() -> None:
    exam = parse_exam(make_farm(animal_type=3))
    assert exam.parse_ok
    assert exam.layout == "farm"
    assert exam.sample_id == "00000123"
    assert exam.animal_type == 3
    assert exam.species_label == "Suíno"
    assert exam.lymph_abs is None
    assert exam.gran_pct is None
    assert exam.plt == 180
    assert exam.hgb == 11.0


def test_parse_goat_has_no_plt() -> None:
    exam = parse_exam(make_goat())
    assert exam.parse_ok
    assert exam.layout == "goat"
    assert exam.animal_type == 6
    assert exam.species_label == "Caprino"
    assert exam.plt is None
    assert exam.mpv is None
    assert exam.lymph_abs is None
    assert exam.wbc == 8.0
    assert exam.hgb == 9.8


def test_star_becomes_null() -> None:
    exam = parse_exam(make_cdh(lymph_abs=None, plt=None))
    assert exam.parse_ok
    assert exam.lymph_abs is None
    assert exam.plt is None


def test_qc_b_and_c() -> None:
    qc_b = parse_body(make_qc_b())
    assert isinstance(qc_b, QcEvent)
    assert qc_b.parse_ok
    assert qc_b.identifier == "B"
    assert qc_b.lot_no == "LOT001"
    assert qc_b.wbc_limit == 2.0
    assert qc_b.hgb == 12.0
    assert qc_b.mchc == 33.0

    qc_c = parse_body(make_qc_c())
    assert isinstance(qc_c, QcEvent)
    assert qc_c.parse_ok
    assert qc_c.identifier == "C"
    assert qc_c.lot_no is None
    assert qc_c.wbc == 9.8
    assert qc_c.hgb == 11.8


def test_user_defined_and_horse() -> None:
    horse = parse_exam(make_cdh(animal_type=2))
    assert horse.parse_ok
    assert horse.layout == "cdh"
    assert horse.species_label == "Cavalo"
    custom = parse_exam(make_farm(animal_type=7))
    assert custom.parse_ok
    assert custom.layout == "farm"
    assert custom.species_label == "Animal 1"
    assert custom.lymph_abs is None


def test_unknown_body_is_kept() -> None:
    exam = parse_body(b"A?????????????????????")
    assert isinstance(exam, Exam)
    assert not exam.parse_ok
    assert exam.layout == "unknown"


def test_live_cdh_dog_20260914() -> None:
    exam = parse_exam(live_cdh_dog())
    assert exam.parse_ok
    assert exam.layout == "cdh"
    assert exam.sample_id == "00002007"
    assert exam.sample_mode == 0
    assert exam.animal_type == 0
    assert exam.species_label == "Cão"
    assert exam.exam_at == datetime(2026, 9, 12, 13, 21)
    assert exam.wbc == 27.4
    assert exam.lymph_abs == 2.7
    assert exam.mid_abs == 0.3
    assert exam.gran_abs == 24.4
    assert exam.lymph_pct == 9.7
    assert exam.mid_pct == 1.1
    assert exam.gran_pct == 89.2
    assert exam.rbc == 5.82
    assert exam.hgb == 13.5
    assert exam.mchc == 31.9
    assert exam.mcv == 72.6
    assert exam.mch == 23.1
    assert exam.rdw == 14.6
    assert exam.hct == 42.2
    assert exam.plt == 430
    assert exam.mpv == 8.5
    assert exam.pdw == 15.8
    assert exam.pct == 0.365


def test_framer_handshake() -> None:
    framer = Framer()
    body = make_cdh()
    stream = bytes([ENQ]) + body + bytes([EOT, ETX])
    actions = framer.feed(stream, 0.0)
    acks = [item for item in actions if isinstance(item, SendByte)]
    frames = [item for item in actions if isinstance(item, CompleteFrame)]
    assert acks[0].value == ACK
    assert acks[-1].value == ACK
    assert frames[0].body == body
    assert frames[0].handshake is True


def test_framer_no_handshake() -> None:
    framer = Framer()
    body = make_farm()
    stream = bytes([STX]) + body + bytes([EOF])
    actions = framer.feed(stream, 0.0)
    assert not any(isinstance(item, SendByte) for item in actions)
    frames = [item for item in actions if isinstance(item, CompleteFrame)]
    assert frames[0].body == body
    assert frames[0].handshake is False


def test_framer_nack_truncated() -> None:
    framer = Framer()
    actions = framer.feed(bytes([ENQ, 0x41, EOT, ETX]), 0.0)
    nacks = [item for item in actions if isinstance(item, SendByte) and item.value == NACK]
    assert nacks
