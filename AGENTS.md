# AGENTS.md — BC-2800Vet Receptor

Handbook for an AI or human continuing this repo. Read this before changing protocol, persistence, or the desktop GUI. Product UI strings are **pt-BR**. Source comments may be Portuguese. Keep new user-facing text in Portuguese.

## What this product is

Windows desktop app that listens to a **Mindray BC-2800Vet** hematology analyzer over **RS-232** (DB9 on analyzer **serial port 2**, pins 2/3/5, USB-serial adapter on the PC). Each sample is stored in **SQLite (source of truth, including raw payload)** and appended as one row in an **Excel `.xlsx`** so the veterinarian can later fill animal name, tutor, and notes.

Not a web app. Not a LIS. No patient registry before the exam arrives.

Entry point: `python -m bc2800` → `bc2800.app:main`. Frozen exe: `dist/BC2800 Receptor/BC2800 Receptor.exe`.

## Hard product decisions (do not reverse without an explicit request)

- SQLite first; Excel is a convenience view. Excel write failure must never roll back SQLite.
- Excel **only appends new exam rows**. Never rewrite the whole workbook (the user edits Nome/Tutor/Observações in Excel).
- QC frames (`B` / `C`) go to SQLite only. No QC sheet in Excel. GUI only shows a “QC recebido” notice.
- Histogram WBC/RBC/PLT (256 channels × 3 ASCII digits × 3 series = **2304 bytes**) is **consumed and discarded**. Do not persist bins or draw charts unless asked.
- Units stay as the analyzer sends them (`g/L`, `10^9/L`, …). No g/dL conversion.
- Species names are **fixed** in `domain/species.py` (Cão, Gato, Cavalo, Suíno, Bovino, Búfalo, Caprino, Animal 1–4). Animal 1–4 are not user-renamable.
- Closing the main window hides to the **system tray**. Only tray **Sair** quits. Autostart via `HKCU\...\Run` is on by default.
- Identifier `"A"` is **not one layout**. Dispatch by trying `cdh` / `farm` / `goat` and validating `animal_type` against disjoint sets.
- `sample_id` is **text** (preserve leading zeros). Excel ID column must stay text (`number_format = "@"`).

## Layout of the repo

```
coms_info.txt              # Mindray appendix D (authoritative field widths)
src/bc2800/
  app.py                   # QApplication, single-instance QLockFile, MainWindow
  paths.py                 # app_root / data / logs (frozen vs source)
  config.py                # data/config.json
  protocol/
    symbols.py             # ENQ/STX/EOT/EOF/ETX/ACK/NACK, HISTO_BYTES
    framer.py              # byte state machine → CompleteFrame | SendByte
    layouts.py             # Field maps (offsets/widths). Edit here, not with regex.
    parser.py              # walk() + layout dispatch → Exam | QcEvent
  serial_io/               # NOT named `serial` (conflicts with pyserial)
    listener.py            # QThread + pyserial; dumps frames; emits Qt signals
  domain/models.py         # Exam, QcEvent dataclasses
  domain/species.py        # species + sample-mode labels
  persistence/
    sqlite_repo.py         # WAL, exams + qc_events, SHA-256 dedup
    excel_writer.py        # append + optional update of 3 user columns
    backup.py              # daily copy to data/backup/
  ui/                      # PySide6 window, tray, settings, autostart
tests/
  frames.py                # synthetic packers used by tests
  test_protocol.py
  test_persistence.py
packaging/bc2800.spec
scripts/build.ps1
```

Runtime files (gitignored): `data/` (sqlite, xlsx, config, lock, backups), `logs/` (`app.log` + `{stamp}-{A|B|C}.bin/.hex`), `dist/`, `build/`, `.venv/`.

## Protocol (must stay aligned with `coms_info.txt`)

Source of truth for field order/width: [`coms_info.txt`](coms_info.txt). Human BC-2800 manuals are similar but **not** identical (Vet ID width and animal-type forks differ).

### Serial / envelope

| Item | Value |
|---|---|
| Analyzer port | Serial **2**, DB9 pins 2 RXD, 3 TXD, 5 GND |
| Default serial | 9600, **7** data bits, 1 stop, parity **N**, no RTS/CTS |
| Handshake On | ENQ → host ACK → body → EOT → ETX → host ACK. NACK = retransmit body. Timeouts ~4 s on the analyzer; framer idle timeout is **8 s**. |
| Handshake Off | STX + body + EOF (no host ACK) |
| ACK policy | ACK if envelope is complete (`len(body) >= MIN_BODY_LEN` = 13). Persist even if `parse_ok=0`. NACK only truncated handshake frames. |
| `*` in a field | `NULL` |

`Framer` always ACKs ENQ and accepts both STX/EOF and ENQ/ETX. The settings checkbox `handshake` is stored for the operator to match the analyzer; the listener does not require it to parse.

