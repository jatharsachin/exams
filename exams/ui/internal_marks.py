"""
Internal Marks Module - Theory IA, Practical, Oral, Project, Termwork
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from database import get_all, insert, query, update, execute


class InternalMarksFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        ttk.Label(self, text="Internal Marks Entry", style="Header.TLabel").pack(anchor="w", pady=(10, 5))

        topf = ttk.LabelFrame(self, text="Enter Internal Marks", padding=10)
        topf.pack(fill="x", padx=5, pady=5)

        r1 = ttk.Frame(topf)
        r1.pack(fill="x", pady=3)
        ttk.Label(r1, text="Subject:").pack(side="left")
        self.im_subject = ttk.Combobox(r1, width=35)
        self.im_subject.pack(side="left", padx=5)
        self.im_subject.bind("<<ComboboxSelected>>", lambda e: self._load_marks())

        r2 = ttk.Frame(topf)
        r2.pack(fill="x", pady=5)
        ttk.Label(r2, text="Theory IA:").pack(side="left")
        self.im_theory = ttk.Entry(r2, width=5)
        self.im_theory.pack(side="left", padx=3)
        ttk.Label(r2, text="Practical:").pack(side="left", padx=(10, 0))
        self.im_prac = ttk.Entry(r2, width=5)
        self.im_prac.pack(side="left", padx=3)
        ttk.Label(r2, text="Oral:").pack(side="left", padx=(10, 0))
        self.im_oral = ttk.Entry(r2, width=5)
        self.im_oral.pack(side="left", padx=3)
        ttk.Label(r2, text="Project:").pack(side="left", padx=(10, 0))
        self.im_proj = ttk.Entry(r2, width=5)
        self.im_proj.pack(side="left", padx=3)
        ttk.Label(r2, text="Termwork:").pack(side="left", padx=(10, 0))
        self.im_tw = ttk.Entry(r2, width=5)
        self.im_tw.pack(side="left", padx=3)
        ttk.Label(r2, text="Att%:").pack(side="left", padx=(10, 0))
        self.im_att = ttk.Entry(r2, width=5)
        self.im_att.pack(side="left", padx=3)
        ttk.Button(r2, text="Apply to Selected", command=self._apply_marks).pack(side="left", padx=10)

        # Marks tree
        self.im_tree = ttk.Treeview(self, columns=("id","prn","name","theory","prac","oral","proj","tw","att","elig"),
                                     show="headings", height=15)
        self.im_tree.pack(fill="both", expand=True, padx=5, pady=5)
        for ci,(c,h,w) in enumerate([("id","ID",30),("prn","PRN",120),("name","Student Name",200),
                                       ("theory","Theory IA",80),("prac","Practical",80),("oral","Oral",60),
                                       ("proj","Project",60),("tw","Termwork",70),("att","Att%",60),("elig","Eligible",60)]):
            self.im_tree.heading(c, text=h); self.im_tree.column(c, width=w)

        bf = ttk.Frame(self)
        bf.pack(fill="x", padx=5, pady=5)
        ttk.Button(bf, text="Save All Marks", command=self._save_all).pack(side="left", padx=5)
        ttk.Button(bf, text="Export for SPPU Upload", command=self._export_marks).pack(side="left", padx=5)

    def refresh(self):
        subjs = query("""
            SELECT DISTINCT nl.subject_code, s.name FROM namelist nl
            LEFT JOIN subjects s ON nl.subject_code=s.code
            WHERE s.type='Theory' OR s.type='Practical'
        """)
        self.im_subject["values"] = [f"{r['subject_code']} - {r['name'] or r['subject_code']}" for r in subjs]

    def _get_code(self):
        val = self.im_subject.get()
        return val.split(" - ")[0] if " - " in val else val

    def _load_marks(self):
        code = self._get_code()
        if not code:
            return
        self.im_tree.delete(*self.im_tree.get_children())

        students = query("SELECT DISTINCT prn, student_name FROM namelist WHERE subject_code=? ORDER BY prn", (code,))
        subj = query("SELECT * FROM subjects WHERE code=?", (code,))

        for st in students:
            existing = query("SELECT * FROM internal_marks WHERE prn=? AND subject_code=?", (st["prn"], code))
            e = existing[0] if existing else None
            is_eligible = "Yes" if (e and e.get("eligible", 1)) else ("No" if e and not e.get("eligible") else "N/A")
            if not e:
                insert("internal_marks", {"prn": st["prn"], "subject_code": code})
            self.im_tree.insert("", "end", values=(
                e["id"] if e else 0, st["prn"], st["student_name"],
                e["theory_ia"] if e else 0, e["practical"] if e else 0,
                e["oral"] if e else 0, e["project"] if e else 0,
                e["termwork"] if e else 0, e["attendance_pct"] if e else "75",
                is_eligible
            ))

    def _apply_marks(self):
        sel = self.im_tree.selection()
        if not sel:
            return
        for item in sel:
            vals = list(self.im_tree.item(item, "values"))
            if self.im_theory.get():
                vals[3] = self.im_theory.get()
            if self.im_prac.get():
                vals[4] = self.im_prac.get()
            if self.im_oral.get():
                vals[5] = self.im_oral.get()
            if self.im_proj.get():
                vals[6] = self.im_proj.get()
            if self.im_tw.get():
                vals[7] = self.im_tw.get()
            if self.im_att.get():
                vals[8] = self.im_att.get()
                try:
                    vals[9] = "Yes" if float(self.im_att.get()) >= 75 else "No"
                except:
                    pass
            self.im_tree.item(item, values=tuple(vals))

    def _save_all(self):
        count = 0
        for item in self.im_tree.get_children():
            vals = self.im_tree.item(item, "values")
            row_id = vals[0]
            if row_id and int(row_id) > 0:
                update("internal_marks", {
                    "theory_ia": int(vals[3] or 0),
                    "practical": int(vals[4] or 0),
                    "oral": int(vals[5] or 0),
                    "project": int(vals[6] or 0),
                    "termwork": int(vals[7] or 0),
                    "attendance_pct": float(vals[8] or 75),
                    "eligible": 1 if vals[9] == "Yes" else 0,
                }, int(row_id))
                count += 1
        messagebox.showinfo("Saved", f"Saved {count} records")

    def _export_marks(self):
        code = self._get_code()
        if not code:
            return
        rows = query("""
            SELECT prn, subject_code, theory_ia, practical, oral, project, termwork, attendance_pct, eligible
            FROM internal_marks WHERE subject_code=?
        """, (code,))
        if not rows:
            return messagebox.showwarning("None", "No marks data")
        fp = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel","*.xlsx")],
                                          initialfile=f"Internal_Marks_{code}.xlsx")
        if fp:
            from utils import export_to_excel
            cols = ["prn","subject_code","theory_ia","practical","oral","project","termwork","attendance_pct","eligible"]
            export_to_excel(rows, cols, fp, "Internal Marks")
            messagebox.showinfo("Done", f"Exported to {fp}")
