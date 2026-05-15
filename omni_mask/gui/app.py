import os
import queue
import threading
import pandas as pd
import tkinter as tk

from tkinter import filedialog, ttk, messagebox

from omni_mask.core.logic import AnonymizerCore, DeanonymizerCore, ANON_TYPE_LABELS, PII_TYPE_LABELS
from omni_mask.loaders.pdf_loader import PDFLoader
from omni_mask.loaders.docx_loader import DocxLoader
from omni_mask.loaders.excel_loader import ExcelLoader
from omni_mask.loaders.text_loader import TextLoader


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Aplikacja do Anonimizacji i Przywracania Danych")
        self.geometry("800x850")

        self.notebook = None
        self.log_area = None
        self.tab_anon = None
        self.tab_deanon = None

        self.deanon_in_dir_var = None
        self.deanon_key_var = None
        self.deanon_out_dir_var = None

        self.anon_in_dir_var = None
        self.anon_out_dir_var = None

        self.btn_deanon_run = None
        self.btn_anon_run = None

        self.deanon_progress_var = None
        self.deanon_progress_bar = None

        self.anon_type_vars = {}
        self.pii_type_vars = {}

        self.anon_logic = AnonymizerCore()
        self.deanon_logic = DeanonymizerCore()
        self.gui_queue = queue.Queue()

        self.loaders = [PDFLoader(), DocxLoader(), ExcelLoader(), TextLoader()]

        self.setup_ui()
        self.process_queue()

    def process_queue(self):
        inserted = False
        try:
            while True:
                msg = self.gui_queue.get_nowait()
                if isinstance(msg, tuple) and msg[0] == "ACTION":
                    action = msg[1]
                    if action == "ENABLE_ANON":
                        self.btn_anon_run.config(state=tk.NORMAL)
                    elif action == "ENABLE_DEANON":
                        self.btn_deanon_run.config(state=tk.NORMAL)
                    elif action == "ENABLE_MAP_BTN":
                        self.btn_anon_map.config(state=tk.NORMAL)
                    elif action == "PROGRESS":
                        num, total = msg[2], msg[3]
                        self.progress_var.set((num / total) * 100 if total else 0)
                    elif action == "PROGRESS_DEANON":
                        num, total = msg[2], msg[3]
                        self.deanon_progress_var.set(
                            (num / total) * 100 if total else 0
                        )
                else:
                    self.log_area.insert("", tk.END, values=(str(msg),))
                    inserted = True
        except queue.Empty:
            pass

        if inserted:
            children = self.log_area.get_children()
            if children:
                self.log_area.see(children[-1])
        self.after(100, self.process_queue)

    def log(self, message):
        self.gui_queue.put(message)

    def setup_ui(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except:
            pass

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tab_anon = ttk.Frame(self.notebook, padding=10)
        self.tab_deanon = ttk.Frame(self.notebook, padding=10)

        self.notebook.add(self.tab_anon, text="1. Anonimizacja")
        self.notebook.add(
            self.tab_deanon, text="2. Przywracanie Danych (De-anonimizacja)"
        )

        self.setup_anon_tab()
        self.setup_deanon_tab()

        frame_log = ttk.LabelFrame(
            self, text="Logi z przebiegu operacji", padding=10
        )
        frame_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        y_scroll = ttk.Scrollbar(frame_log)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        x_scroll = ttk.Scrollbar(frame_log, orient=tk.HORIZONTAL)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        self.log_area = ttk.Treeview(
            frame_log, columns=("Log",), show="headings", height=12
        )
        self.log_area.heading("Log", text="Szczegóły operacji")
        self.log_area.column("Log", anchor="w", stretch=True, width=700)
        self.log_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.log_area.configure(
            yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set
        )
        y_scroll.config(command=self.log_area.yview)
        x_scroll.config(command=self.log_area.xview)

        self.log("Witaj! Aplikacja gotowa do pracy w trybie offline.")

    def setup_anon_tab(self):
        self.anon_in_dir_var = tk.StringVar()
        self.anon_out_dir_var = tk.StringVar()

        frame_in = ttk.Frame(self.tab_anon)
        frame_in.pack(fill=tk.X, pady=5)
        ttk.Label(frame_in, text="Katalog wejściowy z dokumentami:", width=30).pack(
            side=tk.LEFT
        )
        ttk.Entry(
            frame_in, textvariable=self.anon_in_dir_var, state="readonly"
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(
            frame_in,
            text="Wybierz katalog",
            command=lambda: self.select_dir(self.anon_in_dir_var),
        ).pack(side=tk.LEFT)

        frame_out = ttk.Frame(self.tab_anon)
        frame_out.pack(fill=tk.X, pady=5)
        ttk.Label(frame_out, text="Katalog dla zanonimizowanych:", width=30).pack(
            side=tk.LEFT
        )
        ttk.Entry(
            frame_out, textvariable=self.anon_out_dir_var, state="readonly"
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(
            frame_out,
            text="Wybierz katalog",
            command=lambda: self.select_dir(self.anon_out_dir_var),
        ).pack(side=tk.LEFT)

        # PII section
        self.setup_pii_section()

        # FastMasker section
        frame_types = ttk.LabelFrame(
            self.tab_anon, text="Reguły FastMasker – co anonimizować:", padding=8
        )
        frame_types.pack(fill=tk.X, pady=8)
        self.anon_type_vars = {}
        for i, (key, label) in enumerate(ANON_TYPE_LABELS.items()):
            var = tk.BooleanVar(value=True)
            self.anon_type_vars[key] = var
            row, col = divmod(i, 2)
            ttk.Checkbutton(frame_types, text=label, variable=var).grid(
                row=row, column=col, sticky="w", padx=10, pady=3
            )

        frame_btns = ttk.Frame(self.tab_anon)
        frame_btns.pack(fill=tk.X, pady=15)
        self.btn_anon_run = ttk.Button(
            frame_btns,
            text="▶ Rozpocznij Anonimizację",
            command=self.start_anon_processing,
        )
        self.btn_anon_run.pack(side=tk.LEFT, padx=5)
        self.btn_anon_map = ttk.Button(
            frame_btns,
            text="Zapisz obecny Klucz Mapowania",
            command=self.export_mapping,
        )
        self.btn_anon_map.pack(side=tk.LEFT, padx=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.tab_anon, variable=self.progress_var, maximum=100
        )
        self.progress_bar.pack(fill=tk.X, pady=10)

    def setup_pii_section(self):
        frame_pii = ttk.LabelFrame(
            self.tab_anon, text="PII (AI) – co anonimizować:", padding=8
        )
        frame_pii.pack(fill=tk.X, pady=8)
        self.pii_type_vars = {}
        for i, (key, label) in enumerate(PII_TYPE_LABELS.items()):
            var = tk.BooleanVar(value=True)
            self.pii_type_vars[key] = var
            row, col = divmod(i, 2)
            ttk.Checkbutton(frame_pii, text=label, variable=var).grid(
                row=row, column=col, sticky="w", padx=10, pady=3
            )

    def setup_deanon_tab(self):
        self.deanon_in_dir_var = tk.StringVar()
        self.deanon_key_var = tk.StringVar()
        self.deanon_out_dir_var = tk.StringVar()

        lbl_warn = ttk.Label(
            self.tab_deanon,
            text="⚠️ PAMIĘTAJ: Pliki PDF nie mogą być przywrócone (są zakodowane bezpowrotnie).",
            foreground="red",
            font=("Helvetica", 10, "bold"),
        )
        lbl_warn.pack(fill=tk.X, pady=(0, 15))

        frame_key = ttk.Frame(self.tab_deanon)
        frame_key.pack(fill=tk.X, pady=5)
        ttk.Label(
            frame_key, text="Wskaż plik klucza mapowania (.xlsx):", width=30
        ).pack(side=tk.LEFT)
        ttk.Entry(
            frame_key, textvariable=self.deanon_key_var, state="readonly"
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(
            frame_key, text="Wybierz plik Excel", command=self.select_key_file
        ).pack(side=tk.LEFT)

        frame_in = ttk.Frame(self.tab_deanon)
        frame_in.pack(fill=tk.X, pady=5)
        ttk.Label(
            frame_in, text="Katalog ze zanonimizowanymi plikami:", width=30
        ).pack(side=tk.LEFT)
        ttk.Entry(
            frame_in, textvariable=self.deanon_in_dir_var, state="readonly"
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(
            frame_in,
            text="Wybierz katalog",
            command=lambda: self.select_dir(self.deanon_in_dir_var),
        ).pack(side=tk.LEFT)

        frame_out = ttk.Frame(self.tab_deanon)
        frame_out.pack(fill=tk.X, pady=5)
        ttk.Label(
            frame_out, text="Katalog dla przywróconych plików:", width=30
        ).pack(side=tk.LEFT)
        ttk.Entry(
            frame_out, textvariable=self.deanon_out_dir_var, state="readonly"
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(
            frame_out,
            text="Wybierz katalog",
            command=lambda: self.select_dir(self.deanon_out_dir_var),
        ).pack(side=tk.LEFT)

        frame_btns = ttk.Frame(self.tab_deanon)
        frame_btns.pack(fill=tk.X, pady=15)
        self.btn_deanon_run = ttk.Button(
            frame_btns,
            text="▶ Przywróć Oryginalne Dane (Odkoduj)",
            command=self.start_deanon_processing,
        )
        self.btn_deanon_run.pack(side=tk.LEFT, padx=5)

        self.deanon_progress_var = tk.DoubleVar()
        self.deanon_progress_bar = ttk.Progressbar(
            self.tab_deanon, variable=self.deanon_progress_var, maximum=100
        )
        self.deanon_progress_bar.pack(fill=tk.X, pady=10)

    def select_dir(self, var):
        d = filedialog.askdirectory()
        if d:
            var.set(d)

    def select_key_file(self):
        f = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx *.xls")])
        if f:
            self.deanon_key_var.set(f)

    def start_anon_processing(self):
        in_dir = self.anon_in_dir_var.get()
        out_dir = self.anon_out_dir_var.get()
        if not in_dir or not out_dir:
            self.log("[BŁĄD] Wybierz oba katalogi (wejściowy i wyjściowy).")
            return

        # Compute enabled sets from checkbox states
        pii_enabled = {k for k, v in self.pii_type_vars.items() if v.get()}
        enabled_fastmask = {k for k, v in self.anon_type_vars.items() if v.get()}

        # Also update core.enabled for backward compat
        for key, var in self.anon_type_vars.items():
            self.anon_logic.enabled[key] = var.get()

        if not pii_enabled and not enabled_fastmask:
            messagebox.showwarning(
                "Anonimizacja",
                "Zaznacz co najmniej jeden typ danych do anonimizacji.",
            )
            return

        # Reset PII records from predictor
        self.anon_logic._pii_mappings = {}

        self.btn_anon_run.config(state=tk.DISABLED)
        self.log("\n" + "=" * 50)
        self.log(">> START: Anonimizacja w toku...")
        threading.Thread(
            target=self.anon_thread, args=(in_dir, out_dir, pii_enabled, enabled_fastmask), daemon=True
        ).start()

    def anon_thread(self, in_dir, out_dir, pii_enabled, enabled_fastmask):
        try:
            files = [
                f
                for f in os.listdir(in_dir)
                if os.path.isfile(os.path.join(in_dir, f))
            ]
            total = len(files)
            if total == 0:
                self.log("[INFO] Pusty folder wejściowy.")
            for num, fname in enumerate(files, 1):
                filepath = os.path.join(in_dir, fname)
                outpath = os.path.join(out_dir, fname)
                if filepath == outpath:
                    outpath = os.path.join(out_dir, f"pseudo_{fname}")

                handled = False
                for loader in self.loaders:
                    if loader.can_handle(filepath):
                        try:
                            loader.anonymize(
                                filepath, outpath, self.anon_logic,
                                pii_enabled=pii_enabled, enabled_fastmask=enabled_fastmask,
                            )
                            self.log(f"[{num}/{total}] Zakodowano: '{fname}'")
                            handled = True
                            break
                        except Exception as e:
                            self.log(
                                   f"[{num}/{total}] [BŁĄD] Plik '{fname}': {str(e)}"
                            )
                            handled = True  # Próbowaliśmy, ale błąd
                            break

                if handled:
                    self.gui_queue.put(("ACTION", "PROGRESS", num, total))

            key_path = os.path.join(out_dir, "klucz_mapowania.xlsx")
            self.export_mapping_internal(key_path)
        finally:
            self.log("Zakończono.")
            self.gui_queue.put(("ACTION", "ENABLE_ANON"))

    def start_deanon_processing(self):
        key_file = self.deanon_key_var.get()
        in_dir = self.deanon_in_dir_var.get()
        out_dir = self.deanon_out_dir_var.get()

        if not key_file or not in_dir or not out_dir:
            self.log(
                "[BŁĄD] Wypełnij kompletnie wszystkie 3 ścieżki w zakładce przywracania."
            )
            return

        self.btn_deanon_run.config(state=tk.DISABLED)
        self.log("\n" + "=" * 50)
        self.log(">> START: Proces odwracania (de-anonimizacji)...")

        success, msg = self.deanon_logic.load_key(key_file)
        self.log(f"[INFO] {msg}")
        if not success:
            self.btn_deanon_run.config(state=tk.NORMAL)
            return

        threading.Thread(
            target=self.deanon_thread, args=(in_dir, out_dir), daemon=True
        ).start()

    def deanon_thread(self, in_dir, out_dir):
        try:
            files = [
                f
                for f in os.listdir(in_dir)
                if os.path.isfile(os.path.join(in_dir, f))
            ]
            total = len(files)
            for num, fname in enumerate(files, 1):
                if "klucz_mapowania" in fname.lower():
                    continue
                filepath = os.path.join(in_dir, fname)
                outpath = os.path.join(out_dir, fname)
                if filepath == outpath:
                    outpath = os.path.join(out_dir, f"RESTORED_{fname}")

                handled = False
                for loader in self.loaders:
                    if loader.can_handle(filepath):
                        try:
                            loader.deanonymize(filepath, outpath, self.deanon_logic)
                            self.log(f"[{num}/{total}] Odzyskany: '{fname}'")
                            handled = True
                            break
                        except NotImplementedError as e:
                            self.log(
                                   f"[{num}/{total}] Zignorowano '{fname}' - {str(e)}"
                            )
                            handled = True
                            break
                        except Exception as e:
                            self.log(
                                   f"[{num}/{total}] [BŁĄD] Plik '{fname}': {str(e)}"
                            )
                            handled = True
                            break
                if handled:
                    self.gui_queue.put(("ACTION", "PROGRESS_DEANON", num, total))
        finally:
            self.log("Zakończono proces de-anonimizacji.")
            self.gui_queue.put(("ACTION", "ENABLE_DEANON"))

    def export_mapping(self):
        suggested_dir = self.anon_out_dir_var.get() or os.path.expanduser("~")
        f = filedialog.asksaveasfilename(
            initialdir=suggested_dir,
            initialfile="klucz_mapowania.xlsx",
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")],
        )
        if not f:
            return
        self.btn_anon_map.config(state=tk.DISABLED)
        self.log(f"[INFO] Trwa zapisywanie mapy kluczy do: {os.path.basename(f)}...")

        def run_export():
            try:
                self.export_mapping_internal(f)
            finally:
                self.gui_queue.put(("ACTION", "ENABLE_MAP_BTN"))

        threading.Thread(target=run_export, daemon=True).start()

    def export_mapping_internal(self, key_path):
        try:
            # Merge FastMasker and PII records
            all_records = list(self.anon_logic.records)
            all_records.extend(self.anon_logic.pii_records)

            if not all_records:
                self.log(
                    "[OSTRZEŻENIE] Brak danych (0 dopasowań). Klucz mapowania pusty."
                )
                df = pd.DataFrame(
                    columns=[
                        "Oryginalna wartość",
                        "Typ danych",
                        "Wygenerowany pseudonim",
                        "Kontekst",
                    ]
                )
            else:
                df = pd.DataFrame(all_records)
            df.to_excel(key_path, index=False)
            self.log(
                f"[SUKCES] Wygenerowano/zaktualizowano '{os.path.basename(key_path)}'"
            )

            html_path = os.path.splitext(key_path)[0] + "_Raport_Zmian.html"
            html_content = [
                "<html><head><meta charset='utf-8'><title>Raport Zmian</title>",
                "<style>body{font-family: Arial;} table{border-collapse: collapse; width: 100%;} th, td{border: 1px solid #ddd; padding: 8px;} th{background-color: #f2f2f2;}</style>",
                "</head><body><h2>Raport Zmian Anonimizacji</h2>",
                "<table><tr><th>Oryginał</th><th>Kategoria</th><th>Pseudonim</th><th>Kontekst Zdania (Przed Zmianą)</th></tr>",
            ]
            for r in all_records:
                html_content.append(
                    f"<tr><td>{r.get('Oryginalna wartość', '')}</td><td>{r.get('Typ danych', '')}</td><td>{r.get('Wygenerowany pseudonim', '')}</td><td>{r.get('Kontekst', '')}</td></tr>"
                )
            html_content.append("</table></body></html>")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write("\n".join(html_content))
            self.log(
                f"[SUKCES] Wygenerowano raport audytowy '{os.path.basename(html_path)}'"
            )
        except Exception as e:
            self.log(f"[BŁĄD] Zapis klucza nie powiódł się: {str(e)}")


if __name__ == "__main__":
    app = App()
    app.mainloop()
