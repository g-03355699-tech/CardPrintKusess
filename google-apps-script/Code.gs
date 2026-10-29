/**
 * MyKUSESS Studio Card Print — penghubung Google Sheet
 * =====================================================
 * Skrip ini dipasang pada Google Sheet "Sistem Outing dan Pulang Bermalam"
 * (Extensions > Apps Script) dan diterbitkan sebagai Web App. Aplikasi
 * MyKusessCetak.exe memanggilnya untuk:
 *   - action=users  : senarai rekod dari tab "Users" (sama seperti eksport CSV)
 *   - action=photos : foto murid dari folder AppSheet (Users_Images/...)
 *   - action=ping   : uji sambungan
 *
 * Sheet TIDAK perlu dikongsi secara awam. Setiap permintaan mesti membawa
 * kunci rahsia (API_KEY) yang disimpan dalam Script Properties.
 *
 * Panduan pemasangan penuh: google-apps-script/PANDUAN.md
 */

// ---- TETAPAN ----
const SHEET_NAME = 'Users';
// Folder app AppSheet yang mengandungi folder "Users_Images"
// (e-KusessAppsV2-4878841). Laluan GambarID seperti "Users_Images/abc.jpg"
// dicari relatif kepada folder ini.
const PHOTO_ROOT_FOLDER_ID = '1wpNter8No8h24nJaq6MaKffZn39wTcJ7';
const MAX_PHOTOS_PER_REQUEST = 6;
const MAX_PHOTO_BYTES = 8 * 1024 * 1024;

/** Jalankan SEKALI dari editor (pilih fungsi ini > Run) untuk menjana kunci rahsia. */
function setupApiKey() {
  const key = Utilities.getUuid().replace(/-/g, '') + Utilities.getUuid().replace(/-/g, '').slice(0, 8);
  PropertiesService.getScriptProperties().setProperty('API_KEY', key);
  Logger.log('API_KEY baharu (salin ke aplikasi > Tetapan Google Sheet): ' + key);
}

function doGet(e) {
  try {
    const p = (e && e.parameter) || {};
    const expected = PropertiesService.getScriptProperties().getProperty('API_KEY');
    if (!expected) return json_({ ok: false, error: 'API_KEY belum ditetapkan. Jalankan setupApiKey() dalam editor Apps Script.' });
    if (!p.key || p.key !== expected) return json_({ ok: false, error: 'unauthorized' });

    switch (p.action) {
      case 'ping':
        return json_({ ok: true, sheet: SHEET_NAME, spreadsheet: SpreadsheetApp.getActiveSpreadsheet().getName() });
      case 'users':
        return json_(users_());
      case 'photos':
        return json_(photos_(JSON.parse(p.paths || '[]')));
      default:
        return json_({ ok: false, error: 'action tidak dikenali: ' + p.action });
    }
  } catch (err) {
    return json_({ ok: false, error: String(err && err.message || err) });
  }
}

function users_() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  if (!sheet) throw new Error('Tab "' + SHEET_NAME + '" tidak dijumpai');
  const values = sheet.getDataRange().getDisplayValues();
  if (!values.length) return { ok: true, headers: [], rows: [] };
  const headers = values[0].map(function (h) { return String(h).trim(); });
  const rows = values.slice(1).filter(function (r) {
    return r.some(function (c) { return String(c).trim() !== ''; });
  });
  return { ok: true, sheet: SHEET_NAME, headers: headers, rows: rows, generated: new Date().toISOString() };
}

function photos_(paths) {
  if (!Array.isArray(paths)) throw new Error('paths mesti senarai');
  const root = DriveApp.getFolderById(PHOTO_ROOT_FOLDER_ID);
  const out = {};
  paths.slice(0, MAX_PHOTOS_PER_REQUEST).forEach(function (path) {
    try {
      out[path] = photo_(root, String(path));
    } catch (err) {
      out[path] = { error: String(err && err.message || err) };
    }
  });
  return { ok: true, photos: out };
}

function photo_(root, path) {
  // Hanya nama folder/fail biasa — tiada "..", jadi carian tidak boleh keluar dari folder app.
  const parts = path.replace(/\\/g, '/').split('/').filter(function (s) { return s && s !== '.' && s !== '..'; });
  if (!parts.length) throw new Error('laluan kosong');
  const folder = resolveFolder_(root, parts.slice(0, -1));
  const files = folder.getFilesByName(parts[parts.length - 1]);
  if (!files.hasNext()) throw new Error('fail tidak dijumpai');
  const file = files.next();
  if (file.getSize() > MAX_PHOTO_BYTES) throw new Error('fail terlalu besar');
  const blob = file.getBlob();
  const mime = blob.getContentType() || '';
  if (mime.indexOf('image/') !== 0) throw new Error('bukan fail gambar');
  return { mime: mime, data: Utilities.base64Encode(blob.getBytes()) };
}

function resolveFolder_(root, names) {
  if (!names.length) return root;
  const cache = CacheService.getScriptCache();
  const cacheKey = 'folder:' + root.getId() + ':' + names.join('/');
  const cachedId = cache.get(cacheKey);
  if (cachedId) {
    try { return DriveApp.getFolderById(cachedId); } catch (e) { /* cache lapuk */ }
  }
  let folder = root;
  names.forEach(function (name) {
    const it = folder.getFoldersByName(name);
    if (!it.hasNext()) throw new Error('folder tidak dijumpai: ' + name);
    folder = it.next();
  });
  cache.put(cacheKey, folder.getId(), 21600);
  return folder;
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
