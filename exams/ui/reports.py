"""
Reports Module - All printable reports for the exam management system
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from database import get_all, query
from utils import export_to_excel


class ReportsFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        ttk.Label(self, text="Reports & Exports", style="Header.TLabel").pack(anchor="w", pady=(10, 5))

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        self._tab_subject_summary()
        self._tab_student_count()
        self._tab_duty_report()
        self._tab_seating_report()
        self._tab_export()

    def refresh(self):
        pass

    def _tab_subject_summary(self):
        f = ttk.Frame(self.notebook)
        self.notebook.add(f, text="Subject Summary")

        ttk.Label(f, text="Subject-wise Student Count & Room Allocation",
                  font=("Segoe UI", 11, "bold")).pack(pady=8)

        ttk.Button(f, text="Generate Summary", command=self._gen_subj_summary).pack(pady=5)
        ttk.Button(f, text="Export to Excel", command=lambda: self._export_tree(self.sum_tree, "Subject_Summary")).pack(pady=5)

        self.sum_tree = ttk.Treeview(f, columns=("subj","sname","total","seated","unseated","rooms"), show="headings", height=14)
        self.sum_tree.pack(fill="both", expand=True, padx=5, pady=5)
        for ci,(c,h,w) in enumerate([("subj","Subject Code",120),("sname","Subject Name",220),("total","Total Students",100),
                                       ("seated","Seated",80),("unseated","Unseated",80),("rooms","Rooms Used",120)]):
            self.sum_tree.heading(c, text=h); self.sum_tree.column(c, width=w)

    def _gen_subj_summary(self):
        self.sum_tree.delete(*self.sum_tree.get_children())
        rows = query("""
            SELECT nl.subject_code, s.name as sname, COUNT(DISTINCT nl.prn) as total,
                   COUNT(DISTINCT se.prn) as seated
            FROM namelist nl
            LEFT JOIN subjects s ON nl.subject_code = s.code
            LEFT JOIN seating se ON nl.prn = se.prn AND nl.subject_code = se.subject_code
            GROUP BY nl.subject_code
            ORDER BY nl.subject_code
        """)
        for r in rows:
            total = r["total"]
            seated = r["seated"] if r["seated"] else 0
            unseated = total - seated
            rooms_row = query("""
                SELECT DISTINCT r.name FROM seating s
                JOIN rooms r ON s.room_id = r.id
                WHERE s.subject_code=?
            """, (r["subject_code"],))
            room_list = ",".join([x["name"] for x in rooms_row]) if rooms_row else "None"
            self.sum_tree.insert("", "end", values=(r["subject_code"], r["sname"] or "", total, seated, unseated, room_list))

    def _tab_student_count(self):
        f = ttk.Frame(self.notebook)
        self.notebook.add(f, text="Day-wise Summary")

        ttk.Label(f, text="Exam Day-wise Student Count (for Block Planning)",
                  font=("Segoe UI", 11, "bold")).pack(pady=8)

        ttk.Button(f, text="Generate", command=self._gen_day_summary).pack(pady=5)
        ttk.Button(f, text="Export", command=lambda: self._export_tree(self.day_tree, "Day_Summary")).pack(pady=5)

        self.day_tree = ttk.Treeview(f, columns=("date","session","papers","students","rooms"), show="headings", height=14)
        self.day_tree.pack(fill="both", expand=True, padx=5, pady=5)
        for ci,(c,h,w) in enumerate([("date","Date",120),("session","Session",100),("papers","Papers",80),
                                       ("students","Students",100),("rooms","Rooms Used",100)]):
            self.day_tree.heading(c, text=h); self.day_tree.column(c, width=w)

    def _gen_day_summary(self):
        self.day_tree.delete(*self.day_tree.get_children())
        sessions = get_all("exam_sessions")
        dates = query("SELECT DISTINCT exam_date FROM timetable ORDER BY exam_date")
        for d in dates:
            edate = d["exam_date"]
            for sess in sessions:
                papers = query("""
                    SELECT COUNT(DISTINCT t.subject_code) as cnt FROM timetable t
                    WHERE t.exam_date=? AND t.session_id=?
                """, (edate, sess["id"]))
                pc = papers[0]["cnt"] if papers else 0
                if pc == 0:
                    continue
                students = query("""
                    SELECT COUNT(DISTINCT s.prn) as cnt FROM seating s
                    WHERE s.exam_date=? AND s.session_id=?
                """, (edate, sess["id"]))
                sc = students[0]["cnt"] if students else 0
                rooms = query("""
                    SELECT COUNT(DISTINCT room_id) as cnt FROM seating
                    WHERE exam_date=? AND session_id=?
                """, (edate, sess["id"]))
                rc = rooms[0]["cnt"] if rooms else 0
                self.day_tree.insert("", "end", values=(edate, sess["name"], pc, sc, rc))

    def _tab_duty_report(self):
        f = ttk.Frame(self.notebook)
        self.notebook.add(f, text="Staff Duty Summary")

        ttk.Label(f, text="Staff Duty Summary - Who's assigned where",
                  font=("Segoe UI", 11, "bold")).pack(pady=8)

        ttk.Button(f, text="Generate", command=self._gen_duty_report).pack(pady=5)
        ttk.Button(f, text="Export", command=lambda: self._export_tree(self.dut_tree, "Duty_Summary")).pack(pady=5)

        self.dut_tree = ttk.Treeview(f, columns=("staff","role","date","session","room","subject"), show="headings", height=14)
        self.dut_tree.pack(fill="both", expand=True, padx=5, pady=5)
        for ci,(c,h,w) in enumerate([("staff","Staff Name",200),("role","Role",140),("date","Date",100),
                                       ("session","Session",100),("room","Room",120),("subject","Subject",140)]):
            self.dut_tree.heading(c, text=h); self.dut_tree.column(c, width=w)

    def _gen_duty_report(self):
        self.dut_tree.delete(*self.dut_tree.get_children())
        rows = query("""
            SELECT s.name as staff_name, sd.role, sd.exam_date,
                   es.name as session_name, r.name as room, sd.subject_code
            FROM staff_duty sd
            LEFT JOIN staff s ON sd.staff_id = s.id
            LEFT JOIN exam_sessions es ON sd.session_id = es.id
            LEFT JOIN rooms r ON sd.room_id = r.id
            ORDER BY sd.exam_date, es.start_time, sd.role, s.name
        """)
        for r in rows:
            self.dut_tree.insert("", "end", values=(r["staff_name"] or "", r["role"] or "",
                                                     r["exam_date"] or "", r["session_name"] or "",
                                                     r["room"] or "", r["subject_code"] or ""))

    def _tab_seating_report(self):
        f = ttk.Frame(self.notebook)
        self.notebook.add(f, text="Seating Report")

        ttk.Label(f, text="Complete Seating Report - All Subjects",
                  font=("Segoe UI", 11, "bold")).pack(pady=8)

        ttk.Button(f, text="Generate", command=self._gen_seating_report).pack(pady=5)
        ttk.Button(f, text="Export All", command=lambda: self._export_tree(self.sea_tree, "Seating_Report")).pack(pady=5)

        self.sea_tree = ttk.Treeview(f, columns=("subj","date","session","room","prn","name","seat"), show="headings", height=14)
        self.sea_tree.pack(fill="both", expand=True, padx=5, pady=5)
        for ci,(c,h,w) in enumerate([("subj","Subject",120),("date","Date",100),("session","Session",100),
                                       ("room","Room",120),("prn","PRN",120),("name","Student",200),("seat","Seat",80)]):
            self.sea_tree.heading(c, text=h); self.sea_tree.column(c, width=w)

    def _gen_seating_report(self):
        self.sea_tree.delete(*self.sea_tree.get_children())
        rows = query("""
            SELECT s.subject_code, s.exam_date, es.name as session_name,
                   r.name as room, s.prn, n.student_name, s.seat_no
            FROM seating s
            JOIN rooms r ON s.room_id = r.id
            JOIN namelist n ON s.prn=n.prn AND s.subject_code=n.subject_code
            LEFT JOIN exam_sessions es ON s.session_id = es.id
            ORDER BY s.subject_code, s.exam_date, r.name, s.seat_no
        """)
        for r in rows:
            self.sea_tree.insert("", "end", values=(r["subject_code"], r["exam_date"], r["session_name"] or "",
                                                     r["room"], r["prn"], r["student_name"], r["seat_no"]))

    def _tab_export(self):
        f = ttk.Frame(self.notebook)
        self.notebook.add(f, text="Bulk Export")

        ttk.Label(f, text="Bulk Export - Download all data in Excel format",
                  font=("Segoe UI", 11, "bold")).pack(pady=10)

        exports = [
            ("Export Courses & Subjects", "courses_subjects"),
            ("Export Rooms & Blocks", "rooms_blocks"),
            ("Export All Staff", "staff_list"),
            ("Export Complete Namelist", "namelist_full"),
            ("Export All Internal Marks", "all_internal_marks"),
            ("Export QP Inventory", "qp_inventory_report"),
            ("Export Daily Summary (TXT)", "daily_summary_txt"),
        ]

        for text, key in exports:
            ttk.Button(f, text=text, command=lambda k=key: self._bulk_export(k)).pack(pady=5, fill="x", padx=80)

    def _bulk_export(self, key):
        try:
            fp = filedialog.askdirectory(title="Select output folder")
            if not fp:
                return
            import os

            if key == "courses_subjects":
                courses = query("SELECT c.code, c.name, c.faculty, c.duration_years FROM courses c")
                subjects = query("SELECT s.code as subject_code, s.name as subject_name, c.code as course_code, s.type, s.credits FROM subjects s JOIN courses c ON s.course_id=c.id")
                export_to_excel(courses, ["code","name","faculty","duration_years"], os.path.join(fp, "courses.xlsx"))
                export_to_excel(subjects, ["subject_code","subject_name","course_code","type","credits"], os.path.join(fp, "subjects.xlsx"))
                messagebox.showinfo("Done", "Exported courses.xlsx and subjects.xlsx")

            elif key == "rooms_blocks":
                blocks = get_all("blocks")
                rooms = query("SELECT r.name as room, b.name as block, r.capacity, r.bench_count, b.floor FROM rooms r JOIN blocks b ON r.block_id=b.id")
                export_to_excel(blocks, ["id","name","floor"], os.path.join(fp, "blocks.xlsx"))
                export_to_excel(rooms, ["room","block","capacity","bench_count","floor"], os.path.join(fp, "rooms.xlsx"))
                messagebox.showinfo("Done", "Exported rooms and blocks")

            elif key == "staff_list":
                staff = get_all("staff")
                export_to_excel(staff, ["id","name","designation","department","mobile","email","role"], os.path.join(fp, "staff.xlsx"))
                messagebox.showinfo("Done", "Exported staff.xlsx")

            elif key == "namelist_full":
                rows = query("SELECT * FROM namelist ORDER BY subject_code, prn")
                export_to_excel(rows, ["prn","student_name","subject_code","exam_date","session_id"], os.path.join(fp, "namelist.xlsx"))
                messagebox.showinfo("Done", f"Exported {len(rows)} records")

            elif key == "all_internal_marks":
                rows = query("""
                    SELECT im.prn, n.student_name, im.subject_code, im.theory_ia, im.practical,
                           im.oral, im.project, im.termwork, im.attendance_pct, im.eligible
                    FROM internal_marks im LEFT JOIN namelist n ON im.prn=n.prn
                    ORDER BY im.subject_code, im.prn
                """)
                export_to_excel(rows, ["prn","student_name","subject_code","theory_ia","practical","oral","project","termwork","attendance_pct","eligible"], os.path.join(fp, "internal_marks.xlsx"))
                messagebox.showinfo("Done", f"Exported {len(rows)} records")

            elif key == "qp_inventory_report":
                rows = query("""
                    SELECT qi.*, r.name as room FROM qp_inventory qi
                    LEFT JOIN qp_distribution qd ON qi.id=qd.qp_id
                    LEFT JOIN rooms r ON qd.room_id=r.id
                """)
                export_to_excel(rows, ["subject_code","exam_date","total_received","sealed_packs","distributed","balance"], os.path.join(fp, "qp_inventory.xlsx"))
                messagebox.showinfo("Done", "Exported QP inventory")

            elif key == "daily_summary_txt":
                from ui.daily_dashboard import DailyDashboardFrame
                dframe = self.app.frames.get("DailyDashboardFrame")
                if dframe:
                    with open(os.path.join(fp, "daily_summary.txt"), "w", encoding="utf-8") as f:
                        f.write(dframe.dash_text.get("1.0", "end"))
                    messagebox.showinfo("Done", "Exported daily_summary.txt")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _export_tree(self, tree, name):
        fp = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel","*.xlsx")],
                                          initialfile=f"{name}.xlsx")
        if not fp:
            return
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = name
        headers = [tree.heading(c)["text"] for c in tree["columns"]]
        ws.append(headers)
        for item in tree.get_children():
            ws.append(list(tree.item(item, "values")))
        wb.save(fp)
        messagebox.showinfo("Done", f"Saved to {fp}")
