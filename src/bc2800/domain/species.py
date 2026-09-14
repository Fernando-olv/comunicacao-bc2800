from __future__ import annotations

from datetime import datetime

SPECIES_NAMES = {
    0: "Cão",
    1: "Gato",
    2: "Cavalo",
    3: "Suíno",
    4: "Bovino",
    5: "Búfalo",
    6: "Caprino",
    7: "Animal 1",
    8: "Animal 2",
    9: "Animal 3",
    10: "Animal 4",
}

SAMPLE_MODE_NAMES = {
    0: "Sangue total",
    1: "Pré-diluído",
}


def species_name(animal_type: int | None) -> str:
    if animal_type is None:
        return ""
    return SPECIES_NAMES.get(animal_type, str(animal_type))


def sample_mode_label(mode: int | None) -> str:
    if mode is None:
        return ""
    name = SAMPLE_MODE_NAMES.get(mode)
    if name is None:
        return str(mode)
    return f"{mode} ({name})"


def format_exam_at(exam_at: datetime | None) -> str:
    if exam_at is None:
        return ""
    return exam_at.strftime("%d/%m/%Y %H:%M")
