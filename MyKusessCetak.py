import os
import csv
import json
import sys
import re
import random
import string
import datetime
import base64
import concurrent.futures
import hashlib
import subprocess
import threading
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
import zipfile
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageDraw, ImageFont, ImageTk, ImageOps
import qrcode
import win32print
import win32ui
import win32con
from PIL import ImageWin

APP_VERSION = "v1.10"

# --- AUTO-UPDATE (GitHub Releases) ---
UPDATE_REPO = "g-03355699-tech/CardPrintKusess"
UPDATE_API_URL = f"https://api.github.com/repos/{UPDATE_REPO}/releases/latest"
UPDATE_RELEASES_PAGE = f"https://github.com/{UPDATE_REPO}/releases/latest"
# Jika release tiada aset .exe dilampirkan, exe diambil daripada dist/ pada tag release tersebut
# (konvensyen repo: dist/MyKusessCetak.exe di-commit bersama setiap release).
UPDATE_FALLBACK_EXE_URL = "https://github.com/" + UPDATE_REPO + "/raw/{tag}/dist/MyKusessCetak.exe"
UPDATE_SETTINGS_FILENAME = "update_settings.json"
UPDATE_USER_AGENT = f"MyKusessCetak/{APP_VERSION}"

# ============================================================
#  TEMA & GAYA — identiti visual "Studio": navy korporat + aksen teal
# ============================================================
ctk.set_appearance_mode("Light")   # tema cerah konsisten (elak konflik warna hardcode dgn mod gelap)
ctk.set_default_color_theme("blue")

FONT_FAMILY = "Segoe UI"
FONT_FAMILY_SEMIBOLD = "Segoe UI Semibold"   # tajuk & butang (lebih kemas daripada "bold" tiruan)

COLOR_BG             = "#EEF2F7"  # latar belakang tetingkap
COLOR_HEADER_BG      = "#0B1B33"  # header: navy gelap (kiri)...
COLOR_HEADER_BG2     = "#123E66"  # ...ke biru korporat (kanan) — kecerunan
COLOR_HEADER_TEXT    = "#F8FAFC"
COLOR_HEADER_MUTED   = "#93A8C3"
COLOR_SURFACE        = "#FFFFFF"  # permukaan kad / panel
COLOR_SURFACE_ALT    = "#F4F7FA"  # permukaan sekunder (medan, jubin, kawasan pratonton)
COLOR_BORDER         = "#DCE3EB"
COLOR_BORDER_STRONG  = "#C7D2DE"
COLOR_TEXT           = "#0F1C2E"
COLOR_TEXT_MUTED     = "#5B6B7F"
COLOR_TEXT_SUBTLE    = "#8A98AA"
COLOR_PRIMARY        = "#102C4F"  # navy — butang utama, lencana langkah, tab aktif
COLOR_PRIMARY_HOVER  = "#0A1F3A"
COLOR_ACCENT         = "#0E8A86"  # teal — tindakan cetak (CTA), kotak semak, bar kemajuan
COLOR_ACCENT_HOVER   = "#0B706D"
COLOR_ACCENT_SOFT    = "#E2F3F2"
COLOR_SEG_TRACK      = "#E1E7EF"  # trek kawalan bersegmen (tab, justifikasi)
COLOR_SEG_HOVER      = "#D4DCE6"
COLOR_SUCCESS        = "#15803D"
COLOR_SUCCESS_HOVER  = "#116B33"
COLOR_SUCCESS_SOFT   = "#E7F6EC"
COLOR_DANGER         = "#C62828"
COLOR_DANGER_HOVER   = "#A51F1F"
COLOR_DANGER_SOFT    = "#FDECEC"
COLOR_NEUTRAL        = "#64748B"
COLOR_NEUTRAL_HOVER  = "#475569"

# --- IKON (fon Lucide, lesen ISC — lihat assets/LUCIDE-LICENSE.txt) ---
# Ikon dilukis daripada fon ikon ke imej supaya tajam & seragam di semua mesin,
# menggantikan emoji yang rupanya berbeza-beza mengikut versi Windows.
ICON_FONT_FILE = os.path.join("assets", "lucide-icons.ttf")
ICON_CODES = {
    "printer": "e141", "upload": "e19e", "folder-open": "e247", "download": "e0b2", "save": "e14d",
    "refresh-cw": "e145", "search": "e151", "user": "e19f", "image": "e0f6", "square-check": "e559",
    "square": "e167", "id-card": "e617", "users": "e1a4", "file-text": "e0cc", "layout-template": "e207",
    "shuffle": "e15e", "x": "e1b2", "check": "e06c", "eye": "e0ba", "file-spreadsheet": "e326",
    "sliders-horizontal": "e29a", "qr-code": "e1df", "circle-check": "e226", "info": "e0f9",
    "scan-line": "e258", "type": "e198", "sparkles": "e412", "hash": "e0ef", "mail": "e10f",
    "calendar": "e063", "database": "e0ad", "rotate-ccw": "e148", "folder-input": "e334",
    "list-checks": "e1d0", "square-dashed": "e1cb",
    "sheet": "e157", "settings": "e154", "cloud-download": "e089", "link": "e102", "key-round": "e4a3",
    "plug-zap": "e45c", "table": "e17d",
}


