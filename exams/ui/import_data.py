"""
Import SPPU Data - Namelist, Timetable CSV/Excel import
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from database import get_all, insert, query, execute, get_connection
from utils import today_str


class ImportDataFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        ttk.Label(self, text="Import SPPU Data", style="Header.TLabel").pack(anchor="w", pady=(10, 5))

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        self._tab_namelist()
        self._tab_timetable()
        self._tab_demo()

    def refresh(self):
        self._refresh_session()

    def _refresh_session(self):
        sessions = get_all("exam_sessions")
        for attr in ["nl_session", "tt_session"]:
            combo = getattr(self, attr, None)
            if combo and sessions:
                combo["values"] = [f"{s['id']} - {s['name']} ({s['start_time']}-{s['end_time']})" for s in sessions]
                if combo.get() == "" and sessions:
                    combo.set(f"{sessions[0]['id']} - {sessions[0]['name']} ({sessions[0]['start_time']}-{sessions[0]['end_time']})")

    def _tab_namelist(self):
        f = ttk.Frame(self.notebook)
        self.notebook.add(f, text="Namelist Import")

        inp = ttk.LabelFrame(f, text="SPPU Namelist Import", padding=10)
        inp.pack(fill="x", padx=5, pady=5)

        ttk.Label(inp, text="Import from CSV/Excel file with columns: PRN, Student Name, Course Code, Semester, Subject Code, Exam Date").pack(anchor="w")

        ef = ttk.Frame(inp)
        ef.pack(fill="x", pady=5)
        ttk.Label(ef, text="Session:").pack(side="left")
        self.nl_session = ttk.Combobox(ef, width=30)
        self.nl_session.pack(side="left", padx=5)

        bf = ttk.Frame(inp)
        bf.pack(fill="x", pady=5)
        ttk.Button(bf, text="Select File & Import", command=self._import_namelist).pack(side="left", padx=5)
        ttk.Button(bf, text="Download Template", command=self._download_namelist_template).pack(side="left", padx=5)
        ttk.Button(bf, text="Clear All Namelist", command=self._clear_namelist).pack(side="left", padx=5)

        self.nltree = ttk.Treeview(f, columns=("prn","name","course","sem","subj","date"), show="headings", height=12)
        self.nltree.pack(fill="both", expand=True, padx=5, pady=5)
        for ci,(c,h,w) in enumerate([("prn","PRN",120),("name","Student Name",220),("course","Course",80),
                                       ("sem","Sem",50),("subj","Sub Code",100),("date","Exam Date",100)]):
            self.nltree.heading(c, text=h); self.nltree.column(c, width=w)

        self._refresh_namelist_tree()

    def _refresh_namelist_tree(self):
        self.nltree.delete(*self.nltree.get_children())
        rows = query("SELECT prn, student_name, subject_code, exam_date FROM namelist ORDER BY subject_code, prn")
        for r in rows:
            self.nltree.insert("", "end", values=(r["prn"],r["student_name"],"", "", r["subject_code"],r["exam_date"] or ""))

    def _import_namelist(self):
        fp = filedialog.askopenfilename(filetypes=[("Excel/CSV files", "*.xlsx *.xls *.csv"), ("All files", "*.*")])
        if not fp: return
        try:
            import pandas as pd
            if fp.endswith(".csv"):
                df = pd.read_csv(fp)
            else:
                df = pd.read_excel(fp)

            sess_id = int(self.nl_session.get().split(" - ")[0]) if self.nl_session.get() else 1
            count = 0
            for _, row in df.iterrows():
                insert("namelist", {
                    "prn": str(row.get("PRN", "")).strip(),
                    "student_name": str(row.get("Student Name", "")).strip(),
                    "subject_code": str(row.get("Subject Code", "")).strip(),
                    "exam_date": str(row.get("Exam Date", "")).strip(),
                    "session_id": sess_id,
                })
                count += 1
            self._refresh_namelist_tree()
            messagebox.showinfo("Success", f"Imported {count} records")
        except Exception as e:
            messagebox.showerror("Import Error", str(e))

    def _download_namelist_template(self):
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Namelist Template"
        ws.append(["PRN", "Student Name", "Course Code", "Semester", "Subject Code", "Exam Date"])
        ws.append(["72001234", "Rahul Sharma", "BSC", "3", "CH-301", "15-11-2025"])
        ws.append(["72001235", "Priya Patil", "BSC", "3", "CH-301", "15-11-2025"])
        fp = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")], initialfile="SPPU_Namelist_Template.xlsx")
        if fp:
            wb.save(fp)
            messagebox.showinfo("Done", f"Template saved to {fp}")

    def _clear_namelist(self):
        if messagebox.askyesno("Confirm", "Delete ALL namelist data?"):
            execute("DELETE FROM namelist")
            self._refresh_namelist_tree()

    def _tab_timetable(self):
        f = ttk.Frame(self.notebook)
        self.notebook.add(f, text="Timetable Import")

        inp = ttk.LabelFrame(f, text="SPPU Timetable Import", padding=10)
        inp.pack(fill="x", padx=5, pady=5)
        ttk.Label(inp, text="Import exam schedule: Subject Code, Exam Date, Session").pack(anchor="w")

        ef = ttk.Frame(inp)
        ef.pack(fill="x", pady=5)
        ttk.Label(ef, text="Session:").pack(side="left")
        self.tt_session = ttk.Combobox(ef, width=30)
        self.tt_session.pack(side="left", padx=5)

        bf = ttk.Frame(inp)
        bf.pack(fill="x", pady=5)
        ttk.Button(bf, text="Import Timetable", command=self._import_timetable).pack(side="left", padx=5)
        ttk.Button(bf, text="Quick Add Row", command=self._quick_add_tt).pack(side="left", padx=5)
        ttk.Button(bf, text="Clear Timetable", command=self._clear_tt).pack(side="left", padx=5)

        # Quick add fields
        qf = ttk.Frame(f)
        qf.pack(fill="x", padx=5, pady=3)
        ttk.Label(qf, text="Sub Code:").pack(side="left")
        self.tt_code = ttk.Entry(qf, width=15)
        self.tt_code.pack(side="left", padx=3)
        ttk.Label(qf, text="Date:").pack(side="left")
        self.tt_date = ttk.Entry(qf, width=12)
        self.tt_date.pack(side="left", padx=3)
        self.tt_date.insert(0, today_str())

        self.tttree = ttk.Treeview(f, columns=("id","subj","date","session"), show="headings", height=10)
        self.tttree.pack(fill="both", expand=True, padx=5, pady=5)
        for ci,(c,h,w) in enumerate([("id","ID",30),("subj","Subject Code",150),("date","Exam Date",120),("session","Session",200)]):
            self.tttree.heading(c, text=h); self.tttree.column(c, width=w)
        self._refresh_tt_tree()

    def _refresh_tt_tree(self):
        self.tttree.delete(*self.tttree.get_children())
        rows = query("SELECT t.id, t.subject_code, t.exam_date, s.name FROM timetable t JOIN exam_sessions s ON t.session_id=s.id ORDER BY t.exam_date, s.start_time")
        for r in rows:
            self.tttree.insert("", "end", values=(r["id"],r["subject_code"],r["exam_date"],r["name"]))

    def _import_timetable(self):
        fp = filedialog.askopenfilename(filetypes=[("Excel/CSV files", "*.xlsx *.xls *.csv")])
        if not fp: return
        try:
            import pandas as pd
            df = pd.read_csv(fp) if fp.endswith(".csv") else pd.read_excel(fp)
            sess_id = int(self.tt_session.get().split(" - ")[0]) if self.tt_session.get() else 1
            count = 0
            for _, row in df.iterrows():
                insert("timetable", {
                    "subject_code": str(row.get("Subject Code", "")).strip(),
                    "exam_date": str(row.get("Exam Date", "")).strip(),
                    "session_id": sess_id,
                    "acad_year_id": 1,
                })
                count += 1
            self._refresh_tt_tree()
            messagebox.showinfo("Success", f"Imported {count} records")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _quick_add_tt(self):
        code = self.tt_code.get().strip()
        date = self.tt_date.get().strip()
        if not code or not date: return
        sess_id = int(self.tt_session.get().split(" - ")[0]) if self.tt_session.get() else 1
        insert("timetable", {"subject_code": code, "exam_date": date, "session_id": sess_id, "acad_year_id": 1})
        self._refresh_tt_tree()
        self.tt_code.delete(0, "end")

    def _clear_tt(self):
        if messagebox.askyesno("Confirm", "Delete ALL timetable entries?"):
            execute("DELETE FROM timetable")
            self._refresh_tt_tree()

    def _tab_demo(self):
        f = ttk.Frame(self.notebook)
        self.notebook.add(f, text="Demo Data")

        lf = ttk.LabelFrame(f, text="Generate Demo Data for Testing", padding=15)
        lf.pack(expand=True, padx=40, pady=40)

        ttk.Label(lf, text="Quickly populate demo data to test all features",
                  font=("Segoe UI", 12)).pack(pady=10)

        ttk.Button(lf, text="Load Demo Subjects (BSc, BCom, BA)",
                   command=self._load_demo_subjects).pack(pady=8, fill="x")
        ttk.Button(lf, text="Load Demo Rooms & Blocks",
                   command=self._load_demo_rooms).pack(pady=8, fill="x")
        ttk.Button(lf, text="Load Demo Timetable (3 days, 5 papers/day)",
                   command=self._load_demo_timetable).pack(pady=8, fill="x")
        ttk.Button(lf, text="Load Demo Namelist (100 students per subject)",
                   command=self._load_demo_namelist).pack(pady=8, fill="x")
        ttk.Button(lf, text="RESET ALL DATA",
                   command=self._reset_all).pack(pady=15, fill="x")

    def _load_demo_subjects(self):
        courses_data = [
            ("BSC", "Bachelor of Science", "Science & Technology", 3),
            ("BCOM", "Bachelor of Commerce", "Commerce & Management", 3),
            ("BA", "Bachelor of Arts", "Humanities", 3),
        ]
        subjects_data = [
            ("MTC-301","Mathematics Paper 1","BSC",1,3,"Theory"),
            ("MTC-302","Mathematics Paper 2","BSC",2,3,"Theory"),
            ("CH-301","Chemistry Paper 1","BSC",1,3,"Theory"),
            ("CH-302","Chemistry Paper 2","BSC",2,3,"Theory"),
            ("PHY-301","Physics Paper 1","BSC",1,3,"Theory"),
            ("PHY-302","Physics Paper 2","BSC",2,3,"Theory"),
            ("BOT-301","Botany Paper 1","BSC",1,3,"Theory"),
            ("ZOO-301","Zoology Paper 1","BSC",1,3,"Theory"),
            ("COMP-101","Accountancy Paper 1","BCOM",1,3,"Theory"),
            ("COMP-201","Business Economics","BCOM",1,3,"Theory"),
            ("COMP-301","Cost Accounting","BCOM",2,3,"Theory"),
            ("BA-ENG-101","English Literature","BA",1,3,"Theory"),
            ("BA-ECO-201","Economics","BA",2,3,"Theory"),
            ("BA-MAR-101","Marathi","BA",1,3,"Theory"),
            ("CH-303","Chemistry Practical","BSC",3,3,"Practical"),
            ("PHY-303","Physics Practical","BSC",3,3,"Practical"),
        ]
        for code, name, fac, dur in courses_data:
            existing = query("SELECT id FROM courses WHERE code=?", (code,))
            if not existing:
                insert("courses", {"code": code, "name": name, "faculty": fac, "duration_years": dur})
        for scode, sname, ccode, pno, sem, stype in subjects_data:
            existing = query("SELECT id FROM subjects WHERE code=?", (scode,))
            if not existing:
                crs = query("SELECT id FROM courses WHERE code=?", (ccode,))
                if crs:
                    insert("subjects", {"code":scode,"name":sname,"course_id":crs[0]["id"],
                                        "paper_no":pno,"sem_id":sem,"type":stype,"credits":4})
        # setup semesters
        for c in get_all("courses"):
            for sem_no in range(1, c["duration_years"] * 2 + 1):
                existing = query("SELECT id FROM semesters WHERE course_id=? AND semester_no=?", (c["id"], sem_no))
                if not existing:
                    insert("semesters", {"course_id": c["id"], "semester_no": sem_no})
        messagebox.showinfo("Done", "Demo courses and subjects loaded")

    def _load_demo_rooms(self):
        blocks = [("Block A","Ground"),("Block B","Ground"),("Block C","First")]
        rooms = [
            ("A-101", "Block A", 40, 20), ("A-102", "Block A", 40, 20), ("A-103", "Block A", 40, 20),
            ("A-104", "Block A", 40, 20), ("A-105", "Block A", 40, 20),
            ("B-101", "Block B", 60, 30), ("B-102", "Block B", 60, 30),
            ("B-103", "Block B", 60, 30), ("B-104", "Block B", 60, 30),
            ("Seminar Hall", "Block C", 100, 50), ("Conference Room", "Block C", 40, 20),
        ]
        for bname, bfloor in blocks:
            if not query("SELECT id FROM blocks WHERE name=?", (bname,)):
                insert("blocks", {"name": bname, "floor": bfloor})
        for rname, blk, cap, bench in rooms:
            if not query("SELECT id FROM rooms WHERE name=?", (rname,)):
                b = query("SELECT id FROM blocks WHERE name=?", (blk,))
                if b:
                    insert("rooms", {"name":rname,"block_id":b[0]["id"],"capacity":cap,"bench_count":bench})
        messagebox.showinfo("Done", "Demo rooms loaded")

    def _load_demo_timetable(self):
        if not query("SELECT id FROM exam_sessions"):
            execute("INSERT INTO exam_sessions (name, start_time, end_time) VALUES ('Morning','10:00','13:00'),('Afternoon','14:00','17:00')")
        theory = [r["code"] for r in query("SELECT code FROM subjects WHERE type='Theory'")]
        if not theory: return messagebox.showwarning("First", "Load demo subjects first")
        dates = ["15-11-2025", "16-11-2025", "17-11-2025"]
        import itertools
        subjs = list(itertools.islice(itertools.cycle(theory), len(dates) * 5))
        for i, sc in enumerate(subjs):
            day_idx = i // 5
            sess_idx = i % 2
            insert("timetable", {"subject_code": sc, "exam_date": dates[day_idx],
                                 "session_id": sess_idx + 1, "acad_year_id": 1})
        messagebox.showinfo("Done", f"Demo timetable loaded: 3 days, {len(subjs)} papers")

    def _load_demo_namelist(self):
        theory = [r for r in query("SELECT s.code, c.code as course_code, s.sem_id FROM subjects s JOIN courses c ON s.course_id=c.id WHERE s.type='Theory'")]
        if not theory:
            return messagebox.showwarning("First", "Load demo subjects first")
        timetable = query("SELECT subject_code, exam_date FROM timetable ORDER BY exam_date")
        names_pool = ["Rahul","Priya","Amit","Neha","Sachin","Pooja","Vikas","Anjali","Rohit","Deepa",
                      "Siddharth","Kavita","Rajesh","Meena","Sunil","Geeta","Mahesh","Sonali","Nitin","Shweta",
                      "Abhishek","Rupali","Ganesh","Manisha","Dinesh","Lata","Prakash","Radha","Suresh","Nandini",
                      "Manoj","Asha","Vijay","Jyoti","Sanjay","Rekha","Ajay","Seema","Ravi","Kiran"]
        count = 0
        for tt in timetable:
            subj = next((t for t in theory if t["code"] == tt["subject_code"]), theory[0])
            for i in range(40):
                prn = f"72{subj['course_code']}{i+100:04d}"
                insert("namelist", {
                    "prn": prn, "student_name": f"{names_pool[i % len(names_pool)]} {i+1}",
                    "subject_code": tt["subject_code"], "exam_date": tt["exam_date"],
                    "session_id": 1
                })
                count += 1
        messagebox.showinfo("Done", f"Demo namelist loaded: {count} records")

    def _reset_all(self):
        if messagebox.askyesno("WARNING", "Delete ALL exam data? This cannot be undone!"):
            tables = ["seating","staff_duty","attendance","qp_distribution","qp_inventory",
                      "namelist","timetable","internal_marks","subjects","rooms","blocks","courses","semesters"]
            for t in tables:
                execute(f"DELETE FROM {t}")
            messagebox.showinfo("Done", "All data cleared. Demo data can be reloaded.")
