# Panduan: Sambung MyKUSESS Studio Card Print ke Google Sheet

Aplikasi boleh memuat senarai murid terus dari Google Sheet **"Sistem Outing dan Pulang Bermalam"** (tab **Users**) dan memuat turun foto dari folder AppSheet di Google Drive. Sheet **tidak perlu dikongsi secara awam** — aplikasi berhubung melalui skrip kecil dengan kunci rahsia.

Pemasangan dibuat **sekali sahaja** (±10 minit).

## 1. Pasang skrip pada sheet

1. Buka Google Sheet **Sistem Outing dan Pulang Bermalam**.
2. Menu **Extensions → Apps Script**.
3. Padam kandungan `Code.gs` yang sedia ada, kemudian tampal seluruh kandungan fail [`Code.gs`](Code.gs) dari folder ini.
4. Tekan ikon **Simpan** (💾).

> `PHOTO_ROOT_FOLDER_ID` dalam skrip sudah ditetapkan kepada folder app AppSheet `e-KusessAppsV2-4878841` (yang mengandungi `Users_Images`). Tukar hanya jika foto dipindahkan ke folder lain.

## 2. Jana kunci rahsia

1. Dalam editor Apps Script, pilih fungsi **`setupApiKey`** pada dropdown di bar atas, tekan **Run**.
2. Kali pertama, Google akan meminta kebenaran — pilih akaun anda → **Advanced** → **Go to ... (unsafe)** → **Allow**. (Skrip ini milik anda sendiri; amaran ini biasa bagi skrip yang belum disahkan Google.)
3. Buka **Execution log** — salin kunci yang dipaparkan selepas `API_KEY baharu ...`.

Simpan kunci ini dengan selamat. Jika ia terdedah, jalankan `setupApiKey` sekali lagi untuk menjana kunci baharu (kunci lama terus tidak sah), kemudian kemas kini kunci dalam aplikasi.

## 3. Terbitkan sebagai Web App

1. Tekan **Deploy → New deployment**.
2. Ikon gear ⚙ di sebelah *Select type* → pilih **Web app**.
3. Tetapkan:
   - **Execute as:** *Me* (akaun anda)
   - **Who has access:** *Anyone*
4. Tekan **Deploy**, kemudian salin **Web app URL** (berakhir dengan `/exec`).

> **Kenapa "Anyone"?** Aplikasi tidak log masuk ke Google, jadi Web App mesti boleh dicapai tanpa log masuk. Data tetap dilindungi kerana setiap permintaan tanpa kunci rahsia yang betul akan ditolak (`unauthorized`).
>
> Jika pilihan *Anyone* tiada (dihadkan oleh pentadbir Google Workspace MOE), penyelesaian alternatif diperlukan (cth. akses "Anyone within moe-dl.edu.my" tidak boleh digunakan oleh aplikasi tanpa log masuk).

## 4. Masukkan ke dalam aplikasi

1. Buka **MyKUSESS Studio Card Print** → tab **Cetak Pukal**.
2. Tekan ikon **⚙** di sebelah butang **Muat dari Google Sheet**.
3. Tampal **URL Web App** dan **Kunci Rahsia** → tekan **Uji Sambungan**. Mesej hijau *"Berjaya disambung ke 'Sistem Outing dan Pulang Bermalam'"* bermaksud semuanya betul.
4. Tekan **Simpan**, kemudian **Muat dari Google Sheet**.

Kali pertama, aplikasi memuat turun semua foto murid ke folder `photo_cache` di sebelah exe (beberapa minit untuk ±800 murid). Seterusnya hanya foto baharu dimuat turun, jadi muat semula menjadi pantas. Aplikasi juga akan memuat data terkini secara automatik setiap kali dibuka.

## Mengemas kini skrip

Jika `Code.gs` dikemas kini pada masa hadapan: tampal versi baharu → **Deploy → Manage deployments** → ikon pensel ✏ → **Version: New version** → **Deploy**. URL dan kunci kekal sama.

## Masalah biasa

| Mesej dalam aplikasi | Punca & penyelesaian |
|---|---|
| *Kunci rahsia (API Key) tidak sah* | Kunci salah salin atau telah dijana semula. Salin semula dari Execution log. |
| *Respons bukan data JSON* | Web App bukan akses *Anyone*, atau URL bukan yang berakhir `/exec`. |
| *API_KEY belum ditetapkan* | Langkah 2 belum dijalankan. |
| *Foto: N gagal (fail tidak dijumpai)* | Fail foto dalam lajur GambarID sudah dipadam/dialih dalam Drive. Kad tetap boleh dicetak tanpa foto. |
| *Tidak dapat menghubungi Google* | Tiada internet. Data & foto yang dimuat sebelum ini masih boleh digunakan melalui CSV/cache. |

## Privasi

- Folder `photo_cache` mengandungi foto sebenar murid. Jangan kongsi atau muat naik folder ini.
- Kunci rahsia disimpan dalam `app_settings.json` di komputer pengguna sahaja.
