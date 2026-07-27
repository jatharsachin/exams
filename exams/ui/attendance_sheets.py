"""
Attendance Sheets - Generate and track per room per session
QP Management - Question Paper inventory and distribution
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from database import get_all, insert, query, execute


class AttendanceFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        ttk.Label(self, text="Attendance Sheets", style="Header.TLabel").pack(anchor="w", pady=(10, 5))
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)
        self._tab_generate()
        self._tab_mark()

    def refresh(self):
        pass

    def _tab_generate(self):
        f = ttk.Frame(self.notebook)
        self.notebook.add(f, text="Generate Sheets")

        topf = ttk.LabelFrame(f, text="Generate Attendance Sheets", padding=10)
        topf.pack(fill="x", padx=5, pady=5)

        r1 = ttk.Frame(topf)
        r1.pack(fill="x", pady=3)
        ttk.Label(r1, text="Exam Date:").pack(side="left")
        self.at_date = ttk.Combobox(r1, width=15)
        self.at_date.pack(side="left", padx=5)

        ttk.Label(r1, text="Room:").pack(side="left", padx=(20, 0))
        self.at_room = ttk.Combobox(r1, width=20)
        self.at_room.pack(side="left", padx=5)

        r2 = ttk.Frame(topf)
        r2.pack(fill="x", pady=5)
        ttk.Button(r2, text="Preview Attendance Sheet", command=self._preview_sheet).pack(side="left", padx=5)
        ttk.Button(r2, text="Print Attendance Sheet", command=self._print_sheet).pack(side="left", padx=5)
        ttk.Button(r2, text="Print All Sheets for Date", command=self._print_all_sheets).pack(side="left", padx=5)

        self.at_text = tk.Text(f, font=("Courier New", 10), bg="white", padx=10, pady=10, height=20)
        self.at_text.pack(fill="both", expand=True, padx=5, pady=5)

    def _tab_mark(self):
        f = ttk.Frame(self.notebook)
        self.notebook.add(f, text="Mark Attendance")

        topf = ttk.LabelFrame(f, text="Mark Student Attendance", padding=10)
        topf.pack(fill="x", padx=5, pady=5)

        r1 = ttk.Frame(topf)
        r1.pack(fill="x", pady=3)
        ttk.Label(r1, text="Exam Date:").pack(side="left")
        self.ma_date = ttk.Combobox(r1, width=15)
        self.ma_date.pack(side="left", padx=5)
        ttk.Label(r1, text="Room:").pack(side="left", padx=(20, 0))
        self.ma_room = ttk.Combobox(r1, width=20)
        self.ma_room.pack(side="left", padx=5)

        r2 = ttk.Frame(topf)
        r2.pack(fill="x", pady=5)
        ttk.Button(r2, text="Load Students", command=self._load_attendance).pack(side="left", padx=5)
        ttk.Button(r2, text="Mark All Present", command=lambda: self._mark_all("Present")).pack(side="left", padx=5)
        ttk.Button(r2, text="Save Attendance", command=self._save_attendance).pack(side="left", padx=5)

        # Attendance tree with check
        colf = ttk.Frame(f)
        colf.pack(fill="both", expand=True, padx=5, pady=5)

        self.att_tree = ttk.Treeview(colf, columns=("id","prn","name","seat","status"), show="headings", height=15)
        self.att_tree.pack(side="left", fill="both", expand=True)
        self.att_tree.heading("id", text="ID"); self.att_tree.column("id", width=0, stretch=False)
        self.att_tree.heading("prn", text="PRN"); self.att_tree.column("prn", width=120)
        self.att_tree.heading("name", text="Student Name"); self.att_tree.column("name", width=220)
        self.att_tree.heading("seat", text="Seat No"); self.att_tree.column("seat", width=80)
        self.att_tree.heading("status", text="Status"); self.att_tree.column("status", width=80)

        scroll = ttk.Scrollbar(colf, orient="vertical", command=self.att_tree.yview)
        scroll.pack(side="right", fill="y")
        self.att_tree.configure(yscrollcommand=scroll.set)

        self.att_tree.bind("<Double-1>", self._toggle_status)

    def refresh(self):
        dates = query("SELECT DISTINCT exam_date FROM seating ORDER BY exam_date")
        self.at_date["values"] = [d["exam_date"] for d in dates]
        self.ma_date["values"] = [d["exam_date"] for d in dates]
        rooms = get_all("rooms", "name")
        self.at_room["values"] = [r["name"] for r in rooms]
        self.ma_room["values"] = [r["name"] for r in rooms]
        if dates:
            self.at_date.set(dates[0]["exam_date"])
            self.ma_date.set(dates[0]["exam_date"])

    def _preview_sheet(self):
        edate = self.at_date.get()
        room = self.at_room.get()
        if not edate or not room:
            return

        self.at_text.delete("1.0", "end")
        rows = query("""
            SELECT s.prn, n.student_name, s.seat_no, s.subject_code
            FROM seating s
            JOIN namelist n ON s.prn=n.prn AND s.subject_code=n.subject_code
            JOIN rooms r ON s.room_id=r.id
            WHERE s.exam_date=? AND r.name=?
            ORDER BY s.bench_no
        """, (edate, room))

        if not rows:
            self.at_text.insert("end", f"No seating data for {room} on {edate}")
            return

        self.at_text.insert("end", "=" * 75 + "\n")
        self.at_text.insert("end", f"{'SPPU EXAM ATTENDANCE SHEET':^75}\n")
        self.at_text.insert("end", "=" * 75 + "\n")
        self.at_text.insert("end", f"  Date: {edate}        Room: {room}        Sub: {rows[0]['subject_code']}\n")
        self.at_text.insert("end", f"  Session: ________    Total: {len(rows)} Students\n")
        self.at_text.insert("end", "-" * 75 + "\n")
        self.at_text.insert("end", f"{'Seat':<10}{'PRN':<14}{'Student Name':<28}{'Signature':<20}{'Status':<10}\n")
        self.at_text.insert("end", "-" * 75 + "\n")
        for r in rows:
            self.at_text.insert("end", f"{r['seat_no']:<10}{r['prn']:<14}{r['student_name']:<28}{'':<20}{'':<10}\n")
        self.at_text.insert("end", "-" * 75 + "\n")
        self.at_text.insert("end", f"\n  Junior Supervisor: _____________   Senior Sup: _____________\n")

    def _print_sheet(self):
        fp = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text","*.txt")],
                                          initialfile=f"Attendance_{self.at_room.get()}.txt")
        if fp:
            with open(fp, "w", encoding="utf-8") as f:
                f.write(self.at_text.get("1.0", "end"))
            messagebox.showinfo("Done", f"Saved to {fp}")

    def _print_all_sheets(self):
        edate = self.at_date.get()
        if not edate:
            return
        rooms_used = query("SELECT DISTINCT r.name FROM seating s JOIN rooms r ON s.room_id=r.id WHERE s.exam_date=?", (edate,))
        fp = filedialog.askdirectory(title="Select output folder")
        if not fp:
            return
        import os
        for room_row in rooms_used:
            room = room_row["name"]
            self.at_room.set(room)
            self._preview_sheet()
            path = os.path.join(fp, f"Attendance_{room}_{edate}.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.at_text.get("1.0", "end"))
        messagebox.showinfo("Done", f"Saved {len(rooms_used)} sheets to {fp}")

    def _load_attendance(self):
        edate = self.ma_date.get()
        room = self.ma_room.get()
        if not edate or not room:
            return messagebox.showwarning("Missing", "Select date and room")

        self.att_tree.delete(*self.att_tree.get_children())
        rows = query("""
            SELECT s.id, s.prn, n.student_name, s.seat_no,
                   COALESCE(a.status, 'Present') as status
            FROM seating s
            JOIN namelist n ON s.prn=n.prn AND s.subject_code=n.subject_code
            JOIN rooms r ON s.room_id=r.id
            LEFT JOIN attendance a ON a.seating_id = s.id
            WHERE s.exam_date=? AND r.name=?
            ORDER BY s.bench_no
        """, (edate, room))
        for r in rows:
            self.att_tree.insert("", "end", values=(r["id"], r["prn"], r["student_name"], r["seat_no"], r["status"]))

    def _toggle_status(self, evt):
        sel = self.att_tree.selection()
        if not sel:
            return
        item = sel[0]
        current = self.att_tree.item(item, "values")[4]
        new_status = "Absent" if current == "Present" else "UFM" if current == "Absent" else "Present"
        vals = list(self.att_tree.item(item, "values"))
        vals[4] = new_status
        self.att_tree.item(item, values=tuple(vals))

    def _mark_all(self, status):
        for item in self.att_tree.get_children():
            vals = list(self.att_tree.item(item, "values"))
            vals[4] = status
            self.att_tree.item(item, values=tuple(vals))

    def _save_attendance(self):
        count = 0
        for item in self.att_tree.get_children():
            vals = self.att_tree.item(item, "values")
            seat_id = vals[0]
            status = vals[4]
            existing = query("SELECT id FROM attendance WHERE seating_id=?", (seat_id,))
            if existing:
                execute("UPDATE attendance SET status=? WHERE seating_id=?", (status, seat_id))
            else:
                insert("attendance", {"seating_id": seat_id, "status": status})
            count += 1
        messagebox.showinfo("Saved", f"Attendance saved for {count} students")


class QPManagementFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        ttk.Label(self, text="Question Paper Management", style="Header.TLabel").pack(anchor="w", pady=(10, 5))

        topf = ttk.LabelFrame(self, text="QP Inventory Entry", padding=10)
        topf.pack(fill="x", padx=5, pady=5)

        r1 = ttk.Frame(topf)
        r1.pack(fill="x", pady=3)
        ttk.Label(r1, text="Subject:").pack(side="left")
        self.qp_subject = ttk.Combobox(r1, width=30)
        self.qp_subject.pack(side="left", padx=5)
        ttk.Label(r1, text="Date:").pack(side="left", padx=(10, 0))
        self.qp_date = ttk.Entry(r1, width=12)
        self.qp_date.pack(side="left", padx=5)
        ttk.Label(r1, text="Total Received:").pack(side="left", padx=(10, 0))
        self.qp_total = ttk.Entry(r1, width=8)
        self.qp_total.pack(side="left", padx=5)
        ttk.Label(r1, text="Sealed Packs:").pack(side="left", padx=(10, 0))
        self.qp_sealed = ttk.Entry(r1, width=8)
        self.qp_sealed.pack(side="left", padx=5)

        r2 = ttk.Frame(topf)
        r2.pack(fill="x", pady=5)
        ttk.Button(r2, text="Add QP Entry", command=self._add_qp).pack(side="left", padx=5)
        ttk.Button(r2, text="Distribute QP to Rooms", command=self._distribute_qp).pack(side="left", padx=5)
        ttk.Button(r2, text="Print QP Distribution Slip", command=self._print_qp_slip).pack(side="left", padx=5)

        self.qp_tree = ttk.Treeview(self, columns=("id","subj","date","recv","sealed","opened","dist","bal"), show="headings", height=12)
        self.qp_tree.pack(fill="both", expand=True, padx=5, pady=5)
        for ci,(c,h,w) in enumerate([("id","ID",30),("subj","Subject",150),("date","Date",100),
                                       ("recv","Recv",60),("sealed","Sealed",60),("opened","Opened",60),
                                       ("dist","Dist",60),("bal","Balance",60)]):
            self.qp_tree.heading(c, text=h); self.qp_tree.column(c, width=w)

        self._refresh_qp()

    def refresh(self):
        subjs = query("SELECT DISTINCT code FROM subjects WHERE type='Theory'")
        self.qp_subject["values"] = [s["code"] for s in subjs]
        self._refresh_qp()

    def _refresh_qp(self):
        self.qp_tree.delete(*self.qp_tree.get_children())
        for q in get_all("qp_inventory"):
            self.qp_tree.insert("", "end", values=(q["id"],q["subject_code"],q["exam_date"],
                                                    q["total_received"],q["sealed_packs"],q["opened_packs"],
                                                    q["distributed"],q["balance"]))

    def _add_qp(self):
        code = self.qp_subject.get()
        edate = self.qp_date.get()
        if not code or not edate:
            return messagebox.showwarning("Missing", "Enter subject and date")
        total = int(self.qp_total.get() or 0)
        sealed = int(self.qp_sealed.get() or 0)
        insert("qp_inventory", {
            "subject_code": code, "exam_date": edate, "session_id": 1,
            "total_received": total, "sealed_packs": sealed,
            "opened_packs": 0, "distributed": 0, "balance": total
        })
        self._refresh_qp()
        messagebox.showinfo("Done", "QP entry added")

    def _distribute_qp(self):
        sel = self.qp_tree.selection()
        if not sel:
            return messagebox.showwarning("Select", "Select a QP inventory row")
        qp_id = self.qp_tree.item(sel[0], "values")[0]
        qp = query("SELECT * FROM qp_inventory WHERE id=?", (qp_id,))
        if not qp:
            return
        qp = qp[0]
        rooms = query("""
            SELECT DISTINCT r.id, r.name, COUNT(s.id) as cnt
            FROM seating s JOIN rooms r ON s.room_id=r.id
            WHERE s.subject_code=? AND s.exam_date=? AND s.session_id=?
            GROUP BY r.name ORDER BY r.name
        """, (qp["subject_code"], qp["exam_date"], qp["session_id"]))
        if not rooms:
            return messagebox.showwarning("None", "No seating data for this subject")

        execute("DELETE FROM qp_distribution WHERE qp_id=?", (qp_id,))
        for room in rooms:
            insert("qp_distribution", {
                "qp_id": qp_id, "room_id": room["id"],
                "student_count": room["cnt"], "qp_issued": room["cnt"],
                "qp_returned": 0, "supervisor_sign": 0
            })
        total_dist = sum(r["cnt"] for r in rooms)
        execute("UPDATE qp_inventory SET distributed=?, balance=total_received-? WHERE id=?",
                (total_dist, total_dist, qp_id))
        self._refresh_qp()
        messagebox.showinfo("Done", f"QP distributed to {len(rooms)} rooms ({total_dist} copies)")

    def _print_qp_slip(self):
        sel = self.qp_tree.selection()
        if not sel:
            return
        qp_id = self.qp_tree.item(sel[0], "values")[0]
        rows = query("""
            SELECT r.name as room, qd.student_count, qd.qp_issued
            FROM qp_distribution qd JOIN rooms r ON qd.room_id=r.id WHERE qd.qp_id=?
        """, (qp_id,))
        if not rows:
            return messagebox.showwarning("None", "No distribution data")
        fp = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text","*.txt")],
                                          initialfile="QP_Distribution_Slip.txt")
        if fp:
            with open(fp, "w", encoding="utf-8") as f:
                f.write("=" * 60 + "\n")
                f.write(f"{'QP DISTRIBUTION SLIP':^60}\n")
                f.write("=" * 60 + "\n")
                f.write(f"{'Room':<20}{'Students':<15}{'QP Issued':<15}{'Supervisor Sign':<20}\n")
                f.write("-" * 60 + "\n")
                for r in rows:
                    f.write(f"{r['room']:<20}{r['student_count']:<15}{r['qp_issued']:<15}{'':<20}\n")
                f.write("-" * 60 + "\n")
            messagebox.showinfo("Done", "QP slip saved")