def resource_path(relative):
    """Laluan fail sumber yang dibundel (berfungsi dari kod sumber & dari exe PyInstaller)."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


_icon_cache = {}


def make_icon(name, color="#FFFFFF", size=16):
    """CTkImage bagi ikon Lucide; None jika fon ikon tiada (butang tetap berfungsi tanpa ikon)."""
    key = (name, color, size)
    if key in _icon_cache:
        return _icon_cache[key]
    icon = None
    try:
        font = ImageFont.truetype(resource_path(ICON_FONT_FILE), size * 4)
        img = Image.new("RGBA", (size * 4, size * 4), (0, 0, 0, 0))
        ImageDraw.Draw(img).text((size * 2, size * 2), chr(int(ICON_CODES[name], 16)), font=font, fill=color, anchor="mm")
        img = img.resize((size * 2, size * 2), Image.Resampling.LANCZOS)
        icon = ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))
    except Exception:
        icon = None
    _icon_cache[key] = icon
    return icon


def make_horizontal_gradient(width, height, left_hex, right_hex, flat_from=0.62):
    """Imej kecerunan mendatar; warna kanan kekal rata selepas `flat_from` supaya
    widget di sebelah kanan header boleh berlatar warna pepejal yang sepadan."""
    def rgb(h):
        h = h.lstrip("#")
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    l, r = rgb(left_hex), rgb(right_hex)
    stop = max(1, int(width * flat_from))
    row = Image.new("RGB", (width, 1))
    px = row.load()
    for x in range(width):
        t = min(x / stop, 1.0)
        t = t * t * (3 - 2 * t)  # smoothstep — peralihan lebih lembut
        px[x, 0] = tuple(int(l[i] + (r[i] - l[i]) * t) for i in range(3))
    return row.resize((width, height), Image.Resampling.NEAREST)


# ============================================================
#  AUTO-UPDATE: fungsi bantuan (tiada UI, selamat dipanggil dari thread)
# ============================================================
def parse_version(tag):
    """'v1.06' -> (1, 6); '1.10.2' -> (1, 10, 2). Tag tidak sah -> ()."""
    nums = re.findall(r"\d+", tag or "")
    return tuple(int(n) for n in nums)


def is_frozen_exe():
    return getattr(sys, "frozen", False) and sys.executable.lower().endswith(".exe")


def _http_get(url, timeout=15):
    req = urllib.request.Request(url, headers={
        "User-Agent": UPDATE_USER_AGENT,
        "Accept": "application/vnd.github+json",
    })
    return urllib.request.urlopen(req, timeout=timeout)


def fetch_latest_release():
    """Pulangkan dict {tag, name, notes, exe_url, exe_size, sha256, page} bagi release terkini."""
    with _http_get(UPDATE_API_URL) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    tag = data.get("tag_name", "")
    exe_url, exe_size, sha256 = None, None, None
    for asset in data.get("assets", []):
        if asset.get("name", "").lower().endswith(".exe"):
            exe_url = asset.get("browser_download_url")
            exe_size = asset.get("size")
            digest = asset.get("digest") or ""
            if digest.startswith("sha256:"):
                sha256 = digest.split(":", 1)[1].lower()
            break
    if not exe_url:
        exe_url = UPDATE_FALLBACK_EXE_URL.format(tag=tag)

    return {
        "tag": tag,
        "name": data.get("name") or tag,
        "notes": (data.get("body") or "").strip(),
        "exe_url": exe_url,
        "exe_size": exe_size,
        "sha256": sha256,
        "page": data.get("html_url") or UPDATE_RELEASES_PAGE,
    }


def download_update(info, dest_path, progress_cb=None):
    """Muat turun exe baharu ke dest_path & sahkan. Bangkitkan RuntimeError jika rosak."""
    hasher = hashlib.sha256()
    done = 0
    with _http_get(info["exe_url"], timeout=60) as resp, open(dest_path, "wb") as out:
        total = int(resp.headers.get("Content-Length") or 0) or (info.get("exe_size") or 0)
        while True:
            chunk = resp.read(256 * 1024)
            if not chunk:
                break
            out.write(chunk)
            hasher.update(chunk)
            done += len(chunk)
            if progress_cb:
                progress_cb(done, total)

    with open(dest_path, "rb") as f:
        if f.read(2) != b"MZ":
            raise RuntimeError("Fail dimuat turun bukan fail .exe yang sah.")
    if done < 1_000_000:
        raise RuntimeError("Fail dimuat turun terlalu kecil — kemungkinan muat turun tidak lengkap.")
    if info.get("exe_size") and done != info["exe_size"]:
        raise RuntimeError("Saiz fail tidak sepadan — muat turun tidak lengkap.")
    if info.get("sha256") and hasher.hexdigest().lower() != info["sha256"]:
        raise RuntimeError("Semakan SHA-256 gagal — fail mungkin rosak.")


def install_update_and_restart(new_exe_path):
    """Ganti exe yang sedang berjalan dengan versi baharu, kemudian lancar semula.

    Windows tidak benarkan fail exe yang sedang berjalan ditulis ganti, tetapi ia
    BOLEH dinamakan semula. Jadi: exe semasa -> .old, exe baharu -> nama asal,
    lancar exe baharu, dan fail .old dibuang pada permulaan seterusnya.
    """
    current = sys.executable
    old_path = current + ".old"
    if os.path.exists(old_path):
        try:
            os.remove(old_path)
        except OSError:
            old_path = current + f".{datetime.datetime.now():%Y%m%d%H%M%S}.old"

    os.replace(current, old_path)
    try:
        os.replace(new_exe_path, current)
    except Exception:
        os.replace(old_path, current)  # pulihkan versi asal jika gagal
        raise

    # Pastikan proses baharu PyInstaller (onefile) membuat salinan sementara sendiri,
    # bukannya mewarisi folder _MEI proses lama yang akan dipadam bila aplikasi ini tutup.
    env = dict(os.environ)
    env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    for key in list(env):
        if key.startswith("_MEIPASS") or key.startswith("_PYI_"):
            env.pop(key, None)
    subprocess.Popen([current], cwd=os.getcwd(), env=env, close_fds=True,
                     creationflags=getattr(subprocess, "DETACHED_PROCESS", 0))


def cleanup_old_exe():
    if not is_frozen_exe():
        return
    folder = os.path.dirname(sys.executable)
    base = os.path.basename(sys.executable)
    try:
        for name in os.listdir(folder):
            if name.startswith(base) and name.endswith(".old"):
                try:
                    os.remove(os.path.join(folder, name))
                except OSError:
                    pass
    except OSError:
        pass


# ============================================================
#  GOOGLE SHEET (melalui Web App Apps Script — google-apps-script/CardPrint.gs)
# ============================================================
# Permintaan membawa parameter "cardprint" (bukan "action"/"api") supaya ia dihalakan
# ke cardPrintHandle_() oleh doGet sedia ada tanpa bertembung dengan kiosk/ESP32.
PHOTO_CACHE_DIR = "photo_cache"   # salinan tempatan foto dari Drive (data peribadi — gitignored)
GSHEET_PHOTOS_PER_REQUEST = 4     # <= CP_MAX_PHOTOS_PER_REQUEST dalam CardPrint.gs
GSHEET_PARALLEL_REQUESTS = 6


class GSheetError(Exception):
    pass


def gsheet_call(url, key, action, timeout=90, **params):
    query = {"key": key, "cardprint": action}
    query.update(params)
    full_url = url.strip() + ("&" if "?" in url else "?") + urllib.parse.urlencode(query)
    req = urllib.request.Request(full_url, headers={"User-Agent": UPDATE_USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as e:
        raise GSheetError(f"Pelayan Google membalas HTTP {e.code}. Semak URL Web App.") from e
    except urllib.error.URLError as e:
        raise GSheetError(f"Tidak dapat menghubungi Google ({e.reason}). Semak sambungan internet.") from e
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception:
        text = raw[:20000].decode("utf-8", "ignore").lower()
        if "accounts.google.com" in text or "servicelogin" in text or "sign in" in text:
            # Halaman log masuk Google: Web App tidak dibuka kepada "Anyone"
            raise GSheetError("Google meminta log masuk. Pastikan Web App di-deploy dengan akses "
                              "'Anyone' (Sesiapa sahaja) dan URL berakhir dengan /exec.")
        # Halaman HTML lain (cth. halaman kiosk imbasan): doGet belum menghala ke CardPrint
        raise GSheetError("Web App memulangkan halaman web, bukan data. Pastikan baris 'cardprint' telah "
                          "ditambah di awal doGet dan versi baharu telah di-deploy (rujuk PANDUAN.md).")
    if not data.get("ok"):
        err = data.get("error") or "ralat tidak diketahui"
        if err == "unauthorized":
            raise GSheetError("Kunci rahsia (API Key) tidak sah. Semak Tetapan Google Sheet.")
        raise GSheetError(err)
    return data


def gsheet_fetch_rows(url, key):
    """Pulangkan (headers, senarai dict) dari tab Users — bentuk sama seperti csv.DictReader."""
    data = gsheet_call(url, key, "users")
    headers = [str(h).strip() for h in data.get("headers", [])]
    rows = []
    for values in data.get("rows", []):
        values = list(values) + [""] * (len(headers) - len(values))
        rows.append({h: str(v) for h, v in zip(headers, values) if h})
    return headers, rows


def safe_cache_path(cache_root, rel_path):
    """Laluan fail cache bagi laluan relatif GambarID; None jika laluan mencurigakan."""
    parts = [p for p in rel_path.replace("\\", "/").split("/") if p not in ("", ".")]
    if not parts or any(p == ".." or ":" in p for p in parts):
        return None
    return os.path.join(cache_root, *parts)


def gsheet_download_photos(url, key, rel_paths, cache_root, progress_cb=None):
    """Muat turun foto ke cache_root (mengekalkan struktur folder). Pulangkan (berjaya, gagal{laluan: sebab})."""
    batches = [rel_paths[i:i + GSHEET_PHOTOS_PER_REQUEST] for i in range(0, len(rel_paths), GSHEET_PHOTOS_PER_REQUEST)]
    ok_count, failed, done = 0, {}, 0

    def fetch(batch):
        return gsheet_call(url, key, "photos", timeout=120, paths=json.dumps(batch)).get("photos", {})

    with concurrent.futures.ThreadPoolExecutor(max_workers=GSHEET_PARALLEL_REQUESTS) as pool:
        futures = {pool.submit(fetch, b): b for b in batches}
        for fut in concurrent.futures.as_completed(futures):
            batch = futures[fut]
            try:
                photos = fut.result()
            except Exception as e:
                photos = {p: {"error": str(e)} for p in batch}
            for rel in batch:
                item = photos.get(rel) or {"error": "tiada respons"}
                dest = safe_cache_path(cache_root, rel)
                if "data" in item and dest:
                    try:
                        os.makedirs(os.path.dirname(dest), exist_ok=True)
                        tmp = dest + ".part"
                        with open(tmp, "wb") as f:
                            f.write(base64.b64decode(item["data"]))
                        os.replace(tmp, dest)
                        ok_count += 1
                    except Exception as e:
                        failed[rel] = str(e)
                else:
                    failed[rel] = item.get("error", "laluan tidak sah")
                done += 1
                if progress_cb:
                    progress_cb(done, len(rel_paths))
    return ok_count, failed


# ============================================================
#  PINDAH TETAPAN KE PC LAIN (fail .mykusess = zip)
# ============================================================
SETTINGS_BUNDLE_EXT = ".mykusess"
SETTINGS_BUNDLE_FORMAT = "mykusess-settings"
SETTINGS_BUNDLE_VERSION = 1
TEMPLATE_IMPORT_DIR = "templat"   # templat dari fail import disalin ke sini (di sebelah tetapan)
TEMPLATE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}
BUNDLE_MAX_MEMBER_BYTES = 60 * 1024 * 1024


class SettingsBundleError(Exception):
    pass


def build_settings_bundle(dest_path, settings, layout, presets, current_bg, include_gsheet):
    """Tulis fail tetapan. `settings`: dict app_settings; `presets`: senarai 4 slot; pulangkan ringkasan."""
    portable = {k: settings.get(k, "") for k in ("csv_encoding", "intake_year_t1")}
    if include_gsheet:
        portable.update({k: settings.get(k, "") for k in ("data_source", "gsheet_url", "gsheet_key")})

    files = {}            # laluan sumber -> nama dalam zip (fail sama dalam beberapa slot disimpan sekali)
    missing = []

    def add_template(path):
        if not path:
            return None
        if not os.path.isfile(path):
            missing.append(path)
            return None
        if path not in files:
            files[path] = f"templates/{len(files) + 1}_{os.path.basename(path)}"
        return files[path]

    slots = []
    for i, preset in enumerate((list(presets) + [None] * 4)[:4]):
        member = add_template(preset.get("path")) if preset else None
        slots.append({"slot": i, "name": (preset or {}).get("name", ""), "file": member} if member else None)
    manifest = {
        "format": SETTINGS_BUNDLE_FORMAT, "version": SETTINGS_BUNDLE_VERSION, "app_version": APP_VERSION,
        "created": datetime.datetime.now().isoformat(timespec="seconds"),
        "include_gsheet": bool(include_gsheet), "slots": slots, "current_template": add_template(current_bg),
    }

    tmp = dest_path + ".part"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
        z.writestr("settings.json", json.dumps(portable, indent=2, ensure_ascii=False))
        z.writestr("layout.json", json.dumps(layout, indent=2, ensure_ascii=False))
        for src, member in files.items():
            z.write(src, member)
    os.replace(tmp, dest_path)
    return {"templates": len(files), "slots": sum(1 for s_ in slots if s_), "missing": missing,
            "gsheet": bool(include_gsheet and portable.get("gsheet_url"))}


def read_settings_bundle(path):
    """Baca & sahkan fail tetapan. Pulangkan dict {manifest, settings, layout, templates{nama zip: bytes}}."""
    try:
        z = zipfile.ZipFile(path)
    except (zipfile.BadZipFile, OSError) as e:
        raise SettingsBundleError("Fail ini bukan fail tetapan MyKUSESS yang sah.") from e
    with z:
        names = set(z.namelist())
        if "manifest.json" not in names:
            raise SettingsBundleError("Fail ini bukan fail tetapan MyKUSESS yang sah.")

        def read_json(name, default):
            if name not in names:
                return default
            if z.getinfo(name).file_size > 5 * 1024 * 1024:
                raise SettingsBundleError(f"{name} terlalu besar.")
            return json.loads(z.read(name).decode("utf-8"))

        manifest = read_json("manifest.json", {})
        if manifest.get("format") != SETTINGS_BUNDLE_FORMAT:
            raise SettingsBundleError("Fail ini bukan fail tetapan MyKUSESS yang sah.")
        if int(manifest.get("version", 0)) > SETTINGS_BUNDLE_VERSION:
            raise SettingsBundleError("Fail tetapan ini dibuat oleh versi aplikasi yang lebih baharu. Kemas kini aplikasi dahulu.")

        templates = {}
        wanted = [s_.get("file") for s_ in manifest.get("slots", []) if s_] + [manifest.get("current_template")]
        for member in filter(None, wanted):
            if member in templates or member not in names or not member.startswith("templates/"):
                continue
            if os.path.splitext(member)[1].lower() not in TEMPLATE_EXTS:
                raise SettingsBundleError(f"Jenis fail templat tidak disokong: {os.path.basename(member)}")
            if z.getinfo(member).file_size > BUNDLE_MAX_MEMBER_BYTES:
                raise SettingsBundleError(f"Fail templat {member} terlalu besar.")
            templates[member] = z.read(member)
        return {"manifest": manifest, "settings": read_json("settings.json", {}),
                "layout": read_json("layout.json", {}), "templates": templates}


def write_bundle_template(member, data, dest_dir):
    """Simpan templat dari fail import; hanya nama fail biasa dengan sambungan gambar dibenarkan."""
    base = os.path.basename(member.replace("\\", "/"))
    base = re.sub(r"^\d+_", "", base) or "templat.png"
    stem, ext = os.path.splitext(base)
    if ext.lower() not in TEMPLATE_EXTS:
        raise SettingsBundleError(f"Jenis fail templat tidak disokong: {base}")
    stem = re.sub(r"[^\w\- .()]", "_", stem).strip(" .") or "templat"
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, stem + ext)
    n = 2
    while os.path.exists(dest):
        with open(dest, "rb") as f:
            if f.read() == data:
                return dest   # fail sama sudah wujud (import kali kedua)
        dest = os.path.join(dest_dir, f"{stem} ({n}){ext}")
        n += 1
    with open(dest, "wb") as f:
        f.write(data)
    return dest


class CardPrinterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        _icon_cache.clear()  # imej ikon terikat pada tetingkap Tk yang mencipta mereka

        self.title(f"MyKUSESS Studio Card Print {APP_VERSION} — Sistem Cetakan Kad Pintar")
        self.geometry("1400x900")
        self.minsize(1240, 780)
        self.configure(fg_color=COLOR_BG)

        # --- KETETAPAN IKON PERISIAN ---
        self.app_icon_path = None
        icon_path = resource_path("logo.ico")
        if os.path.exists(icon_path):
            self.app_icon_path = icon_path
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        self.bg_path = ""
        self.photo_folder = ""
        self.single_photo_path = ""
        self.csv_data = []  # Menyimpan data penuh: [{'kod_qr':..., 'pilih': True/False, ...}]
        self.generated_card = None
        self.config_filename = "layout_config.json"
        self.template_presets_filename = "template_presets.json"
        self.template_presets = [None, None, None, None]  # sehingga 4 tetapan asas template (background) tersimpan
        self.load_template_presets()
        self.app_settings_filename = "app_settings.json"
        self.last_csv_path = ""  # laluan fail CSV terakhir dimuat naik (untuk pulihkan semasa mula)
        # Sumber data senarai murid: "csv" (fail) atau "gsheet" (Google Sheet melalui Apps Script)
        self.data_source = "csv"
        self.gsheet_url = ""
        self.gsheet_key = ""
        self.photo_cache_dir = os.path.abspath(PHOTO_CACHE_DIR)
        self._gsheet_busy = False

        # --- GRID UTAMA (0 = header jenama, 1 = kandungan, 2 = bar status) ---
        self.grid_columnconfigure(0, weight=4, minsize=680)
        self.grid_columnconfigure(1, weight=5, minsize=540)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        self.build_header()

        # --- BAHAGIAN KIRI: TAB KAWALAN ---
        self.notebook = ctk.CTkTabview(
            self,
            corner_radius=0,
            fg_color=COLOR_BG,
            border_width=0,
            segmented_button_fg_color=COLOR_SEG_TRACK,
            segmented_button_selected_color=COLOR_SURFACE,
            segmented_button_selected_hover_color=COLOR_SURFACE,
            segmented_button_unselected_color=COLOR_SEG_TRACK,
            segmented_button_unselected_hover_color=COLOR_SEG_HOVER,
            text_color=COLOR_PRIMARY,
            anchor="w",
        )
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=(18, 9), pady=(6, 14))
        try:
            self.notebook._segmented_button.configure(
                font=ctk.CTkFont(family=FONT_FAMILY_SEMIBOLD, size=13), height=38, corner_radius=10,
                border_width=4, text_color_disabled=COLOR_TEXT_SUBTLE,
            )
        except Exception:
            pass

        self.tab_single = self.notebook.add("   Cetak Satu-Satu   ")
        self.tab_batch = self.notebook.add("   Cetak Pukal (CSV)   ")
        self.tab_config = self.notebook.add("   Konfigurasi Layout   ")
        self.notebook.set("   Cetak Pukal (CSV)   ")

        # --- BAHAGIAN KANAN: PANEL PREVIEW & PRINTER ---
        self.right_frame = ctk.CTkFrame(self, corner_radius=16, fg_color=COLOR_SURFACE, border_width=1, border_color=COLOR_BORDER)
        self.right_frame.grid(row=1, column=1, sticky="nsew", padx=(9, 18), pady=(18, 14))

        self.build_tab_single()
        self.build_tab_batch()
        self.build_tab_config()
        self.load_layout_config(silent=True)
        self.use_template_slot(0, silent=True)
        self.restore_app_settings()
        self.build_preview_panel()
        self.build_status_bar()

        self.protocol("WM_DELETE_WINDOW", self.on_app_close)

        # Semak kemas kini secara senyap di latar belakang selepas UI siap dipaparkan
        self._update_check_running = False
        cleanup_old_exe()
        self.after(2500, lambda: self.check_for_updates(manual=False))

    def on_app_close(self):
        # Jaring keselamatan terakhir - pastikan sebarang suntingan konfigurasi
        # layout yang belum dikesan (cth. medan terakhir tanpa fokus keluar)
        # tetap disimpan sebelum aplikasi ditutup.
        self.auto_save_layout_config()
        self.destroy()

    # ============================================================
    #  KOMPONEN UI BOLEH GUNA SEMULA (helper widget & gaya)
    # ============================================================
    def build_header(self):
        HEADER_H = 72
        self.header_canvas = tk.Canvas(self, height=HEADER_H, highlightthickness=0, bd=0, bg=COLOR_HEADER_BG)
        self.header_canvas.grid(row=0, column=0, columnspan=2, sticky="ew")
        self._header_bg_item = self.header_canvas.create_image(0, 0, anchor="nw")
        self._header_photo = None

        x = 24
        if self.app_icon_path:
            try:
                logo_img = Image.open(self.app_icon_path).convert("RGBA")
                logo_img.thumbnail((40, 40), Image.Resampling.LANCZOS)
                self._header_logo = ImageTk.PhotoImage(logo_img)
                self.header_canvas.create_image(x, HEADER_H // 2, image=self._header_logo, anchor="w")
                x += logo_img.width + 14
            except Exception:
                pass

        self.header_canvas.create_text(x, 25, anchor="w", text="MyKUSESS Studio Card Print", fill=COLOR_HEADER_TEXT,
                                       font=(FONT_FAMILY_SEMIBOLD, 17))
        self.header_canvas.create_text(x, 49, anchor="w", text="Sistem Cetakan Kad Pintar  ·  SM Sains Kuala Selangor",
                                       fill=COLOR_HEADER_MUTED, font=(FONT_FAMILY, 10))

        right = ctk.CTkFrame(self.header_canvas, fg_color=COLOR_HEADER_BG2, bg_color=COLOR_HEADER_BG2)
        self._header_right = self.header_canvas.create_window(0, HEADER_H // 2, window=right, anchor="e")

        self.btn_check_update = ctk.CTkButton(
            right, text="Semak Kemas Kini", image=make_icon("refresh-cw", "#D7E3F1", 14), compound="left",
            command=lambda: self.check_for_updates(manual=True),
            fg_color="transparent", hover_color="#1B4D7A", text_color="#E6EEF7", bg_color=COLOR_HEADER_BG2,
            border_width=1, border_color="#3E6890", corner_radius=9, height=32, width=164,
            font=ctk.CTkFont(family=FONT_FAMILY_SEMIBOLD, size=12),
        )
        self.btn_check_update.pack(side="left", padx=(0, 12))
        ctk.CTkButton(
            right, text="Pindah Tetapan", image=make_icon("folder-input", "#D7E3F1", 14), compound="left",
            command=self.open_transfer_dialog,
            fg_color="transparent", hover_color="#1B4D7A", text_color="#E6EEF7", bg_color=COLOR_HEADER_BG2,
            border_width=1, border_color="#3E6890", corner_radius=9, height=32, width=146,
            font=ctk.CTkFont(family=FONT_FAMILY_SEMIBOLD, size=12),
        ).pack(side="left", padx=(0, 10), before=self.btn_check_update)
        ctk.CTkLabel(
            right, text=APP_VERSION, font=ctk.CTkFont(family=FONT_FAMILY_SEMIBOLD, size=12),
            text_color=COLOR_HEADER_BG, fg_color="#7FE0D6", bg_color=COLOR_HEADER_BG2, corner_radius=9, width=58, height=28,
        ).pack(side="left")

        def on_resize(event):
            w = max(event.width, 1)
            self._header_photo = ImageTk.PhotoImage(make_horizontal_gradient(w, HEADER_H, COLOR_HEADER_BG, COLOR_HEADER_BG2))
            self.header_canvas.itemconfigure(self._header_bg_item, image=self._header_photo)
            self.header_canvas.coords(self._header_right, w - 24, HEADER_H // 2)

        self.header_canvas.bind("<Configure>", on_resize)

    def section_card(self, parent, number, title, subtitle=None, icon=None, pady=(0, 14)):
        """Kad seksyen putih bernombor. Pulangkan bingkai isi (body) untuk diletakkan widget."""
        card = ctk.CTkFrame(parent, fg_color=COLOR_SURFACE, corner_radius=14, border_width=1, border_color=COLOR_BORDER)
        card.pack(fill="x", pady=pady, padx=2)

        head = ctk.CTkFrame(card, fg_color="transparent")
        head.pack(fill="x", padx=18, pady=(14, 10))
        ctk.CTkLabel(
            head, text=str(number), width=28, height=28, corner_radius=8, fg_color=COLOR_PRIMARY,
            text_color="#FFFFFF", font=ctk.CTkFont(family=FONT_FAMILY_SEMIBOLD, size=13),
        ).pack(side="left", padx=(0, 12), anchor="n" if subtitle else "center")
        text_box = ctk.CTkFrame(head, fg_color="transparent")
        text_box.pack(side="left", fill="x", expand=True, anchor="w")
        ctk.CTkLabel(text_box, text=title, font=ctk.CTkFont(family=FONT_FAMILY_SEMIBOLD, size=15),
                     text_color=COLOR_TEXT, height=20).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(text_box, text=subtitle, font=ctk.CTkFont(family=FONT_FAMILY, size=11),
                         text_color=COLOR_TEXT_MUTED, height=16, justify="left", anchor="w").pack(anchor="w")
        if icon:
            ctk.CTkLabel(head, text="", image=make_icon(icon, COLOR_TEXT_SUBTLE, 18)).pack(side="right")

        ctk.CTkFrame(card, height=1, fg_color=COLOR_BORDER).pack(fill="x")
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=18, pady=(14, 18))
        return body

    def section_header(self, parent, number, text, subtitle=None):
        # Dikekalkan untuk keserasian; reka bentuk semasa menggunakan section_card.
        return self.section_card(parent, number, text, subtitle)

    def field_label(self, parent, text):
        return ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(family=FONT_FAMILY_SEMIBOLD, size=12), text_color=COLOR_TEXT_MUTED,
                            anchor="w", justify="left")

    def hint_label(self, parent, text, wraplength=420):
        return ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=COLOR_TEXT_SUBTLE,
                            wraplength=wraplength, justify="left", anchor="w")

    def status_label(self, parent, text):
        # Status belum lengkap dipaparkan neutral (bukan merah) — ralat sebenar tetap guna COLOR_DANGER.
        return ctk.CTkLabel(parent, text=text, text_color=COLOR_TEXT_SUBTLE, font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                            wraplength=400, justify="left", anchor="w")

    def text_entry(self, parent, placeholder="", width=200, height=38):
        return ctk.CTkEntry(parent, width=width, height=height, corner_radius=9, border_width=1, border_color=COLOR_BORDER,
                            fg_color=COLOR_SURFACE_ALT, text_color=COLOR_TEXT, placeholder_text=placeholder,
                            placeholder_text_color=COLOR_TEXT_SUBTLE, font=ctk.CTkFont(family=FONT_FAMILY, size=13))

    def combo_box(self, parent, values, width=200, command=None):
        return ctk.CTkComboBox(parent, values=values, width=width, height=38, corner_radius=9, border_width=0,
                               fg_color=COLOR_SEG_TRACK, button_color=COLOR_SEG_TRACK,
                               button_hover_color=COLOR_SEG_HOVER, text_color=COLOR_TEXT,
                               dropdown_fg_color=COLOR_SURFACE, dropdown_hover_color=COLOR_ACCENT_SOFT,
                               dropdown_text_color=COLOR_TEXT, font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                               dropdown_font=ctk.CTkFont(family=FONT_FAMILY, size=13), command=command)

    def _btn(self, parent, text, command, icon, icon_color, **kw):
        if icon:
            kw.setdefault("image", make_icon(icon, icon_color, 16))
            kw.setdefault("compound", "left")
        kw.setdefault("corner_radius", 10)
        return ctk.CTkButton(parent, text=text, command=command, **kw)

    def btn_primary(self, parent, text, command, icon=None, **kw):
        kw.setdefault("height", 40)
        return self._btn(parent, text, command, icon, "#FFFFFF", fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER,
                         text_color="#FFFFFF", text_color_disabled="#AEBBCB",
                         font=ctk.CTkFont(family=FONT_FAMILY_SEMIBOLD, size=13), **kw)

    def btn_cta(self, parent, text, command, icon=None, **kw):
        """Tindakan utama skrin (cetak) — teal supaya menonjol daripada butang navy biasa."""
        kw.setdefault("height", 46)
        return self._btn(parent, text, command, icon, "#FFFFFF", fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
                         text_color="#FFFFFF", text_color_disabled="#CFE7E5",
                         font=ctk.CTkFont(family=FONT_FAMILY_SEMIBOLD, size=14), **kw)

    def btn_secondary(self, parent, text, command, icon=None, **kw):
        kw.setdefault("height", 38)
        return self._btn(parent, text, command, icon, COLOR_PRIMARY, fg_color=COLOR_SURFACE, hover_color=COLOR_SURFACE_ALT,
                         text_color=COLOR_PRIMARY, border_width=1, border_color=COLOR_BORDER_STRONG,
                         font=ctk.CTkFont(family=FONT_FAMILY_SEMIBOLD, size=12), **kw)

    def btn_success(self, parent, text, command, icon=None, **kw):
        kw.setdefault("height", 40)
        return self._btn(parent, text, command, icon, "#FFFFFF", fg_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS_HOVER,
                         font=ctk.CTkFont(family=FONT_FAMILY_SEMIBOLD, size=13), **kw)

    def btn_danger(self, parent, text, command, icon=None, **kw):
        kw.setdefault("height", 36)
        return self._btn(parent, text, command, icon, COLOR_DANGER, fg_color=COLOR_SURFACE, hover_color=COLOR_DANGER_SOFT,
                         text_color=COLOR_DANGER, border_width=1, border_color="#F1C6C6",
                         font=ctk.CTkFont(family=FONT_FAMILY_SEMIBOLD, size=12), **kw)

    def scroll_area(self, parent):
        area = ctk.CTkScrollableFrame(parent, fg_color="transparent", scrollbar_button_color=COLOR_BORDER_STRONG,
                                      scrollbar_button_hover_color=COLOR_TEXT_SUBTLE)
        area.pack(fill="both", expand=True, padx=0, pady=(6, 0))
        return area

    # ============================================================
    # TAB 1: CETAK SATU-SATU
    # ============================================================
    def build_tab_single(self):
        pad = self.scroll_area(self.tab_single)

        body = self.section_card(pad, "1", "Templat Kad", "Latar belakang kad & templat tersimpan", icon="layout-template")
        row = ctk.CTkFrame(body, fg_color="transparent")
        row.pack(fill="x")
        self.btn_secondary(row, "Pilih Templat Kad", self.select_bg, icon="image", width=190).pack(side="left")
        self.lbl_bg = self.status_label(row, "Template: Tiada fail dipilih")
        self.lbl_bg.pack(side="left", padx=14)

        self.field_label(body, "Templat tersimpan").pack(anchor="w", pady=(16, 2))
        self.hint_label(body, "Tekan 'Guna' untuk muat templat, ikon simpan untuk simpan templat semasa ke slot.", wraplength=620).pack(anchor="w", pady=(0, 8))
        slot_frame = ctk.CTkFrame(body, fg_color="transparent")
        slot_frame.pack(fill="x")
        self.lbl_template_slots = []
        for i in range(4):
            slot_frame.grid_columnconfigure(i, weight=1, uniform="slot")
            tile = ctk.CTkFrame(slot_frame, fg_color=COLOR_SURFACE_ALT, corner_radius=10, border_width=1, border_color=COLOR_BORDER)
            tile.grid(row=0, column=i, padx=(0 if i == 0 else 5, 0 if i == 3 else 5), sticky="nsew")
            lbl = ctk.CTkLabel(tile, text=f"Slot {i+1}: Kosong", font=ctk.CTkFont(family=FONT_FAMILY, size=11),
                               text_color=COLOR_TEXT_MUTED, wraplength=120, justify="center", height=34)
            lbl.pack(padx=8, pady=(10, 6), fill="x")
            self.lbl_template_slots.append(lbl)
            btn_row = ctk.CTkFrame(tile, fg_color="transparent")
            btn_row.pack(pady=(0, 10))
            ctk.CTkButton(btn_row, text="Guna", width=58, height=28, fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER,
                          font=ctk.CTkFont(family=FONT_FAMILY_SEMIBOLD, size=11), corner_radius=7,
                          command=lambda idx=i: self.use_template_slot(idx)).pack(side="left", padx=(0, 4))
            ctk.CTkButton(btn_row, text="", image=make_icon("save", COLOR_PRIMARY, 14), width=30, height=28,
                          fg_color=COLOR_SURFACE, hover_color=COLOR_BORDER, border_width=1, border_color=COLOR_BORDER_STRONG,
                          corner_radius=7, command=lambda idx=i: self.save_template_slot(idx)).pack(side="left")
        self.refresh_template_slot_labels()

        body = self.section_card(pad, "2", "Maklumat Individu", "Foto dan butiran yang akan dicetak pada kad", icon="user")
        row = ctk.CTkFrame(body, fg_color="transparent")
        row.pack(fill="x")
        self.btn_secondary(row, "Pilih Foto Guru/Murid", self.select_single_photo, icon="user", width=190).pack(side="left")
        self.lbl_photo = self.status_label(row, "Foto: Tiada fail dipilih")
        self.lbl_photo.pack(side="left", padx=14)

        form = ctk.CTkFrame(body, fg_color="transparent")
        form.pack(fill="x", pady=(16, 0))
        form.grid_columnconfigure(0, weight=1, uniform="f")
        form.grid_columnconfigure(1, weight=1, uniform="f")

        self.field_label(form, "Kod Unik QR").grid(row=0, column=0, sticky="w", pady=(0, 6))
        qr_input_frame = ctk.CTkFrame(form, fg_color="transparent")
        qr_input_frame.grid(row=1, column=0, sticky="ew", padx=(0, 8))
        self.ent_qr_code = self.text_entry(qr_input_frame, "Contoh: wpwj727", width=150)
        self.ent_qr_code.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.btn_generate_qr = self.btn_secondary(qr_input_frame, "Jana", self.generate_random_qr_code, icon="shuffle", width=84)
        self.btn_generate_qr.pack(side="left")

        self.field_label(form, "Batch (Huruf Besar)").grid(row=0, column=1, sticky="w", padx=(8, 0), pady=(0, 6))
        self.ent_batch = self.text_entry(form, "Contoh: BATCH 2026")
        self.ent_batch.grid(row=1, column=1, sticky="ew", padx=(8, 0))

        self.field_label(form, "Nama Penuh").grid(row=2, column=0, columnspan=2, sticky="w", pady=(14, 6))
        self.ent_full_name = self.text_entry(form, "Contoh: AMINAH BINTI ALI")
        self.ent_full_name.grid(row=3, column=0, columnspan=2, sticky="ew")

        self.field_label(form, "Email MOE").grid(row=4, column=0, columnspan=2, sticky="w", pady=(14, 6))
        self.ent_email_moe = self.text_entry(form, "Contoh: m-1234567@moe-dl.edu.my")
        self.ent_email_moe.grid(row=5, column=0, columnspan=2, sticky="ew")

        self.btn_primary(pad, "Jana Pratonton Kad", self.generate_single_preview, icon="eye", height=46).pack(fill="x", padx=2, pady=(2, 16))

    # ============================================================
    # TAB 2: CETAK PUKAL (BATCH CSV)
    # ============================================================
    def build_tab_batch(self):
        pad = self.scroll_area(self.tab_batch)

        body = self.section_card(pad, "1", "Sumber Data", "Senarai murid/guru dari Google Sheet atau fail CSV", icon="database")
        body.grid_columnconfigure(1, weight=1)

        self.btn_secondary(body, "Pilih Folder Gambar", self.select_photo_folder, icon="folder-open", width=242).grid(row=2, column=0, sticky="w", pady=(0, 14))
        self.lbl_folder = self.status_label(body, "Folder: Tiada dipilih")
        self.lbl_folder.configure(wraplength=300)
        self.lbl_folder.grid(row=2, column=1, padx=(14, 0), pady=(0, 14), sticky="w")

        gs_box = ctk.CTkFrame(body, fg_color="transparent")
        gs_box.grid(row=0, column=0, sticky="w", pady=(0, 10))
        self.btn_gsheet = self.btn_primary(gs_box, "Muat dari Google Sheet", lambda: self.load_from_gsheet(), icon="sheet", width=196)
        self.btn_gsheet.pack(side="left")
        ctk.CTkButton(gs_box, text="", image=make_icon("settings", COLOR_PRIMARY, 16), width=40, height=40, corner_radius=10,
                      fg_color=COLOR_SURFACE, hover_color=COLOR_SURFACE_ALT, border_width=1, border_color=COLOR_BORDER_STRONG,
                      command=self.open_gsheet_settings).pack(side="left", padx=(6, 0))
        self.lbl_gsheet = self.status_label(body, "Google Sheet: Belum disambung — tekan ikon tetapan")
        self.lbl_gsheet.configure(wraplength=300)
        self.lbl_gsheet.grid(row=0, column=1, padx=(14, 0), pady=(0, 10), sticky="w")

        self.btn_secondary(body, "Muat Naik CSV", self.load_csv, icon="upload", width=242).grid(row=1, column=0, sticky="w", pady=(0, 10))
        self.lbl_csv = self.status_label(body, "CSV: Tiada fail dipilih")
        self.lbl_csv.configure(wraplength=300)
        self.lbl_csv.grid(row=1, column=1, padx=(14, 0), pady=(0, 10), sticky="w")

        opts = ctk.CTkFrame(body, fg_color=COLOR_SURFACE_ALT, corner_radius=10)
        opts.grid(row=3, column=0, columnspan=2, sticky="ew")
        opts.grid_columnconfigure(1, weight=1)
        self.field_label(opts, "Pengekodan CSV").grid(row=0, column=0, padx=(14, 10), pady=(12, 6), sticky="w")
        self.cbo_encoding = self.combo_box(opts, ["UTF-8", "UTF-8-SIG (With BOM)", "ANSI (cp1252)"], width=210)
        self.cbo_encoding.configure(fg_color=COLOR_SURFACE, button_color=COLOR_SURFACE, button_hover_color=COLOR_BORDER)
        self.cbo_encoding.set("UTF-8")
        self.cbo_encoding.grid(row=0, column=1, padx=(0, 14), pady=(12, 6), sticky="w")

        self.field_label(opts, "Tahun Kemasukan T1").grid(row=1, column=0, padx=(14, 10), pady=(6, 12), sticky="w")
        intake_frame = ctk.CTkFrame(opts, fg_color="transparent")
        intake_frame.grid(row=1, column=1, padx=(0, 14), pady=(6, 12), sticky="w")
        self.ent_intake_year_t1 = self.text_entry(intake_frame, width=90)
        self.ent_intake_year_t1.configure(fg_color=COLOR_SURFACE)
        self.ent_intake_year_t1.insert(0, str(datetime.date.today().year))
        self.ent_intake_year_t1.pack(side="left")
        self.ent_intake_year_t1.bind("<FocusOut>", lambda _e: self.save_app_settings())
        self.hint_label(intake_frame, "Untuk kira Batch daripada Tahap/Tgkt (CSV mentah)", wraplength=320).pack(side="left", padx=(10, 0))

        body = self.section_card(pad, "2", "Senarai Murid", "Klik baris untuk tanda & pratonton · Dwi-klik Nama Penuh / Email MOE untuk sunting", icon="users")

        toolbar = ctk.CTkFrame(body, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, 10))
        search_box = ctk.CTkFrame(toolbar, fg_color=COLOR_SURFACE_ALT, corner_radius=9, border_width=1, border_color=COLOR_BORDER, height=38)
        search_box.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(search_box, text="", image=make_icon("search", COLOR_TEXT_SUBTLE, 15), width=20).pack(side="left", padx=(12, 2))
        self.ent_search = ctk.CTkEntry(search_box, placeholder_text="Cari nama atau batch...", height=34, border_width=0,
                                       fg_color=COLOR_SURFACE_ALT, text_color=COLOR_TEXT, placeholder_text_color=COLOR_TEXT_SUBTLE,
                                       font=ctk.CTkFont(family=FONT_FAMILY, size=13))
        self.ent_search.pack(side="left", fill="x", expand=True, padx=(0, 4), pady=2)
        self.ent_search.bind("<KeyRelease>", self.filter_search)
        ctk.CTkButton(search_box, text="", image=make_icon("x", COLOR_TEXT_MUTED, 14), width=28, height=28, corner_radius=7,
                      fg_color="transparent", hover_color=COLOR_BORDER, command=self.clear_search).pack(side="left", padx=(0, 6))

        self.btn_secondary(toolbar, "Pilih Semua", self.select_all_records, icon="square-check", width=128).pack(side="left", padx=(10, 6))
        self.btn_danger(toolbar, "Nyahpilih", self.deselect_all_records, icon="square", width=112, height=38).pack(side="left")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", font=(FONT_FAMILY, 9), rowheight=30, background=COLOR_SURFACE, fieldbackground=COLOR_SURFACE,
                        foreground=COLOR_TEXT, borderwidth=0, relief="flat")
        style.configure("Treeview.Heading", font=(FONT_FAMILY_SEMIBOLD, 8), background=COLOR_SURFACE_ALT, foreground=COLOR_TEXT_MUTED,
                        relief="flat", borderwidth=0, padding=(8, 8))
        style.map("Treeview.Heading", background=[("active", COLOR_BORDER)])
        style.map("Treeview", background=[("selected", COLOR_PRIMARY)], foreground=[("selected", "#FFFFFF")])
        style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
        style.configure("Studio.Vertical.TScrollbar", background=COLOR_BORDER_STRONG, troughcolor=COLOR_SURFACE_ALT,
                        bordercolor=COLOR_SURFACE_ALT, lightcolor=COLOR_BORDER_STRONG, darkcolor=COLOR_BORDER_STRONG,
                        arrowcolor=COLOR_TEXT_MUTED, gripcount=0, arrowsize=12)
        style.map("Studio.Vertical.TScrollbar", background=[("active", COLOR_TEXT_SUBTLE)])

        tree_frame = ctk.CTkFrame(body, fg_color=COLOR_BORDER, corner_radius=10)
        tree_frame.pack(fill="both", expand=True)
        tree_inner = tk.Frame(tree_frame, bg=COLOR_SURFACE, bd=0, highlightthickness=0)
        tree_inner.pack(fill="both", expand=True, padx=1, pady=1)

        self.tree = ttk.Treeview(tree_inner, columns=("Pilih", "QR", "Batch", "Penuh", "Email"), show="headings", height=9)
        self.tree.heading("Pilih", text="TANDA")
        self.tree.heading("QR", text="KOD QR", anchor="w")
        self.tree.heading("Batch", text="BATCH", anchor="w")
        self.tree.heading("Penuh", text="NAMA PENUH", anchor="w")
        self.tree.heading("Email", text="EMAIL MOE", anchor="w")
        self.tree.column("Pilih", width=58, minwidth=50, anchor="center", stretch=False)
        self.tree.column("QR", width=96, minwidth=60)
        self.tree.column("Batch", width=84, minwidth=60)
        self.tree.column("Penuh", width=200, minwidth=120)
        self.tree.column("Email", width=150, minwidth=100)

        # Slider skrol menegak di sebelah senarai supaya senarai panjang (ratusan
        # rekod CSV) boleh diskrol pantas dengan menyeret, bukan sekadar roda tetikus.
        tree_scroll = ttk.Scrollbar(tree_inner, orient="vertical", command=self.tree.yview, style="Studio.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=tree_scroll.set)

        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

        # Warna latar baris mengikut status tanda — teal lembut bila dipilih,
        # supaya senarai mudah dibaca sekali pandang (bukan sekadar simbol teks).
        self.tree.tag_configure("row_on", background=COLOR_ACCENT_SOFT)
        self.tree.tag_configure("row_off", background=COLOR_SURFACE)

        self.tree.bind("<ButtonRelease-1>", self.on_tree_click)
        self.tree.bind("<Double-1>", self.on_tree_double_click)

        self.lbl_tree_count = ctk.CTkLabel(body, text="Tiada rekod dimuat", font=ctk.CTkFont(family=FONT_FAMILY, size=11),
                                           text_color=COLOR_TEXT_MUTED, anchor="w")
        self.lbl_tree_count.pack(fill="x", pady=(8, 0))

        body = self.section_card(pad, "3", "Cetak & Eksport", "Cetak terus ke pencetak kad atau jana PDF bagi rekod bertanda", icon="printer")
        self.progress_frame = ctk.CTkFrame(body, fg_color="transparent")
        self.progress_frame.pack(fill="x", pady=(0, 12))
        self.lbl_progress_status = ctk.CTkLabel(self.progress_frame, text="Status: Sedia", font=ctk.CTkFont(family=FONT_FAMILY_SEMIBOLD, size=12),
                                                text_color=COLOR_TEXT_MUTED, anchor="w")
        self.lbl_progress_status.pack(fill="x")
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, progress_color=COLOR_ACCENT, fg_color=COLOR_SURFACE_ALT, height=8, corner_radius=4)
        self.progress_bar.pack(fill="x", pady=(6, 0))
        self.progress_bar.set(0)

        btn_action_frame = ctk.CTkFrame(body, fg_color="transparent")
        btn_action_frame.pack(fill="x")
        btn_action_frame.grid_columnconfigure(0, weight=3, uniform="act")
        btn_action_frame.grid_columnconfigure(1, weight=2, uniform="act")
        self.btn_cta(btn_action_frame, "Cetak Semua Ditanda", self.print_batch, icon="printer").grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.btn_secondary(btn_action_frame, "Muat Turun PDF", self.download_pdf_batch, icon="file-text", height=46).grid(row=0, column=1, sticky="ew", padx=(6, 0))
        ctk.CTkFrame(pad, height=6, fg_color="transparent").pack()

    # ============================================================
    # TAB 3: KONFIGURASI LAYOUT (SCROLLABLE)
    # ============================================================
    def build_tab_config(self):
        self.scrollable_frame = self.scroll_area(self.tab_config)
        pad = self.scrollable_frame

        FONT_OPTIONS = ["arial.ttf", "calibri.ttf", "times.ttf", "tahoma.ttf", "verdana.ttf", "cour.ttf"]

        def grid_body(body):
            body.grid_columnconfigure(0, minsize=118)
            body.grid_columnconfigure(1, weight=1, uniform="cfgval")
            body.grid_columnconfigure(2, minsize=124)
            body.grid_columnconfigure(3, weight=1, uniform="cfgval")
            return body

        # 1. Gambar Foto
        body = grid_body(self.section_card(pad, "1", "Gambar Foto", "Kotak sempadan foto pada kanvas 1013 × 638 px", icon="user"))
        self.cfg_img_x = self.create_cfg_entry(body, "Kedudukan X", "40", row=0, col=0)
        self.cfg_img_y = self.create_cfg_entry(body, "Kedudukan Y", "250", row=0, col=2)
        self.cfg_img_w = self.create_cfg_entry(body, "Maks Lebar (W)", "240", row=1, col=0)
        self.cfg_img_h = self.create_cfg_entry(body, "Maks Tinggi (H)", "310", row=1, col=2)

        # 2. QR Code
        body = grid_body(self.section_card(pad, "2", "Kod QR", "Kedudukan & saiz kod QR", icon="qr-code"))
        self.cfg_qr_x = self.create_cfg_entry(body, "Kedudukan X", "735", row=0, col=0)
        self.cfg_qr_y = self.create_cfg_entry(body, "Kedudukan Y", "255", row=0, col=2)
        self.cfg_qr_size = self.create_cfg_entry(body, "Saiz QR", "230", row=1, col=0)

        # 3-5. Medan teks (Batch, Nama Penuh, Email MOE) — struktur sama, nama atribut cfg_n1/n2/n3
        text_groups = [
            ("n1", "3", "Batch", (340, 410, 45), True, False),
            ("n2", "4", "Nama Penuh", (320, 480, 30), False, False),
            ("n3", "5", "Email MOE", (320, 550, 25), False, True),
        ]
        for key, num, title, (dx, dy, dfont), dbold, ditalic in text_groups:
            body = grid_body(self.section_card(pad, num, title, "Kedudukan, saiz & gaya fon", icon="type"))
            setattr(self, f"cfg_{key}_x", self.create_cfg_entry(body, "Kedudukan X", str(dx), row=0, col=0))
            setattr(self, f"cfg_{key}_y", self.create_cfg_entry(body, "Kedudukan Y", str(dy), row=0, col=2))
            setattr(self, f"cfg_{key}_font", self.create_cfg_entry(body, "Saiz Font", str(dfont), row=1, col=0))

            self.field_label(body, "Jenis Font").grid(row=1, column=2, sticky="w", padx=(12, 10), pady=6)
            font_cbo = self.combo_box(body, FONT_OPTIONS, width=150, command=self.auto_save_layout_config)
            font_cbo.set("arial.ttf")
            font_cbo.grid(row=1, column=3, sticky="w", pady=6)
            setattr(self, f"cfg_{key}_font_file", font_cbo)

            bold_var = tk.BooleanVar(value=dbold)
            italic_var = tk.BooleanVar(value=ditalic)
            bold_var.trace_add("write", self.auto_save_layout_config)
            italic_var.trace_add("write", self.auto_save_layout_config)
            setattr(self, f"cfg_{key}_bold", bold_var)
            setattr(self, f"cfg_{key}_italic", italic_var)

            self.field_label(body, "Gaya").grid(row=2, column=0, sticky="w", padx=(0, 10), pady=6)
            style_box = ctk.CTkFrame(body, fg_color="transparent")
            style_box.grid(row=2, column=1, sticky="w", pady=6)
            for text, var in (("Bold", bold_var), ("Italic", italic_var)):
                ctk.CTkCheckBox(style_box, text=text, variable=var, fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
                                border_color=COLOR_BORDER_STRONG, border_width=2, corner_radius=5, checkbox_width=20, checkbox_height=20,
                                text_color=COLOR_TEXT, font=ctk.CTkFont(family=FONT_FAMILY, size=12)).pack(side="left", padx=(0, 14))

            self.field_label(body, "Justifikasi").grid(row=2, column=2, sticky="w", padx=(12, 10), pady=6)
            just_var = ctk.StringVar(value="Left")
            just_var.trace_add("write", self.auto_save_layout_config)
            setattr(self, f"cfg_{key}_justify", just_var)
            just_menu = ctk.CTkSegmentedButton(body, values=["Left", "Center", "Right"], variable=just_var, width=150, height=32,
                                               fg_color=COLOR_SEG_TRACK, unselected_color=COLOR_SEG_TRACK,
                                               unselected_hover_color=COLOR_SEG_HOVER, selected_color=COLOR_SURFACE,
                                               selected_hover_color=COLOR_SURFACE, text_color=COLOR_PRIMARY,
                                               font=ctk.CTkFont(family=FONT_FAMILY_SEMIBOLD, size=11), corner_radius=8)
            just_menu.grid(row=2, column=3, sticky="w", pady=6)
            setattr(self, f"cfg_{key}_just_menu", just_menu)

        frame_buttons = ctk.CTkFrame(pad, fg_color="transparent")
        frame_buttons.pack(fill="x", padx=2, pady=(2, 10))
        frame_buttons.grid_columnconfigure((0, 1), weight=1, uniform="cfgbtn")
        self.btn_success(frame_buttons, "Simpan Layout", self.save_layout_config, icon="save").grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.btn_secondary(frame_buttons, "Muat Tetapan", self.load_layout_config, icon="folder-input", height=40).grid(row=0, column=1, sticky="ew", padx=(6, 0))

        self.btn_primary(pad, "Kemas Kini & Jana Pratonton", self.trigger_refresh_preview, icon="refresh-cw", height=46).pack(fill="x", padx=2, pady=(0, 16))

    def config_group_label(self, parent, text):
        return ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(family=FONT_FAMILY_SEMIBOLD, size=12), text_color=COLOR_PRIMARY)

    # ============================================================
    # PANEL KANAN: PREVIEW & KAWALAN OUTPUT
    # ============================================================
    PREVIEW_W, PREVIEW_H = 520, 328   # nisbah kad 1013 × 638

    def build_preview_panel(self):
        head = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        head.pack(fill="x", padx=28, pady=(22, 0))
        title_box = ctk.CTkFrame(head, fg_color="transparent")
        title_box.pack(side="left")
        ctk.CTkLabel(title_box, text="Pratonton Kad", font=ctk.CTkFont(family=FONT_FAMILY_SEMIBOLD, size=18),
                     text_color=COLOR_TEXT, height=24).pack(anchor="w")
        ctk.CTkLabel(title_box, text="Semakan visual sebelum dicetak", font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                     text_color=COLOR_TEXT_MUTED, height=18).pack(anchor="w")
        ctk.CTkLabel(head, text="  CR-80  ·  86 × 54 mm  ", image=make_icon("id-card", COLOR_PRIMARY, 14), compound="left",
                     font=ctk.CTkFont(family=FONT_FAMILY_SEMIBOLD, size=11), text_color=COLOR_PRIMARY,
                     fg_color=COLOR_SURFACE_ALT, corner_radius=8, height=28).pack(side="right")

        # Pentas pratonton: latar kelabu lembut dengan kad "terapung" (bingkai bayang)
        stage = ctk.CTkFrame(self.right_frame, corner_radius=14, fg_color=COLOR_SURFACE_ALT, border_width=1, border_color=COLOR_BORDER)
        stage.pack(fill="x", padx=28, pady=(16, 0))
        shadow = ctk.CTkFrame(stage, corner_radius=16, fg_color="#DDE4EC")
        shadow.pack(padx=28, pady=(30, 30))
        self.preview_container = ctk.CTkFrame(shadow, width=self.PREVIEW_W, height=self.PREVIEW_H, corner_radius=14,
                                              fg_color=COLOR_SURFACE, border_width=1, border_color=COLOR_BORDER_STRONG)
        self.preview_container.pack(padx=(0, 3), pady=(0, 4))
        self.preview_container.pack_propagate(False)

        self.lbl_preview = ctk.CTkLabel(self.preview_container, text="Belum ada pratonton\n\nPilih murid dalam senarai atau tekan 'Jana Pratonton Kad'",
                                        image=None, text_color=COLOR_TEXT_SUBTLE, font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                                        justify="center")
        self.lbl_preview.pack(fill="both", expand=True, padx=3, pady=3)

        out = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        out.pack(fill="x", padx=28, pady=(22, 0))
        out.grid_columnconfigure(0, weight=1)

        label_row = ctk.CTkFrame(out, fg_color="transparent")
        label_row.grid(row=0, column=0, sticky="w", pady=(0, 6))
        ctk.CTkLabel(label_row, text="", image=make_icon("printer", COLOR_TEXT_MUTED, 15), width=18).pack(side="left", padx=(0, 6))
        self.field_label(label_row, "Pencetak Kad").pack(side="left")

        self.cbo_printer = self.combo_box(out, [], width=420, command=lambda _v: self.update_status_bar())
        self.cbo_printer.grid(row=1, column=0, sticky="ew")
        self.populate_printers()

        self.btn_global_print = self.btn_cta(out, "Cetak Kad Ini Sekarang", self.print_single_card, icon="printer", height=50, state="disabled")
        self.btn_global_print.grid(row=2, column=0, sticky="ew", pady=(16, 10))

        self.btn_global_download = self.btn_secondary(out, "Muat Turun Gambar Kad (PNG)", self.download_card_image, icon="download", height=42)
        self.btn_global_download.grid(row=3, column=0, sticky="ew")

    def build_status_bar(self):
        bar = ctk.CTkFrame(self, height=30, corner_radius=0, fg_color=COLOR_SURFACE, border_width=0)
        bar.grid(row=2, column=0, columnspan=2, sticky="ew")
        bar.pack_propagate(False)
        ctk.CTkFrame(bar, height=1, fg_color=COLOR_BORDER).pack(side="top", fill="x")
        ctk.CTkLabel(bar, text="●", font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color="#22A55A", width=10).pack(side="left", padx=(18, 6))
        self.lbl_status_left = ctk.CTkLabel(bar, text="", font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=COLOR_TEXT_MUTED)
        self.lbl_status_left.pack(side="left")
        ctk.CTkLabel(bar, text=f"MyKUSESS Studio Card Print {APP_VERSION}", font=ctk.CTkFont(family=FONT_FAMILY, size=11),
                     text_color=COLOR_TEXT_SUBTLE).pack(side="right", padx=18)
        self.update_status_bar()

    def update_status_bar(self):
        if not hasattr(self, "lbl_status_left"):
            return
        printer = self.cbo_printer.get() if hasattr(self, "cbo_printer") else "-"
        total = len(self.csv_data)
        marked = sum(1 for r in self.csv_data if r.get("pilih"))
        self.lbl_status_left.configure(text=f"Sedia     |     Pencetak: {printer or '-'}     |     Rekod: {total}  ·  Ditanda: {marked}")

    # ============================================================
    #  LOGIK APLIKASI (tidak berubah — hanya paparan diubah suai)
    # ============================================================
    def generate_random_qr_code(self):
        chars = string.ascii_lowercase + string.digits
        random_code = ''.join(random.choices(chars, k=7))
        self.ent_qr_code.delete(0, tk.END)
        self.ent_qr_code.insert(0, random_code)

    def create_cfg_entry(self, parent, label_text, default_val, row, col, step=1):
        self.field_label(parent, label_text).grid(row=row, column=col, sticky="w", padx=(0 if col == 0 else 12, 10), pady=6)
        container = ctk.CTkFrame(parent, fg_color=COLOR_SURFACE_ALT, corner_radius=9, border_width=1, border_color=COLOR_BORDER)
        container.grid(row=row, column=col + 1, sticky="w", pady=6)
        entry = ctk.CTkEntry(container, width=70, height=32, border_width=0, fg_color=COLOR_SURFACE_ALT, text_color=COLOR_TEXT,
                             justify="center", font=ctk.CTkFont(family=FONT_FAMILY, size=13))
        entry.insert(0, default_val)
        entry.pack(side="left", padx=(4, 0), pady=2)
        entry.bind("<FocusOut>", self.auto_save_layout_config)
        spin_frame = ctk.CTkFrame(container, fg_color="transparent")
        spin_frame.pack(side="left", padx=(0, 4), pady=3)
        for symbol, delta in (("▲", step), ("▼", -step)):
            ctk.CTkButton(spin_frame, text=symbol, width=22, height=15, corner_radius=4, fg_color=COLOR_SURFACE,
                          hover_color=COLOR_BORDER, text_color=COLOR_TEXT_MUTED, font=ctk.CTkFont(family=FONT_FAMILY, size=8),
                          command=lambda d=delta: self.step_cfg_entry(entry, d)).pack(pady=(0, 1))
        return entry

    def step_cfg_entry(self, entry, delta):
        try:
            current = int(entry.get())
        except ValueError:
            current = 0
        entry.delete(0, tk.END)
        entry.insert(0, str(current + delta))
        self.auto_save_layout_config()

    def populate_printers(self):
        try:
            printers = [printer[2] for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
            self.cbo_printer.configure(values=printers)
            default_p = win32print.GetDefaultPrinter()
            if default_p in printers:
                self.cbo_printer.set(default_p)
            elif printers:
                self.cbo_printer.set(printers[0])
        except Exception:
            self.cbo_printer.configure(values=["Tiada Printer Ditemui"])
            self.cbo_printer.set("Tiada Printer Ditemui")

    def save_layout_config(self, silent=False):
        config_data = self.layout_config_dict()
        try:
            with open(self.config_filename, "w") as f:
                json.dump(config_data, f, indent=4)
            if not silent:
                messagebox.showinfo("Berjaya", "Konfigurasi layout berjaya disimpan!")
        except Exception as e:
            if not silent:
                messagebox.showerror("Ralat", f"Gagal menyimpan fail konfigurasi:\n{str(e)}")

    def layout_config_dict(self):
        return {
            "img_x": self.cfg_img_x.get(), "img_y": self.cfg_img_y.get(),
            "img_w": self.cfg_img_w.get(), "img_h": self.cfg_img_h.get(),
            "qr_x": self.cfg_qr_x.get(), "qr_y": self.cfg_qr_y.get(), "qr_size": self.cfg_qr_size.get(),
            "n1_x": self.cfg_n1_x.get(), "n1_y": self.cfg_n1_y.get(), "n1_font": self.cfg_n1_font.get(),
            "n1_font_file": self.cfg_n1_font_file.get(), "n1_bold": self.cfg_n1_bold.get(), "n1_italic": self.cfg_n1_italic.get(),
            "n1_justify": self.cfg_n1_justify.get(),
            "n2_x": self.cfg_n2_x.get(), "n2_y": self.cfg_n2_y.get(), "n2_font": self.cfg_n2_font.get(),
            "n2_font_file": self.cfg_n2_font_file.get(), "n2_bold": self.cfg_n2_bold.get(), "n2_italic": self.cfg_n2_italic.get(),
            "n2_justify": self.cfg_n2_justify.get(),
            "n3_x": self.cfg_n3_x.get(), "n3_y": self.cfg_n3_y.get(), "n3_font": self.cfg_n3_font.get(),
            "n3_font_file": self.cfg_n3_font_file.get(), "n3_bold": self.cfg_n3_bold.get(), "n3_italic": self.cfg_n3_italic.get(),
            "n3_justify": self.cfg_n3_justify.get()
        }

    def auto_save_layout_config(self, *_args):
        # Dipanggil setiap kali mana-mana medan konfigurasi layout berubah,
        # supaya tetapan pengguna terus dikekalkan tanpa perlu tekan "Simpan Layout".
        self.save_layout_config(silent=True)

    def load_layout_config(self, silent=False):
        if not os.path.exists(self.config_filename): return
        try:
            with open(self.config_filename, "r") as f:
                data = json.load(f)
            def set_val(entry, val):
                entry.delete(0, tk.END)
                entry.insert(0, str(val))
            set_val(self.cfg_img_x, data.get("img_x", "40"))
            set_val(self.cfg_img_y, data.get("img_y", "250"))
            set_val(self.cfg_img_w, data.get("img_w", "240"))
            set_val(self.cfg_img_h, data.get("img_h", "310"))
            set_val(self.cfg_qr_x, data.get("qr_x", "735"))
            set_val(self.cfg_qr_y, data.get("qr_y", "255"))
            set_val(self.cfg_qr_size, data.get("qr_size", "230"))
            set_val(self.cfg_n1_x, data.get("n1_x", "340"))
            set_val(self.cfg_n1_y, data.get("n1_y", "410"))
            set_val(self.cfg_n1_font, data.get("n1_font", "45"))
            self.cfg_n1_font_file.set(data.get("n1_font_file", "arial.ttf"))
            self.cfg_n1_bold.set(data.get("n1_bold", True))
            self.cfg_n1_italic.set(data.get("n1_italic", False))
            self.cfg_n1_justify.set(data.get("n1_justify", "Left"))
            set_val(self.cfg_n2_x, data.get("n2_x", "320"))
            set_val(self.cfg_n2_y, data.get("n2_y", "480"))
            set_val(self.cfg_n2_font, data.get("n2_font", "30"))
            self.cfg_n2_font_file.set(data.get("n2_font_file", "arial.ttf"))
            self.cfg_n2_bold.set(data.get("n2_bold", False))
            self.cfg_n2_italic.set(data.get("n2_italic", False))
            self.cfg_n2_justify.set(data.get("n2_justify", "Left"))
            set_val(self.cfg_n3_x, data.get("n3_x", "320"))
            set_val(self.cfg_n3_y, data.get("n3_y", "550"))
            set_val(self.cfg_n3_font, data.get("n3_font", "25"))
            self.cfg_n3_font_file.set(data.get("n3_font_file", "arial.ttf"))
            self.cfg_n3_bold.set(data.get("n3_bold", False))
            self.cfg_n3_italic.set(data.get("n3_italic", True))
            self.cfg_n3_justify.set(data.get("n3_justify", "Left"))
            if not silent:
                messagebox.showinfo("Berjaya", "Tetapan layout berjaya dipulihkan!")
                self.trigger_refresh_preview()
        except Exception as e:
            if not silent: messagebox.showerror("Ralat", str(e))

    def select_bg(self):
        self.bg_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        if self.bg_path:
            self.lbl_bg.configure(text=f"Template: {os.path.basename(self.bg_path)}", text_color=COLOR_SUCCESS)

    # ============================================================
    # TEMPLAT TERSIMPAN (sehingga 4 slot tetapan asas template)
    # ============================================================
    def load_template_presets(self):
        self.template_presets = [None, None, None, None]
        if not os.path.exists(self.template_presets_filename):
            return
        try:
            with open(self.template_presets_filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            for i in range(min(4, len(data))):
                self.template_presets[i] = data[i]
        except Exception:
            pass

    def ask_text_input(self, title, label_text, initial_value=""):
        # Dialog input tersendiri (bukan simpledialog Tk lalai) supaya medan
        # teks cukup lebar untuk nama/label panjang dan konsisten dengan gaya app.
        result = {"value": None}
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("480x170")
        dialog.resizable(False, False)
        dialog.configure(fg_color=COLOR_SURFACE)
        dialog.transient(self)

        ctk.CTkLabel(dialog, text=label_text, font=ctk.CTkFont(family=FONT_FAMILY, size=13), text_color=COLOR_TEXT).pack(anchor="w", padx=20, pady=(22, 8))

        entry = ctk.CTkEntry(dialog, width=440, height=38, border_color=COLOR_BORDER, font=ctk.CTkFont(family=FONT_FAMILY, size=13))
        entry.insert(0, initial_value)
        entry.pack(padx=20)

        def on_ok(event=None):
            result["value"] = entry.get()
            dialog.destroy()

        def on_cancel(event=None):
            dialog.destroy()

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=(18, 15))
        self.btn_secondary(btn_frame, "Batal", on_cancel, width=100).pack(side="left", padx=(0, 8))
        self.btn_primary(btn_frame, "OK", on_ok, width=100).pack(side="left")

        entry.bind("<Return>", on_ok)
        dialog.bind("<Escape>", on_cancel)
        dialog.protocol("WM_DELETE_WINDOW", on_cancel)

        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        dialog.grab_set()
        entry.focus()
        entry.select_range(0, tk.END)
        entry.icursor(tk.END)
        dialog.wait_window()
        return result["value"]

    # ============================================================
    # AUTO-UPDATE (GitHub Releases)
    # ============================================================
    # Thread latar hanya membuat panggilan rangkaian & mengisi dict hasil;
    # semua kemas kini UI dibuat dari thread utama Tk melalui pengundian after().
    def load_update_settings(self):
        try:
            with open(UPDATE_SETTINGS_FILENAME, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_update_settings(self, data):
        try:
            with open(UPDATE_SETTINGS_FILENAME, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception:
            pass

    def _run_in_background(self, work, on_done, poll_ms=150):
        state = {"done": False, "result": None, "error": None}

        def runner():
            try:
                state["result"] = work()
            except Exception as e:
                state["error"] = e
            state["done"] = True

        def poll():
            if state["done"]:
                on_done(state["result"], state["error"])
            else:
                self.after(poll_ms, poll)

        threading.Thread(target=runner, daemon=True).start()
        self.after(poll_ms, poll)

    def check_for_updates(self, manual=False):
        if self._update_check_running:
            return
        self._update_check_running = True
        self.btn_check_update.configure(state="disabled", text="Menyemak...")

        def on_done(info, error):
            self._update_check_running = False
            self.btn_check_update.configure(state="normal", text="Semak Kemas Kini")
            if error is not None:
                # Semakan automatik gagal (cth. tiada internet) -> senyap sahaja
                if manual:
                    messagebox.showwarning(
                        "Semak Kemas Kini",
                        f"Tidak dapat menyemak kemas kini.\nPastikan komputer disambung ke internet.\n\n({error})")
                return

            latest = parse_version(info["tag"])
            if not latest or latest <= parse_version(APP_VERSION):
                if manual:
                    messagebox.showinfo("Semak Kemas Kini", f"Anda sudah menggunakan versi terkini ({APP_VERSION}).")
                return

            if not manual and self.load_update_settings().get("skipped_version") == info["tag"]:
                return
            self.show_update_dialog(info)

        self._run_in_background(fetch_latest_release, on_done)

    def show_update_dialog(self, info):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Kemas Kini Tersedia")
        dialog.geometry("560x470")
        dialog.resizable(False, False)
        dialog.configure(fg_color=COLOR_SURFACE)
        dialog.transient(self)

        ctk.CTkLabel(dialog, text="Versi baharu tersedia!", font=ctk.CTkFont(family=FONT_FAMILY, size=18, weight="bold"),
                     text_color=COLOR_TEXT).pack(anchor="w", padx=22, pady=(20, 2))
        ctk.CTkLabel(dialog, text=f"Versi semasa: {APP_VERSION}    →    Versi baharu: {info['tag']}",
                     font=ctk.CTkFont(family=FONT_FAMILY, size=13), text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=22)

        self.field_label(dialog, "Nota keluaran:").pack(anchor="w", padx=22, pady=(14, 4))
        notes = ctk.CTkTextbox(dialog, width=516, height=220, border_width=1, border_color=COLOR_BORDER,
                               fg_color=COLOR_SURFACE_ALT, text_color=COLOR_TEXT, wrap="word",
                               font=ctk.CTkFont(family=FONT_FAMILY, size=12))
        notes.insert("1.0", info["notes"] or info["name"] or "(Tiada nota keluaran)")
        notes.configure(state="disabled")
        notes.pack(padx=22)

        progress = ctk.CTkProgressBar(dialog, width=516, progress_color=COLOR_ACCENT)
        progress.set(0)
        lbl_status = ctk.CTkLabel(dialog, text="", font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=COLOR_TEXT_MUTED)

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", padx=22, pady=(10, 18))

        def on_skip():
            data = self.load_update_settings()
            data["skipped_version"] = info["tag"]
            self.save_update_settings(data)
            dialog.destroy()

        def on_later():
            dialog.destroy()

        def on_update():
            if not is_frozen_exe():
                # Berjalan dari kod sumber (python MyKusessCetak.py) - tiada exe untuk diganti
                webbrowser.open(info["page"])
                dialog.destroy()
                return
            for b in (btn_skip, btn_later, btn_update):
                b.configure(state="disabled")
            dialog.protocol("WM_DELETE_WINDOW", lambda: None)  # jangan tutup semasa muat turun
            progress.pack(padx=22, pady=(12, 0))
            lbl_status.pack(anchor="w", padx=22)
            self.start_update_download(info, dialog, progress, lbl_status, on_fail=on_download_failed)

        def on_download_failed():
            for b in (btn_skip, btn_later, btn_update):
                b.configure(state="normal")
            dialog.protocol("WM_DELETE_WINDOW", on_later)

        btn_skip = ctk.CTkButton(btn_frame, text="Langkau versi ini", command=on_skip, fg_color="transparent",
                                 hover_color=COLOR_SURFACE_ALT, text_color=COLOR_TEXT_MUTED, width=130, height=36,
                                 font=ctk.CTkFont(family=FONT_FAMILY, size=12))
        btn_skip.pack(side="left")
        btn_update = self.btn_primary(btn_frame, "Kemas Kini Sekarang", on_update, width=170)
        btn_update.pack(side="right")
        btn_later = self.btn_secondary(btn_frame, "Nanti", on_later, width=90)
        btn_later.pack(side="right", padx=(0, 8))

        dialog.bind("<Escape>", lambda _e: on_later())
        dialog.protocol("WM_DELETE_WINDOW", on_later)

        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        dialog.grab_set()

    def start_update_download(self, info, dialog, progress, lbl_status, on_fail):
        new_path = sys.executable + ".new"
        prog = {"done": 0, "total": 0}

        def work():
            download_update(info, new_path, progress_cb=lambda d, t: prog.update(done=d, total=t))

        def tick():
            if not dialog.winfo_exists() or prog.get("finished"):
                return
            mb = prog["done"] / 1_048_576
            if prog["total"]:
                progress.set(min(prog["done"] / prog["total"], 1.0))
                lbl_status.configure(text=f"Memuat turun... {mb:.1f} / {prog['total'] / 1_048_576:.1f} MB")
            else:
                lbl_status.configure(text=f"Memuat turun... {mb:.1f} MB")
            self.after(200, tick)

        def on_done(_result, error):
            prog["finished"] = True
            if error is None:
                progress.set(1.0)
                lbl_status.configure(text="Memasang kemas kini & memulakan semula aplikasi...")
                dialog.update_idletasks()
                try:
                    self.auto_save_layout_config()
                    install_update_and_restart(new_path)
                except Exception as e:
                    error = e
                else:
                    self.destroy()
                    return

            try:
                if os.path.exists(new_path):
                    os.remove(new_path)
            except OSError:
                pass
            lbl_status.configure(text="")
            progress.set(0)
            on_fail()
            hint = ""
            if isinstance(error, PermissionError):
                hint = ("\n\nFolder aplikasi tidak boleh ditulis. Cuba jalankan aplikasi sebagai Administrator, "
                        "atau muat turun versi baharu secara manual.")
            if messagebox.askyesno("Kemas Kini Gagal",
                                   f"Kemas kini tidak berjaya:\n{error}{hint}\n\nBuka halaman muat turun di pelayar?",
                                   parent=dialog):
                webbrowser.open(info["page"])

        tick()
        self._run_in_background(work, on_done)

    def save_template_presets(self):
        try:
            with open(self.template_presets_filename, "w", encoding="utf-8") as f:
                json.dump(self.template_presets, f, indent=4)
        except Exception as e:
            messagebox.showerror("Ralat", f"Gagal menyimpan templat tersimpan:\n{str(e)}")

    def refresh_template_slot_labels(self):
        for i, lbl in enumerate(self.lbl_template_slots):
            preset = self.template_presets[i]
            if preset and preset.get("path"):
                lbl.configure(text=f"Slot {i+1}: {preset.get('name') or os.path.basename(preset['path'])}")
            else:
                lbl.configure(text=f"Slot {i+1}: Kosong")

    def save_template_slot(self, idx):
        if not self.bg_path:
            messagebox.showwarning("Ralat", "Sila pilih Template Kad (Background) terlebih dahulu sebelum menyimpan ke slot.")
            return
        name = self.ask_text_input("Nama Templat", f"Nama untuk Slot {idx+1}:",
                                    os.path.splitext(os.path.basename(self.bg_path))[0])
        if name is None:
            return
        self.template_presets[idx] = {"name": name.strip() or os.path.basename(self.bg_path), "path": self.bg_path}
        self.save_template_presets()
        self.refresh_template_slot_labels()
        messagebox.showinfo("Berjaya", f"Template disimpan ke Slot {idx+1}.")

    def use_template_slot(self, idx, silent=False):
        preset = self.template_presets[idx]
        if not preset or not preset.get("path"):
            if not silent:
                messagebox.showinfo("Slot Kosong", f"Slot {idx+1} belum mempunyai templat tersimpan.\nPilih Template Kad dahulu, kemudian tekan 💾 untuk simpan ke slot ini.")
            return
        if not os.path.exists(preset["path"]):
            if not silent:
                messagebox.showerror("Ralat", f"Fail templat untuk Slot {idx+1} tidak dijumpai:\n{preset['path']}")
            return
        self.bg_path = preset["path"]
        self.lbl_bg.configure(text=f"Template: {os.path.basename(self.bg_path)}", text_color=COLOR_SUCCESS)

    def select_single_photo(self):
        self.single_photo_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        if self.single_photo_path:
            self.lbl_photo.configure(text=f"Foto: {os.path.basename(self.single_photo_path)}", text_color=COLOR_SUCCESS)

    def select_photo_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.photo_folder = folder
            self.lbl_folder.configure(text=f"Folder: {self.photo_folder}", text_color=COLOR_SUCCESS)
            self.save_app_settings()

    def load_csv(self):
        csv_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not csv_path: return
        if self._load_csv_from_path(csv_path):
            self.save_app_settings()

    # Lajur skema mentah eksport "Sistem Outing dan Pulang Bermalam" (GambarID, Nama,
    # Tahap/Tgkt, Kelas, ..., Emel, IDmykusess, ...) -> lajur skema dalaman aplikasi.
    # Pengguna hanya perlu import CSV mentah terus tanpa perlu susun semula lajur sendiri.
    RAW_SCHEMA_MARKER_COLUMN = "IDmykusess"

    def _normalize_csv_row(self, row, is_raw_schema):
        if not is_raw_schema:
            return {
                'kod_qr': row.get('kod_qr', ''),
                'batch': row.get('batch', ''),
                'nama_penuh': row.get('nama_penuh', ''),
                'email_moe': row.get('email_moe', ''),
                'fail_gambar': row.get('fail_gambar', '')
            }

        tahap = (row.get('Tahap/Tgkt') or '').strip()
        kelas = (row.get('Kelas') or '').strip()
        email = (row.get('Emel') or '').strip()
        if email.lower() == 'not_found@missing.my':
            email = ''  # placeholder eksport bagi murid/guru tiada Email MOE
        return {
            'kod_qr': (row.get('IDmykusess') or '').strip(),
            'batch': self._tahap_to_batch_label(tahap) or f"{tahap} {kelas}".strip(),
            'nama_penuh': (row.get('Nama') or '').strip(),
            'email_moe': email,
            'fail_gambar': (row.get('GambarID') or '').strip()
        }

    def _tahap_to_batch_label(self, tahap):
        # Label Batch murid mengikut kohort kemasukan Tingkatan 1, bukan tahap semasa:
        # cth. tahun kemasukan T1=2026 -> T1="BATCH 26-30", T2="BATCH 25-29" (masuk 2025,
        # tamat 2029), dst. Balik None jika Tahap/Tgkt tidak berformat "T<nombor>" atau
        # medan "Tahun Kemasukan Tingkatan 1" tidak diisi/tidak sah, supaya pemanggil boleh
        # gunakan gantian (fallback) selamat.
        match = re.fullmatch(r'T(\d+)', tahap, flags=re.IGNORECASE)
        if not match:
            return None
        try:
            t1_intake_year = int(self.ent_intake_year_t1.get().strip())
        except (ValueError, AttributeError):
            return None

        tahap_num = int(match.group(1))
        intake_year = t1_intake_year - (tahap_num - 1)
        return f"BATCH {intake_year % 100:02d}-{(intake_year + 4) % 100:02d}"

    def _rows_to_records(self, fieldnames, rows, previous=None):
        """Tukar baris (dict per lajur, dari CSV atau Google Sheet) kepada rekod dalaman.
        `previous`: rekod lama — status tanda dikekalkan bagi kod QR yang sama semasa muat semula."""
        is_raw_schema = 'kod_qr' not in fieldnames and self.RAW_SCHEMA_MARKER_COLUMN in fieldnames
        marks = {r['kod_qr']: r['pilih'] for r in (previous or []) if r.get('kod_qr')}
        records = []
        for row in rows:
            row_data = self._normalize_csv_row(row, is_raw_schema)
            row_data['pilih'] = marks.get(row_data['kod_qr'], True)  # rekod baharu lalai ditanda
            records.append(row_data)
        return records

    def _load_csv_from_path(self, csv_path, silent=False):
        # Pengekodan CSV mengikut pilihan pengguna
        enc_option = self.cbo_encoding.get()
        encoding_map = {
            "UTF-8": "utf-8",
            "UTF-8-SIG (With BOM)": "utf-8-sig",
            "ANSI (cp1252)": "cp1252"
        }
        selected_encoding = encoding_map.get(enc_option, "utf-8")

        try:
            with open(csv_path, mode='r', encoding=selected_encoding) as f:
                reader = csv.DictReader(f)
                self.csv_data = self._rows_to_records(reader.fieldnames or [], reader)
            self.refresh_treeview()
            self.lbl_csv.configure(text=f"CSV: {os.path.basename(csv_path)} ({len(self.csv_data)} rekod)", text_color=COLOR_SUCCESS)
            self.last_csv_path = csv_path
            self.data_source = "csv"
            return True
        except Exception as e:
            if not silent:
                messagebox.showerror("Ralat CSV", f"Gagal membaca CSV menggunakan {selected_encoding}:\n{str(e)}")
            return False

    # ============================================================
    # PINDAH TETAPAN KE PC LAIN
    # ============================================================
    def open_transfer_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Pindah Tetapan ke PC Lain")
        dialog.geometry("620x520")
        dialog.resizable(False, False)
        dialog.configure(fg_color=COLOR_BG)
        dialog.transient(self)

        head = ctk.CTkFrame(dialog, fg_color="transparent")
        head.pack(fill="x", padx=24, pady=(20, 4))
        ctk.CTkLabel(head, text="Pindah Tetapan ke PC Lain", font=ctk.CTkFont(family=FONT_FAMILY_SEMIBOLD, size=18),
                     text_color=COLOR_TEXT).pack(anchor="w")
        self.hint_label(head, "Satu fail .mykusess mengandungi templat kad & slot, susun atur kad, tahun kemasukan "
                              "dan sambungan Google Sheet. Foto murid tidak disertakan — ia dimuat turun semula secara automatik.",
                        wraplength=550).pack(anchor="w", pady=(4, 0))

        wrap = ctk.CTkFrame(dialog, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=22, pady=(0, 16))
        body = self.section_card(wrap, "1", "Eksport dari PC ini", "Simpan semua tetapan ke satu fail", icon="download", pady=(14, 10))
        include_gs = tk.BooleanVar(value=bool(self.gsheet_url and self.gsheet_key))
        cb = ctk.CTkCheckBox(body, text="Sertakan sambungan Google Sheet (URL & kunci rahsia)", variable=include_gs,
                             fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, border_color=COLOR_BORDER_STRONG,
                             border_width=2, corner_radius=5, checkbox_width=20, checkbox_height=20,
                             text_color=COLOR_TEXT, font=ctk.CTkFont(family=FONT_FAMILY, size=12))
        cb.pack(anchor="w")
        if not (self.gsheet_url and self.gsheet_key):
            cb.configure(state="disabled")
        self.hint_label(body, "Fail yang mengandungi kunci rahsia hanya untuk PC sekolah — jangan kongsi secara umum.",
                        wraplength=520).pack(anchor="w", pady=(6, 10))
        self.btn_primary(body, "Eksport ke Fail...", lambda: self.export_settings(include_gs.get(), dialog),
                         icon="download", width=200).pack(anchor="w")

        body = self.section_card(wrap, "2", "Import ke PC ini", "Guna fail .mykusess dari PC lain", icon="upload", pady=(0, 10))
        self.hint_label(body, "Tetapan semasa di PC ini akan digantikan. Templat disalin ke folder 'templat' di sebelah aplikasi.",
                        wraplength=520).pack(anchor="w", pady=(0, 10))
        self.btn_secondary(body, "Import dari Fail...", lambda: self.import_settings(dialog), icon="upload", width=200).pack(anchor="w")

        dialog.bind("<Escape>", lambda _e: dialog.destroy())
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        dialog.grab_set()

    def export_settings(self, include_gsheet, parent=None):
        self.auto_save_layout_config()
        default_name = f"Tetapan MyKUSESS {datetime.date.today():%Y-%m-%d}{SETTINGS_BUNDLE_EXT}"
        path = filedialog.asksaveasfilename(parent=parent, defaultextension=SETTINGS_BUNDLE_EXT, initialfile=default_name,
                                            filetypes=[("Tetapan MyKUSESS", f"*{SETTINGS_BUNDLE_EXT}")])
        if not path:
            return
        try:
            summary = build_settings_bundle(path, self.app_settings_dict(), self.layout_config_dict(),
                                            self.template_presets, self.bg_path, include_gsheet)
        except Exception as e:
            messagebox.showerror("Eksport Gagal", f"Tetapan tidak dapat dieksport:\n{e}", parent=parent)
            return
        lines = [f"Tetapan disimpan ke:\n{path}", "",
                 f"• Templat: {summary['templates']} fail ({summary['slots']} slot)",
                 "• Susun atur kad",
                 f"• Google Sheet: {'disertakan' if summary['gsheet'] else 'tidak disertakan'}"]
        if summary["missing"]:
            lines += ["", "Fail templat ini tiada dan tidak disertakan:"] + [f"  {m}" for m in summary["missing"]]
        lines += ["", "Salin fail ini ke PC lain, kemudian pilih Pindah Tetapan → Import."]
        messagebox.showinfo("Eksport Berjaya", "\n".join(lines), parent=parent)

    def import_settings(self, parent=None):
        path = filedialog.askopenfilename(parent=parent, filetypes=[("Tetapan MyKUSESS", f"*{SETTINGS_BUNDLE_EXT}"), ("Semua fail", "*.*")])
        if not path:
            return
        try:
            bundle = read_settings_bundle(path)
        except (SettingsBundleError, ValueError) as e:
            messagebox.showerror("Import Gagal", str(e), parent=parent)
            return

        man, st = bundle["manifest"], bundle["settings"]
        has_gs = bool(st.get("gsheet_url") and st.get("gsheet_key"))
        slot_count = sum(1 for s_ in man.get("slots", []) if s_)
        msg = (f"Import tetapan dari fail ini?\n\nDibuat: {man.get('created', '-')}  (aplikasi {man.get('app_version', '-')})\n"
               f"• Templat: {slot_count} slot\n• Susun atur kad\n• Google Sheet: {'ya' if has_gs else 'tidak'}\n\n"
               "Tetapan semasa di PC ini akan digantikan.")
        if not messagebox.askyesno("Sahkan Import", msg, parent=parent):
            return

        try:
            dest_dir = os.path.abspath(TEMPLATE_IMPORT_DIR)
            written = {m: write_bundle_template(m, data, dest_dir) for m, data in bundle["templates"].items()}

            # Susun atur kad
            if bundle["layout"]:
                with open(self.config_filename, "w") as f:
                    json.dump(bundle["layout"], f, indent=4)
                self.load_layout_config(silent=True)

            # Slot templat (laluan baharu di PC ini)
            presets = [None, None, None, None]
            for s_ in man.get("slots", []):
                if s_ and s_.get("file") in written and 0 <= int(s_.get("slot", -1)) < 4:
                    presets[int(s_["slot"])] = {"name": s_.get("name") or os.path.basename(written[s_["file"]]),
                                                "path": written[s_["file"]]}
            self.template_presets = presets
            self.save_template_presets()
            self.refresh_template_slot_labels()
            current = written.get(man.get("current_template"))
            if current:
                self.bg_path = current
                self.lbl_bg.configure(text=f"Template: {os.path.basename(current)}", text_color=COLOR_SUCCESS)
            else:
                self.use_template_slot(0, silent=True)

            # Tetapan aplikasi
            if st.get("csv_encoding"):
                self.cbo_encoding.set(st["csv_encoding"])
            if st.get("intake_year_t1"):
                self.ent_intake_year_t1.delete(0, tk.END)
                self.ent_intake_year_t1.insert(0, st["intake_year_t1"])
            if has_gs:
                self.gsheet_url, self.gsheet_key = st["gsheet_url"], st["gsheet_key"]
                self.lbl_gsheet.configure(text="Google Sheet: Disambung — tekan butang untuk muat data", text_color=COLOR_TEXT_SUBTLE)
                if st.get("data_source") == "gsheet":
                    self.data_source = "gsheet"
            self.save_app_settings()
        except Exception as e:
            messagebox.showerror("Import Gagal", f"Tetapan tidak dapat diimport sepenuhnya:\n{e}", parent=parent)
            return

        if parent is not None:
            parent.destroy()
        if self.generated_card is not None:
            try:
                self.trigger_refresh_preview()
            except Exception:
                pass
        done = "Tetapan berjaya diimport."
        if has_gs and self.data_source == "gsheet":
            done += "\n\nSenarai murid kini dimuat dari Google Sheet (foto dimuat turun kali pertama — beberapa minit)."
        messagebox.showinfo("Import Berjaya", done)
        if has_gs and self.data_source == "gsheet":
            self.notebook.set("   Cetak Pukal (CSV)   ")
            self.load_from_gsheet(silent=False)

    # ============================================================
    # SUMBER DATA: GOOGLE SHEET
    # ============================================================
    def batch_photo_path(self, photo_filename):
        """Foto rekod pukal: cuba folder gambar dipilih, kemudian cache foto Google Drive."""
        if not photo_filename:
            return ""
        candidates = []
        if self.photo_folder:
            candidates.append(os.path.join(self.photo_folder, photo_filename))
        cached = safe_cache_path(self.photo_cache_dir, photo_filename)
        if cached:
            candidates.append(cached)
        for path in candidates:
            if os.path.exists(path):
                return path
        return candidates[0] if candidates else ""

    def open_gsheet_settings(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Tetapan Google Sheet")
        dialog.geometry("600x420")
        dialog.resizable(False, False)
        dialog.configure(fg_color=COLOR_SURFACE)
        dialog.transient(self)

        head = ctk.CTkFrame(dialog, fg_color="transparent")
        head.pack(fill="x", padx=24, pady=(22, 0))
        ctk.CTkLabel(head, text="", image=make_icon("sheet", COLOR_ACCENT, 22)).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(head, text="Sambungan Google Sheet", font=ctk.CTkFont(family=FONT_FAMILY_SEMIBOLD, size=17),
                     text_color=COLOR_TEXT).pack(side="left")
        self.hint_label(dialog, "Tampal URL Web App sedia ada (yang sama digunakan kiosk/ESP32) dan kunci rahsia "
                                "daripada setupCardPrintKey(). Rujuk google-apps-script/PANDUAN.md.",
                        wraplength=550).pack(anchor="w", padx=24, pady=(8, 14))

        self.field_label(dialog, "URL Web App (berakhir dengan /exec)").pack(anchor="w", padx=24, pady=(0, 6))
        ent_url = self.text_entry(dialog, "https://script.google.com/macros/s/.../exec", width=552)
        ent_url.pack(padx=24)
        if self.gsheet_url:
            ent_url.insert(0, self.gsheet_url)

        self.field_label(dialog, "Kunci Rahsia (API Key)").pack(anchor="w", padx=24, pady=(14, 6))
        key_row = ctk.CTkFrame(dialog, fg_color="transparent")
        key_row.pack(fill="x", padx=24)
        ent_key = self.text_entry(key_row, "Dijana oleh setupCardPrintKey() dalam Apps Script", width=460)
        ent_key.configure(show="•")
        ent_key.pack(side="left", fill="x", expand=True)
        if self.gsheet_key:
            ent_key.insert(0, self.gsheet_key)

        def toggle_key():
            ent_key.configure(show="" if ent_key.cget("show") else "•")
        self.btn_secondary(key_row, "Papar", toggle_key, icon="eye", width=84).pack(side="left", padx=(8, 0))

        lbl_test = ctk.CTkLabel(dialog, text="", font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=COLOR_TEXT_MUTED,
                                wraplength=550, justify="left", anchor="w")
        lbl_test.pack(fill="x", padx=24, pady=(14, 0))

        def on_test():
            url, key = ent_url.get().strip(), ent_key.get().strip()
            if not url or not key:
                lbl_test.configure(text="Sila isi URL dan kunci rahsia.", text_color=COLOR_DANGER)
                return
            btn_test.configure(state="disabled")
            lbl_test.configure(text="Menguji sambungan...", text_color=COLOR_TEXT_MUTED)

            def done(result, error):
                if not dialog.winfo_exists():
                    return
                btn_test.configure(state="normal")
                if error:
                    lbl_test.configure(text=f"Gagal: {error}", text_color=COLOR_DANGER)
                else:
                    lbl_test.configure(text=f"Berjaya disambung ke '{result.get('spreadsheet', '')}' (tab {result.get('sheet', '')}).",
                                       text_color=COLOR_SUCCESS)
            self._run_in_background(lambda: gsheet_call(url, key, "ping", timeout=30), done)

        def on_save():
            self.gsheet_url = ent_url.get().strip()
            self.gsheet_key = ent_key.get().strip()
            self.save_app_settings()
            if self.gsheet_url and self.gsheet_key:
                self.lbl_gsheet.configure(text="Google Sheet: Disambung — tekan butang untuk muat data", text_color=COLOR_TEXT_SUBTLE)
            dialog.destroy()

        btns = ctk.CTkFrame(dialog, fg_color="transparent")
        btns.pack(side="bottom", fill="x", padx=24, pady=(10, 20))
        btn_test = self.btn_secondary(btns, "Uji Sambungan", on_test, icon="plug-zap", width=150)
        btn_test.pack(side="left")
        self.btn_primary(btns, "Simpan", on_save, icon="save", width=120).pack(side="right")
        self.btn_secondary(btns, "Batal", dialog.destroy, width=90).pack(side="right", padx=(0, 8))
        dialog.bind("<Escape>", lambda _e: dialog.destroy())

        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        dialog.grab_set()
        ent_url.focus()

    def load_from_gsheet(self, silent=False):
        if self._gsheet_busy:
            return
        if not (self.gsheet_url and self.gsheet_key):
            if not silent:
                self.open_gsheet_settings()
            return
        self._gsheet_busy = True
        self.btn_gsheet.configure(state="disabled", text="Memuat...")
        self.lbl_gsheet.configure(text="Google Sheet: Memuat senarai murid...", text_color=COLOR_TEXT_MUTED)
        url, key = self.gsheet_url, self.gsheet_key

        def done(result, error):
            if error is not None:
                self._gsheet_busy = False
                self.btn_gsheet.configure(state="normal", text="Muat dari Google Sheet")
                self.lbl_gsheet.configure(text=f"Google Sheet: Gagal — {error}", text_color=COLOR_DANGER)
                if not silent:
                    messagebox.showerror("Google Sheet", f"Gagal memuat data dari Google Sheet:\n\n{error}")
                return
            headers, rows = result
            self.csv_data = self._rows_to_records(headers, rows, previous=self.csv_data if self.data_source == "gsheet" else None)
            self.data_source = "gsheet"
            self.refresh_treeview(self.ent_search.get())
            self.lbl_csv.configure(text="CSV: Tidak digunakan (sumber: Google Sheet)", text_color=COLOR_TEXT_SUBTLE)
            if not self.photo_folder:
                self.lbl_folder.configure(text="Folder: Pilihan — foto diambil terus dari Google Drive", text_color=COLOR_TEXT_SUBTLE)
            loaded_at = datetime.datetime.now().strftime("%H:%M")
            self._gsheet_summary = f"Google Sheet: {len(self.csv_data)} rekod · dimuat {loaded_at}"
            self.lbl_gsheet.configure(text=self._gsheet_summary, text_color=COLOR_SUCCESS)
            self.save_app_settings()
            self._sync_gsheet_photos(url, key)

        self._run_in_background(lambda: gsheet_fetch_rows(url, key), done)

    def _sync_gsheet_photos(self, url, key):
        """Muat turun foto yang belum ada (di folder dipilih atau cache) secara latar belakang."""
        needed = sorted({r['fail_gambar'] for r in self.csv_data
                         if r.get('fail_gambar') and not os.path.exists(self.batch_photo_path(r['fail_gambar']))
                         and safe_cache_path(self.photo_cache_dir, r['fail_gambar'])})
        if not needed:
            self._finish_gsheet_sync(0, {})
            return

        prog = {"done": 0, "total": len(needed)}
        self.btn_gsheet.configure(text="Memuat foto...")

        def tick():
            if not self._gsheet_busy:
                return
            self.lbl_gsheet.configure(text=f"{self._gsheet_summary}\nFoto: {prog['done']}/{prog['total']} dimuat turun...",
                                      text_color=COLOR_TEXT_MUTED)
            self.after(400, tick)

        def work():
            return gsheet_download_photos(url, key, needed, self.photo_cache_dir,
                                          progress_cb=lambda d, t: prog.update(done=d))

        def done(result, error):
            if error is not None:
                self._finish_gsheet_sync(0, {"*": str(error)})
            else:
                self._finish_gsheet_sync(*result)

        tick()
        self._run_in_background(work, done, poll_ms=300)

    def _finish_gsheet_sync(self, ok_count, failed):
        self._gsheet_busy = False
        self.btn_gsheet.configure(state="normal", text="Muat Semula dari Google Sheet")
        text = self._gsheet_summary
        if ok_count:
            text += f"\nFoto: {ok_count} baharu dimuat turun"
        if failed:
            text += f"\nFoto: {len(failed)} gagal (cth. {next(iter(failed.values()))})"
            self.lbl_gsheet.configure(text=text, text_color="#B45309")
        else:
            self.lbl_gsheet.configure(text=text, text_color=COLOR_SUCCESS)
        # Muat semula pratonton murid yang sedang dipaparkan supaya foto yang baru tiba kelihatan
        qr = getattr(self, "_preview_kod_qr", None)
        record = next((r for r in self.csv_data if r['kod_qr'] == qr), None) if (qr and ok_count) else None
        if record:
            try:
                self.update_preview_ui(self.make_card_image(record['kod_qr'], record['batch'], record['nama_penuh'],
                                                            record['email_moe'], record['fail_gambar'], is_batch=True))
            except Exception:
                pass

    # ============================================================
    # TETAPAN APLIKASI TERSIMPAN (folder gambar & fail CSV terakhir)
    # ============================================================
    def restore_app_settings(self):
        if not os.path.exists(self.app_settings_filename):
            return
        try:
            with open(self.app_settings_filename, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return

        folder = data.get("photo_folder", "")
        if folder and os.path.isdir(folder):
            self.photo_folder = folder
            self.lbl_folder.configure(text=f"Folder: {self.photo_folder}", text_color=COLOR_SUCCESS)

        enc = data.get("csv_encoding", "")
        if enc:
            self.cbo_encoding.set(enc)

        intake_year_t1 = data.get("intake_year_t1", "")
        if intake_year_t1:
            self.ent_intake_year_t1.delete(0, tk.END)
            self.ent_intake_year_t1.insert(0, intake_year_t1)

        self.gsheet_url = data.get("gsheet_url", "")
        self.gsheet_key = data.get("gsheet_key", "")
        if self.gsheet_url and self.gsheet_key:
            self.lbl_gsheet.configure(text="Google Sheet: Disambung — tekan butang untuk muat data")

        csv_path = data.get("csv_path", "")
        if data.get("data_source") == "gsheet" and self.gsheet_url and self.gsheet_key:
            # Sumber terakhir ialah Google Sheet: muat semula data terkini selepas UI siap
            self.data_source = "gsheet"
            self.after(1200, lambda: self.load_from_gsheet(silent=True))
        elif csv_path and os.path.exists(csv_path):
            self._load_csv_from_path(csv_path, silent=True)

    def save_app_settings(self):
        data = self.app_settings_dict()
        try:
            with open(self.app_settings_filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception:
            pass

    def app_settings_dict(self):
        return {
            "photo_folder": self.photo_folder,
            "csv_path": self.last_csv_path,
            "csv_encoding": self.cbo_encoding.get(),
            "intake_year_t1": self.ent_intake_year_t1.get().strip(),
            "data_source": self.data_source,
            "gsheet_url": self.gsheet_url,
            "gsheet_key": self.gsheet_key,
        }

    def refresh_treeview(self, filter_text=""):
        self.tree.delete(*self.tree.get_children())
        for row in self.csv_data:
            # Tapis carian secara tidak sensitif huruf (case-insensitive)
            if filter_text:
                f_text = filter_text.lower()
                if f_text not in row['nama_penuh'].lower() and f_text not in row['batch'].lower():
                    continue

            pilih_symbol = "✅" if row['pilih'] else "⬜"
            row_tag = "row_on" if row['pilih'] else "row_off"
            # Papar penanda jelas apabila Email MOE sengaja dikosongkan (murid tiada email),
            # supaya senarai tidak kelihatan seperti data hilang/tertinggal.
            email_display = row['email_moe'] if row['email_moe'] else "(Tiada Email)"
            self.tree.insert("", tk.END, values=(pilih_symbol, row['kod_qr'], row['batch'], row['nama_penuh'], email_display), tags=(row_tag,))

        if hasattr(self, "lbl_tree_count"):
            total = len(self.csv_data)
            marked = sum(1 for r in self.csv_data if r.get("pilih"))
            shown = len(self.tree.get_children())
            if total:
                text = f"{total} rekod  ·  {marked} ditanda untuk dicetak"
                if shown != total:
                    text += f"  ·  {shown} dipaparkan (carian)"
            else:
                text = "Tiada rekod dimuat"
            self.lbl_tree_count.configure(text=text)
        self.update_status_bar()

    def filter_search(self, event):
        query = self.ent_search.get()
        self.refresh_treeview(query)

    def clear_search(self):
        self.ent_search.delete(0, tk.END)
        self.refresh_treeview()

    def select_all_records(self):
        """Menandakan semua rekod murid."""
        if not self.csv_data: return
        for row in self.csv_data:
            row['pilih'] = True
        self.refresh_treeview(self.ent_search.get())

    def deselect_all_records(self):
        """Mengosongkan tanda daripada semua rekod murid."""
        if not self.csv_data: return
        for row in self.csv_data:
            row['pilih'] = False
        self.refresh_treeview(self.ent_search.get())

    def on_tree_click(self, event):
        # Mengesan baris dan lajur yang diklik
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell": return

        column = self.tree.identify_column(event.x)
        selected_item = self.tree.focus()
        if not selected_item: return

        values = self.tree.item(selected_item, "values")
        kod_qr_val = values[1]

        # Cari data murid dalam self.csv_data
        record = next((r for r in self.csv_data if r['kod_qr'] == kod_qr_val), None)
        if not record: return

        # Jika kolum pertama (Pilih) diklik, tukar status checkbox
        if column == "#1":
            record['pilih'] = not record['pilih']
            self.refresh_treeview(self.ent_search.get())

        # Tunjuk preview kad secara automatik apabila baris disentuh
        try:
            card = self.make_card_image(record['kod_qr'], record['batch'], record['nama_penuh'], record['email_moe'], record['fail_gambar'], is_batch=True)
            self.update_preview_ui(card)
            self._preview_kod_qr = record['kod_qr']
        except Exception as e:
            self.lbl_preview.configure(image="", text=f"Gagal Preview:\n{str(e)}", text_color=COLOR_DANGER)
            self.btn_global_print.configure(state="disabled")

    def on_tree_double_click(self, event):
        # Dwi-klik pada lajur "Nama Penuh" (#4) atau "Email MOE" (#5) membolehkan
        # pengguna sunting terus - cth. memendekkan nama panjang, atau mengosongkan
        # Email MOE murid yang tiada emel (kosongkan medan = tiada emel dicetak pada kad).
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell": return

        column = self.tree.identify_column(event.x)
        if column not in ("#4", "#5"): return

        selected_item = self.tree.focus()
        if not selected_item: return

        values = self.tree.item(selected_item, "values")
        kod_qr_val = values[1]
        record = next((r for r in self.csv_data if r['kod_qr'] == kod_qr_val), None)
        if not record: return

        if column == "#4":
            field, title, label = "nama_penuh", "Edit Nama Penuh", "Nama Penuh:"
        else:
            field, title, label = "email_moe", "Edit Email MOE", "Email MOE (kosongkan jika murid tiada Email MOE):"

        new_val = self.ask_text_input(title, label, record[field])
        if new_val is None: return
        new_val = new_val.strip()
        if field == "nama_penuh" and not new_val:
            messagebox.showwarning("Ralat", "Nama tidak boleh kosong.")
            return

        record[field] = new_val
        self.refresh_treeview(self.ent_search.get())

        try:
            card = self.make_card_image(record['kod_qr'], record['batch'], record['nama_penuh'], record['email_moe'], record['fail_gambar'], is_batch=True)
            self.update_preview_ui(card)
        except Exception as e:
            self.lbl_preview.configure(image="", text=f"Gagal Preview:\n{str(e)}", text_color=COLOR_DANGER)
            self.btn_global_print.configure(state="disabled")

    def get_font_path(self, base_font, bold, italic):
        font_map = {
            "arial.ttf": {"b": "arialbd.ttf", "i": "ariali.ttf", "bi": "arialbi.ttf", "r": "arial.ttf"},
            "calibri.ttf": {"b": "calibrib.ttf", "i": "calibrii.ttf", "bi": "calibriz.ttf", "r": "calibri.ttf"},
            "times.ttf": {"b": "timesbd.ttf", "i": "timesi.ttf", "bi": "timesbi.ttf", "r": "times.ttf"},
            "tahoma.ttf": {"b": "tahomabd.ttf", "i": "tahoma.ttf", "bi": "tahomabd.ttf", "r": "tahoma.ttf"},
            "verdana.ttf": {"b": "verdanab.ttf", "i": "verdanai.ttf", "bi": "verdanaz.ttf", "r": "verdana.ttf"},
            "cour.ttf": {"b": "courbd.ttf", "i": "couri.ttf", "bi": "courbi.ttf", "r": "cour.ttf"}
        }
        selected = font_map.get(base_font, font_map["arial.ttf"])
        return selected["bi"] if bold and italic else selected["b"] if bold else selected["i"] if italic else selected["r"]

    def crop_to_square_keep_width(self, img):
        # Sesetengah foto murid/guru bukan nisbah 1:1 (cth. potret menegak) — dipotong
        # (crop) tengah menegak supaya tinggi menyamai lebar asal, supaya foto sentiasa
        # persegi dan tidak melimpah menutup teks nama di bawahnya semasa preview/cetak.
        w, h = img.size
        if h <= w:
            return img
        top = (h - w) // 2
        return img.crop((0, top, w, top + w))

    def make_card_image(self, qr_code, batch, full_name, email_moe, photo_filename, is_batch=False):
        if not self.bg_path: raise Exception("Sila pilih gambar Template Kad terlebih dahulu!")
        p_path = photo_filename if not is_batch else self.batch_photo_path(photo_filename)
        has_photo = bool(photo_filename) and os.path.exists(p_path)

        img_x, img_y = int(self.cfg_img_x.get()), int(self.cfg_img_y.get())
        img_w, img_h = int(self.cfg_img_w.get()), int(self.cfg_img_h.get())
        qr_x, qr_y = int(self.cfg_qr_x.get()), int(self.cfg_qr_y.get())
        qr_sz = int(self.cfg_qr_size.get())
        n1_x, n1_y = int(self.cfg_n1_x.get()), int(self.cfg_n1_y.get())
        n1_fs = int(self.cfg_n1_font.get())
        n2_x, n2_y = int(self.cfg_n2_x.get()), int(self.cfg_n2_y.get())
        n2_fs = int(self.cfg_n2_font.get())
        n3_x, n3_y = int(self.cfg_n3_x.get()), int(self.cfg_n3_y.get())
        n3_fs = int(self.cfg_n3_font.get())

        card = Image.open(self.bg_path).convert('RGBA').resize((1013, 638))
        if has_photo:
            raw_photo = Image.open(p_path).convert('RGBA')
            square_photo = self.crop_to_square_keep_width(raw_photo)
            teacher_img = ImageOps.contain(square_photo, (img_w, img_h))
            actual_w, actual_h = teacher_img.size
            card.paste(teacher_img, (img_x + (img_w - actual_w) // 2, img_y + (img_h - actual_h) // 2), teacher_img)

        clean_code = qr_code.strip().lower()
        if clean_code.startswith("mykusses:"):
            clean_code = clean_code[len("mykusses:"):]
        qr = qrcode.QRCode(box_size=6, border=1)
        qr.add_data(f"mykusses:{clean_code}")
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGBA').resize((qr_sz, qr_sz), resample=Image.NEAREST)
        card.paste(qr_img, (qr_x, qr_y))

        draw = ImageDraw.Draw(card)
        try: font_n1 = ImageFont.truetype(self.get_font_path(self.cfg_n1_font_file.get(), self.cfg_n1_bold.get(), self.cfg_n1_italic.get()), n1_fs)
        except: font_n1 = ImageFont.load_default()
        try: font_n2 = ImageFont.truetype(self.get_font_path(self.cfg_n2_font_file.get(), self.cfg_n2_bold.get(), self.cfg_n2_italic.get()), n2_fs)
        except: font_n2 = ImageFont.load_default()
        try: font_n3 = ImageFont.truetype(self.get_font_path(self.cfg_n3_font_file.get(), self.cfg_n3_bold.get(), self.cfg_n3_italic.get()), n3_fs)
        except: font_n3 = ImageFont.load_default()

        align_map = {
            "Left": "la",
            "Center": "ma",
            "Right": "ra"
        }
        anchor1 = align_map.get(self.cfg_n1_justify.get(), "la")
        anchor2 = align_map.get(self.cfg_n2_justify.get(), "la")
        anchor3 = align_map.get(self.cfg_n3_justify.get(), "la")

        draw.text((n1_x, n1_y), batch.upper(), fill="black", font=font_n1, anchor=anchor1)
        draw.text((n2_x, n2_y), full_name.upper(), fill="black", font=font_n2, anchor=anchor2)
        draw.text((n3_x, n3_y), email_moe.lower(), fill="black", font=font_n3, anchor=anchor3)
        return card

    def update_preview_ui(self, card_image):
        self.generated_card = card_image
        w, h = self.PREVIEW_W - 6, self.PREVIEW_H - 6
        preview_img = card_image.copy().convert("RGB").resize((w * 2, h * 2), resample=Image.Resampling.LANCZOS)
        self.photo_preview = ctk.CTkImage(light_image=preview_img, dark_image=preview_img, size=(w, h))
        self.lbl_preview.configure(image=self.photo_preview, text="")
        self.btn_global_print.configure(state="normal")

    def generate_single_preview(self):
        if not self.ent_qr_code.get() or not self.ent_batch.get() or not self.ent_full_name.get() or not self.ent_email_moe.get() or not self.single_photo_path:
            messagebox.showwarning("Ralat", "Sila lengkapkan maklumat individu!")
            return
        try:
            card = self.make_card_image(self.ent_qr_code.get(), self.ent_batch.get(), self.ent_full_name.get(), self.ent_email_moe.get(), self.single_photo_path)
            self.update_preview_ui(card)
        except Exception as e: messagebox.showerror("Ralat", str(e))

    def trigger_refresh_preview(self):
        self.auto_save_layout_config()
        selected_items = self.tree.selection()
        if selected_items:
            # Trigger preview baris pertama yang diserlahkan
            values = self.tree.item(selected_items[0], "values")
            record = next((r for r in self.csv_data if r['kod_qr'] == values[1]), None)
            if record:
                try:
                    card = self.make_card_image(record['kod_qr'], record['batch'], record['nama_penuh'], record['email_moe'], record['fail_gambar'], is_batch=True)
                    self.update_preview_ui(card)
                except Exception as e: messagebox.showerror("Ralat", str(e))
        elif self.ent_qr_code.get() and self.single_photo_path:
            self.generate_single_preview()

    def print_single_card(self):
        if self.generated_card is None: return
        try:
            self.generated_card.save("temp_print.png")
            self.send_to_printer("temp_print.png")
            messagebox.showinfo("Berjaya", "Kad berjaya dihantar ke pencetak!")
        except Exception as e: messagebox.showerror("Ralat", str(e))

    def download_card_image(self):
        if self.generated_card is None: return
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Image", "*.png")])
        if file_path:
            self.generated_card.save(file_path)
            messagebox.showinfo("Berjaya", "Gambar kad berjaya disimpan!")

    def print_batch(self):
        # Ambil data bertanda [x] sahaja
        selected_records = [r for r in self.csv_data if r['pilih']]
        if not selected_records:
            messagebox.showwarning("Ralat", "Sila tanda [x] pada senarai murid terlebih dahulu!")
            return
        if not self.bg_path or not (self.photo_folder or self.data_source == "gsheet"):
            messagebox.showwarning("Ralat", "Sila pastikan Template Kad dan Folder Gambar telah dipilih!")
            return
        if not messagebox.askyesno("Sahkan", f"Cetak {len(selected_records)} keping kad murid yang ditandakan?"): return

        total_cards = len(selected_records)
        success_count = 0
        failed_cards = []

        for index, record in enumerate(selected_records):
            self.lbl_progress_status.configure(text=f"Mencetak ({index + 1}/{total_cards}): {record['nama_penuh']}")
            self.update_idletasks()
            try:
                card = self.make_card_image(record['kod_qr'], record['batch'], record['nama_penuh'], record['email_moe'], record['fail_gambar'], is_batch=True)
                card.save("temp_batch_print.png")
                self.send_to_printer("temp_batch_print.png")
                success_count += 1
            except Exception as e:
                failed_cards.append(record['nama_penuh'])

            self.progress_bar.set((index + 1) / total_cards)
            self.update_idletasks()

        self.lbl_progress_status.configure(text="Status: Selesai.")
        messagebox.showinfo("Selesai", f"Berjaya cetak: {success_count} kad.\nGagal: {len(failed_cards)}")

    def download_pdf_batch(self):
        selected_records = [r for r in self.csv_data if r['pilih']]
        if not selected_records:
            messagebox.showwarning("Ralat", "Sila tanda [x] pada sekurang-kurangnya satu murid untuk menjana PDF!")
            return
        if not self.bg_path or not (self.photo_folder or self.data_source == "gsheet"):
            messagebox.showwarning("Ralat", "Sila pastikan Template Kad dan Folder Gambar telah dipilih!")
            return

        pdf_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Document", "*.pdf")])
        if not pdf_path: return

        total_cards = len(selected_records)
        pdf_images = []

        for index, record in enumerate(selected_records):
            self.lbl_progress_status.configure(text=f"Menjana PDF ({index + 1}/{total_cards}): {record['nama_penuh']}")
            self.update_idletasks()
            try:
                card = self.make_card_image(record['kod_qr'], record['batch'], record['nama_penuh'], record['email_moe'], record['fail_gambar'], is_batch=True)
                # Tukar ke mod RGB untuk simpanan PDF yang disokong PIL
                pdf_images.append(card.convert("RGB"))
            except Exception as e:
                messagebox.showerror("Ralat Fail", f"Gagal menghasilkan kad bagi {record['nama_penuh']}:\n{str(e)}")
                return

            self.progress_bar.set((index + 1) / total_cards)
            self.update_idletasks()

        if pdf_images:
            try:
                # Simpan berbilang imej sebagai satu dokumen PDF
                pdf_images[0].save(pdf_path, save_all=True, append_images=pdf_images[1:])
                self.lbl_progress_status.configure(text="Status: PDF Berjaya Dijana.")
                messagebox.showinfo("Berjaya", f"Fail PDF berjaya disimpan di:\n{pdf_path}")
            except Exception as e:
                messagebox.showerror("Ralat PDF", f"Gagal menyimpan PDF:\n{str(e)}")

    def send_to_printer(self, filename):
        printer_name = self.cbo_printer.get()
        if not printer_name or printer_name == "Tiada Printer Ditemui": raise Exception("Pencetak tidak sah!")
        hdc = win32ui.CreateDC()
        try:
            hdc.CreatePrinterDC(printer_name)
            hdc.StartDoc("Batch Cetak MyKUSESS")
            hdc.StartPage()
            with Image.open(filename) as bmp:
                # Kad ID (86mm x 54mm) menyamai keseluruhan "halaman" fizikal pada
                # pencetak kad — tiada kertas/margin tambahan di luar kad itu sendiri.
                # Lukis terus merentasi PHYSICALWIDTH/HEIGHT sebenar (bukan kira semula
                # saiz sasaran daripada mm x DPI dan "centering" ke tengah halaman):
                # percubaan sebelum ini mengira dest_w/h berasingan daripada mm/DPI
                # meninggalkan jidar putih ~1-2mm di satu sisi apabila hasil bulatan
                # (rounding) itu tidak tepat menyamai saiz sebenar yang dilaporkan
                # pencetak. Menggunakan PHYSICALWIDTH/HEIGHT terus (dikira pencetak
                # sendiri mengikut DPI per-paksi) tetap mengekalkan nisbah aspek betul
                # tanpa risiko regangan (stretch) — cf. bug "tertarik menegak" v1.00.
                page_w = hdc.GetDeviceCaps(win32con.PHYSICALWIDTH) or hdc.GetDeviceCaps(win32con.HORZRES)
                page_h = hdc.GetDeviceCaps(win32con.PHYSICALHEIGHT) or hdc.GetDeviceCaps(win32con.VERTRES)
                offset_x = -hdc.GetDeviceCaps(win32con.PHYSICALOFFSETX)
                offset_y = -hdc.GetDeviceCaps(win32con.PHYSICALOFFSETY)

                dib = ImageWin.Dib(bmp)
                dib.draw(hdc.GetHandleOutput(), (offset_x, offset_y, offset_x + page_w, offset_y + page_h))
            hdc.EndPage()
            hdc.EndDoc()
        finally:
            hdc.DeleteDC()


if __name__ == "__main__":
    app = CardPrinterApp()
    app.mainloop()
