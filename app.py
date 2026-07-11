import os
import csv
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageDraw, ImageFont, ImageTk, ImageOps
import qrcode
import win32print
import win32ui
from PIL import ImageWin

class CardPrinterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistem Cetakan Kad MyKUSESS (Versi Save Layout + Double Preview)")
        self.root.geometry("1300x780") # Dinaikkan sedikit tinggi untuk muat elemen baru
        
        # --- KETETAPAN IKON PERISIAN ---
        try:
            # Pastikan anda letak fail 'logo.ico' dalam folder yang sama
            self.root.iconbitmap("logo.ico")
        except Exception:
            pass # Skip jika fail tiada supaya tidak crash semasa coding
        
        self.bg_path = ""
        self.photo_folder = ""
        self.single_photo_path = ""
        self.csv_data = [] 
        self.generated_card = None 
        
        # Fail untuk simpan konfigurasi secara kekal
        self.config_filename = "layout_config.json"
        
        # --- SUSUN ATUR UTAMA (GRID) ---
        self.root.columnconfigure(0, weight=4, minsize=600)
        self.root.columnconfigure(1, weight=5, minsize=550)
        self.root.rowconfigure(0, weight=1)
        
        # Notebook (Tab) untuk Bahagian Kiri
        self.notebook = ttk.Notebook(root)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        self.tab_single = tk.Frame(self.notebook, padx=15, pady=15)
        self.tab_batch = tk.Frame(self.notebook, padx=15, pady=15)
        self.tab_config = tk.Frame(self.notebook, padx=15, pady=15)
        
        self.notebook.add(self.tab_single, text=" Cetak Satu-Satu ")
        self.notebook.add(self.tab_batch, text=" Cetak Pukal (CSV) ")
        self.notebook.add(self.tab_config, text=" Konfigurasi Layout ")
        
        # Frame Kanan (Ruangan Preview Global & Pilihan Printer)
        right_frame = tk.Frame(root, padx=20, pady=20, bg="#f5f5f5")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        # --- KETETAPAN ASAS ---
        tk.Label(self.tab_single, text="1. Tetapan Asas Template", font=("Arial", 11, "bold"), fg="darkgreen").pack(anchor=tk.W, pady=5)
        tk.Button(self.tab_single, text="Pilih Template Kad (Background)", command=self.select_bg, width=35).pack(anchor=tk.W, pady=2)
        self.lbl_bg = tk.Label(self.tab_single, text="Template: Tiada fail dipilih", fg="red", wraplength=400, justify="left")
        self.lbl_bg.pack(anchor=tk.W, pady=2)
        
        # --- TAB 1: CETAK SATU-SATU ---
        tk.Label(self.tab_single, text="\n2. Maklumat Individu", font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=5)
        tk.Button(self.tab_single, text="Pilih Foto Guru/Murid", command=self.select_single_photo, width=35).pack(anchor=tk.W, pady=2)
        self.lbl_photo = tk.Label(self.tab_single, text="Foto: Tiada fail dipilih", fg="red", wraplength=400, justify="left")
        self.lbl_photo.pack(anchor=tk.W, pady=2)
        
        tk.Label(self.tab_single, text="Kod Unik QR (Contoh: wpwj727):").pack(anchor=tk.W, pady=2)
        self.ent_qr_code = tk.Entry(self.tab_single, width=45)
        self.ent_qr_code.pack(anchor=tk.W)
        
        tk.Label(self.tab_single, text="Nama Panggilan (Huruf Besar):").pack(anchor=tk.W, pady=2)
        self.ent_short_name = tk.Entry(self.tab_single, width=45)
        self.ent_short_name.pack(anchor=tk.W)
        
        tk.Label(self.tab_single, text="Nama Penuh:").pack(anchor=tk.W, pady=2)
        self.ent_full_name = tk.Entry(self.tab_single, width=45)
        self.ent_full_name.pack(anchor=tk.W)
        
        # BUTANG JANA PREVIEW 1 (Tab Cetak Satu-Satu)
        tk.Button(self.tab_single, text="JANA PREVIEW (SINGLE)", bg="#007acc", fg="white", font=("Arial", 10, "bold"), width=35, command=self.generate_single_preview).pack(pady=15)
        
        # --- TAB 2: CETAK PUKAL (BATCH CSV) ---
        tk.Label(self.tab_batch, text="1. Pilih Folder Gambar & Fail CSV", font=("Arial", 11, "bold"), fg="darkgreen").pack(anchor=tk.W, pady=5)
        tk.Button(self.tab_batch, text="Pilih Folder Semua Gambar", command=self.select_photo_folder, width=35).pack(anchor=tk.W, pady=2)
        self.lbl_folder = tk.Label(self.tab_batch, text="Folder: Tiada folder dipilih", fg="red", wraplength=400, justify="left")
        self.lbl_folder.pack(anchor=tk.W, pady=2)
        
        tk.Button(self.tab_batch, text="Muat Naik Fail CSV Senarai Murid", command=self.load_csv, width=35).pack(anchor=tk.W, pady=2)
        self.lbl_csv = tk.Label(self.tab_batch, text="CSV: Tiada fail dipilih", fg="red")
        self.lbl_csv.pack(anchor=tk.W, pady=2)
        
        tk.Label(self.tab_batch, text="\n2. Senarai Murid (Sila pilih untuk preview/cetak):", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=5)
        
        self.tree = ttk.Treeview(self.tab_batch, columns=("QR", "Panggilan", "Penuh"), show="headings", height=8)
        self.tree.heading("QR", text="Kod QR")
        self.tree.heading("Panggilan", text="Nama Panggilan")
        self.tree.heading("Penuh", text="Nama Penuh")
        self.tree.column("QR", width=80)
        self.tree.column("Panggilan", width=100)
        self.tree.column("Penuh", width=220)
        self.tree.pack(fill=tk.BOTH, expand=True, pady=5)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select) 
        
        # --- BAR KEMAJUAN (PROGRESS BAR) BATCH PRINT ---
        self.progress_frame = tk.Frame(self.tab_batch)
        self.progress_frame.pack(fill=tk.X, pady=5)
        self.lbl_progress_status = tk.Label(self.progress_frame, text="Status: Sedia", font=("Arial", 9))
        self.lbl_progress_status.pack(anchor=tk.W)
        self.progress_bar = ttk.Progressbar(self.progress_frame, orient="horizontal", mode="determinate")
        self.progress_bar.pack(fill=tk.X, pady=2)
        
        tk.Button(self.tab_batch, text="CETAK SEMUA YANG DIPIH (BATCH)", bg="purple", fg="white", font=("Arial", 11, "bold"), width=35, command=self.print_batch).pack(pady=5)

        # --- TAB 3: TAB KONFIGURASI LAYOUT ---
        container = ttk.Frame(self.tab_config)
        container.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(container, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        tk.Label(self.scrollable_frame, text="Ubah Suai Saiz, Kedudukan & Gaya Font", font=("Arial", 12, "bold"), fg="darkblue").grid(row=0, column=0, columnspan=4, pady=10, sticky=tk.W)
        
        FONT_OPTIONS = ["arial.ttf", "calibri.ttf", "times.ttf", "tahoma.ttf", "verdana.ttf", "cour.ttf"]
        
        # 1. Tetapan Gambar Foto
        tk.Label(self.scrollable_frame, text="[ GAMBAR FOTO - Kotak Sempadan ]", font=("Arial", 9, "bold")).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.cfg_img_x = self.create_cfg_entry(self.scrollable_frame, "Kedudukan X:", "40", row=2, col=0)
        self.cfg_img_y = self.create_cfg_entry(self.scrollable_frame, "Kedudukan Y:", "250", row=2, col=2)
        self.cfg_img_w = self.create_cfg_entry(self.scrollable_frame, "Maks Lebar (W):", "240", row=3, col=0)
        self.cfg_img_h = self.create_cfg_entry(self.scrollable_frame, "Maks Tinggi (H):", "310", row=3, col=2)
        
        # 2. Tetapan QR Code
        tk.Label(self.scrollable_frame, text="[ QR CODE ]", font=("Arial", 9, "bold")).grid(row=4, column=0, sticky=tk.W, pady=10)
        self.cfg_qr_x = self.create_cfg_entry(self.scrollable_frame, "Kedudukan X:", "735", row=5, col=0)
        self.cfg_qr_y = self.create_cfg_entry(self.scrollable_frame, "Kedudukan Y:", "255", row=5, col=2)
        self.cfg_qr_size = self.create_cfg_entry(self.scrollable_frame, "Saiz QR:", "230", row=6, col=0)
        
        # 3. Tetapan Teks Nama Panggilan
        tk.Label(self.scrollable_frame, text="[ NAMA PANGGILAN ]", font=("Arial", 9, "bold")).grid(row=7, column=0, sticky=tk.W, pady=10)
        self.cfg_n1_x = self.create_cfg_entry(self.scrollable_frame, "Kedudukan X:", "340", row=8, col=0)
        self.cfg_n1_y = self.create_cfg_entry(self.scrollable_frame, "Kedudukan Y:", "460", row=8, col=2)
        self.cfg_n1_font = self.create_cfg_entry(self.scrollable_frame, "Saiz Font:", "45", row=9, col=0)
        
        tk.Label(self.scrollable_frame, text="Jenis Font:").grid(row=9, column=2, sticky=tk.W, padx=5)
        self.cfg_n1_font_file = ttk.Combobox(self.scrollable_frame, values=FONT_OPTIONS, width=12, state="readonly")
        self.cfg_n1_font_file.set("arial.ttf")
        self.cfg_n1_font_file.grid(row=9, column=3, sticky=tk.W, padx=5)
        
        self.cfg_n1_bold = tk.BooleanVar(value=True)
        self.cfg_n1_italic = tk.BooleanVar(value=False)
        tk.Checkbutton(self.scrollable_frame, text="Bold", variable=self.cfg_n1_bold).grid(row=10, column=0, sticky=tk.W, padx=5)
        tk.Checkbutton(self.scrollable_frame, text="Italic", variable=self.cfg_n1_italic).grid(row=10, column=1, sticky=tk.W, padx=5)
        
        # 4. Tetapan Teks Nama Penuh
        tk.Label(self.scrollable_frame, text="[ NAMA PENUH ]", font=("Arial", 9, "bold")).grid(row=11, column=0, sticky=tk.W, pady=10)
        self.cfg_n2_x = self.create_cfg_entry(self.scrollable_frame, "Kedudukan X:", "320", row=12, col=0)
        self.cfg_n2_y = self.create_cfg_entry(self.scrollable_frame, "Kedudukan Y:", "560", row=12, col=2)
        self.cfg_n2_font = self.create_cfg_entry(self.scrollable_frame, "Saiz Font:", "30", row=13, col=0)
        
        tk.Label(self.scrollable_frame, text="Jenis Font:").grid(row=13, column=2, sticky=tk.W, padx=5)
        self.cfg_n2_font_file = ttk.Combobox(self.scrollable_frame, values=FONT_OPTIONS, width=12, state="readonly")
        self.cfg_n2_font_file.set("arial.ttf")
        self.cfg_n2_font_file.grid(row=13, column=3, sticky=tk.W, padx=5)
        
        self.cfg_n2_bold = tk.BooleanVar(value=False)
        self.cfg_n2_italic = tk.BooleanVar(value=False)
        tk.Checkbutton(self.scrollable_frame, text="Bold", variable=self.cfg_n2_bold).grid(row=14, column=0, sticky=tk.W, padx=5)
        tk.Checkbutton(self.scrollable_frame, text="Italic", variable=self.cfg_n2_italic).grid(row=14, column=1, sticky=tk.W, padx=5)
        
        # --- RUANGAN BUTANG KAWALAN CONFIG & JANA PREVIEW 2 ---
        frame_buttons = tk.Frame(self.scrollable_frame, pady=10)
        frame_buttons.grid(row=15, column=0, columnspan=4, sticky=tk.W)
        
        # Butang Simpan & Muat Tetapan
        tk.Button(frame_buttons, text="💾 Simpan Tetapan Layout", bg="#28a745", fg="white", font=("Arial", 9, "bold"), command=self.save_layout_config).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_buttons, text="📂 Muat Tetapan Semula", bg="#6c757d", fg="white", font=("Arial", 9, "bold"), command=self.load_layout_config).pack(side=tk.LEFT, padx=5)
        
        # BUTANG JANA PREVIEW 2 (Tab Konfigurasi Layout)
        tk.Button(self.scrollable_frame, text="🔄 KEMAS KINI & JANA PREVIEW", bg="#007acc", fg="white", font=("Arial", 11, "bold"), height=2, command=self.trigger_refresh_preview).grid(row=16, column=0, columnspan=4, pady=15, sticky=tk.EW)

        tk.Label(self.scrollable_frame, text="*Nota: Nilai kedudukan dalam unit piksel (px).", fg="gray", font=("Arial", 8)).grid(row=17, column=0, columnspan=4, pady=5, sticky=tk.W)

        # Autoload fail konfigurasi jika wujud semasa perisian mula dibuka
        self.load_layout_config(silent=True)

        # --- KOMPONEN KANAN (PREVIEW & CETAK GLOBAL) ---
        tk.Label(right_frame, text="PREVIEW KAD", font=("Arial", 12, "bold"), bg="#f5f5f5").pack(pady=5)
        
        self.preview_container = tk.Frame(right_frame, width=450, height=283, bg="white", highlightbackground="black", highlightthickness=1)
        self.preview_container.pack(pady=10)
        self.preview_container.pack_propagate(False)
        
        self.lbl_preview = tk.Label(self.preview_container, text="Sila jana preview atau pilih murid dari senarai", bg="white")
        self.lbl_preview.pack(fill=tk.BOTH, expand=True)
        
        # --- CIRI BARU: SELEKSI PRINTER WINDOWS ---
        tk.Label(right_frame, text="Pilih Pencetak Kad (Printer):", font=("Arial", 9, "bold"), bg="#f5f5f5").pack(anchor=tk.W, padx=25, pady=2)
        self.cbo_printer = ttk.Combobox(right_frame, width=40, state="readonly")
        self.cbo_printer.pack(pady=2)
        self.populate_printers() # Mengisi senarai nama printer sistem
        
        self.btn_global_print = tk.Button(right_frame, text="CETAK KAD INI SEKARANG", bg="green", fg="white", font=("Arial", 12, "bold"), width=35, command=self.print_single_card, state=tk.DISABLED)
        self.btn_global_print.pack(pady=12)
        
        self.btn_global_download = tk.Button(right_frame, text="💾 MUAT TURUN PREVIEW (PNG/JPG)", bg="#007acc", fg="white", font=("Arial", 11, "bold"), width=38, command=self.download_card_image)
        self.btn_global_download.pack(pady=2)

    def create_cfg_entry(self, parent, label_text, default_val, row, col):
        tk.Label(parent, text=label_text).grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)
        entry = tk.Entry(parent, width=8)
        entry.insert(0, default_val)
        entry.grid(row=row, column=col+1, sticky=tk.W, padx=5, pady=2)
        return entry

    # --- FUNGSI CARI PENCETAK WINDOWS ---
    def populate_printers(self):
        try:
            printers = [printer[2] for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
            self.cbo_printer['values'] = printers
            default_p = win32print.GetDefaultPrinter()
            if default_p in printers:
                self.cbo_printer.set(default_p)
            elif printers:
                self.cbo_printer.current(0)
        except Exception:
            self.cbo_printer['values'] = ["Tiada Printer Ditemui"]
            self.cbo_printer.current(0)

    # --- FUNGSI SIMPAN & RESTORE LAYOUT ---
    def save_layout_config(self):
        config_data = {
            "img_x": self.cfg_img_x.get(), "img_y": self.cfg_img_y.get(),
            "img_w": self.cfg_img_w.get(), "img_h": self.cfg_img_h.get(),
            "qr_x": self.cfg_qr_x.get(), "qr_y": self.cfg_qr_y.get(), "qr_size": self.cfg_qr_size.get(),
            "n1_x": self.cfg_n1_x.get(), "n1_y": self.cfg_n1_y.get(), "n1_font": self.cfg_n1_font.get(),
            "n1_font_file": self.cfg_n1_font_file.get(), "n1_bold": self.cfg_n1_bold.get(), "n1_italic": self.cfg_n1_italic.get(),
            "n2_x": self.cfg_n2_x.get(), "n2_y": self.cfg_n2_y.get(), "n2_font": self.cfg_n2_font.get(),
            "n2_font_file": self.cfg_n2_font_file.get(), "n2_bold": self.cfg_n2_bold.get(), "n2_italic": self.cfg_n2_italic.get()
        }
        try:
            with open(self.config_filename, "w") as f:
                json.dump(config_data, f, indent=4)
            messagebox.showinfo("Berjaya", "Konfigurasi layout berjaya disimpan!")
        except Exception as e:
            messagebox.showerror("Ralat", f"Gagal menyimpan fail konfigurasi:\n{str(e)}")

    def load_layout_config(self, silent=False):
        if not os.path.exists(self.config_filename):
            if not silent:
                messagebox.showwarning("Tiada Fail", "Tiada fail tetapan disimpan sebelum ini.")
            return
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
            set_val(self.cfg_n2_x, data.get("n2_x", "320"))
            set_val(self.cfg_n2_y, data.get("n2_y", "560"))
            set_val(self.cfg_n2_font, data.get("n2_font", "30"))
            self.cfg_n2_font_file.set(data.get("n2_font_file", "arial.ttf"))
            self.cfg_n2_bold.set(data.get("n2_bold", False))
            self.cfg_n2_italic.set(data.get("n2_italic", False))
            if not silent:
                messagebox.showinfo("Berjaya", "Tetapan layout berjaya dipulihkan!")
                self.trigger_refresh_preview()
        except Exception as e:
            if not silent:
                messagebox.showerror("Ralat", f"Gagal memuat tetapan:\n{str(e)}")

    def select_bg(self):
        self.bg_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        if self.bg_path:
            self.lbl_bg.config(text=f"Template: {os.path.basename(self.bg_path)}", fg="green")

    def select_single_photo(self):
        self.single_photo_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        if self.single_photo_path:
            self.lbl_photo.config(text=f"Foto: {os.path.basename(self.single_photo_path)}", fg="green")

    def select_photo_folder(self):
        self.photo_folder = filedialog.askdirectory()
        if self.photo_folder:
            self.lbl_folder.config(text=f"Folder: {self.photo_folder}", fg="green")

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
            self.lbl_csv.config(text=f"CSV: {os.path.basename(csv_path)} ({len(self.csv_data)} rekod)", fg="green")
        except Exception as e:
            messagebox.showerror("Ralat CSV", f"Gagal membaca fail CSV.\nInfo: {str(e)}")

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
        if bold and italic: return selected["bi"]
        elif bold: return selected["b"]
        elif italic: return selected["i"]
        else: return selected["r"]

    def make_card_image(self, qr_code, short_name, full_name, photo_filename, is_batch=False):
        if not self.bg_path:
            raise Exception("Sila pilih gambar Template Kad (Background) terlebih dahulu!")
            
        p_path = photo_filename if not is_batch else os.path.join(self.photo_folder, photo_filename)
        if not os.path.exists(p_path):
            raise Exception(f"Fail gambar tidak ditemui: {os.path.basename(p_path)}")
            
        try:
            img_x, img_y = int(self.cfg_img_x.get()), int(self.cfg_img_y.get())
            img_w, img_h = int(self.cfg_img_w.get()), int(self.cfg_img_h.get())
            qr_x, qr_y = int(self.cfg_qr_x.get()), int(self.cfg_qr_y.get())
            qr_sz = int(self.cfg_qr_size.get())
            n1_x, n1_y = int(self.cfg_n1_x.get()), int(self.cfg_n1_y.get())
            n1_fs = int(self.cfg_n1_font.get())
            n2_x, n2_y = int(self.cfg_n2_x.get()), int(self.cfg_n2_y.get())
            n2_fs = int(self.cfg_n2_font.get())
        except ValueError:
            raise Exception("Pastikan semua nilai ukuran diisi dengan NOMBOR bulat sahaja!")

        card = Image.open(self.bg_path).convert('RGBA').resize((1013, 638))
        
        raw_photo = Image.open(p_path).convert('RGBA')
        teacher_img = ImageOps.contain(raw_photo, (img_w, img_h))
        actual_w, actual_h = teacher_img.size
        centered_x = img_x + (img_w - actual_w) // 2
        centered_y = img_y + (img_h - actual_h) // 2
        card.paste(teacher_img, (centered_x, centered_y), teacher_img if teacher_img.mode == 'RGBA' else None)
        
        qr_data = f"mykusses:{qr_code.strip().lower()}"
        qr = qrcode.QRCode(box_size=6, border=1)
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGBA').resize((qr_sz, qr_sz))
        card.paste(qr_img, (qr_x, qr_y))
        
        draw = ImageDraw.Draw(card)
        font1_file = self.get_font_path(self.cfg_n1_font_file.get(), self.cfg_n1_bold.get(), self.cfg_n1_italic.get())
        font2_file = self.get_font_path(self.cfg_n2_font_file.get(), self.cfg_n2_bold.get(), self.cfg_n2_italic.get())
        
        try: font_short = ImageFont.truetype(font1_file, n1_fs)
        except: font_short = ImageFont.load_default()
        try: font_full = ImageFont.truetype(font2_file, n2_fs)
        except: font_full = ImageFont.load_default()
        
        draw.text((n1_x, n1_y), short_name.upper(), fill="black", font=font_short)
        draw.text((n2_x, n2_y), full_name.upper(), fill="black", font=font_full)
        
        return card

    def update_preview_ui(self, card_image):
        self.generated_card = card_image
        preview_img = card_image.copy().resize((450, 283), resample=Image.Resampling.LANCZOS)
        self.photo_preview = ImageTk.PhotoImage(preview_img)
        self.lbl_preview.config(image=self.photo_preview, text="")
        self.btn_global_print.config(state=tk.NORMAL)

    def generate_single_preview(self):
        if not self.ent_qr_code.get() or not self.ent_short_name.get() or not self.ent_full_name.get() or not self.single_photo_path:
            messagebox.showwarning("Ralat", "Sila lengkapkan borang di Tab Cetak Satu-Satu dan pilih foto!")
            return
        try:
            card = self.make_card_image(self.ent_qr_code.get(), self.ent_short_name.get(), self.ent_full_name.get(), self.single_photo_path, is_batch=False)
            self.update_preview_ui(card)
        except Exception as e:
            messagebox.showerror("Ralat", str(e))

    def trigger_refresh_preview(self):
        selected_items = self.tree.selection()
        if selected_items:
            self.on_tree_select(None)
            return
        if self.ent_qr_code.get() and self.single_photo_path:
            self.generate_single_preview()
            return
        messagebox.showwarning("Info", "Sila masukkan maklumat profil di Tab 'Cetak Satu-Satu' atau pilih nama di Tab 'Cetak Pukal' terlebih dahulu untuk menjana preview.")

    def on_tree_select(self, event):
        selected_items = self.tree.selection()
        if not selected_items: return
        item = selected_items[0]
        values = self.tree.item(item, "values")
        record = next((r for r in self.csv_data if r['kod_qr'] == values[0]), None)
        if record:
            try:
                card = self.make_card_image(record['kod_qr'], record['nama_panggilan'], record['nama_penuh'], record['fail_gambar'], is_batch=True)
                self.update_preview_ui(card)
            except Exception as e:
                self.lbl_preview.config(image="", text=f"Gagal Preview:\n{str(e)}", fg="red")
                self.btn_global_print.config(state=tk.DISABLED)

    def print_single_card(self):
        if self.generated_card is None: return
        try:
            self.generated_card.save("temp_print.png")
            self.send_to_printer("temp_print.png")
            messagebox.showinfo("Berjaya", "Kad semasa berjaya dihantar ke pencetak pilihan!")
        except Exception as e:
            messagebox.showerror("Ralat", str(e))

    def download_card_image(self):
        if self.generated_card is None:
            messagebox.showwarning("Tiada Data", "Tiada data kad aktif untuk dimuat turun. Sila jana preview dahulu!")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("JPEG Image", "*.jpg"), ("All Files", "*.*")],
            title="Simpan Grafik Kad Sebagai Gambar"
        )
        if not file_path: return
        try:
            output_image = self.generated_card.copy()
            if file_path.lower().endswith(('.jpg', '.jpeg')):
                output_image = output_image.convert('RGB')
            output_image.save(file_path)
            messagebox.showinfo("Berjaya", f"Fail imej kad beresolusi penuh berjaya disimpan di:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Ralat", f"Gagal menyimpan gambar kad: {str(e)}")

    # --- PENGUBAHSUAIAN CETAK PUKAL DENGAN PROGRESS BAR & SKIP ERROR ---
    def print_batch(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Pilihan Kosong", "Sila pilih nama dari jadual untuk dicetak!")
            return
        if not self.bg_path or not self.photo_folder:
            messagebox.showwarning("Ralat", "Sila pastikan Template Kad dan Folder Gambar telah dipilih!")
            return
        
        confirm = messagebox.askyesno("Sahkan Cetakan Pukal", f"Adakah anda pasti mahu mencetak {len(selected_items)} keping kad?")
        if not confirm: return

        # Set awal Progress Bar
        total_cards = len(selected_items)
        self.progress_bar["maximum"] = total_cards
        self.progress_bar["value"] = 0
        
        success_count = 0
        failed_cards = []

        for index, item in enumerate(selected_items):
            values = self.tree.item(item, "values")
            record = next((r for r in self.csv_data if r['kod_qr'] == values[0]), None)
            
            if record:
                # Kemaskini Status UI Secara Masa Nyata
                self.lbl_progress_status.config(text=f"Mencetak ({index + 1}/{total_cards}): {values[2]}")
                self.root.update_idletasks() # Paksa Windows kemaskini visual bar tanpa 'freezing'
                
                try:
                    card = self.make_card_image(record['kod_qr'], record['nama_panggilan'], record['nama_penuh'], record['fail_gambar'], is_batch=True)
                    card.save("temp_batch_print.png")
                    self.send_to_printer("temp_batch_print.png")
                    success_count += 1
                except Exception as e:
                    # Sistem memintas ralat fail/nama dan menyimpannya ke list failed tanpa crash
                    failed_cards.append(f"{values[2]} (Ralat: {str(e)})")
                    print(f"Gagal mencetak {values[2]}: {str(e)}")
            
            # Gerakkan progress bar satu tangga ke depan
            self.progress_bar["value"] = index + 1
            self.root.update_idletasks()

        # Set bar status selesai
        self.lbl_progress_status.config(text="Status: Semua Proses Cetakan Selesai.")
        
        # Mesej rumusan akhir cetakan pukal
        if len(failed_cards) == 0:
            messagebox.showinfo("Selesai Cetakan Pukal", f"Proses selesai! Semua {success_count} kad berjaya dicetak.")
        else:
            ralat_msg = "\n".join(failed_cards[:5]) # Tunjukkan 5 teratas sahaja jika terlalu panjang
            if len(failed_cards) > 5:
                ralat_msg += f"\n... dan {len(failed_cards) - 5} kad lain."
            messagebox.showwarning("Selesai Dengan Amaran", f"Berjaya cetak: {success_count} kad.\nGagal/Langkau: {len(failed_cards)} kad.\n\nSenarai terjejas:\n{ralat_msg}")

    # --- PENGUBAHSUAIAN LOGIK PRINTER MENGIKUT PILIHAN DROPDOWN ---
    def send_to_printer(self, filename):
        # Ambil nama pencetak yang dipilih dari dropdown Combobox UI
        printer_name = self.cbo_printer.get()
        if not printer_name or printer_name == "Tiada Printer Ditemui":
            raise Exception("Pencetak tidak sah atau tidak dipilih dengan betul!")

        bmp = Image.open(filename)
        hdc = win32ui.CreateDC()
        hdc.CreatePrinterDC(printer_name)
        hdc.StartDoc("Batch Cetak MyKUSESS")
        hdc.StartPage()
        dib = ImageWin.Dib(bmp)
        dib.draw(hdc.GetHandleOutput(), (0, 0, 1013, 638))
        hdc.EndPage()
        hdc.EndDoc()
        hdc.DeleteDC()

if __name__ == "__main__":
    root = tk.Tk()
    app = CardPrinterApp(root)
    root.mainloop()