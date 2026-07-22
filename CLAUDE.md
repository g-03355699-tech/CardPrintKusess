# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies (no requirements.txt exists — install manually)
pip install customtkinter pillow qrcode pywin32

# Run the app
python app.py

# Build the Windows executable (entry point: app.py, per app.spec)
pyinstaller app.spec
```

There are no tests, no linter, and no `requirements.txt` in this repo.

## Architecture

This is a single-window CustomTkinter desktop app (`app.py`, one `ctk.CTk` subclass named `CardPrinterApp`, Windows-only, uses `pywin32` for GDI printing) that composites a background template + student/teacher photo + QR code + text fields into a 1013×638 PNG "card" image, then either previews it, saves it, or sends it straight to a Windows printer via `win32ui`/`ImageWin`.

> As of v1.00, `app.py` is the single source of truth. Earlier development history had three independently-evolved, duplicate copies of this app (`app.py`, `MyKusessPrint.py`, `MyKusessPrintV2.py`) with inconsistent CSV schemas; they were consolidated into this one file and the other two deleted. Do not recreate that split — if a feature genuinely needs a variant, branch in git rather than forking the file.

### File structure

`__init__` is split into builder methods, each responsible for one region of the UI:

- `build_header` — top navy bar with app icon/name and the `APP_VERSION` badge.
- `build_tab_single` / `build_tab_batch` / `build_tab_config` — the three `CTkTabview` tabs (single card, batch CSV, layout config).
- `build_preview_panel` — the right-hand fixed preview + printer dropdown + print/download buttons.

Shared style tokens (`COLOR_*`, `FONT_FAMILY`) and small widget-factory helpers (`section_header`, `field_label`, `status_label`, `btn_primary`, `btn_secondary`, `btn_success`, `btn_danger`, `config_group_label`) live near the top of the class — reuse these instead of hardcoding colors/fonts when touching the UI, so the look stays consistent. The app forces `ctk.set_appearance_mode("Light")` deliberately: the styling uses hardcoded hex colors that aren't dark-mode aware.

The business-logic methods (unchanged in behavior across the redesign) are, in order:

1. **Config entries** (`cfg_img_*`, `cfg_qr_*`, `cfg_n1_*`, `cfg_n2_*`, `cfg_n3_*`) — raw `CTkEntry` widgets holding x/y/width/height/font-size/font-file/bold/italic/justify per element, built via `create_cfg_entry`. These are read back as plain strings and `int()`-parsed on every card render — there's no numeric validation, so non-numeric input surfaces as a raw exception in a message box.
2. **`save_layout_config` / `load_layout_config`** — serialize/deserialize the `cfg_*` widgets to/from `layout_config.json` in the CWD.
3. **`load_csv`** — reads the CSV (`kod_qr, batch, nama_penuh, email_moe, fail_gambar`) into `self.csv_data` (list of dicts, each tagged with `'pilih'` selection state) using a user-selected encoding (UTF-8 / UTF-8-SIG / cp1252), and populates the `ttk.Treeview`. `filter_search`/`refresh_treeview(filter_text)` do case-insensitive filtering by name/batch without touching `self.csv_data`.
4. **`make_card_image`** — the core renderer: opens the background template, resizes to 1013×638, pastes the contained/aspect-fit photo, generates and pastes the QR (`qrcode` lib, payload is `mykusses:<code>` — codes coming from CSV already carry the `mykusses:` prefix, so it's stripped before re-adding to avoid double-prefixing; QR is resized with `Image.NEAREST` to stay scan-sharp), then draws each text field with `ImageDraw` using a Windows system font resolved via `get_font_path` (maps a base font name to its bold/italic/bold-italic file name; Tahoma has no italic file on Windows and falls back to regular/bold).
5. **Preview / print / download** — `update_preview_ui` (resizes for the fixed-size preview panel), `generate_single_preview` / `on_tree_click` (batch), `print_single_card` / `print_batch` (writes a temp PNG then calls `send_to_printer`), `download_card_image`, `download_pdf_batch` (multi-page PDF via Pillow's `save_all`/`append_images`).
6. **`send_to_printer`** — raw GDI printing: creates a printer DC (`win32ui.CreateDC().CreatePrinterDC(name)`), `StartDoc`/`StartPage`, blits the image via `ImageWin.Dib` into a rect computed from the printer's actual printable area (`GetDeviceCaps(HORZRES/VERTRES)`) scaled to fit while preserving the card's aspect ratio — **do not** hardcode the destination rect back to a fixed pixel size, that's what caused v1.00's "stretched print" bug. Releases the DC in `finally` so a mid-print failure doesn't leak it.

### Card coordinate system

All layout coordinates (`img_x/y/w/h`, `qr_x/y/size`, `n1/n2/n3_x/y`) are pixel positions on the fixed 1013×638 canvas, independent of the background template's original resolution (the template is always resized to fill that canvas first). When adjusting default layout values or debugging misplaced elements, coordinates are relative to that canvas, not the source template image.

### Batch/CSV image resolution

In batch mode, `fail_gambar` from the CSV is joined with the user-selected photo folder (`os.path.join(self.photo_folder, photo_filename)`) — in the real exported CSVs, `fail_gambar` already includes a `Users_Images/...` subpath, so the folder the user picks in the UI is the *parent* of `Users_Images/`, not that folder itself.

### Sensitive data

`Eksport_APDM_*.csv` and `Users_Images/` contain real students'/teachers' names, emails, and photos, and are gitignored. Never re-add them to git, and be careful not to commit generated card renders (`temp_print.png`, `temp_print_card.png`, `temp_batch_print.png`) since those embed a real photo — they're gitignored too.
