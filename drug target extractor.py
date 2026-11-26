
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import urllib.request
import urllib.error
import json
import re
import csv
import os
import threading


class DrugTargetExtractor:

    def __init__(self, root):
        self.root = root
        self.root.title("Drug Target and PDB Identifier Finder")
        self.root.geometry("1150x780")
        self.root.minsize(900, 600)

        self.results = []
        self.targets = []

        self.create_interface()

    # ----------------------------------
    # INTERFACE
    # ----------------------------------

    def create_interface(self):

        tk.Label(
            self.root,
            text="DRUG TARGET EXTRACTOR",
            font=("Arial", 23, "bold"),
            fg="#17365D"
        ).pack(pady=(15, 3))

        tk.Label(
            self.root,
            text="Drug Target Identification and PDB Structure Retrieval",
            font=("Arial", 11)
        ).pack(pady=3)

        buttons = tk.Frame(self.root)
        buttons.pack(pady=12)

        tk.Button(
            buttons,
            text="Upload TXT File",
            command=self.upload_file,
            bg="#286090",
            fg="white",
            font=("Arial", 11, "bold"),
            padx=15
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            buttons,
            text="Clear",
            command=self.clear_all,
            font=("Arial", 11),
            padx=15
        ).pack(side=tk.LEFT, padx=5)

        tk.Label(
            self.root,
            text="Paste Research Article Text",
            font=("Arial", 12, "bold")
        ).pack(pady=5)

        text_frame = tk.Frame(self.root)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=20)

        self.text_area = tk.Text(
            text_frame,
            height=11,
            wrap=tk.WORD,
            font=("Arial", 11)
        )

        scroll = ttk.Scrollbar(
            text_frame,
            command=self.text_area.yview
        )

        self.text_area.configure(
            yscrollcommand=scroll.set
        )

        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Button(
            self.root,
            text="IDENTIFY TARGETS AND SEARCH PDB",
            command=self.start_extraction,
            bg="#198754",
            fg="white",
            font=("Arial", 12, "bold"),
            padx=20,
            pady=9
        ).pack(pady=13)

        self.status = tk.Label(
            self.root,
            text="Ready",
            fg="gray",
            font=("Arial", 10)
        )
        self.status.pack(pady=4)

        tk.Label(
            self.root,
            text="DRUG TARGET AND PDB RESULTS",
            font=("Arial", 14, "bold"),
            fg="#17365D"
        ).pack(pady=7)

        result_frame = tk.Frame(self.root)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=8)

        columns = (
            "Target",
            "Type",
            "PDB ID",
            "Structure Title",
            "Method",
            "Resolution"
        )

        self.table = ttk.Treeview(
            result_frame,
            columns=columns,
            show="headings"
        )

        widths = {
            "Target": 120,
            "Type": 110,
            "PDB ID": 85,
            "Structure Title": 340,
            "Method": 150,
            "Resolution": 100
        }

        for column in columns:
            self.table.heading(column, text=column)
            self.table.column(
                column,
                width=widths[column],
                minwidth=70
            )

        y_scroll = ttk.Scrollbar(
            result_frame,
            orient=tk.VERTICAL,
            command=self.table.yview
        )

        x_scroll = ttk.Scrollbar(
            result_frame,
            orient=tk.HORIZONTAL,
            command=self.table.xview
        )

        self.table.configure(
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set
        )

        self.table.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        self.download_button = tk.Button(
            self.root,
            text="Download Results",
            command=self.download_results,
            bg="#286090",
            fg="white",
            font=("Arial", 11, "bold"),
            state=tk.DISABLED
        )

        self.download_button.pack(pady=10)

    # ----------------------------------
    # UPLOAD FILE
    # ----------------------------------

    def upload_file(self):

        path = filedialog.askopenfilename(
            filetypes=[("Text Files", "*.txt")]
        )

        if path:
            try:
                with open(
                    path,
                    "r",
                    encoding="utf-8-sig"
                ) as file:

                    content = file.read()

                self.text_area.delete("1.0", tk.END)
                self.text_area.insert(tk.END, content)

                self.status.config(
                    text="Uploaded: " + os.path.basename(path)
                )

            except Exception as error:
                messagebox.showerror("File Error", str(error))

    # ----------------------------------
    # CLEAR
    # ----------------------------------

    def clear_all(self):

        self.text_area.delete("1.0", tk.END)

        for item in self.table.get_children():
            self.table.delete(item)

        self.results = []
        self.targets = []

        self.download_button.config(state=tk.DISABLED)
        self.status.config(text="Ready")

    # ----------------------------------
    # IDENTIFY TARGETS
    # ----------------------------------

    def identify_targets(self, article):

        known_targets = {
            "EGFR": "Epidermal Growth Factor Receptor",
            "ERBB2": "HER2 Receptor",
            "HER2": "HER2 Receptor",
            "TP53": "Tumor Protein p53",
            "AKT1": "AKT Serine/Threonine Kinase 1",
            "AKT": "AKT Kinase",
            "BRAF": "B-Raf Proto-Oncogene",
            "KRAS": "KRAS Proto-Oncogene",
            "NRAS": "NRAS Proto-Oncogene",
            "JAK1": "Janus Kinase 1",
            "JAK2": "Janus Kinase 2",
            "STAT3": "Signal Transducer and Activator of Transcription 3",
            "TNF": "Tumor Necrosis Factor",
            "IL6": "Interleukin 6",
            "PTGS2": "Cyclooxygenase 2",
            "COX-2": "Cyclooxygenase 2",
            "MAPK1": "Mitogen Activated Protein Kinase 1",
            "MAPK": "Mitogen Activated Protein Kinase",
            "PI3K": "Phosphoinositide 3-Kinase",
            "MTOR": "Mechanistic Target of Rapamycin",
            "CDK2": "Cyclin Dependent Kinase 2",
            "CDK4": "Cyclin Dependent Kinase 4",
            "CDK6": "Cyclin Dependent Kinase 6",
            "PARP1": "Poly ADP-Ribose Polymerase 1",
            "ACE": "Angiotensin Converting Enzyme",
            "ESR1": "Estrogen Receptor 1",
            "AR": "Androgen Receptor",
            "MYC": "MYC Proto-Oncogene",
            "MMP2": "Matrix Metalloproteinase 2",
            "MMP9": "Matrix Metalloproteinase 9",
            "CASP3": "Caspase 3",
            "BCL2": "B-Cell Lymphoma 2",
            "PPARG": "Peroxisome Proliferator Activated Receptor Gamma",
            "NOS2": "Nitric Oxide Synthase 2"
        }

        sentences = re.split(
            r'(?<=[.!?])\s+',
            article
        )

        keywords = [
            "target",
            "protein",
            "gene",
            "receptor",
            "kinase",
            "enzyme",
            "inhibitor",
            "expression",
            "signaling",
            "signalling",
            "binding",
            "activation",
            "overexpression"
        ]

        found = {}

        for sentence in sentences:

            lower = sentence.lower()

            if not any(word in lower for word in keywords):
                continue

            for symbol, full_name in known_targets.items():

                pattern = (
                    r'(?<![A-Za-z0-9])'
                    + re.escape(symbol)
                    + r'(?![A-Za-z0-9])'
                )

                if re.search(pattern, sentence, re.IGNORECASE):

                    key = symbol.upper()

                    if key not in found:

                        found[key] = {
                            "target": symbol,
                            "full_name": full_name,
                            "context": sentence.strip(),
                            "type": "Gene/Protein"
                        }

        return list(found.values())

    # ----------------------------------
    # RCSB PDB SEARCH
    # ----------------------------------

    def search_pdb(self, target, full_name):

        search_url = (
            "https://search.rcsb.org/rcsbsearch/v2/query"
        )

        # Search using the biological target name,
        # not a PDB ID taken from the article.

        query = {
            "query": {
                "type": "terminal",
                "service": "full_text",
                "parameters": {
                    "value": full_name
                }
            },
            "return_type": "entry",
            "request_options": {
                "paginate": {
                    "start": 0,
                    "rows": 10
                },
                "results_content_type": ["experimental"]
            }
        }

        try:

            body = json.dumps(query).encode("utf-8")

            request = urllib.request.Request(
                search_url,
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "DrugTargetPDBFinder/1.0"
                },
                method="POST"
            )

            with urllib.request.urlopen(
                request,
                timeout=25
            ) as response:

                data = json.loads(
                    response.read().decode("utf-8")
                )

            entries = data.get("result_set", [])

            structures = []

            for entry in entries:

                pdb_id = entry.get("identifier")

                if not pdb_id:
                    continue

                details_url = (
                    "https://data.rcsb.org/rest/v1/core/entry/"
                    + pdb_id
                )

                try:

                    with urllib.request.urlopen(
                        details_url,
                        timeout=15
                    ) as response:

                        details = json.loads(
                            response.read().decode("utf-8")
                        )

                    title = details.get(
                        "struct", {}
                    ).get(
                        "title", "Title unavailable"
                    )

                    info = details.get(
                        "rcsb_entry_info", {}
                    )

                    methods = info.get(
                        "experimental_method", []
                    )

                    if isinstance(methods, list):
                        method = ", ".join(methods)
                    else:
                        method = str(methods or "Not available")

                    resolutions = info.get(
                        "resolution_combined", []
                    )

                    resolution = (
                        str(resolutions[0]) + " Å"
                        if resolutions
                        else "Not available"
                    )

                    structures.append({
                        "pdb_id": pdb_id,
                        "title": title,
                        "method": method,
                        "resolution": resolution
                    })

                except Exception:
                    continue

            return structures

        except urllib.error.HTTPError as error:

            if error.code == 204:
                return []

            print("PDB HTTP error:", error)
            return []

        except Exception as error:

            print("PDB connection error:", error)
            return []

    # ----------------------------------
    # START EXTRACTION
    # ----------------------------------

    def start_extraction(self):

        article = self.text_area.get(
            "1.0",
            tk.END
        ).strip()

        if not article:

            messagebox.showwarning(
                "Input Required",
                "Upload a text file or paste research article text."
            )

            return

        self.download_button.config(state=tk.DISABLED)

        for item in self.table.get_children():
            self.table.delete(item)

        self.results = []

        self.status.config(text="Identifying potential targets...")
        self.root.update_idletasks()

        self.targets = self.identify_targets(article)

        if not self.targets:

            messagebox.showinfo(
                "No Targets",
                "No targets from the current target dictionary were identified."
            )

            self.status.config(text="No targets identified")
            return

        # Run network searches in background

        threading.Thread(
            target=self.perform_pdb_search,
            daemon=True
        ).start()

    # ----------------------------------
    # SEARCH PDB FOR EACH TARGET
    # ----------------------------------

    def perform_pdb_search(self):

        total = len(self.targets)

        for index, target in enumerate(self.targets, start=1):

            name = target["target"]
            full_name = target["full_name"]

            self.root.after(
                0,
                lambda n=name, i=index, t=total:
                self.status.config(
                    text=f"Searching PDB for {n} ({i}/{t})..."
                )
            )

            structures = self.search_pdb(
                name,
                full_name
            )

            if structures:

                for structure in structures:

                    result = {
                        **target,
                        **structure
                    }

                    self.results.append(result)

                    self.root.after(
                        0,
                        lambda r=result: self.display_result(r)
                    )

            else:

                result = {
                    **target,
                    "pdb_id": "No match found",
                    "title": "No experimental structure retrieved",
                    "method": "Not available",
                    "resolution": "Not available"
                }

                self.results.append(result)

                self.root.after(
                    0,
                    lambda r=result: self.display_result(r)
                )

        self.root.after(0, self.search_completed)

    # ----------------------------------
    # DISPLAY RESULTS
    # ----------------------------------

    def display_result(self, result):

        self.table.insert(
            "",
            tk.END,
            values=(
                result["target"],
                result["type"],
                result["pdb_id"],
                result["title"],
                result["method"],
                result["resolution"]
            )
        )

    # ----------------------------------
    # COMPLETION
    # ----------------------------------

    def search_completed(self):

        self.status.config(
            text=f"Completed: {len(self.targets)} targets searched"
        )

        if not self.results:
            messagebox.showinfo(
                "Completed",
                "No PDB results were retrieved."
            )
            return

        answer = messagebox.askyesno(
            "Search Completed",
            f"Identified targets: {len(self.targets)}\n"
            f"Structure records: {len(self.results)}\n\n"
            "Would you like to download the results?"
        )

        if answer:
            self.download_results()
        else:
            self.status.config(
                text="Results displayed. Download skipped."
            )

        self.download_button.config(state=tk.NORMAL)

    # ----------------------------------
    # DOWNLOAD
    # ----------------------------------

    def download_results(self):

        if not self.results:
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile="Drug_Target_PDB_Results.csv",
            filetypes=[
                ("CSV Files", "*.csv")
            ]
        )

        if not path:
            return

        try:

            fields = [
                "target",
                "full_name",
                "type",
                "pdb_id",
                "title",
                "method",
                "resolution",
                "context"
            ]

            with open(
                path,
                "w",
                newline="",
                encoding="utf-8-sig"
            ) as file:

                writer = csv.DictWriter(
                    file,
                    fieldnames=fields
                )

                writer.writeheader()

                writer.writerows(self.results)

            messagebox.showinfo(
                "Download Complete",
                "Results saved successfully!"
            )

        except Exception as error:

            messagebox.showerror(
                "Download Error",
                str(error)
            )


# ----------------------------------
# RUN APPLICATION
# ----------------------------------

if __name__ == "__main__":

    root = tk.Tk()

    app = DrugTargetExtractor(root)

    root.mainloop()
