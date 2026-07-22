# MyKUSESS Studio v1.00

Aplikasi desktop (Windows, Python + CustomTkinter) untuk menjana dan mencetak kad pengenalan (ID card) guru/murid MyKUSESS, lengkap dengan gambar, kod QR unik, dan maklumat individu. Menyokong cetakan satu-satu atau pukal (batch) daripada fail CSV.

## v1.00 — Nota Keluaran

Ini keluaran rasmi pertama. Sebelum ini projek mempunyai tiga skrip aplikasi berasingan hasil evolusi pembangunan (`app.py`, `MyKusessPrint.py`, `MyKusessPrintV2.py`) dengan skema CSV yang tidak konsisten antara satu sama lain. Kesemuanya kini **disatukan menjadi satu fail rasmi, `app.py`**, menggunakan skema yang sepadan dengan data export sebenar (`batch`/`email_moe`).

Selain penyatuan itu, v1.00 turut membawa:
- **Reka bentuk semula UI** — bar header berjenama, palet warna profesional konsisten (tema cerah, aksen biru), kad seksyen bernombor, dan panel pratonton yang lebih menonjol — dipermudahkan mengikut gaya perisian reka bentuk kad seperti Badgy Studio.
- **Pembetulan bug cetakan**: kod QR tidak lagi berganda-prefix (`mykusses:mykusses:...`) apabila mencetak dari CSV; QR diresize dengan penapis nearest-neighbour supaya kekal tajam/boleh diimbas; hasil cetakan tidak lagi diregangkan (stretched) berbanding pratonton — petak cetakan kini dikira mengikut kawasan boleh cetak sebenar pencetak sambil mengekalkan nisbah aspek kad; kebocoran resource pencetak (device context) apabila cetakan gagal turut dibetulkan.

## Ciri-ciri Utama

- **Cetak Satu-Satu** — masukkan maklumat individu secara manual dan jana kad terus.
- **Cetak Pukal (CSV)** — muat naik senarai murid/guru dari CSV + folder gambar, cari/tapis, tanda rekod yang mahu dicetak, cetak semua sekali gus.
- **Konfigurasi Layout** — laraskan kedudukan, saiz, font (bold/italic/justify) bagi gambar, QR code, dan setiap medan teks pada kad; boleh disimpan/dimuat semula (`layout_config.json`).
- **Kod QR** — dijana automatik dengan prefix `mykusses:` merujuk kod unik setiap individu (tidak berganda walaupun kod dari CSV sudah mengandungi prefix tersebut).
- **Muat Turun** — simpan kad sebagai PNG, atau jana PDF pukal bagi semua rekod bertanda.
- **Cetak Terus ke Pencetak** — melalui Windows Print API (`pywin32`), dengan nisbah aspek kad dikekalkan tepat seperti pratonton.

## Struktur Fail

- `app.py` — **fail aplikasi rasmi** (satu-satunya, entry point untuk `python app.py` dan build `.exe`).
- `logo.ico` — ikon aplikasi (dipaparkan juga pada bar header).
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
```

## Membina Fail Executable (.exe)

```bash
pyinstaller app.spec
```

Output akan berada dalam folder `dist/`.

## Format CSV

```
kod_qr,batch,nama_penuh,email_moe,fail_gambar
mykusses:tnf4042,Batch 26-30,MUHAMMAD HARITH BIN MUHD AZIB,contoh@moe-dl.edu.my,Users_Images/nama_fail.png
```

`fail_gambar` adalah path relatif kepada folder gambar yang dipilih dalam aplikasi (biasanya folder ibu bapa yang mengandungi `Users_Images/`).

## Nota

- Fail `Eksport_APDM_*.csv` dan `Users_Images/` mengandungi data peribadi (nama, emel, foto) — tidak ditrack dalam git (`.gitignore`); pastikan tidak dikongsi/dipush ke repositori awam tanpa kebenaran.
