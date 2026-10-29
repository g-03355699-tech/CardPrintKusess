# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies (no requirements.txt exists — install manually)
pip install customtkinter pillow qrcode pywin32

# Run the app
python MyKusessCetak.py

# Build the Windows executable (entry point: MyKusessCetak.py, per MyKusessCetak.spec)
pyinstaller MyKusessCetak.spec
```

There are no tests, no linter, and no `requirements.txt` in this repo.

### Release convention

`dist/MyKusessCetak.exe` and `build/` **are committed to git** (not gitignored) — this repo ships the built binary alongside source. After a behavior change intended for release, bump `APP_VERSION` in `MyKusessCetak.py`, rebuild with `pyinstaller MyKusessCetak.spec`, and commit source + rebuilt `dist/`/`build/` together. Match the existing commit message style, e.g. `Release v1.04: fix stretched/cropped card printing, rebuild exe` or `v1.03: editable Nama Penuh in batch list, rebuild exe`.

### Auto-update

On startup (2.5s after the UI is up) and via the header's "Semak Kemas Kini" button, the app queries `releases/latest` on the GitHub REST API (`UPDATE_REPO`), compares `tag_name` to `APP_VERSION` with `parse_version` (numeric tuple, so `v1.10 > v1.09`), and offers the update in `show_update_dialog`. The download prefers a `.exe` release asset (verified against its size and `sha256:` digest when the API provides them) and falls back to `dist/MyKusessCetak.exe` at that tag. Network calls run in a daemon thread via `_run_in_background`, which polls with `after()` so Tk is only touched from the main thread. `install_update_and_restart` renames the running exe to `.old` (Windows allows renaming, not overwriting, a running exe), moves `.new` into place, relaunches with `PYINSTALLER_RESET_ENVIRONMENT=1` so the onefile child doesn't reuse the dying parent's `_MEI` dir, and `cleanup_old_exe` deletes `.old` on the next start. Only active when frozen (`is_frozen_exe`); from source it just opens the release page. "Langkau versi ini" is stored in `update_settings.json` (gitignored), separate from `app_settings.json` because `save_app_settings` rewrites that file wholesale.

`.github/workflows/build-release.yml` automates releases: on a push to `main` touching `MyKusessCetak.py`, if no release exists for the current `APP_VERSION`, it builds the exe on `windows-latest`, creates a release tagged `APP_VERSION` (notes extracted from the README's `## <version> — Nota Keluaran` section, up to the next `## ` heading) and attaches the exe. So to ship: bump `APP_VERSION`, add the README release-notes section, push to `main` — no manual build or release needed. A manually published Release is also built and gets the exe attached, but the job **fails if `APP_VERSION` ≠ the release tag**, because a mismatched release would make every client re-download it forever (installed exe would still report an older version).

## Architecture

This is a single-window CustomTkinter desktop app (`MyKusessCetak.py`, one `ctk.CTk` subclass named `CardPrinterApp`, Windows-only, uses `pywin32` for GDI printing) that composites a background template + student/teacher photo + QR code + text fields into a 1013×638 PNG "card" image, then either previews it, saves it, or sends it straight to a Windows printer via `win32ui`/`ImageWin`.

> As of v1.00, this app was consolidated from three independently-evolved, duplicate copies (`app.py`, `MyKusessPrint.py`, `MyKusessPrintV2.py`) with inconsistent CSV schemas into one file, then renamed `app.py` → `MyKusessCetak.py`. `MyKusessCetak.py` is the single source of truth. Do not recreate that split — if a feature genuinely needs a variant, branch in git rather than forking the file.

### File structure

`__init__` is split into builder methods, each responsible for one region of the UI:

- `build_header` — gradient navy header canvas with app icon/name, "Pindah Tetapan" and update buttons, and the `APP_VERSION` badge.
- `build_tab_single` / `build_tab_batch` / `build_tab_config` — the three `CTkTabview` tabs (single card, batch CSV, layout config).
- `build_preview_panel` — the right-hand fixed preview (`PREVIEW_W`×`PREVIEW_H`, card ratio, shown as a HiDPI `CTkImage`) + printer dropdown + print/download buttons.
- `build_status_bar` — bottom status bar (row 2).

