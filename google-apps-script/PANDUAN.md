# Panduan: Sambung MyKUSESS Studio Card Print ke Google Sheet

Aplikasi boleh memuat senarai murid terus dari Google Sheet **"Sistem Outing dan Pulang Bermalam"** (tab **Users**) dan memuat turun foto dari folder AppSheet di Google Drive. Sheet **tidak perlu dikongsi secara awam**. Aplikasi berhubung melalui projek Apps Script **sedia ada** pada sheet itu, iaitu projek yang sama yang digunakan oleh kiosk imbasan dan ESP32, dan dilindungi kunci rahsia.

Pemasangan dibuat **sekali sahaja** (±10 minit). **Kiosk imbasan dan ESP32 tidak terjejas**, dan URL Web App kekal sama.

## 1. Tambah fail CardPrint.gs

1. Buka Google Sheet **Sistem Outing dan Pulang Bermalam** → **Extensions → Apps Script**.
2. Di panel kiri, tekan **＋** di sebelah *Files* → **Script** → namakan **`CardPrint`**.
3. Tampal seluruh kandungan fail [`CardPrint.gs`](CardPrint.gs) ke dalam fail baharu itu.
4. **Jangan ubah `Code.gs` selain langkah 2 di bawah.** `CardPrint.gs` sengaja tidak mempunyai `doGet` sendiri supaya tidak menindih `doGet` kiosk.

> `CP_PHOTO_ROOT_FOLDER_ID` sudah ditetapkan kepada folder app AppSheet `e-KusessAppsV2-4878841` (yang mengandungi `Users_Images`). Tukar hanya jika foto dipindahkan ke folder lain.

## 2. Tambah SATU baris dalam doGet sedia ada

Dalam `Code.gs`, tambah baris bertanda `// CardPrint` sebagai baris **pertama** dalam `doGet`:

```javascript
function doGet(e) {
  if (e && e.parameter && e.parameter.cardprint) return cardPrintHandle_(e); // CardPrint
  var api = (e && e.parameter && e.parameter.api) || '';
  var action = (e && e.parameter && e.parameter.action) || '';
  // ... selebihnya kekal sama ...
```

Baris ini hanya bertindak apabila permintaan membawa parameter `cardprint`. Hanya aplikasi kad yang menghantar parameter itu. Permintaan kiosk (`HalamanImbas`) dan ESP32 (`api=sebab`, `api=rekod`, `doPost`) berjalan seperti biasa.

Tekan **Simpan** (💾).

## 3. Jana kunci rahsia

1. Pada dropdown fungsi di bar atas, pilih **`setupCardPrintKey`**, kemudian tekan **Run**.
2. Jika Google meminta kebenaran baharu (akses Drive untuk membaca foto): pilih akaun anda → **Advanced** → **Go to ... (unsafe)** → **Allow**.
3. Buka **Execution log** dan salin kunci yang dipaparkan.

Jika kunci terdedah, jalankan `setupCardPrintKey` sekali lagi. Kunci lama terus tidak sah, kemudian kemas kini kunci dalam aplikasi.

## 4. Deploy versi baharu (URL kekal sama)

> ⚠️ **Jangan buat *New deployment*.** Kemas kini deployment sedia ada supaya URL kiosk dan ESP32 kekal sama.

1. **Deploy → Manage deployments**.
2. Pilih deployment Web App sedia ada → ikon pensel ✏.
3. **Version:** pilih **New version** → **Deploy**.
4. Salin **Web app URL** (berakhir dengan `/exec`). Ini URL yang sama yang digunakan kiosk dan ESP32.

Pastikan **Who has access** ialah *Anyone*. Biasanya ia sudah begitu kerana ESP32 menggunakan URL yang sama tanpa log masuk.

## 5. Masukkan ke dalam aplikasi

1. Buka **MyKUSESS Studio Card Print** → tab **Cetak Pukal**.
2. Tekan ikon **⚙** di sebelah butang **Muat dari Google Sheet**.
3. Tampal **URL Web App** dan **Kunci Rahsia**, kemudian tekan **Uji Sambungan**. Mesej hijau *"Berjaya disambung ke 'Sistem Outing dan Pulang Bermalam'"* bermaksud semuanya betul.
4. Tekan **Simpan**, kemudian **Muat dari Google Sheet**.

Kali pertama, aplikasi memuat turun semua foto murid ke folder `photo_cache` di sebelah exe (beberapa minit untuk ±800 murid). Selepas itu hanya foto baharu dimuat turun. Aplikasi juga memuat data terkini secara automatik setiap kali dibuka.

## Mengemas kini CardPrint.gs pada masa hadapan

Tampal versi baharu ke fail `CardPrint`, kemudian **Deploy → Manage deployments → ✏ → New version → Deploy**. URL dan kunci kekal sama.

## Masalah biasa

| Mesej dalam aplikasi | Punca & penyelesaian |
|---|---|
| *Web App memulangkan halaman web, bukan data* | Baris `cardprint` belum ditambah dalam `doGet`, atau versi baharu belum di-deploy (langkah 2 & 4). |
| *Kunci rahsia (API Key) tidak sah* | Kunci salah salin atau telah dijana semula. Salin semula dari Execution log. |
| *Kunci rahsia belum ditetapkan* | Langkah 3 belum dijalankan. |
| *Google meminta log masuk* | Deployment bukan akses *Anyone*, atau URL bukan yang berakhir `/exec`. |
| *Foto: N gagal (fail tidak dijumpai)* | Fail foto dalam lajur GambarID sudah dipadam atau dialih dalam Drive. Kad tetap boleh dicetak tanpa foto. |
| *Tidak dapat menghubungi Google* | Tiada internet. Foto yang sudah dimuat turun kekal dalam cache. |

## Privasi

- Folder `photo_cache` mengandungi foto sebenar murid. Jangan kongsi atau muat naik folder ini.
- Kunci rahsia disimpan dalam `app_settings.json` di komputer pengguna sahaja.
