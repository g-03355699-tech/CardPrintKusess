import os
import csv
import json
import sys
import random
import string
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageDraw, ImageFont, ImageTk, ImageOps
import qrcode
import win32print
import win32ui
from PIL import ImageWin

# Tetapan Tema Global Perisian
ctk.set_appearance_mode("System")  # Mengikut tetapan Windows (Dark/Light)
ctk.set_default_color_theme("blue") # Tema warna profesional (Blue, Green, Dark-Blue)

class CardPrinterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Sistem Cetakan Kad MyKUSESS (Versi Save Layout + Multi-Encoding & PDF)")
        self.geometry("1400x850")
        
        # --- KETETAPAN IKON PERISIAN ---
        try:
            if hasattr(sys, '_MEIPASS'):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.abspath(".")
            icon_path = os.path.join(base_path, "logo.ico")
            self.iconbitmap(icon_path)
        except Exception:
            pass
        
        self.bg_path = ""
        self.photo_folder = ""
        self.single_photo_path = ""
        self.csv_data = [] # Menyimpan data penuh: [{'kod_qr':..., 'pilih': True/False, ...}]
        self.generated_card = None
        self.config_filename = "layout_config.json"
        
        # --- GRID UTAMA ---
        self.grid_columnconfigure(0, weight=4, minsize=700)
        self.grid_columnconfigure(1, weight=5, minsize=550)
        self.grid_rowconfigure(0, weight=1)
        
        # --- BAHAGIAN KIRI: TAB KAWALAN (MODEN) ---
        self.notebook = ctk.CTkTabview(self, segmented_button_selected_color="#1f538d")
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        
        self.tab_single = self.notebook.add(" Cetak Satu-Satu ")
        self.tab_batch = self.notebook.add(" Cetak Pukal (CSV) ")
        self.tab_config = self.notebook.add(" Konfigurasi Layout ")
        
        # --- BAHAGIAN KANAN: PANEL PREVIEW & PRINTER ---
        self.right_frame = ctk.CTkFrame(self, corner_radius=15)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        
        # ==========================================
        # TAB 1: CETAK SATU-SATU
        # ==========================================
        ctk.CTkLabel(self.tab_single, text="1. Tetapan Asas Template", font=ctk.CTkFont(size=14, weight="bold"), text_color="#2ecc71").pack(anchor="w", pady=(10, 5))
        ctk.CTkButton(self.tab_single, text="Pilih Template Kad (Background)", command=self.select_bg, width=300).pack(anchor="w", pady=5)
        self.lbl_bg = ctk.CTkLabel(self.tab_single, text="Template: Tiada fail dipilih", text_color="#e74c3c", wraplength=400, justify="left")
        self.lbl_bg.pack(anchor="w", pady=2)
        
        ctk.CTkLabel(self.tab_single, text="2. Maklumat Individu", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(20, 5))
        ctk.CTkButton(self.tab_single, text="Pilih Foto Guru/Murid", fg_color="#34495e", hover_color="#2c3e50", command=self.select_single_photo, width=300).pack(anchor="w", pady=5)
        self.lbl_photo = ctk.CTkLabel(self.tab_single, text="Foto: Tiada fail dipilih", text_color="#e74c3c", wraplength=400, justify="left")
        self.lbl_photo.pack(anchor="w", pady=2)
        
        ctk.CTkLabel(self.tab_single, text="Kod Unik QR:").pack(anchor="w", pady=(5, 2))
        qr_input_frame = ctk.CTkFrame(self.tab_single, fg_color="transparent")
        qr_input_frame.pack(anchor="w", pady=2)
        self.ent_qr_code = ctk.CTkEntry(qr_input_frame, width=280, placeholder_text="Contoh: wpwj727")
        self.ent_qr_code.pack(side="left", padx=(0, 10))
        self.btn_generate_qr = ctk.CTkButton(qr_input_frame, text="Jana Kod", width=110, fg_color="#1abc9c", hover_color="#16a085", command=self.generate_random_qr_code)
        self.btn_generate_qr.pack(side="left")
        
        ctk.CTkLabel(self.tab_single, text="Batch (Huruf Besar):").pack(anchor="w", pady=(5, 2))
        self.ent_batch = ctk.CTkEntry(self.tab_single, width=400, placeholder_text="Contoh: BATCH 2026")
        self.ent_batch.pack(anchor="w", pady=2)
        
        ctk.CTkLabel(self.tab_single, text="Nama Penuh:").pack(anchor="w", pady=(5, 2))
        self.ent_full_name = ctk.CTkEntry(self.tab_single, width=400, placeholder_text="Contoh: AMINAH BINTI ALI")
        self.ent_full_name.pack(anchor="w", pady=2)
        
        ctk.CTkLabel(self.tab_single, text="Email MOE:").pack(anchor="w", pady=(5, 2))
        self.ent_email_moe = ctk.CTkEntry(self.tab_single, width=400, placeholder_text="Contoh: m-1234567@moe-dl.edu.my")
        self.ent_email_moe.pack(anchor="w", pady=2)
        
        ctk.CTkButton(self.tab_single, text="JANA PREVIEW (SINGLE)", fg_color="#1f538d", font=ctk.CTkFont(weight="bold"), width=300, height=40, command=self.generate_single_preview).pack(pady=20)
        
        # ==========================================
        # TAB 2: CETAK PUKAL (BATCH CSV)
        # ==========================================
        ctk.CTkLabel(self.tab_batch, text="1. Sediakan Tetapan Fail", font=ctk.CTkFont(size=14, weight="bold"), text_color="#2ecc71").pack(anchor="w", pady=(10, 2))
        
        # Grid Pilihan Folder Gambar, Encoding dan CSV
        setting_frame = ctk.CTkFrame(self.tab_batch, fg_color="transparent")
        setting_frame.pack(fill="x", pady=5)
        
        ctk.CTkButton(setting_frame, text="Pilih Folder Gambar", command=self.select_photo_folder, width=180).grid(row=0, column=0, padx=5, pady=5)
        self.lbl_folder = ctk.CTkLabel(setting_frame, text="Folder: Tiada dipilih", text_color="#e74c3c", wraplength=200, justify="left")
        self.lbl_folder.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ctk.CTkLabel(setting_frame, text="Format CSV Encoding:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.cbo_encoding = ctk.CTkComboBox(setting_frame, values=["UTF-8", "UTF-8-SIG (With BOM)", "ANSI (cp1252)"], width=180)
        self.cbo_encoding.set("UTF-8")
        self.cbo_encoding.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        ctk.CTkButton(setting_frame, text="Muat Naik CSV", fg_color="#2980b9", command=self.load_csv, width=180).grid(row=2, column=0, padx=5, pady=5)
        self.lbl_csv = ctk.CTkLabel(setting_frame, text="CSV: Tiada fail dipilih", text_color="#e74c3c")
        self.lbl_csv.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        # Bar Carian (Search)
        search_frame = ctk.CTkFrame(self.tab_batch, fg_color="transparent")
        search_frame.pack(fill="x", pady=(10, 5))
        ctk.CTkLabel(search_frame, text="Carian Nama / Batch:").pack(side="left", padx=5)
        self.ent_search = ctk.CTkEntry(search_frame, placeholder_text="Masukkan nama kata kunci...", width=250)
        self.ent_search.pack(side="left", padx=5)
        self.ent_search.bind("<KeyRelease>", self.filter_search)
        
        ctk.CTkButton(search_frame, text="Kosongkan", width=80, fg_color="#7f8c8d", command=self.clear_search).pack(side="left", padx=5)
        
        ctk.CTkLabel(self.tab_batch, text="2. Senarai Murid (Klik untuk tanda/pilih & Preview):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 2))
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", font=("Arial", 9), rowheight=26, background="#2b2b2b" if ctk.get_appearance_mode()=="Dark" else "#ffffff", fieldbackground="#2b2b2b" if ctk.get_appearance_mode()=="Dark" else "#ffffff", foreground="white" if ctk.get_appearance_mode()=="Dark" else "black")
        style.configure("Treeview.Heading", font=("Arial", 9, "bold"))
        
        self.tree = ttk.Treeview(self.tab_batch, columns=("Pilih", "QR", "Batch", "Penuh", "Email"), show="headings", height=8)
        self.tree.heading("Pilih", text="[X]")
        self.tree.heading("QR", text="Kod QR")
        self.tree.heading("Batch", text="Batch")
        self.tree.heading("Penuh", text="Nama Penuh")
        self.tree.heading("Email", text="Email MOE")
        self.tree.column("Pilih", width=40, anchor="center")
        self.tree.column("QR", width=80)
        self.tree.column("Batch", width=90)
        self.tree.column("Penuh", width=200)
        self.tree.column("Email", width=180)
        self.tree.pack(fill="both", expand=True, pady=5)
        
        self.tree.bind("<ButtonRelease-1>", self.on_tree_click)
        
        self.progress_frame = ctk.CTkFrame(self.tab_batch, fg_color="transparent")
        self.progress_frame.pack(fill="x", pady=5)
        self.lbl_progress_status = ctk.CTkLabel(self.progress_frame, text="Status: Sedia", font=ctk.CTkFont(size=12))
        self.lbl_progress_status.pack(anchor="w")
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(fill="x", pady=5)
        self.progress_bar.set(0)
        
        # Butang Tindakan Pukal
        btn_action_frame = ctk.CTkFrame(self.tab_batch, fg_color="transparent")
        btn_action_frame.pack(fill="x", pady=5)
        
        ctk.CTkButton(btn_action_frame, text="CETAK SEMUA TANDA [X]", fg_color="#9b59b6", hover_color="#8e44ad", font=ctk.CTkFont(weight="bold"), height=40, command=self.print_batch).pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(btn_action_frame, text="MUAT TURUN PDF TANDA [X]", fg_color="#e67e22", hover_color="#d35400", font=ctk.CTkFont(weight="bold"), height=40, command=self.download_pdf_batch).pack(side="left", fill="x", expand=True, padx=5)

        # ==========================================
        # TAB 3: TAB KONFIGURASI LAYOUT (SCROLLABLE)
        # ==========================================
        self.scrollable_frame = ctk.CTkScrollableFrame(self.tab_config, width=650, height=700)
        self.scrollable_frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(self.scrollable_frame, text="Ubah Suai Saiz, Kedudukan & Gaya Font", font=ctk.CTkFont(size=15, weight="bold"), text_color="#3498db").grid(row=0, column=0, columnspan=4, pady=10, sticky="w")
        
        FONT_OPTIONS = ["arial.ttf", "calibri.ttf", "times.ttf", "tahoma.ttf", "verdana.ttf", "cour.ttf"]
        
        # 1. Gambar Foto
        ctk.CTkLabel(self.scrollable_frame, text="[ GAMBAR FOTO - Kotak Sempadan ]", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, columnspan=4, sticky="w", pady=(10,5))
        self.cfg_img_x = self.create_cfg_entry(self.scrollable_frame, "Kedudukan X:", "40", row=2, col=0)
        self.cfg_img_y = self.create_cfg_entry(self.scrollable_frame, "Kedudukan Y:", "250", row=2, col=2)
        self.cfg_img_w = self.create_cfg_entry(self.scrollable_frame, "Maks Lebar (W):", "240", row=3, col=0)
        self.cfg_img_h = self.create_cfg_entry(self.scrollable_frame, "Maks Tinggi (H):", "310", row=3, col=2)
        
        # 2. QR Code
        ctk.CTkLabel(self.scrollable_frame, text="[ QR CODE ]", font=ctk.CTkFont(weight="bold")).grid(row=4, column=0, columnspan=4, sticky="w", pady=(15,5))
        self.cfg_qr_x = self.create_cfg_entry(self.scrollable_frame, "Kedudukan X:", "735", row=5, col=0)
        self.cfg_qr_y = self.create_cfg_entry(self.scrollable_frame, "Kedudukan Y:", "255", row=5, col=2)
        self.cfg_qr_size = self.create_cfg_entry(self.scrollable_frame, "Saiz QR:", "230", row=6, col=0)
        
        # 3. Batch
        ctk.CTkLabel(self.scrollable_frame, text="[ BATCH ]", font=ctk.CTkFont(weight="bold")).grid(row=7, column=0, columnspan=4, sticky="w", pady=(15,5))
        self.cfg_n1_x = self.create_cfg_entry(self.scrollable_frame, "Kedudukan X:", "340", row=8, col=0)
        self.cfg_n1_y = self.create_cfg_entry(self.scrollable_frame, "Kedudukan Y:", "410", row=8, col=2)
        self.cfg_n1_font = self.create_cfg_entry(self.scrollable_frame, "Saiz Font:", "45", row=9, col=0)
        
        ctk.CTkLabel(self.scrollable_frame, text="Jenis Font:").grid(row=9, column=2, sticky="w", padx=5)
        self.cfg_n1_font_file = ctk.CTkComboBox(self.scrollable_frame, values=FONT_OPTIONS, width=130)
        self.cfg_n1_font_file.set("arial.ttf")
        self.cfg_n1_font_file.grid(row=9, column=3, sticky="w", padx=5)
        
        self.cfg_n1_bold = tk.BooleanVar(value=True)
        self.cfg_n1_italic = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.scrollable_frame, text="Bold", variable=self.cfg_n1_bold).grid(row=10, column=0, sticky="w", padx=5, pady=5)
        ctk.CTkCheckBox(self.scrollable_frame, text="Italic", variable=self.cfg_n1_italic).grid(row=10, column=1, sticky="w", padx=5, pady=5)
        
        ctk.CTkLabel(self.scrollable_frame, text="Justifikasi:").grid(row=10, column=2, sticky="w", padx=5, pady=5)
        self.cfg_n1_justify = ctk.StringVar(value="Left")
        self.cfg_n1_just_menu = ctk.CTkSegmentedButton(self.scrollable_frame, values=["Left", "Center", "Right"], variable=self.cfg_n1_justify, width=130)
        self.cfg_n1_just_menu.grid(row=10, column=3, sticky="w", padx=5, pady=5)
        
        # 4. Nama Penuh
        ctk.CTkLabel(self.scrollable_frame, text="[ NAMA PENUH ]", font=ctk.CTkFont(weight="bold")).grid(row=11, column=0, columnspan=4, sticky="w", pady=(15,5))
        self.cfg_n2_x = self.create_cfg_entry(self.scrollable_frame, "Kedudukan X:", "320", row=12, col=0)
        self.cfg_n2_y = self.create_cfg_entry(self.scrollable_frame, "Kedudukan Y:", "480", row=12, col=2)
        self.cfg_n2_font = self.create_cfg_entry(self.scrollable_frame, "Saiz Font:", "30", row=13, col=0)
        
        ctk.CTkLabel(self.scrollable_frame, text="Jenis Font:").grid(row=13, column=2, sticky="w", padx=5)
        self.cfg_n2_font_file = ctk.CTkComboBox(self.scrollable_frame, values=FONT_OPTIONS, width=130)
        self.cfg_n2_font_file.set("arial.ttf")
        self.cfg_n2_font_file.grid(row=13, column=3, sticky="w", padx=5)
        
        self.cfg_n2_bold = tk.BooleanVar(value=False)
        self.cfg_n2_italic = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.scrollable_frame, text="Bold", variable=self.cfg_n2_bold).grid(row=14, column=0, sticky="w", padx=5, pady=5)
        ctk.CTkCheckBox(self.scrollable_frame, text="Italic", variable=self.cfg_n2_italic).grid(row=14, column=1, sticky="w", padx=5, pady=5)
        
        ctk.CTkLabel(self.scrollable_frame, text="Justifikasi:").grid(row=14, column=2, sticky="w", padx=5, pady=5)
        self.cfg_n2_justify = ctk.StringVar(value="Left")
        self.cfg_n2_just_menu = ctk.CTkSegmentedButton(self.scrollable_frame, values=["Left", "Center", "Right"], variable=self.cfg_n2_justify, width=130)
        self.cfg_n2_just_menu.grid(row=14, column=3, sticky="w", padx=5, pady=5)

        # 5. Email MOE (Baharu)
        ctk.CTkLabel(self.scrollable_frame, text="[ EMAIL MOE ]", font=ctk.CTkFont(weight="bold")).grid(row=15, column=0, columnspan=4, sticky="w", pady=(15,5))
        self.cfg_n3_x = self.create_cfg_entry(self.scrollable_frame, "Kedudukan X:", "320", row=16, col=0)
        self.cfg_n3_y = self.create_cfg_entry(self.scrollable_frame, "Kedudukan Y:", "550", row=16, col=2)
        self.cfg_n3_font = self.create_cfg_entry(self.scrollable_frame, "Saiz Font:", "25", row=17, col=0)
        
        ctk.CTkLabel(self.scrollable_frame, text="Jenis Font:").grid(row=17, column=2, sticky="w", padx=5)
        self.cfg_n3_font_file = ctk.CTkComboBox(self.scrollable_frame, values=FONT_OPTIONS, width=130)
        self.cfg_n3_font_file.set("arial.ttf")
        self.cfg_n3_font_file.grid(row=17, column=3, sticky="w", padx=5)
        
        self.cfg_n3_bold = tk.BooleanVar(value=False)
        self.cfg_n3_italic = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(self.scrollable_frame, text="Bold", variable=self.cfg_n3_bold).grid(row=18, column=0, sticky="w", padx=5, pady=5)
        ctk.CTkCheckBox(self.scrollable_frame, text="Italic", variable=self.cfg_n3_italic).grid(row=18, column=1, sticky="w", padx=5, pady=5)
        
        ctk.CTkLabel(self.scrollable_frame, text="Justifikasi:").grid(row=18, column=2, sticky="w", padx=5, pady=5)
        self.cfg_n3_justify = ctk.StringVar(value="Left")
        self.cfg_n3_just_menu = ctk.CTkSegmentedButton(self.scrollable_frame, values=["Left", "Center", "Right"], variable=self.cfg_n3_justify, width=130)
        self.cfg_n3_just_menu.grid(row=18, column=3, sticky="w", padx=5, pady=5)
        
        frame_buttons = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        frame_buttons.grid(row=19, column=0, columnspan=4, sticky="w", pady=15)
        
        ctk.CTkButton(frame_buttons, text="💾 Simpan Layout", fg_color="#27ae60", hover_color="#219150", command=self.save_layout_config).pack(side="left", padx=5)
        ctk.CTkButton(frame_buttons, text="📂 Muat Tetapan", fg_color="#7f8c8d", hover_color="#717d7e", command=self.load_layout_config).pack(side="left", padx=5)
        
        ctk.CTkButton(self.scrollable_frame, text="🔄 KEMAS KINI & JANA PREVIEW", fg_color="#2980b9", font=ctk.CTkFont(weight="bold"), height=40, command=self.trigger_refresh_preview).grid(row=20, column=0, columnspan=4, pady=10, sticky="ew")

        self.load_layout_config(silent=True)

        # ==========================================
        # PANEL KANAN: PREVIEW & KAWALAN OUTPUT
        # ==========================================
        ctk.CTkLabel(self.right_frame, text="PREVIEW KAD", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        self.preview_container = ctk.CTkFrame(self.right_frame, width=450, height=283, fg_color="#ffffff")
        self.preview_container.pack(pady=10)
        self.preview_container.pack_propagate(False)
        
        self.lbl_preview = ctk.CTkLabel(self.preview_container, text="Sila jana preview atau pilih murid", text_color="black")
        self.lbl_preview.pack(fill="both", expand=True)
        
        ctk.CTkLabel(self.right_frame, text="Pilih Pencetak Kad (Printer):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=50, pady=(15, 2))
        self.cbo_printer = ctk.CTkComboBox(self.right_frame, width=350)
        self.cbo_printer.pack(pady=5)
        self.populate_printers()
        
        self.btn_global_print = ctk.CTkButton(self.right_frame, text="CETAK KAD INI SEKARANG", fg_color="#27ae60", hover_color="#219150", font=ctk.CTkFont(size=14, weight="bold"), width=350, height=45, command=self.print_single_card, state="disabled")
        self.btn_global_print.pack(pady=10)
        
        self.btn_global_download = ctk.CTkButton(self.right_frame, text="💾 MUAT TURUN GAMBAR KAD (PNG)", fg_color="#2980b9", hover_color="#2471a3", font=ctk.CTkFont(size=13), width=350, command=self.download_card_image)
        self.btn_global_download.pack(pady=5)

    def generate_random_qr_code(self):
        chars = string.ascii_lowercase + string.digits
        random_code = ''.join(random.choices(chars, k=7))
        self.ent_qr_code.delete(0, tk.END)
        self.ent_qr_code.insert(0, random_code)

    def create_cfg_entry(self, parent, label_text, default_val, row, col):
        ctk.CTkLabel(parent, text=label_text).grid(row=row, column=col, sticky="w", padx=5, pady=5)
        entry = ctk.CTkEntry(parent, width=80)
        entry.insert(0, default_val)
        entry.grid(row=row, column=col+1, sticky="w", padx=5, pady=5)
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
            self.lbl_bg.configure(text=f"Template: {os.path.basename(self.bg_path)}", text_color="#2ecc71")

    def select_single_photo(self):
        self.single_photo_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        if self.single_photo_path:
            self.lbl_photo.configure(text=f"Foto: {os.path.basename(self.single_photo_path)}", text_color="#2ecc71")

    def select_photo_folder(self):
        self.photo_folder = filedialog.askdirectory()
        if self.photo_folder:
            self.lbl_folder.configure(text=f"Folder: {self.photo_folder}", text_color="#2ecc71")

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
            self.lbl_csv.configure(text=f"CSV: {os.path.basename(csv_path)} ({len(self.csv_data)} rekod)", text_color="#2ecc71")
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
            
            pilih_symbol = "☑" if row['pilih'] else "☐"
            self.tree.insert("", tk.END, values=(pilih_symbol, row['kod_qr'], row['batch'], row['nama_penuh'], row['email_moe']))

    def filter_search(self, event):
        query = self.ent_search.get()
        self.refresh_treeview(query)

    def clear_search(self):
        self.ent_search.delete(0, tk.END)
        self.refresh_treeview()

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
            self.lbl_preview.configure(image="", text=f"Gagal Preview:\n{str(e)}", text_color="red")
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
                dib = ImageWin.Dib(bmp)
                dib.draw(hdc.GetHandleOutput(), (0, 0, 1013, 638))
            hdc.EndPage()
            hdc.EndDoc()
        finally:
            hdc.DeleteDC()

if __name__ == "__main__":
    app = CardPrinterApp()
    app.mainloop()