Shared style tokens (`COLOR_*`, `FONT_FAMILY`, `FONT_FAMILY_SEMIBOLD`) and widget-factory helpers live near the top of the class — reuse these instead of hardcoding colors/fonts when touching the UI, so the look stays consistent. The v1.08 "Studio" design: navy `COLOR_PRIMARY` for ordinary primary buttons/step badges, teal `COLOR_ACCENT` reserved for print CTAs (`btn_cta`), checkboxes and progress; `section_card(parent, number, title, subtitle, icon)` builds a numbered white card and returns its body frame (every tab is a `scroll_area` of these cards); `btn_primary`/`btn_cta`/`btn_secondary`/`btn_success`/`btn_danger` take an optional `icon=` name; `text_entry`, `combo_box`, `field_label`, `hint_label`, `status_label` (neutral grey by default — logic code sets `COLOR_SUCCESS`/`COLOR_DANGER` on outcome). Segmented controls (main tabs, justify) use the white-pill-on-grey-track style (`COLOR_SEG_TRACK`) because CTk's segmented button has a single `text_color`, so a dark selected pill would hide its label. Icons come from `assets/lucide-icons.ttf` (a subset of the ISC-licensed Lucide font, bundled via the spec's `datas`) rendered to `CTkImage` by `make_icon(name, color, size)` — to add an icon, add its codepoint to `ICON_CODES` **and** re-subset the font with that glyph (`pyftsubset lucide.ttf --unicodes=...`), otherwise it renders blank. `make_icon` returns `None` if the font is missing so buttons still work. The header is a `tk.Canvas` with a gradient image (`make_horizontal_gradient`, flat on the right so the right-hand widgets can sit on solid `COLOR_HEADER_BG2`). `build_status_bar`/`update_status_bar` show printer + record counts (refreshed from `refresh_treeview` and the printer combo). The app forces `ctk.set_appearance_mode("Light")` deliberately: the styling uses hardcoded hex colors that aren't dark-mode aware.

The business-logic methods (unchanged in behavior across the redesign) are, in order:

