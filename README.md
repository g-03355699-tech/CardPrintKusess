# MyKUSESS Studio v1.03

Aplikasi desktop (Windows, Python + CustomTkinter) untuk menjana dan mencetak kad pengenalan (ID card) guru/murid MyKUSESS, lengkap dengan gambar, kod QR unik, dan maklumat individu. Menyokong cetakan satu-satu atau pukal (batch) daripada fail CSV.

## v1.03 — Nota Keluaran

- **Tetapan folder gambar & fail CSV disimpan automatik** — sebaik sahaja folder gambar dipilih atau CSV dimuat naik (termasuk pengekodan yang dipilih), tetapan tersebut disimpan (`app_settings.json`) dan dipulihkan secara automatik & senyap setiap kali aplikasi dimulakan; CSV terakhir turut dimuat semula terus ke senarai tanpa perlu klik "Muat Naik CSV" lagi.
- **Butang naik/turun (▲/▼) pada semua medan angka** di tab Konfigurasi Layout (kedudukan X/Y, lebar/tinggi, saiz QR, saiz font) — laraskan nilai dengan klik tanpa perlu menaip.
- **Pembetulan butang tersembunyi**: tab "Cetak Satu-Satu" dan "Cetak Pukal" kini boleh skrol — sebelum ini butang di bahagian bawah (cth. "Jana Preview", "Cetak Semua") boleh terpotong/hilang di luar paparan apabila kandungan tab lebih tinggi daripada ruang skrin.
- **Konfigurasi Layout disimpan automatik** — sebarang perubahan pada medan kedudukan/saiz, font, bold/italic, atau justifikasi kini terus disimpan (semasa medan kehilangan fokus, tukar dropdown/checkbox/justifikasi, tekan "Kemas Kini & Jana Preview", atau tutup aplikasi) supaya tetapan terakhir sentiasa dikekalkan tanpa perlu tekan "Simpan Layout" secara manual.

## v1.02 — Nota Keluaran

- **Templat Tersimpan (sehingga 4 slot)** — simpan sehingga 4 templat kad (background) asas terus dalam aplikasi (`template_presets.json`), tekan "Guna" untuk muat semula tanpa perlu buka dialog fail setiap kali. Slot 1 dimuat automatik secara senyap semasa aplikasi dimulakan.

## v1.01 — Nota Keluaran

- **Pulihkan butang "Pilih Semua" / "Nyahpilih Semua"** pada tab Cetak Pukal — tertinggal semasa penyatuan fail v1.00.
- **Simbol tanda baris lebih profesional & berwarna**: `✅`/`⬜` menggantikan `☑`/`☐`, dengan latar hijau lembut pada baris yang ditanda supaya senarai mudah dibaca sekali pandang.
- Fail aplikasi rasmi dinamakan semula: `app.py` → **`MyKusessCetak.py`** (dan `app.spec` → `MyKusessCetak.spec`, `dist/app.exe` → `dist/MyKusessCetak.exe`).

## v1.00 — Nota Keluaran

Ini keluaran rasmi pertama. Sebelum ini projek mempunyai tiga skrip aplikasi berasingan hasil evolusi pembangunan (`app.py`, `MyKusessPrint.py`, `MyKusessPrintV2.py`) dengan skema CSV yang tidak konsisten antara satu sama lain. Kesemuanya kini **disatukan menjadi satu fail rasmi** (dinamakan semula `MyKusessCetak.py` sejak v1.01), menggunakan skema yang sepadan dengan data export sebenar (`batch`/`email_moe`).

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

- `MyKusessCetak.py` — **fail aplikasi rasmi** (satu-satunya, entry point untuk `python MyKusessCetak.py` dan build `.exe`).
- `logo.ico` — ikon aplikasi (dipaparkan juga pada bar header).
- `layout_config.json` — tetapan layout kad tersimpan.
- `Users_Images/` — folder gambar murid/guru (rujukan oleh lajur `fail_gambar` dalam CSV).
- `Eksport_APDM_*.csv` — contoh/data export senarai murid.
- `Panduan_Pengguna_Sistem_Cetakan_Kad_MyKUSESS.pdf` — manual pengguna.
- `build/`, `dist/` — output PyInstaller (`dist/MyKusessCetak.exe`).
- `MyKusessCetak.spec` — konfigurasi build PyInstaller (entry point: `MyKusessCetak.py`).

## Keperluan

- Python 3.x (Windows, kerana bergantung pada `pywin32` untuk cetakan)
- Pakej: `customtkinter`, `Pillow`, `qrcode`, `pywin32`

```bash
pip install customtkinter pillow qrcode pywin32
```

## Menjalankan Aplikasi

```bash
python MyKusessCetak.py
```

## Membina Fail Executable (.exe)

```bash
pyinstaller MyKusessCetak.spec
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
