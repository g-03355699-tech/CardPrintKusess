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
import win32con
from PIL import ImageWin

# Tetapan Tema Global Perisian
ctk.set_appearance_mode("System")  # Mengikut tetapan Windows (Dark/Light)
ctk.set_default_color_theme("blue") # Tema warna profesional (Blue, Green, Dark-Blue)

class CardPrinterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Sistem Cetakan Kad MyKUSESS (Versi Save Layout + Double Preview)")
        self.geometry("1350x820")  # Diperbetulkan ralat sintaks height
        
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
        self.csv_data = []
        self.generated_card = None
        self.config_filename = "layout_config.json"
        
        # --- GRID UTAMA ---
        self.grid_columnconfigure(0, weight=4, minsize=650)
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
        
        # Frame untuk letak Entry QR dan Butang Generate sebelah-menyebelah
        qr_input_frame = ctk.CTkFrame(self.tab_single, fg_color="transparent")
        qr_input_frame.pack(anchor="w", pady=2)
        
        self.ent_qr_code = ctk.CTkEntry(qr_input_frame, width=280, placeholder_text="Contoh: wpwj727")
        self.ent_qr_code.pack(side="left", padx=(0, 10))
        
        self.btn_generate_qr = ctk.CTkButton(qr_input_frame, text="Jana Kod", width=110, fg_color="#1abc9c", hover_color="#16a085", command=self.generate_random_qr_code)
        self.btn_generate_qr.pack(side="left")
        
        ctk.CTkLabel(self.tab_single, text="Nama Panggilan (Huruf Besar):").pack(anchor="w", pady=(5, 2))
        self.ent_short_name = ctk.CTkEntry(self.tab_single, width=400, placeholder_text="Contoh: AMINAH")
        self.ent_short_name.pack(anchor="w", pady=2)
        
        ctk.CTkLabel(self.tab_single, text="Nama Penuh:").pack(anchor="w", pady=(5, 2))
        self.ent_full_name = ctk.CTkEntry(self.tab_single, width=400, placeholder_text="Contoh: AMINAH BINTI ALI")
        self.ent_full_name.pack(anchor="w", pady=2)
        
        ctk.CTkButton(self.tab_single, text="JANA PREVIEW (SINGLE)", fg_color="#1f538d", font=ctk.CTkFont(weight="bold"), width=300, height=40, command=self.generate_single_preview).pack(pady=25)
        
        # ==========================================
        # TAB 2: CETAK PUKAL (BATCH CSV)
        # ==========================================
        ctk.CTkLabel(self.tab_batch, text="1. Pilih Folder Gambar & Fail CSV", font=ctk.CTkFont(size=14, weight="bold"), text_color="#2ecc71").pack(anchor="w", pady=(10, 5))
        ctk.CTkButton(self.tab_batch, text="Pilih Folder Semua Gambar", command=self.select_photo_folder, width=300).pack(anchor="w", pady=5)
        self.lbl_folder = ctk.CTkLabel(self.tab_batch, text="Folder: Tiada folder dipilih", text_color="#e74c3c", wraplength=400, justify="left")
        self.lbl_folder.pack(anchor="w", pady=2)
        
        ctk.CTkButton(self.tab_batch, text="Muat Naik Fail CSV Senarai Murid", fg_color="#2980b9", command=self.load_csv, width=300).pack(anchor="w", pady=5)
        self.lbl_csv = ctk.CTkLabel(self.tab_batch, text="CSV: Tiada fail dipilih", text_color="#e74c3c")
        self.lbl_csv.pack(anchor="w", pady=2)
        
        ctk.CTkLabel(self.tab_batch, text="2. Senarai Murid (Sila pilih untuk preview/cetak):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(15, 5))
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", font=("Arial", 10), rowheight=26, background="#2b2b2b" if ctk.get_appearance_mode()=="Dark" else "#ffffff", fieldbackground="#2b2b2b" if ctk.get_appearance_mode()=="Dark" else "#ffffff", foreground="white" if ctk.get_appearance_mode()=="Dark" else "black")
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))
        
        self.tree = ttk.Treeview(self.tab_batch, columns=("QR", "Panggilan", "Penuh"), show="headings", height=8)
        self.tree.heading("QR", text="Kod QR")
        self.tree.heading("Panggilan", text="Nama Panggilan")
        self.tree.heading("Penuh", text="Nama Penuh")
        self.tree.column("QR", width=90)
        self.tree.column("Panggilan", width=120)
        self.tree.column("Penuh", width=250)
        self.tree.pack(fill="both", expand=True, pady=5)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        
        self.progress_frame = ctk.CTkFrame(self.tab_batch, fg_color="transparent")
        self.progress_frame.pack(fill="x", pady=10)
        self.lbl_progress_status = ctk.CTkLabel(self.progress_frame, text="Status: Sedia", font=ctk.CTkFont(size=12))
        self.lbl_progress_status.pack(anchor="w")
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(fill="x", pady=5)
        self.progress_bar.set(0)
        
        ctk.CTkButton(self.tab_batch, text="CETAK SEMUA YANG DIPIH (BATCH)", fg_color="#9b59b6", hover_color="#8e44ad", font=ctk.CTkFont(weight="bold"), height=40, command=self.print_batch).pack(fill="x", pady=5)

        # ==========================================
        # TAB 3: TAB KONFIGURASI LAYOUT (SCROLLABLE)
        # ==========================================
        self.scrollable_frame = ctk.CTkScrollableFrame(self.tab_config, width=600, height=650)
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
        
        # 3. Nama Panggilan
        ctk.CTkLabel(self.scrollable_frame, text="[ NAMA PANGGILAN ]", font=ctk.CTkFont(weight="bold")).grid(row=7, column=0, columnspan=4, sticky="w", pady=(15,5))
        self.cfg_n1_x = self.create_cfg_entry(self.scrollable_frame, "Kedudukan X:", "340", row=8, col=0)
        self.cfg_n1_y = self.create_cfg_entry(self.scrollable_frame, "Kedudukan Y:", "460", row=8, col=2)
        self.cfg_n1_font = self.create_cfg_entry(self.scrollable_frame, "Saiz Font:", "45", row=9, col=0)
        
        ctk.CTkLabel(self.scrollable_frame, text="Jenis Font:").grid(row=9, column=2, sticky="w", padx=5)
        self.cfg_n1_font_file = ctk.CTkComboBox(self.scrollable_frame, values=FONT_OPTIONS, width=130)
        self.cfg_n1_font_file.set("arial.ttf")
        self.cfg_n1_font_file.grid(row=9, column=3, sticky="w", padx=5)
        
        self.cfg_n1_bold = tk.BooleanVar(value=True)
        self.cfg_n1_italic = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.scrollable_frame, text="Bold", variable=self.cfg_n1_bold).grid(row=10, column=0, sticky="w", padx=5, pady=5)
        ctk.CTkCheckBox(self.scrollable_frame, text="Italic", variable=self.cfg_n1_italic).grid(row=10, column=1, sticky="w", padx=5, pady=5)
        
        # Justifikasi Nama Panggilan
        ctk.CTkLabel(self.scrollable_frame, text="Justifikasi:").grid(row=10, column=2, sticky="w", padx=5, pady=5)
        self.cfg_n1_justify = ctk.StringVar(value="Left")
        self.cfg_n1_just_menu = ctk.CTkSegmentedButton(self.scrollable_frame, values=["Left", "Center", "Right"], variable=self.cfg_n1_justify, width=130)
        self.cfg_n1_just_menu.grid(row=10, column=3, sticky="w", padx=5, pady=5)
        
        # 4. Nama Penuh
        ctk.CTkLabel(self.scrollable_frame, text="[ NAMA PENUH ]", font=ctk.CTkFont(weight="bold")).grid(row=11, column=0, columnspan=4, sticky="w", pady=(15,5))
        self.cfg_n2_x = self.create_cfg_entry(self.scrollable_frame, "Kedudukan X:", "320", row=12, col=0)
        self.cfg_n2_y = self.create_cfg_entry(self.scrollable_frame, "Kedudukan Y:", "560", row=12, col=2)
        self.cfg_n2_font = self.create_cfg_entry(self.scrollable_frame, "Saiz Font:", "30", row=13, col=0)
        
        ctk.CTkLabel(self.scrollable_frame, text="Jenis Font:").grid(row=13, column=2, sticky="w", padx=5)
        self.cfg_n2_font_file = ctk.CTkComboBox(self.scrollable_frame, values=FONT_OPTIONS, width=130)
        self.cfg_n2_font_file.set("arial.ttf")
        self.cfg_n2_font_file.grid(row=13, column=3, sticky="w", padx=5)
        
        self.cfg_n2_bold = tk.BooleanVar(value=False)
        self.cfg_n2_italic = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.scrollable_frame, text="Bold", variable=self.cfg_n2_bold).grid(row=14, column=0, sticky="w", padx=5, pady=5)
        ctk.CTkCheckBox(self.scrollable_frame, text="Italic", variable=self.cfg_n2_italic).grid(row=14, column=1, sticky="w", padx=5, pady=5)
        
        # Justifikasi Nama Penuh
        ctk.CTkLabel(self.scrollable_frame, text="Justifikasi:").grid(row=14, column=2, sticky="w", padx=5, pady=5)
        self.cfg_n2_justify = ctk.StringVar(value="Left")
        self.cfg_n2_just_menu = ctk.CTkSegmentedButton(self.scrollable_frame, values=["Left", "Center", "Right"], variable=self.cfg_n2_justify, width=130)
        self.cfg_n2_just_menu.grid(row=14, column=3, sticky="w", padx=5, pady=5)
        
        frame_buttons = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        frame_buttons.grid(row=15, column=0, columnspan=4, sticky="w", pady=15)
        
        ctk.CTkButton(frame_buttons, text="💾 Simpan Layout", fg_color="#27ae60", hover_color="#219150", command=self.save_layout_config).pack(side="left", padx=5)
        ctk.CTkButton(frame_buttons, text="📂 Muat Tetapan", fg_color="#7f8c8d", hover_color="#717d7e", command=self.load_layout_config).pack(side="left", padx=5)
        
        ctk.CTkButton(self.scrollable_frame, text="🔄 KEMAS KINI & JANA PREVIEW", fg_color="#2980b9", font=ctk.CTkFont(weight="bold"), height=40, command=self.trigger_refresh_preview).grid(row=16, column=0, columnspan=4, pady=10, sticky="ew")

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
        # Menjana 7 karakter rawak (huruf kecil a-z dan nombor 0-9)
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
            "n2_justify": self.cfg_n2_justify.get()
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
            set_val(self.cfg_n1_y, data.get("n1_y", "460"))
            set_val(self.cfg_n1_font, data.get("n1_font", "45"))
            self.cfg_n1_font_file.set(data.get("n1_font_file", "arial.ttf"))
            self.cfg_n1_bold.set(data.get("n1_bold", True))
            self.cfg_n1_italic.set(data.get("n1_italic", False))
            self.cfg_n1_justify.set(data.get("n1_justify", "Left"))
            set_val(self.cfg_n2_x, data.get("n2_x", "320"))
            set_val(self.cfg_n2_y, data.get("n2_y", "560"))
            set_val(self.cfg_n2_font, data.get("n2_font", "30"))
            self.cfg_n2_font_file.set(data.get("n2_font_file", "arial.ttf"))
            self.cfg_n2_bold.set(data.get("n2_bold", False))
            self.cfg_n2_italic.set(data.get("n2_italic", False))
            self.cfg_n2_justify.set(data.get("n2_justify", "Left"))
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
        self.tree.delete(*self.tree.get_children())
        self.csv_data = []
        try:
            with open(csv_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.csv_data.append(row)
                    self.tree.insert("", tk.END, values=(row['kod_qr'], row['nama_panggilan'], row['nama_penuh']))
            self.lbl_csv.configure(text=f"CSV: {os.path.basename(csv_path)} ({len(self.csv_data)} rekod)", text_color="#2ecc71")
        except Exception as e:
            messagebox.showerror("Ralat CSV", str(e))

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

    def make_card_image(self, qr_code, short_name, full_name, photo_filename, is_batch=False):
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
        try: font_short = ImageFont.truetype(self.get_font_path(self.cfg_n1_font_file.get(), self.cfg_n1_bold.get(), self.cfg_n1_italic.get()), n1_fs)
        except: font_short = ImageFont.load_default()
        try: font_full = ImageFont.truetype(self.get_font_path(self.cfg_n2_font_file.get(), self.cfg_n2_bold.get(), self.cfg_n2_italic.get()), n2_fs)
        except: font_full = ImageFont.load_default()
        
        # Logik Pemilihan Justifikasi Teks (Left / Center / Right) menggunakan parameter Anchor Pillow
        align_map = {
            "Left": "la",    # Kiri
            "Center": "ma",  # Tengah
            "Right": "ra"    # Kanan
        }
        anchor1 = align_map.get(self.cfg_n1_justify.get(), "la")
        anchor2 = align_map.get(self.cfg_n2_justify.get(), "la")
        
        draw.text((n1_x, n1_y), short_name.upper(), fill="black", font=font_short, anchor=anchor1)
        draw.text((n2_x, n2_y), full_name.upper(), fill="black", font=font_full, anchor=anchor2)
        return card

    def update_preview_ui(self, card_image):
        self.generated_card = card_image
        preview_img = card_image.copy().resize((450, 283), resample=Image.Resampling.LANCZOS)
        self.photo_preview = ImageTk.PhotoImage(preview_img)
        self.lbl_preview.configure(image=self.photo_preview, text="")
        self.btn_global_print.configure(state="normal")

    def generate_single_preview(self):
        if not self.ent_qr_code.get() or not self.ent_short_name.get() or not self.ent_full_name.get() or not self.single_photo_path:
            messagebox.showwarning("Ralat", "Sila lengkapkan maklumat individu!")
            return
        try:
            card = self.make_card_image(self.ent_qr_code.get(), self.ent_short_name.get(), self.ent_full_name.get(), self.single_photo_path)
            self.update_preview_ui(card)
        except Exception as e: messagebox.showerror("Ralat", str(e))

    def trigger_refresh_preview(self):
        selected_items = self.tree.selection()
        if selected_items: self.on_tree_select(None)
        elif self.ent_qr_code.get() and self.single_photo_path: self.generate_single_preview()

    def on_tree_select(self, event):
        selected_items = self.tree.selection()
        if not selected_items: return
        values = self.tree.item(selected_items[0], "values")
        record = next((r for r in self.csv_data if r['kod_qr'] == values[0]), None)
        if record:
            try:
                card = self.make_card_image(record['kod_qr'], record['nama_panggilan'], record['nama_penuh'], record['fail_gambar'], is_batch=True)
                self.update_preview_ui(card)
            except Exception as e:
                self.lbl_preview.configure(image="", text=f"Gagal Preview:\n{str(e)}", text_color="red")
                self.btn_global_print.configure(state="disabled")

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
        selected_items = self.tree.selection()
        if not selected_items or not self.bg_path or not self.photo_folder: return
        if not messagebox.askyesno("Sahkan", f"Cetak {len(selected_items)} keping kad?"): return

        total_cards = len(selected_items)
        success_count = 0
        failed_cards = []

        for index, item in enumerate(selected_items):
            values = self.tree.item(item, "values")
            record = next((r for r in self.csv_data if r['kod_qr'] == values[0]), None)
            if record:
                self.lbl_progress_status.configure(text=f"Mencetak ({index + 1}/{total_cards}): {values[2]}")
                self.update_idletasks()
                try:
                    card = self.make_card_image(record['kod_qr'], record['nama_panggilan'], record['nama_penuh'], record['fail_gambar'], is_batch=True)
                    card.save("temp_batch_print.png")
                    self.send_to_printer("temp_batch_print.png")
                    success_count += 1
                except Exception as e:
                    failed_cards.append(values[2])
            
            self.progress_bar.set((index + 1) / total_cards)
            self.update_idletasks()

        self.lbl_progress_status.configure(text="Status: Selesai.")
        messagebox.showinfo("Selesai", f"Berjaya cetak: {success_count} kad.\nGagal: {len(failed_cards)}")

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