1. **Config entries** (`cfg_img_*`, `cfg_qr_*`, `cfg_n1_*`, `cfg_n2_*`, `cfg_n3_*`) — raw `CTkEntry` widgets holding x/y/width/height/font-size/font-file/bold/italic/justify per element, built via `create_cfg_entry`. These are read back as plain strings and `int()`-parsed on every card render — there's no numeric validation, so non-numeric input surfaces as a raw exception in a message box.
2. **`save_layout_config` / `load_layout_config`** — serialize/deserialize the `cfg_*` widgets to/from `layout_config.json` in the CWD.
3. **`load_csv`** — reads the CSV into `self.csv_data` (list of dicts, each tagged with `'pilih'` selection state) using a user-selected encoding (UTF-8 / UTF-8-SIG / cp1252), and populates the `ttk.Treeview`. `_load_csv_from_path` supports two header schemas via `_normalize_csv_row`, both normalized down to the internal `kod_qr, batch, nama_penuh, email_moe, fail_gambar` shape: the app's own schema (detected by a `kod_qr` header), and the raw "Sistem Outing dan Pulang Bermalam" export schema (detected by an `IDmykusess` header with no `kod_qr`) — mapping `IDmykusess`→`kod_qr`, `Tahap/Tgkt`+`Kelas`→`batch`, `Nama`→`nama_penuh`, `Emel`→`email_moe` (treating the `not_found@missing.my` placeholder as blank), `GambarID`→`fail_gambar`. This lets users import that raw export directly with no manual column reshuffling; add further raw schemas the same way, gated on a header that uniquely identifies them. `filter_search`/`refresh_treeview(filter_text)` do case-insensitive filtering by name/batch without touching `self.csv_data`.
4. **`make_card_image`** — the core renderer: opens the background template, resizes to 1013×638, then — if the resolved photo path exists (`has_photo`; missing/blank `fail_gambar` just skips the paste instead of raising, so a preview/print/PDF still renders without a photo) — square-crops the photo via `crop_to_square_keep_width` (center-crops height down to width for portrait photos; landscape/square photos pass through untouched) before fitting it into the photo box with `ImageOps.contain`, so a non-1:1 photo can no longer overflow into the name text below it. Then generates and pastes the QR (`qrcode` lib, payload is `mykusses:<code>` — codes coming from CSV already carry the `mykusses:` prefix, so it's stripped before re-adding to avoid double-prefixing; QR is resized with `Image.NEAREST` to stay scan-sharp), then draws each text field with `ImageDraw` using a Windows system font resolved via `get_font_path` (maps a base font name to its bold/italic/bold-italic file name; Tahoma has no italic file on Windows and falls back to regular/bold).
5. **Preview / print / download** — `update_preview_ui` (resizes for the fixed-size preview panel), `generate_single_preview` / `on_tree_click` (batch), `print_single_card` / `print_batch` (writes a temp PNG then calls `send_to_printer`), `download_card_image`, `download_pdf_batch` (multi-page PDF via Pillow's `save_all`/`append_images`).
6. **`send_to_printer`** — raw GDI printing: creates a printer DC (`win32ui.CreateDC().CreatePrinterDC(name)`), `StartDoc`/`StartPage`, blits the image via `ImageWin.Dib` edge-to-edge across the printer's full physical page (`GetDeviceCaps(PHYSICALWIDTH/HEIGHT)`, offset by `PHYSICALOFFSET`, falling back to `HORZRES`/`VERTRES` if unavailable) — **do not** reintroduce an independently-computed mm×DPI destination rect centered within that page, that both caused v1.00's "stretched print" bug (mismatched per-axis DPI) and, when "fixed" by computing per-axis size from `CARD_WIDTH_MM`/`CARD_HEIGHT_MM`, a ~1-2mm unprinted gap from rounding not matching the driver's own reported page size (v1.05). The physical page *is* the card on ID card printers, so filling it exactly is both simpler and correct. Releases the DC in `finally` so a mid-print failure doesn't leak it.

### Card coordinate system

All layout coordinates (`img_x/y/w/h`, `qr_x/y/size`, `n1/n2/n3_x/y`) are pixel positions on the fixed 1013×638 canvas, independent of the background template's original resolution (the template is always resized to fill that canvas first). When adjusting default layout values or debugging misplaced elements, coordinates are relative to that canvas, not the source template image.

### Google Sheet data source

Besides CSV, `load_from_gsheet` pulls the "Users" tab of the "Sistem Outing dan Pulang Bermalam" sheet through that sheet's **existing** Apps Script Web App — the same project/deployment/URL that serves the guard-house kiosk page (`HalamanImbas`) and the ESP32 API (`api=sebab|rekod`, `doPost`). `google-apps-script/CardPrint.gs` is added as an extra file with **no `doGet` of its own** (a second `doGet` would clobber the kiosk); the existing `doGet` gets one first line `if (e && e.parameter && e.parameter.cardprint) return cardPrintHandle_(e);`. So the app sends `GET <exec url>?key=<key>&cardprint=ping|users|photos` — never `action`/`api`, which the kiosk code uses. Globals in CardPrint.gs are `var` with a `CP_`/`cp` prefix because all .gs files share one global scope. The key lives in Script Property `CARDPRINT_API_KEY` (`setupCardPrintKey()`); after editing CardPrint.gs, redeploy as a *new version of the existing deployment* (Manage deployments), never a new deployment, or the kiosk/ESP32 URL changes. Setup steps for the user: `google-apps-script/PANDUAN.md`.

Module-level helpers (`gsheet_call`, `gsheet_fetch_rows`, `gsheet_download_photos`, `safe_cache_path`, no Tk) run on background threads via `_run_in_background`. `gsheet_call` turns a non-JSON reply into a specific error: a Google login page → "deployment must be Anyone"; any other HTML (i.e. the kiosk page, meaning the `cardprint` line is missing or not redeployed) → "add the cardprint line and redeploy". `cardprint=users` returns `getDisplayValues()` rows, fed through the same `_rows_to_records` → `_normalize_csv_row` path as CSV (raw-schema detection by the `IDmykusess` header), so both sources produce identical records; `_rows_to_records(previous=...)` preserves `pilih` marks by `kod_qr` on reload. Photos (`GambarID` = `Users_Images/...`, resolved in CardPrint.gs relative to the AppSheet app folder `CP_PHOTO_ROOT_FOLDER_ID`) are fetched as base64 in batches (`GSHEET_PHOTOS_PER_REQUEST` ≤ `CP_MAX_PHOTOS_PER_REQUEST`, `GSHEET_PARALLEL_REQUESTS` threads) into `photo_cache/` mirroring the relative path; only files not already present are downloaded. `self.data_source` is `"csv"` or `"gsheet"` and is persisted with `gsheet_url`/`gsheet_key` in `app_settings.json`; when it's `"gsheet"` startup re-loads from the sheet instead of the last CSV, and the batch print/PDF guards accept no photo folder. If you change CardPrint.gs's response shape, update `gsheet_fetch_rows`/`gsheet_download_photos` together.

### Settings transfer (.mykusess)

The header's "Pindah Tetapan" button (`open_transfer_dialog`) exports/imports a zip with `manifest.json` (`format: mykusess-settings`, `version`, slot→member map, `current_template`), `settings.json` (portable keys only — `csv_encoding`, `intake_year_t1`, plus `data_source`/`gsheet_url`/`gsheet_key` when "include Google Sheet" is ticked; never machine paths like `photo_folder`/`csv_path`), `layout.json` (`layout_config_dict()`), and `templates/<n>_<basename>` (each distinct template file once, even if used by several slots). Pure helpers `build_settings_bundle` / `read_settings_bundle` / `write_bundle_template` have no Tk. Import validates everything before writing (format, version ≤ `SETTINGS_BUNDLE_VERSION`, image extensions only, size caps), never uses `extractall`, writes templates by sanitized basename into `TEMPLATE_IMPORT_DIR` (`templat/`, de-duplicated by content), rewrites slot paths to those copies, then reloads layout/presets/settings and, if the source is Google Sheet, calls `load_from_gsheet`. `app_settings_dict()`/`layout_config_dict()` are the single sources for what gets saved — add new persisted settings there, and to the portable key list in `build_settings_bundle` if they should travel between PCs. Bump `SETTINGS_BUNDLE_VERSION` only for incompatible format changes. `.mykusess` files contain the API key and are gitignored.

### Batch/CSV image resolution

In batch mode, `fail_gambar` is resolved by `batch_photo_path`: first joined with the user-selected photo folder (`os.path.join(self.photo_folder, photo_filename)`), then `photo_cache/` (Google Drive downloads) — in the real exported CSVs, `fail_gambar` already includes a `Users_Images/...` subpath, so the folder the user picks in the UI is the *parent* of `Users_Images/`, not that folder itself.

### Persisted state files

- `layout_config.json` — card layout; tracked in git as the shipped default (see `save_layout_config`/`load_layout_config` above).
- `app_settings.json` (gitignored) — last-used photo folder, CSV path, CSV encoding, data source (`csv`/`gsheet`), Google Sheet Web App URL + API key, and the "Tahun Kemasukan Tingkatan 1" intake year (used by `_tahap_to_batch_label`), silently restored on startup via `restore_app_settings`/saved via `save_app_settings` — restored *before* the last CSV auto-loads, so raw-schema batch labels compute correctly on startup.
- `template_presets.json` (gitignored) — up to 4 saved background template slots (`load_template_presets`/`save_template_presets`); slot 1 auto-loads silently on startup.

### Sensitive data

`Eksport_APDM_*.csv`, `Sistem Outing dan Pulang Bermalam - Users.csv`, `Users_Images/`, and `photo_cache/` (Google Drive photo cache) contain real students'/teachers' names, emails, and photos, and are gitignored. Never re-add them to git, and be careful not to commit generated card renders (`temp_print.png`, `temp_print_card.png`, `temp_batch_print.png`) since those embed a real photo — they're gitignored too.
