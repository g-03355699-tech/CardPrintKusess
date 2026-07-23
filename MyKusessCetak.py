import os
import csv
import json
import sys
import random
import string
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk, simpledialog
from PIL import Image, ImageDraw, ImageFont, ImageTk, ImageOps
import qrcode
import win32print
import win32ui
import win32con
from PIL import ImageWin

APP_VERSION = "v1.02"

# ============================================================
#  TEMA & GAYA — reka bentuk profesional seakan Badgy Studio
# ============================================================
ctk.set_appearance_mode("Light")   # tema cerah konsisten (elak konflik warna hardcode dgn mod gelap)
ctk.set_default_color_theme("blue")

FONT_FAMILY = "Segoe UI"

COLOR_BG            = "#F1F5F9"   # latar belakang tetingkap
COLOR_HEADER_BG      = "#0F172A"  # bar header navy gelap
COLOR_SURFACE        = "#FFFFFF"  # permukaan panel
COLOR_SURFACE_ALT    = "#EEF2F7"  # permukaan sekunder (tab tidak aktif, dsb.)
COLOR_BORDER         = "#E2E8F0"
COLOR_TEXT           = "#1E293B"
COLOR_TEXT_MUTED     = "#64748B"
COLOR_ACCENT         = "#2F6FED"
COLOR_ACCENT_HOVER   = "#2557C7"
COLOR_SUCCESS        = "#16A34A"
COLOR_SUCCESS_HOVER  = "#128A3E"
COLOR_DANGER         = "#DC2626"
COLOR_DANGER_HOVER   = "#B91C1C"
COLOR_NEUTRAL        = "#64748B"
COLOR_NEUTRAL_HOVER  = "#475569"


class CardPrinterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"MyKUSESS Studio {APP_VERSION} — Sistem Cetakan Kad Pintar")
        self.geometry("1400x900")
        self.configure(fg_color=COLOR_BG)

        # --- KETETAPAN IKON PERISIAN ---
        self.app_icon_path = None
        try:
            if hasattr(sys, '_MEIPASS'):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.abspath(".")
            icon_path = os.path.join(base_path, "logo.ico")
            self.iconbitmap(icon_path)
            self.app_icon_path = icon_path
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

        # --- GRID UTAMA (baris 0 = header jenama, baris 1 = kandungan) ---
        self.grid_columnconfigure(0, weight=4, minsize=700)
        self.grid_columnconfigure(1, weight=5, minsize=550)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        self.build_header()

        # --- BAHAGIAN KIRI: TAB KAWALAN ---
        self.notebook = ctk.CTkTabview(
            self,
            corner_radius=14,
            fg_color=COLOR_SURFACE,
            border_width=1,
            border_color=COLOR_BORDER,
            segmented_button_fg_color=COLOR_SURFACE_ALT,
            segmented_button_selected_color=COLOR_ACCENT,
            segmented_button_selected_hover_color=COLOR_ACCENT_HOVER,
            segmented_button_unselected_color=COLOR_SURFACE_ALT,
            segmented_button_unselected_hover_color=COLOR_BORDER,
            text_color=COLOR_TEXT,
        )
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=(15, 8), pady=(0, 15))

        self.tab_single = self.notebook.add(" 🪪  Cetak Satu-Satu ")
        self.tab_batch = self.notebook.add(" 📇  Cetak Pukal (CSV) ")
        self.tab_config = self.notebook.add(" ⚙️  Konfigurasi Layout ")

        # --- BAHAGIAN KANAN: PANEL PREVIEW & PRINTER ---
        self.right_frame = ctk.CTkFrame(self, corner_radius=14, fg_color=COLOR_SURFACE, border_width=1, border_color=COLOR_BORDER)
        self.right_frame.grid(row=1, column=1, sticky="nsew", padx=(8, 15), pady=(0, 15))

        self.build_tab_single()
        self.build_tab_batch()
        self.build_tab_config()
        self.load_layout_config(silent=True)
        self.use_template_slot(0, silent=True)
        self.build_preview_panel()

    # ============================================================
    #  KOMPONEN UI BOLEH GUNA SEMULA (helper widget & gaya)
    # ============================================================
    def build_header(self):
        header = ctk.CTkFrame(self, height=64, corner_radius=0, fg_color=COLOR_HEADER_BG)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_propagate(False)

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", padx=20, pady=8)

        if self.app_icon_path:
            try:
                logo_img = Image.open(self.app_icon_path).convert("RGBA")
                logo_img.thumbnail((36, 36))
                ctk_logo = ctk.CTkImage(light_image=logo_img, dark_image=logo_img, size=logo_img.size)
                ctk.CTkLabel(left, image=ctk_logo, text="").pack(side="left", padx=(0, 10))
            except Exception:
                pass

        title_box = ctk.CTkFrame(left, fg_color="transparent")
        title_box.pack(side="left")
        ctk.CTkLabel(title_box, text="MyKUSESS Studio", font=ctk.CTkFont(family=FONT_FAMILY, size=18, weight="bold"), text_color="#FFFFFF").pack(anchor="w")
        ctk.CTkLabel(title_box, text="Sistem Cetakan Kad MyKusess", font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color="#94A3B8").pack(anchor="w")

        right = ctk.CTkFrame(header, fg_color="transparent")
        right.pack(side="right", padx=20, pady=8)
        ctk.CTkLabel(
            right, text=APP_VERSION, font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            text_color="#FFFFFF", fg_color=COLOR_ACCENT, corner_radius=10, width=52, height=24,
        ).pack(side="right")

    def section_header(self, parent, number, text):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(anchor="w", fill="x", pady=(18, 10))
        ctk.CTkLabel(
            row, text=str(number), width=22, height=22, corner_radius=11, fg_color=COLOR_ACCENT,
            text_color="#FFFFFF", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(row, text=text, font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"), text_color=COLOR_TEXT).pack(side="left")
        return row

    def field_label(self, parent, text):
        return ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=COLOR_TEXT_MUTED)

    def status_label(self, parent, text):
        return ctk.CTkLabel(parent, text=text, text_color=COLOR_DANGER, font=ctk.CTkFont(family=FONT_FAMILY, size=11), wraplength=400, justify="left")

    def btn_primary(self, parent, text, command, **kw):
        kw.setdefault("height", 38)
        return ctk.CTkButton(parent, text=text, command=command, fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
                              font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"), corner_radius=8, **kw)

    def btn_secondary(self, parent, text, command, **kw):
        kw.setdefault("height", 36)
        return ctk.CTkButton(parent, text=text, command=command, fg_color="transparent", hover_color=COLOR_SURFACE_ALT,
                              text_color=COLOR_TEXT, border_width=1, border_color=COLOR_BORDER,
                              font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"), corner_radius=8, **kw)

    def btn_success(self, parent, text, command, **kw):
        kw.setdefault("height", 38)
        return ctk.CTkButton(parent, text=text, command=command, fg_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS_HOVER,
                              font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"), corner_radius=8, **kw)

    def btn_danger(self, parent, text, command, **kw):
        kw.setdefault("height", 34)
        return ctk.CTkButton(parent, text=text, command=command, fg_color="#FDECEC", hover_color="#FBD5D5",
                              text_color=COLOR_DANGER, font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"), corner_radius=8, **kw)

    # ============================================================
    # TAB 1: CETAK SATU-SATU
    # ============================================================
    def build_tab_single(self):
        pad = ctk.CTkFrame(self.tab_single, fg_color="transparent")
        pad.pack(fill="both", expand=True, padx=8)

        self.section_header(pad, "1", "Tetapan Asas Template")
        self.btn_secondary(pad, "🖼  Pilih Template Kad (Background)", self.select_bg, width=320).pack(anchor="w", pady=5)
        self.lbl_bg = self.status_label(pad, "Template: Tiada fail dipilih")
        self.lbl_bg.pack(anchor="w", pady=2)

        self.field_label(pad, "Templat Tersimpan (sehingga 4 slot) — 'Guna' untuk muat, 💾 untuk simpan template semasa").pack(anchor="w", pady=(12, 4))
        slot_frame = ctk.CTkFrame(pad, fg_color=COLOR_SURFACE_ALT, corner_radius=10)
        slot_frame.pack(anchor="w", pady=2, fill="x")
        self.lbl_template_slots = []
        for i in range(4):
            col = ctk.CTkFrame(slot_frame, fg_color="transparent")
            col.grid(row=0, column=i, padx=8, pady=8, sticky="n")
            lbl = ctk.CTkLabel(col, text=f"Slot {i+1}: Kosong", font=ctk.CTkFont(family=FONT_FAMILY, size=10),
                                text_color=COLOR_TEXT_MUTED, wraplength=95, justify="center")
            lbl.pack(pady=(0, 4))
            self.lbl_template_slots.append(lbl)
            btn_row = ctk.CTkFrame(col, fg_color="transparent")
            btn_row.pack()
            ctk.CTkButton(btn_row, text="Guna", width=50, height=26, fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
                          font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"), corner_radius=6,
                          command=lambda idx=i: self.use_template_slot(idx)).pack(side="left", padx=(0, 3))
            ctk.CTkButton(btn_row, text="💾", width=30, height=26, fg_color="transparent", hover_color=COLOR_SURFACE,
                          text_color=COLOR_TEXT, border_width=1, border_color=COLOR_BORDER, corner_radius=6,
                          command=lambda idx=i: self.save_template_slot(idx)).pack(side="left")
        self.refresh_template_slot_labels()

        self.section_header(pad, "2", "Maklumat Individu")
        self.btn_secondary(pad, "👤  Pilih Foto Guru/Murid", self.select_single_photo, width=320).pack(anchor="w", pady=5)
        self.lbl_photo = self.status_label(pad, "Foto: Tiada fail dipilih")
        self.lbl_photo.pack(anchor="w", pady=2)

        self.field_label(pad, "Kod Unik QR").pack(anchor="w", pady=(14, 4))
        qr_input_frame = ctk.CTkFrame(pad, fg_color="transparent")
        qr_input_frame.pack(anchor="w", pady=2, fill="x")
        self.ent_qr_code = ctk.CTkEntry(qr_input_frame, width=280, height=34, border_color=COLOR_BORDER, placeholder_text="Contoh: wpwj727")
        self.ent_qr_code.pack(side="left", padx=(0, 10))
        self.btn_generate_qr = self.btn_secondary(qr_input_frame, "🎲 Jana Kod", self.generate_random_qr_code, width=110, height=34)
        self.btn_generate_qr.pack(side="left")

        self.field_label(pad, "Batch (Huruf Besar)").pack(anchor="w", pady=(12, 4))
        self.ent_batch = ctk.CTkEntry(pad, width=400, height=34, border_color=COLOR_BORDER, placeholder_text="Contoh: BATCH 2026")
        self.ent_batch.pack(anchor="w", pady=2)

        self.field_label(pad, "Nama Penuh").pack(anchor="w", pady=(12, 4))
        self.ent_full_name = ctk.CTkEntry(pad, width=400, height=34, border_color=COLOR_BORDER, placeholder_text="Contoh: AMINAH BINTI ALI")
        self.ent_full_name.pack(anchor="w", pady=2)

        self.field_label(pad, "Email MOE").pack(anchor="w", pady=(12, 4))
        self.ent_email_moe = ctk.CTkEntry(pad, width=400, height=34, border_color=COLOR_BORDER, placeholder_text="Contoh: m-1234567@moe-dl.edu.my")
        self.ent_email_moe.pack(anchor="w", pady=2)

        self.btn_primary(pad, "JANA PREVIEW", self.generate_single_preview, width=320, height=42).pack(pady=25)

    # ============================================================
    # TAB 2: CETAK PUKAL (BATCH CSV)
    # ============================================================
    def build_tab_batch(self):
        pad = ctk.CTkFrame(self.tab_batch, fg_color="transparent")
        pad.pack(fill="both", expand=True, padx=8)

        self.section_header(pad, "1", "Sediakan Tetapan Fail")

        setting_frame = ctk.CTkFrame(pad, fg_color=COLOR_SURFACE_ALT, corner_radius=10)
        setting_frame.pack(fill="x", pady=5)

        self.btn_secondary(setting_frame, "📁 Pilih Folder Gambar", self.select_photo_folder, width=180).grid(row=0, column=0, padx=10, pady=10)
        self.lbl_folder = self.status_label(setting_frame, "Folder: Tiada dipilih")
        self.lbl_folder.configure(wraplength=200)
        self.lbl_folder.grid(row=0, column=1, padx=5, pady=10, sticky="w")

        self.field_label(setting_frame, "Format CSV Encoding").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.cbo_encoding = ctk.CTkComboBox(setting_frame, values=["UTF-8", "UTF-8-SIG (With BOM)", "ANSI (cp1252)"], width=190, button_color=COLOR_ACCENT, border_color=COLOR_BORDER)
        self.cbo_encoding.set("UTF-8")
        self.cbo_encoding.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        self.btn_primary(setting_frame, "⬆  Muat Naik CSV", self.load_csv, width=180, height=34).grid(row=2, column=0, padx=10, pady=10)
        self.lbl_csv = self.status_label(setting_frame, "CSV: Tiada fail dipilih")
        self.lbl_csv.grid(row=2, column=1, padx=5, pady=10, sticky="w")

        search_frame = ctk.CTkFrame(pad, fg_color="transparent")
        search_frame.pack(fill="x", pady=(14, 5))
        self.field_label(search_frame, "🔍 Carian Nama / Batch").pack(side="left", padx=(0, 8))
        self.ent_search = ctk.CTkEntry(search_frame, placeholder_text="Masukkan nama kata kunci...", width=250, height=32, border_color=COLOR_BORDER)
        self.ent_search.pack(side="left", padx=5)
        self.ent_search.bind("<KeyRelease>", self.filter_search)
        self.btn_secondary(search_frame, "Kosongkan", self.clear_search, width=90, height=32).pack(side="left", padx=5)

        self.section_header(pad, "2", "Senarai Murid (Klik untuk tanda/pilih & Preview)")

        selection_btn_frame = ctk.CTkFrame(pad, fg_color="transparent")
        selection_btn_frame.pack(fill="x", pady=(0, 5))
        self.btn_secondary(selection_btn_frame, "✅  Pilih Semua", self.select_all_records, width=140, height=32).pack(side="left", padx=(0, 8))
        self.btn_danger(selection_btn_frame, "⬜  Nyahpilih Semua", self.deselect_all_records, width=140).pack(side="left")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", font=(FONT_FAMILY, 9), rowheight=27, background=COLOR_SURFACE, fieldbackground=COLOR_SURFACE, foreground=COLOR_TEXT, borderwidth=0)
        style.configure("Treeview.Heading", font=(FONT_FAMILY, 9, "bold"), background=COLOR_SURFACE_ALT, foreground=COLOR_TEXT, relief="flat")
        style.map("Treeview", background=[("selected", COLOR_ACCENT)], foreground=[("selected", "#FFFFFF")])

        self.tree = ttk.Treeview(pad, columns=("Pilih", "QR", "Batch", "Penuh", "Email"), show="headings", height=8)
        self.tree.heading("Pilih", text="Tanda")
        self.tree.heading("QR", text="Kod QR")
        self.tree.heading("Batch", text="Batch")
        self.tree.heading("Penuh", text="Nama Penuh")
        self.tree.heading("Email", text="Email MOE")
        self.tree.column("Pilih", width=60, anchor="center")
        self.tree.column("QR", width=80)
        self.tree.column("Batch", width=90)
        self.tree.column("Penuh", width=200)
        self.tree.column("Email", width=180)
        self.tree.pack(fill="both", expand=True, pady=5)

        # Warna latar baris mengikut status tanda — hijau lembut bila dipilih,
        # supaya senarai mudah dibaca sekali pandang (bukan sekadar simbol teks).
        self.tree.tag_configure("row_on", background="#EAFBF1")
        self.tree.tag_configure("row_off", background=COLOR_SURFACE)

        self.tree.bind("<ButtonRelease-1>", self.on_tree_click)

        self.progress_frame = ctk.CTkFrame(pad, fg_color="transparent")
        self.progress_frame.pack(fill="x", pady=10)
        self.lbl_progress_status = ctk.CTkLabel(self.progress_frame, text="Status: Sedia", font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=COLOR_TEXT_MUTED)
        self.lbl_progress_status.pack(anchor="w")
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, progress_color=COLOR_ACCENT, fg_color=COLOR_SURFACE_ALT)
        self.progress_bar.pack(fill="x", pady=5)
        self.progress_bar.set(0)

        btn_action_frame = ctk.CTkFrame(pad, fg_color="transparent")
        btn_action_frame.pack(fill="x", pady=5)
        self.btn_primary(btn_action_frame, "🖨  CETAK SEMUA TANDA [X]", self.print_batch, height=42).pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.btn_secondary(btn_action_frame, "📄  MUAT TURUN PDF TANDA [X]", self.download_pdf_batch, height=42).pack(side="left", fill="x", expand=True, padx=(5, 0))

    # ============================================================
    # TAB 3: KONFIGURASI LAYOUT (SCROLLABLE)
    # ============================================================
    def build_tab_config(self):
        self.scrollable_frame = ctk.CTkScrollableFrame(self.tab_config, fg_color="transparent")
        self.scrollable_frame.pack(fill="both", expand=True, padx=8)

        ctk.CTkLabel(self.scrollable_frame, text="Ubah Suai Saiz, Kedudukan & Gaya Font", font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"), text_color=COLOR_TEXT).grid(row=0, column=0, columnspan=4, pady=(10, 15), sticky="w")

        FONT_OPTIONS = ["arial.ttf", "calibri.ttf", "times.ttf", "tahoma.ttf", "verdana.ttf", "cour.ttf"]

        # 1. Gambar Foto
        self.config_group_label(self.scrollable_frame, "GAMBAR FOTO — Kotak Sempadan").grid(row=1, column=0, columnspan=4, sticky="w", pady=(6, 5))
        self.cfg_img_x = self.create_cfg_entry(self.scrollable_frame, "Kedudukan X:", "40", row=2, col=0)
        self.cfg_img_y = self.create_cfg_entry(self.scrollable_frame, "Kedudukan Y:", "250", row=2, col=2)
        self.cfg_img_w = self.create_cfg_entry(self.scrollable_frame, "Maks Lebar (W):", "240", row=3, col=0)
        self.cfg_img_h = self.create_cfg_entry(self.scrollable_frame, "Maks Tinggi (H):", "310", row=3, col=2)

        # 2. QR Code
        self.config_group_label(self.scrollable_frame, "QR CODE").grid(row=4, column=0, columnspan=4, sticky="w", pady=(18, 5))
        self.cfg_qr_x = self.create_cfg_entry(self.scrollable_frame, "Kedudukan X:", "735", row=5, col=0)
        self.cfg_qr_y = self.create_cfg_entry(self.scrollable_frame, "Kedudukan Y:", "255", row=5, col=2)
        self.cfg_qr_size = self.create_cfg_entry(self.scrollable_frame, "Saiz QR:", "230", row=6, col=0)

        # 3. Batch
        self.config_group_label(self.scrollable_frame, "BATCH").grid(row=7, column=0, columnspan=4, sticky="w", pady=(18, 5))
        self.cfg_n1_x = self.create_cfg_entry(self.scrollable_frame, "Kedudukan X:", "340", row=8, col=0)
        self.cfg_n1_y = self.create_cfg_entry(self.scrollable_frame, "Kedudukan Y:", "410", row=8, col=2)
        self.cfg_n1_font = self.create_cfg_entry(self.scrollable_frame, "Saiz Font:", "45", row=9, col=0)

        self.field_label(self.scrollable_frame, "Jenis Font:").grid(row=9, column=2, sticky="w", padx=5)
        self.cfg_n1_font_file = ctk.CTkComboBox(self.scrollable_frame, values=FONT_OPTIONS, width=130, button_color=COLOR_ACCENT, border_color=COLOR_BORDER)
        self.cfg_n1_font_file.set("arial.ttf")
        self.cfg_n1_font_file.grid(row=9, column=3, sticky="w", padx=5)

        self.cfg_n1_bold = tk.BooleanVar(value=True)
        self.cfg_n1_italic = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.scrollable_frame, text="Bold", variable=self.cfg_n1_bold, fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER).grid(row=10, column=0, sticky="w", padx=5, pady=5)
        ctk.CTkCheckBox(self.scrollable_frame, text="Italic", variable=self.cfg_n1_italic, fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER).grid(row=10, column=1, sticky="w", padx=5, pady=5)

        self.field_label(self.scrollable_frame, "Justifikasi:").grid(row=10, column=2, sticky="w", padx=5, pady=5)
        self.cfg_n1_justify = ctk.StringVar(value="Left")
        self.cfg_n1_just_menu = ctk.CTkSegmentedButton(self.scrollable_frame, values=["Left", "Center", "Right"], variable=self.cfg_n1_justify, width=130, selected_color=COLOR_ACCENT, selected_hover_color=COLOR_ACCENT_HOVER)
        self.cfg_n1_just_menu.grid(row=10, column=3, sticky="w", padx=5, pady=5)

        # 4. Nama Penuh
        self.config_group_label(self.scrollable_frame, "NAMA PENUH").grid(row=11, column=0, columnspan=4, sticky="w", pady=(18, 5))
        self.cfg_n2_x = self.create_cfg_entry(self.scrollable_frame, "Kedudukan X:", "320", row=12, col=0)
        self.cfg_n2_y = self.create_cfg_entry(self.scrollable_frame, "Kedudukan Y:", "480", row=12, col=2)
        self.cfg_n2_font = self.create_cfg_entry(self.scrollable_frame, "Saiz Font:", "30", row=13, col=0)

        self.field_label(self.scrollable_frame, "Jenis Font:").grid(row=13, column=2, sticky="w", padx=5)
        self.cfg_n2_font_file = ctk.CTkComboBox(self.scrollable_frame, values=FONT_OPTIONS, width=130, button_color=COLOR_ACCENT, border_color=COLOR_BORDER)
        self.cfg_n2_font_file.set("arial.ttf")
        self.cfg_n2_font_file.grid(row=13, column=3, sticky="w", padx=5)

        self.cfg_n2_bold = tk.BooleanVar(value=False)
        self.cfg_n2_italic = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.scrollable_frame, text="Bold", variable=self.cfg_n2_bold, fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER).grid(row=14, column=0, sticky="w", padx=5, pady=5)
        ctk.CTkCheckBox(self.scrollable_frame, text="Italic", variable=self.cfg_n2_italic, fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER).grid(row=14, column=1, sticky="w", padx=5, pady=5)

        self.field_label(self.scrollable_frame, "Justifikasi:").grid(row=14, column=2, sticky="w", padx=5, pady=5)
        self.cfg_n2_justify = ctk.StringVar(value="Left")
        self.cfg_n2_just_menu = ctk.CTkSegmentedButton(self.scrollable_frame, values=["Left", "Center", "Right"], variable=self.cfg_n2_justify, width=130, selected_color=COLOR_ACCENT, selected_hover_color=COLOR_ACCENT_HOVER)
        self.cfg_n2_just_menu.grid(row=14, column=3, sticky="w", padx=5, pady=5)

        # 5. Email MOE
        self.config_group_label(self.scrollable_frame, "EMAIL MOE").grid(row=15, column=0, columnspan=4, sticky="w", pady=(18, 5))
        self.cfg_n3_x = self.create_cfg_entry(self.scrollable_frame, "Kedudukan X:", "320", row=16, col=0)
        self.cfg_n3_y = self.create_cfg_entry(self.scrollable_frame, "Kedudukan Y:", "550", row=16, col=2)
        self.cfg_n3_font = self.create_cfg_entry(self.scrollable_frame, "Saiz Font:", "25", row=17, col=0)

        self.field_label(self.scrollable_frame, "Jenis Font:").grid(row=17, column=2, sticky="w", padx=5)
        self.cfg_n3_font_file = ctk.CTkComboBox(self.scrollable_frame, values=FONT_OPTIONS, width=130, button_color=COLOR_ACCENT, border_color=COLOR_BORDER)
        self.cfg_n3_font_file.set("arial.ttf")
        self.cfg_n3_font_file.grid(row=17, column=3, sticky="w", padx=5)

        self.cfg_n3_bold = tk.BooleanVar(value=False)
        self.cfg_n3_italic = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(self.scrollable_frame, text="Bold", variable=self.cfg_n3_bold, fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER).grid(row=18, column=0, sticky="w", padx=5, pady=5)
        ctk.CTkCheckBox(self.scrollable_frame, text="Italic", variable=self.cfg_n3_italic, fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER).grid(row=18, column=1, sticky="w", padx=5, pady=5)

        self.field_label(self.scrollable_frame, "Justifikasi:").grid(row=18, column=2, sticky="w", padx=5, pady=5)
        self.cfg_n3_justify = ctk.StringVar(value="Left")
        self.cfg_n3_just_menu = ctk.CTkSegmentedButton(self.scrollable_frame, values=["Left", "Center", "Right"], variable=self.cfg_n3_justify, width=130, selected_color=COLOR_ACCENT, selected_hover_color=COLOR_ACCENT_HOVER)
        self.cfg_n3_just_menu.grid(row=18, column=3, sticky="w", padx=5, pady=5)

        frame_buttons = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        frame_buttons.grid(row=19, column=0, columnspan=4, sticky="w", pady=18)
        self.btn_success(frame_buttons, "💾  Simpan Layout", self.save_layout_config, width=160).pack(side="left", padx=(0, 8))
        self.btn_secondary(frame_buttons, "📂  Muat Tetapan", self.load_layout_config, width=160, height=38).pack(side="left")

        self.btn_primary(self.scrollable_frame, "🔄  KEMAS KINI & JANA PREVIEW", self.trigger_refresh_preview, height=42).grid(row=20, column=0, columnspan=4, pady=(0, 15), sticky="ew")

    def config_group_label(self, parent, text):
        return ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"), text_color=COLOR_ACCENT)

    # ============================================================
    # PANEL KANAN: PREVIEW & KAWALAN OUTPUT
    # ============================================================
    def build_preview_panel(self):
        ctk.CTkLabel(self.right_frame, text="PRATONTON KAD", font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"), text_color=COLOR_TEXT).pack(pady=(20, 4))
        ctk.CTkLabel(self.right_frame, text="Semakan visual sebelum cetak", font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=COLOR_TEXT_MUTED).pack(pady=(0, 12))

        preview_frame = ctk.CTkFrame(self.right_frame, corner_radius=14, fg_color=COLOR_SURFACE_ALT, border_width=1, border_color=COLOR_BORDER)
        preview_frame.pack(pady=5, padx=30)

        self.preview_container = ctk.CTkFrame(preview_frame, width=450, height=283, corner_radius=10, fg_color="#ffffff")
        self.preview_container.pack(padx=14, pady=14)
        self.preview_container.pack_propagate(False)

        self.lbl_preview = ctk.CTkLabel(self.preview_container, text="Sila jana preview atau pilih murid", text_color=COLOR_TEXT_MUTED, font=ctk.CTkFont(family=FONT_FAMILY, size=12))
        self.lbl_preview.pack(fill="both", expand=True)

        divider = ctk.CTkFrame(self.right_frame, height=1, fg_color=COLOR_BORDER)
        divider.pack(fill="x", padx=30, pady=(20, 15))

        self.field_label(self.right_frame, "Pilih Pencetak Kad (Printer)").pack(anchor="w", padx=50, pady=(0, 6))
        self.cbo_printer = ctk.CTkComboBox(self.right_frame, width=350, button_color=COLOR_ACCENT, border_color=COLOR_BORDER)
        self.cbo_printer.pack(pady=5)
        self.populate_printers()

        self.btn_global_print = self.btn_primary(self.right_frame, "🖨  CETAK KAD INI SEKARANG", self.print_single_card, width=350, height=46, state="disabled")
        self.btn_global_print.pack(pady=(18, 8))

        self.btn_global_download = self.btn_secondary(self.right_frame, "💾  MUAT TURUN GAMBAR KAD (PNG)", self.download_card_image, width=350, height=38)
        self.btn_global_download.pack(pady=5)

    # ============================================================
    #  LOGIK APLIKASI (tidak berubah — hanya paparan diubah suai)
    # ============================================================
    def generate_random_qr_code(self):
        chars = string.ascii_lowercase + string.digits
        random_code = ''.join(random.choices(chars, k=7))
        self.ent_qr_code.delete(0, tk.END)
        self.ent_qr_code.insert(0, random_code)

    def create_cfg_entry(self, parent, label_text, default_val, row, col):
        self.field_label(parent, label_text).grid(row=row, column=col, sticky="w", padx=5, pady=5)
        entry = ctk.CTkEntry(parent, width=80, border_color=COLOR_BORDER)
        entry.insert(0, default_val)
        entry.grid(row=row, column=col + 1, sticky="w", padx=5, pady=5)
        return entry

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

    def save_layout_config(self):
        config_data = {
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
        try:
            with open(self.config_filename, "w") as f:
                json.dump(config_data, f, indent=4)
            messagebox.showinfo("Berjaya", "Konfigurasi layout berjaya disimpan!")
        except Exception as e:
            messagebox.showerror("Ralat", f"Gagal menyimpan fail konfigurasi:\n{str(e)}")

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
        name = simpledialog.askstring("Nama Templat", f"Nama untuk Slot {idx+1}:",
                                       initialvalue=os.path.splitext(os.path.basename(self.bg_path))[0])
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
        self.photo_folder = filedialog.askdirectory()
        if self.photo_folder:
            self.lbl_folder.configure(text=f"Folder: {self.photo_folder}", text_color=COLOR_SUCCESS)

    def load_csv(self):
        csv_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not csv_path: return

        # Pengekodan CSV mengikut pilihan pengguna
        enc_option = self.cbo_encoding.get()
        encoding_map = {
            "UTF-8": "utf-8",
            "UTF-8-SIG (With BOM)": "utf-8-sig",
            "ANSI (cp1252)": "cp1252"
        }
        selected_encoding = encoding_map.get(enc_option, "utf-8")

        self.csv_data = []
        try:
            with open(csv_path, mode='r', encoding=selected_encoding) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Setiap rekod lalai mempunyai 'pilih': True (ditanda)
                    row_data = {
                        'pilih': True,
                        'kod_qr': row.get('kod_qr', ''),
                        'batch': row.get('batch', ''),
                        'nama_penuh': row.get('nama_penuh', ''),
                        'email_moe': row.get('email_moe', ''),
                        'fail_gambar': row.get('fail_gambar', '')
                    }
                    self.csv_data.append(row_data)
            self.refresh_treeview()
            self.lbl_csv.configure(text=f"CSV: {os.path.basename(csv_path)} ({len(self.csv_data)} rekod)", text_color=COLOR_SUCCESS)
        except Exception as e:
            messagebox.showerror("Ralat CSV", f"Gagal membaca CSV menggunakan {selected_encoding}:\n{str(e)}")

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
            self.tree.insert("", tk.END, values=(pilih_symbol, row['kod_qr'], row['batch'], row['nama_penuh'], row['email_moe']), tags=(row_tag,))

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

    def make_card_image(self, qr_code, batch, full_name, email_moe, photo_filename, is_batch=False):
        if not self.bg_path: raise Exception("Sila pilih gambar Template Kad terlebih dahulu!")
        p_path = photo_filename if not is_batch else os.path.join(self.photo_folder, photo_filename)
        if not os.path.exists(p_path): raise Exception(f"Fail gambar tidak ditemui: {os.path.basename(p_path)}")

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
        raw_photo = Image.open(p_path).convert('RGBA')
        teacher_img = ImageOps.contain(raw_photo, (img_w, img_h))
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
        preview_img = card_image.copy().resize((450, 283), resample=Image.Resampling.LANCZOS)
        self.photo_preview = ImageTk.PhotoImage(preview_img)
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
        if not self.bg_path or not self.photo_folder:
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
        if not self.bg_path or not self.photo_folder:
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
                src_w, src_h = bmp.size
                # Kira petak sasaran mengikut kawasan boleh cetak sebenar
                # pencetak (bukan andaian 1013x638px tetap) supaya nisbah
                # aspek kad dikekalkan dan tidak diregangkan (stretched).
                page_w = hdc.GetDeviceCaps(win32con.HORZRES)
                page_h = hdc.GetDeviceCaps(win32con.VERTRES)
                scale = min(page_w / src_w, page_h / src_h)
                dest_w, dest_h = int(src_w * scale), int(src_h * scale)
                offset_x, offset_y = (page_w - dest_w) // 2, (page_h - dest_h) // 2
                dib = ImageWin.Dib(bmp)
                dib.draw(hdc.GetHandleOutput(), (offset_x, offset_y, offset_x + dest_w, offset_y + dest_h))
            hdc.EndPage()
            hdc.EndDoc()
        finally:
            hdc.DeleteDC()


if __name__ == "__main__":
    app = CardPrinterApp()
    app.mainloop()