Do not put control bytes in synthetic bodies. Histogram padding in tests is ASCII `'0'`.

### Exam identifier `"A"` — three layouts

`AnimalType` is **not** at a fixed offset. `parse_exam()` tries all three maps; species sets are disjoint.

| Layout | Species | ID width | DIFF (Lymph/Mid/Gran) | PLT/MPV/PDW/PCT | `animal_type` width | Prefix length |
|---|---|---|---|---|---|---|
| `cdh` | 0 Cão, 1 Gato, 2 Cavalo | 6 | yes | yes | 2 | **153** |
| `farm` | 3 Suíno, 4 Bovino, 5 Búfalo, 7–10 Animal 1–4 | 8 | no (reserved 16+5) | yes | 2 | **149** |
| `goat` | 6 Caprino | 8 | no | **no** (reserved 13+15) | **1** | **149** |

Trailing histograms: ignore extra bytes after the prefix (`HISTO_BYTES = 2304` when present). Prefix-only bodies are valid.

Numeric fields: only digits, space, `.`, `*` are plausible (`parser._plausible`). **Do not** run that check on `text` fields (`A`/`B`/`C`, lot numbers).

If no layout matches: `Exam(parse_ok=False, layout="unknown")` still persisted with `raw_payload`.

### QC

- `B` Standard L-J: prefix length **114**. `File No.` is treated as **1 byte** (`coms_info.txt` writes `File No. "B"`, likely a transcription error vs human `#`). Confirm on first live QC dump.
- `C` Run L-J: prefix length **62**. No lot / limits.

### Live calibration (first real analyzer)

1. Leave logging on; inspect `logs/*.hex`.
2. If ASCII is garbage, try **8N1** (or parity Odd/Even) in Settings to match the unit.
3. Confirm histogram skip and QC B file_no width against a real frame.
4. Adjust **only** `protocol/layouts.py` field lists, then add a fixture in `tests/frames.py`.

## Data flow

```
Analyzer --RS232--> SerialListener (QThread)
                 --> Framer.feed
                 --> dump_frame (logs/)
                 --> parse_body
                 --> Qt signal Exam | QcEvent
Main thread     --> SqliteRepo.insert_* (commit)
                 --> ExcelWriter.append_exam  (exams only; PermissionError → pending)
                 --> UI refresh / tray / beep
```

Dedup: `payload_sha256` UNIQUE on both tables. Exams also have a partial unique index on `(sample_id, exam_at, animal_type)` when all three are NOT NULL (NACK retransmission with identical payload, or same sample resent with different histo).

Pending Excel: `exams.excel_synced_at IS NULL`. Timer every **15 s** + button **Sincronizar planilha**.

User edits (Nome/Tutor/Obs): SQLite update, then `ExcelWriter.update_user_fields` matches row by ID + exam datetime label + species. If Excel is locked, SQLite still wins.

Daily backup: `data/backup/bc2800-YYYY-MM-DD.sqlite` (skip if today’s file exists).

## How to run, test, pack

Python **3.12+**, Windows.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m bc2800
python -m pytest tests -q
.\scripts\build.ps1
```

PyInstaller spec lives under `packaging/`; `SPECPATH` is that folder, so `ROOT = spec_dir.parent`. Always pass `--distpath dist --workpath build` from the **project root** (see `scripts/build.ps1`).

Analyzer-side setup to tell the operator: Handshake On, Auto transmit On, baud/parity matching the app (default 9600 7N1).

## Coding conventions for this repo

- Python 3.12, `from __future__ import annotations`, stdlib `sqlite3`, dataclasses.
- Protocol maps are **width tables**, never regex over the whole body.
- Package directory is `serial_io` on purpose.
- Persistence and UI run on the Qt main thread; the serial thread only parses and emits.
- GUI: `QApplication.setQuitOnLastWindowClosed(False)`. Keep the `QLockFile` alive for the process lifetime (`main()` already does this by holding `lock` across `app.exec()`).
- Do not add README/docs unless asked. Do not commit `data/`, `logs/`, `.venv/`, `dist/`, `build/`.
- After protocol or Excel-column changes, extend `tests/frames.py` and run pytest. Keep goat PLT empty and farm DIFF empty in the unified spreadsheet.
- Prefer editing existing modules over new layers. New exam fields belong in `Exam`, SQLite schema, `exam_row()`, and the GUI table together.

## Out of scope unless the user asks

- Histogram charts, QC Excel sheet, pre-exam animal registry, HGB g/dL, custom names for Animal 1–4, clinic LIS integration, non-Windows ports as a product target.

## Pointers

- Field widths: `coms_info.txt` + `src/bc2800/protocol/layouts.py`
- Operator-facing how-to: `README.md`
- Cursor always-on rule: `.cursor/rules/project-context.mdc`
