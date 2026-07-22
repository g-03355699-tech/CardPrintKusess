# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies (no requirements.txt exists — install manually)
pip install customtkinter pillow qrcode pywin32

# Run the app (pick the file you're actually working on — see "Which file is real" below)
python app.py
python MyKusessPrint.py
python MyKusessPrintV2.py

# Build the Windows executable (entry point is hardcoded to app.py in app.spec)
pyinstaller app.spec
```

There are no tests, no linter, and no `requirements.txt` in this repo.

## Architecture

This is a single-window CustomTkinter desktop app (Windows-only, uses `pywin32` for GDI printing) that composites a background template + student/teacher photo + QR code + text fields into a 1013×638 PNG "card" image, then either previews it, saves it, or sends it straight to a Windows printer via `win32ui`/`ImageWin`.

### Three parallel copies of the same app — know which one you're editing

The repo contains three near-duplicate, independently-evolved copies of the entire app, each a single self-contained `ctk.CTk` subclass (`CardPrinterApp`) with no shared modules:

- **`app.py`** — the file `app.spec` actually builds into `dist/app.exe`. CSV schema: `kod_qr, nama_panggilan, nama_penuh, fail_gambar`.
- **`MyKusessPrintV2.py`** — same schema as `app.py`, plus tick-box row selection in the batch tab (`Pilih Semua` / `Nyahpilih Semua`, `select_all_records`/`deselect_all_records`/`on_tree_click`/`refresh_treeview`) instead of single-row `<<TreeviewSelect>>`.
- **`MyKusessPrint.py`** — a *different* CSV schema: `kod_qr, batch, nama_penuh, email_moe, fail_gambar` (adds a third text field + CSV encoding selector + search box + PDF batch export). This is the schema that matches the real exported data in this repo (`Eksport_APDM_*.csv`) and the saved `layout_config.json` (which has `n3_*` keys — only `MyKusessPrint.py` reads those).

**Because of this, a bug fix or feature almost always needs to be applied in all three files** (they don't share code), and before making CSV/schema-related changes, check which file's field names match `layout_config.json` and any CSV the user is actually testing with. When in doubt, ask which file is the intended source of truth rather than guessing — `app.py` being the PyInstaller entry point does not necessarily mean it's the actively-developed one.

### Per-file structure (identical across all three)

Each file is one big class with these regions, in order:

1. **`__init__`**: builds a 2-column grid — left side is a `CTkTabview` with three tabs (`Cetak Satu-Satu` / single card, `Cetak Pukal (CSV)` / batch, `Konfigurasi Layout` / layout config), right side is a fixed preview panel + printer dropdown + print/download buttons.
2. **Config entries** (`cfg_img_*`, `cfg_qr_*`, `cfg_n1_*`, `cfg_n2_*`, [`cfg_n3_*`]) — raw `CTkEntry` widgets holding x/y/width/height/font-size/font-file/bold/italic/justify per element, built via `create_cfg_entry`. These are read back as plain strings and `int()`-parsed on every card render — there's no numeric validation, so non-numeric input surfaces as a raw exception in a message box.
3. **`save_layout_config` / `load_layout_config`** — serialize/deserialize the `cfg_*` widgets to/from `layout_config.json` in the CWD.
4. **`load_csv`** — reads the CSV into `self.csv_data` (list of dicts, each tagged with `'pilih'` selection state) and populates the `ttk.Treeview`.
5. **`make_card_image`** — the core renderer: opens the background template, resizes to 1013×638, pastes the contained/aspect-fit photo, generates and pastes the QR (`qrcode` lib, payload is `mykusses:<code>` — codes coming from CSV already carry the `mykusses:` prefix, so it's stripped before re-adding to avoid double-prefixing), then draws each text field with `ImageDraw` using a Windows system font resolved via `get_font_path` (maps a base font name to its bold/italic/bold-italic file name; Tahoma has no italic file on Windows and falls back to regular/bold).
6. **Preview / print / download** — `update_preview_ui` (resizes for the fixed-size preview panel), `generate_single_preview` / batch tree click handlers, `print_single_card` / `print_batch` (writes a temp PNG then calls `send_to_printer`), `download_card_image`, and in `MyKusessPrint.py` only, `download_pdf_batch` (multi-page PDF via Pillow's `save_all`/`append_images`).
7. **`send_to_printer`** — raw GDI printing: creates a printer DC (`win32ui.CreateDC().CreatePrinterDC(name)`), `StartDoc`/`StartPage`, blits the image via `ImageWin.Dib`, `EndPage`/`EndDoc`, and releases the DC in `finally` so a mid-print failure doesn't leak the DC.

### Card coordinate system

All layout coordinates (`img_x/y/w/h`, `qr_x/y/size`, `n1/n2/n3_x/y`) are pixel positions on the fixed 1013×638 canvas, independent of the background template's original resolution (the template is always resized to fill that canvas first). When adjusting default layout values or debugging misplaced elements, coordinates are relative to that canvas, not the source template image.

### Batch/CSV image resolution

In batch mode, `fail_gambar` from the CSV is joined with the user-selected photo folder (`os.path.join(self.photo_folder, photo_filename)`) — in the real exported CSVs, `fail_gambar` already includes a `Users_Images/...` subpath, so the folder the user picks in the UI is the *parent* of `Users_Images/`, not that folder itself.
