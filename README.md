# Sistem Cetakan Kad MyKUSESS

Aplikasi desktop (Windows, Python + CustomTkinter) untuk menjana dan mencetak kad pengenalan (ID card) guru/murid MyKUSESS, lengkap dengan gambar, kod QR unik, dan maklumat individu. Menyokong cetakan satu-satu atau pukal (batch) daripada fail CSV.

## Ciri-ciri Utama

- **Cetak Satu-Satu** — masukkan maklumat individu secara manual dan jana kad terus.
- **Cetak Pukal (CSV)** — muat naik senarai murid/guru dari CSV + folder gambar, tanda rekod yang mahu dicetak, cetak semua sekali gus.
- **Konfigurasi Layout** — laraskan kedudukan, saiz, font (bold/italic/justify) bagi gambar, QR code, dan setiap medan teks pada kad; boleh disimpan/dimuat semula (`layout_config.json`).
- **Kod QR** — dijana automatik dengan prefix `mykusses:` merujuk kod unik setiap individu.
- **Muat Turun** — simpan kad sebagai PNG (dan PDF pukal, dalam `MyKusessPrint.py`).
- **Cetak Terus ke Pencetak** — melalui Windows Print API (`pywin32`).

## Struktur Fail

Projek ini mempunyai beberapa varian skrip aplikasi hasil evolusi pembangunan — **ketahui perbezaan skema sebelum edit**:

| Fail | Skema CSV | Status |
|---|---|---|
| `app.py` | `kod_qr, nama_panggilan, nama_penuh, fail_gambar` | Dibina oleh `app.spec` → `dist/app.exe` |
| `MyKusessPrint.py` | `kod_qr, batch, nama_penuh, email_moe, fail_gambar` | Sepadan dengan CSV export sebenar (`Eksport_APDM_*.csv`); ada carian, PDF batch, pilihan encoding CSV |
| `MyKusessPrintV2.py` | sama seperti `app.py` + ciri tanda/tick pilihan (Pilih Semua / Nyahpilih Semua) pada senarai batch |

> ⚠️ `app.py` (fail rasmi yang dibina jadi `.exe`) **tidak serasi** dengan format CSV export sebenar yang digunakan (`Eksport_APDM_2026-07-15.csv`). Sila tentukan fail mana yang menjadi sumber rasmi sebelum build seterusnya.

Fail/folder lain:
- `logo.ico` — ikon aplikasi.
- `layout_config.json` — tetapan layout kad tersimpan.
- `Users_Images/` — folder gambar murid/guru (rujukan oleh lajur `fail_gambar` dalam CSV).
- `Eksport_APDM_*.csv` — contoh/data export senarai murid.
- `Panduan_Pengguna_Sistem_Cetakan_Kad_MyKUSESS.pdf` — manual pengguna.
- `build/`, `dist/` — output PyInstaller.
- `app.spec` — konfigurasi build PyInstaller (entry point: `app.py`).

## Keperluan

- Python 3.x (Windows, kerana bergantung pada `pywin32` untuk cetakan)
- Pakej: `customtkinter`, `Pillow`, `qrcode`, `pywin32`

```bash
pip install customtkinter pillow qrcode pywin32
```

## Menjalankan Aplikasi

```bash
python app.py
# atau
python MyKusessPrint.py
```

## Membina Fail Executable (.exe)

```bash
pyinstaller app.spec
```

Output akan berada dalam folder `dist/`.

## Format CSV (contoh: `MyKusessPrint.py`)

```
kod_qr,batch,nama_penuh,email_moe,fail_gambar
mykusses:tnf4042,Batch 26-30,MUHAMMAD HARITH BIN MUHD AZIB,contoh@moe-dl.edu.my,Users_Images/nama_fail.png
```

`fail_gambar` adalah path relatif kepada folder gambar yang dipilih dalam aplikasi.

## Nota

- Fail `Eksport_APDM_*.csv` dan `Users_Images/` mengandungi data peribadi (nama, emel) — pastikan tidak dikongsi/dipush ke repositori awam tanpa kebenaran.
