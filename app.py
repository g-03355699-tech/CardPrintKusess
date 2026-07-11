import os
import csv
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageDraw, ImageFont, ImageTk
import qrcode
import win32print
import win32ui
from PIL import ImageWin

class CardPrinterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistem Cetakan Kad MyKUSESS (Versi Pro + Batch CSV)")
        self.root.geometry("1100x650")
        
        self.bg_path = ""
        self.photo_folder = ""
        self.csv_data = [] # Menyimpan data dari CSV
        self.generated_card = None 
        
        # --- SUSUN ATUR UTAMA (GRID) ---
        self.root.columnconfigure(0, weight=4, minsize=500)
        self.root.columnconfigure(1, weight=5, minsize=500)
        self.root.rowconfigure(0, weight=1)
        
        # Notebook (Tab) untuk Bahagian Kiri
        self.notebook = ttk.Notebook(root)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        self.tab_single = tk.Frame(self.notebook, padx=15, pady=15)
        self.tab_batch = tk.Frame(self.notebook, padx=15, pady=15)
        
        self.notebook.add(self.tab_single, text=" Cetak Satu-Satu ")
        self.notebook.add(self.tab_batch, text=" Cetak Pukal (CSV) ")
        
        # Frame Kanan (Ruangan Preview Global)
        right_frame = tk.Frame(root, padx=20, pady=20, bg="#f5f5f5")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10) # <-- PEMBETULAN: y=10 ditukur ke pady=10 di sini!
        
        # --- KETETAPAN ASAS (Dikongsi Bersama) ---
        tk.Label(self.tab_single, text="1. Tetapan Asas Template", font=("Arial", 11, "bold"), fg="darkgreen").pack(anchor=tk.W, pady=5)
        tk.Button(self.tab_single, text="Pilih Template Kad (Background)", command=self.select_bg, width=35).pack(anchor=tk.W, pady=2)
        self.lbl_bg = tk.Label(self.tab_single, text="Template: Tiada fail dipilih", fg="red", wraplength=400, justify="left")
        self.lbl_bg.pack(anchor=tk.W, pady=2)
        
        # ---------------------------------------------------------
        # --- TAB 1: CETAK SATU-SATU ---
        # ---------------------------------------------------------
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
        
        tk.Button(self.tab_single, text="JANA PREVIEW (SINGLE)", bg="#007acc", fg="white", font=("Arial", 10, "bold"), width=35, command=self.generate_single_preview).pack(pady=15)
        
        # ---------------------------------------------------------
        # --- TAB 2: CETAK PUKAL (BATCH CSV) ---
        # ---------------------------------------------------------
        tk.Label(self.tab_batch, text="1. Pilih Folder Gambar & Fail CSV", font=("Arial", 11, "bold"), fg="darkgreen").pack(anchor=tk.W, pady=5)
        tk.Button(self.tab_batch, text="Pilih Folder Semua Gambar", command=self.select_photo_folder, width=35).pack(anchor=tk.W, pady=2)
        self.lbl_folder = tk.Label(self.tab_batch, text="Folder: Tiada folder dipilih", fg="red", wraplength=400, justify="left")
        self.lbl_folder.pack(anchor=tk.W, pady=2)
        
        tk.Button(self.tab_batch, text="Muat Naik Fail CSV Senarai Murid", command=self.load_csv, width=35).pack(anchor=tk.W, pady=2)
        self.lbl_csv = tk.Label(self.tab_batch, text="CSV: Tiada fail dipilih", fg="red")
        self.lbl_csv.pack(anchor=tk.W, pady=2)
        
        tk.Label(self.tab_batch, text="\n2. Senarai Murid (Sila pilih untuk preview/cetak):", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=5)
        
        # Treeview (Jadual) untuk tunjuk senarai CSV dengan fungsi Multi-Select
        self.tree = ttk.Treeview(self.tab_batch, columns=("QR", "Panggilan", "Penuh"), show="headings", height=10)
        self.tree.heading("QR", text="Kod QR")
        self.tree.heading("Panggilan", text="Nama Panggilan")
        self.tree.heading("Penuh", text="Nama Penuh")
        self.tree.column("QR", width=80)
        self.tree.column("Panggilan", width=100)
        self.tree.column("Penuh", width=220)
        self.tree.pack(fill=tk.BOTH, expand=True, pady=5)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select) 
        
        tk.Button(self.tab_batch, text="CETAK SEMUA YANG DIPIH (BATCH)", bg="purple", fg="white", font=("Arial", 11, "bold"), width=35, command=self.print_batch).pack(pady=10)

        # --- KOMPONEN KANAN (PREVIEW & CETAK GLOBAL) ---
        tk.Label(right_frame, text="PREVIEW KAD", font=("Arial", 12, "bold"), bg="#f5f5f5").pack(pady=5)
        
        self.preview_container = tk.Frame(right_frame, width=450, height=283, bg="white", highlightbackground="black", highlightthickness=1)
        self.preview_container.pack(pady=10)
        self.preview_container.pack_propagate(False)
        
        self.lbl_preview = tk.Label(self.preview_container, text="Sila jana preview atau pilih murid dari senarai", bg="white")
        self.lbl_preview.pack(fill=tk.BOTH, expand=True)
        
        self.btn_global_print = tk.Button(right_frame, text="CETAK KAD INI SEKARANG", bg="green", fg="white", font=("Arial", 12, "bold"), width=35, command=self.print_single_card, state=tk.DISABLED)
        self.btn_global_print.pack(pady=15)

    # --- FUNGSI KAWALAN FAIL ---
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
        if not csv_path:
            return
            
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
            messagebox.showerror("Ralat CSV", f"Gagal membaca fail CSV. Pastikan header betul.\nInfo: {str(e)}")

    # --- LOGIK PEMPROSESAN GRAFIK KAD ---
    def make_card_image(self, qr_code, short_name, full_name, photo_filename, is_batch=False):
        if not self.bg_path:
            raise Exception("Sila pilih gambar Template Kad (Background) terlebih dahulu!")
            
        p_path = photo_filename if not is_batch else os.path.join(self.photo_folder, photo_filename)
        if not os.path.exists(p_path):
            raise Exception(f"Fail gambar tidak ditemui: {os.path.basename(p_path)}")
            
        card = Image.open(self.bg_path).convert('RGBA').resize((1013, 638))
        
        teacher_img = Image.open(p_path).convert('RGBA').resize((240, 310))
        card.paste(teacher_img, (40, 250), teacher_img if teacher_img.mode == 'RGBA' else None)
        
        qr_data = f"mykusses:{qr_code.strip().lower()}"
        qr = qrcode.QRCode(box_size=6, border=1)
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGBA').resize((210, 210))
        card.paste(qr_img, (730, 350))
        
        draw = ImageDraw.Draw(card)
        font_short = ImageFont.truetype("arialbd.ttf", 36)
        font_full = ImageFont.truetype("arial.ttf", 24)
        
        draw.text((340, 460), short_name.upper(), fill="black", font=font_short)
        draw.text((320, 560), full_name.upper(), fill="black", font=font_full)
        
        return card

    def update_preview_ui(self, card_image):
        self.generated_card = card_image
        preview_img = card_image.copy().resize((450, 283), resample=Image.Resampling.LANCZOS)
        self.photo_preview = ImageTk.PhotoImage(preview_img)
        self.lbl_preview.config(image=self.photo_preview, text="")
        self.btn_global_print.config(state=tk.NORMAL)

    def generate_single_preview(self):
        if not self.ent_qr_code.get() or not self.ent_short_name.get() or not self.ent_full_name.get() or not hasattr(self, 'single_photo_path'):
            messagebox.showwarning("Ralat", "Sila lengkapkan borang di Tab Cetak Satu-Satu!")
            return
        try:
            card = self.make_card_image(self.ent_qr_code.get(), self.ent_short_name.get(), self.ent_full_name.get(), self.single_photo_path, is_batch=False)
            self.update_preview_ui(card)
        except Exception as e:
            messagebox.showerror("Ralat", str(e))

    def on_tree_select(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            return
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
        if self.generated_card is None:
            return
        try:
            self.generated_card.save("temp_print.png")
            self.send_to_printer("temp_print.png")
            messagebox.showinfo("Berjaya", "Kad semasa berjaya dihantar ke pencetak Badgy200!")
        except Exception as e:
            messagebox.showerror("Ralat", str(e))

    def print_batch(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Pilihan Kosong", "Sila pilih/highlight sekurang-kurangnya satu atau lebih nama dari jadual untuk dicetak!")
            return
        
        if not self.bg_path or not self.photo_folder:
            messagebox.showwarning("Ralat", "Sila pastikan Template Kad dan Folder Gambar telah dipilih!")
            return

        confirm = messagebox.askyesno("Sahkan Cetakan Pukal", f"Adakah anda pasti mahu mencetak sebanyak {len(selected_items)} keping kad secara pukal?")
        if not confirm:
            return

        success_count = 0
        for item in selected_items:
            values = self.tree.item(item, "values")
            record = next((r for r in self.csv_data if r['kod_qr'] == values[0]), None)
            if record:
                try:
                    card = self.make_card_image(record['kod_qr'], record['nama_panggilan'], record['nama_penuh'], record['fail_gambar'], is_batch=True)
                    card.save("temp_batch_print.png")
                    self.send_to_printer("temp_batch_print.png")
                    success_count += 1
                except Exception as e:
                    print(f"Gagal mencetak {values[2]}: {str(e)}")
        
        messagebox.showinfo("Selesai Cetakan Pukal", f"Proses selesai! {success_count} daripada {len(selected_items)} kad berjaya dihantar ke pencetak.")

    def send_to_printer(self, filename):
        printer_name = win32print.GetDefaultPrinter()
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