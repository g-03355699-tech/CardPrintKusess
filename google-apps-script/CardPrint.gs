/**
 * MyKUSESS Studio Card Print — penghubung Google Sheet
 * =====================================================
 * Fail TAMBAHAN untuk projek Apps Script sedia ada pada sheet
 * "Sistem Outing dan Pulang Bermalam" (yang sudah ada doGet/doPost untuk
 * kiosk imbasan & ESP32). Fail ini TIDAK mengandungi doGet sendiri supaya
 * tidak menindih doGet sedia ada. Ia diaktifkan dengan SATU baris di awal
 * doGet sedia ada:
 *
 *     if (e && e.parameter && e.parameter.cardprint) return cardPrintHandle_(e);
 *
 * Permintaan aplikasi MyKusessCetak.exe sentiasa membawa parameter
 * "cardprint", jadi permintaan kiosk/ESP32 (api=..., action=rekod) tidak
 * terjejas langsung.
 *
 *   ?cardprint=ping    — uji sambungan
 *   ?cardprint=users   — senarai rekod tab "Users" (sama seperti eksport CSV)
 *   ?cardprint=photos  — foto murid dari folder AppSheet (Users_Images/...)
 *
 * Setiap permintaan mesti membawa ?key=<kunci rahsia> (Script Property
 * CARDPRINT_API_KEY, dijana oleh setupCardPrintKey()).
 *
 * Panduan pemasangan: google-apps-script/PANDUAN.md
 */

// ---- TETAPAN (awalan CP_ supaya tidak bertembung dengan kod sedia ada) ----
var CP_SHEET_NAME = 'Users';
// Folder app AppSheet yang mengandungi folder "Users_Images"
// (e-KusessAppsV2-4878841). Laluan GambarID seperti "Users_Images/abc.jpg"
// dicari relatif kepada folder ini.
var CP_PHOTO_ROOT_FOLDER_ID = '1wpNter8No8h24nJaq6MaKffZn39wTcJ7';
var CP_MAX_PHOTOS_PER_REQUEST = 6;
var CP_MAX_PHOTO_BYTES = 8 * 1024 * 1024;
var CP_KEY_PROPERTY = 'CARDPRINT_API_KEY';

/** Jalankan SEKALI dari editor (pilih fungsi ini > Run) untuk menjana kunci rahsia. */
function setupCardPrintKey() {
  var key = Utilities.getUuid().replace(/-/g, '') + Utilities.getUuid().replace(/-/g, '').slice(0, 8);
  PropertiesService.getScriptProperties().setProperty(CP_KEY_PROPERTY, key);
  Logger.log('Kunci rahsia CardPrint baharu (salin ke aplikasi > Tetapan Google Sheet): ' + key);
}

/** Dipanggil dari doGet sedia ada apabila parameter "cardprint" wujud. */
function cardPrintHandle_(e) {
  try {
    var p = (e && e.parameter) || {};
    var expected = PropertiesService.getScriptProperties().getProperty(CP_KEY_PROPERTY);
    if (!expected) return cpJson_({ ok: false, error: 'Kunci rahsia belum ditetapkan. Jalankan setupCardPrintKey() dalam editor Apps Script.' });
    if (!p.key || p.key !== expected) return cpJson_({ ok: false, error: 'unauthorized' });

    switch (p.cardprint) {
      case 'ping':
        return cpJson_({ ok: true, sheet: CP_SHEET_NAME, spreadsheet: SpreadsheetApp.getActiveSpreadsheet().getName() });
      case 'users':
        return cpJson_(cpUsers_());
      case 'photos':
        return cpJson_(cpPhotos_(JSON.parse(p.paths || '[]')));
      default:
        return cpJson_({ ok: false, error: 'permintaan tidak dikenali: ' + p.cardprint });
    }
  } catch (err) {
    return cpJson_({ ok: false, error: String(err && err.message || err) });
  }
}

function cpUsers_() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(CP_SHEET_NAME);
  if (!sheet) throw new Error('Tab "' + CP_SHEET_NAME + '" tidak dijumpai');
  var values = sheet.getDataRange().getDisplayValues();
  if (!values.length) return { ok: true, headers: [], rows: [] };
  var headers = values[0].map(function (h) { return String(h).trim(); });
  var rows = values.slice(1).filter(function (r) {
    return r.some(function (c) { return String(c).trim() !== ''; });
  });
  return { ok: true, sheet: CP_SHEET_NAME, headers: headers, rows: rows, generated: new Date().toISOString() };
}

function cpPhotos_(paths) {
  if (!Array.isArray(paths)) throw new Error('paths mesti senarai');
  var root = DriveApp.getFolderById(CP_PHOTO_ROOT_FOLDER_ID);
  var out = {};
  paths.slice(0, CP_MAX_PHOTOS_PER_REQUEST).forEach(function (path) {
    try {
      out[path] = cpPhoto_(root, String(path));
    } catch (err) {
      out[path] = { error: String(err && err.message || err) };
    }
  });
  return { ok: true, photos: out };
}

function cpPhoto_(root, path) {
  // Hanya nama folder/fail biasa — tiada "..", jadi carian tidak boleh keluar dari folder app.
  var parts = path.replace(/\\/g, '/').split('/').filter(function (s) { return s && s !== '.' && s !== '..'; });
  if (!parts.length) throw new Error('laluan kosong');
  var folder = cpResolveFolder_(root, parts.slice(0, -1));
  var files = folder.getFilesByName(parts[parts.length - 1]);
  if (!files.hasNext()) throw new Error('fail tidak dijumpai');
  var file = files.next();
  if (file.getSize() > CP_MAX_PHOTO_BYTES) throw new Error('fail terlalu besar');
  var blob = file.getBlob();
  var mime = blob.getContentType() || '';
  if (mime.indexOf('image/') !== 0) throw new Error('bukan fail gambar');
  return { mime: mime, data: Utilities.base64Encode(blob.getBytes()) };
}

function cpResolveFolder_(root, names) {
  if (!names.length) return root;
  var cache = CacheService.getScriptCache();
  var cacheKey = 'cpfolder:' + root.getId() + ':' + names.join('/');
  var cachedId = cache.get(cacheKey);
  if (cachedId) {
    try { return DriveApp.getFolderById(cachedId); } catch (e) { /* cache lapuk */ }
  }
  var folder = root;
  names.forEach(function (name) {
    var it = folder.getFoldersByName(name);
    if (!it.hasNext()) throw new Error('folder tidak dijumpai: ' + name);
    folder = it.next();
  });
  cache.put(cacheKey, folder.getId(), 21600);
  return folder;
}

function cpJson_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
