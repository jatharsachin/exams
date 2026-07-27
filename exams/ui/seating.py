"""
Block Arrangement / Seating Plan - Auto-generate seating per subject
"""

import tkinter as tk
from tkinter import ttk, messagebox
from database import get_all, insert, query, execute
import math


class SeatingFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        ttk.Label(self, text="Block Arrangement - Seating Plan", style="Header.TLabel").pack(anchor="w", pady=(10, 5))

        # Top filters
        topf = ttk.LabelFrame(self, text="Generate Seating Plan", padding=10)
        topf.pack(fill="x", padx=5, pady=5)

        r1 = ttk.Frame(topf)
        r1.pack(fill="x", pady=3)
        ttk.Label(r1, text="Subject:").pack(side="left")
        self.seat_subject = ttk.Combobox(r1, width=40)
        self.seat_subject.pack(side="left", padx=5)
        ttk.Label(r1, text="Exam Date:").pack(side="left", padx=(20, 0))
        self.seat_date = ttk.Entry(r1, width=12)
        self.seat_date.pack(side="left", padx=5)

        r2 = ttk.Frame(topf)
        r2.pack(fill="x", pady=3)
        ttk.Label(r2, text="Session:").pack(side="left")
        self.seat_session = ttk.Combobox(r2, width=20)
        self.seat_session.pack(side="left", padx=5)
        ttk.Label(r2, text="Students:").pack(side="left", padx=(20, 0))
        self.seat_students = ttk.Label(r2, text="0", font=("Segoe UI", 11, "bold"))
        self.seat_students.pack(side="left", padx=5)

        r3 = ttk.Frame(topf)
        r3.pack(fill="x", pady=8)
        ttk.Button(r3, text="🔍 Check Student Count", command=self._check_count).pack(side="left", padx=5)
        ttk.Button(r3, text="Generate Seating Plan", command=self._generate_seating).pack(side="left", padx=5)
        ttk.Button(r3, text="Clear Seating for Subject", command=self._clear_subject_seating).pack(side="left", padx=5)
        ttk.Button(r3, text="Generate All Seating", command=self._generate_all).pack(side="left", padx=5)
        ttk.Button(r3, text="Print Seating Chart", command=self._print_chart).pack(side="left", padx=5)

        # Room allocation result
        self.seat_result = ttk.Treeview(self, columns=("room","block","capacity","allotted","seat_from","seat_to","occ%"),
                                         show="headings", height=6)
        self.seat_result.pack(fill="x", padx=5, pady=5)
        for ci,(c,h,w) in enumerate([("room","Room",120),("block","Block",100),("capacity","Capacity",70),
                                       ("allotted","Allotted",70),("seat_from","From",70),("seat_to","To",70),("occ%","Occ%",60)]):
            self.seat_result.heading(c, text=h); self.seat_result.column(c, width=w)

        # Student list with seat numbers
        self.seat_tree = ttk.Treeview(self, columns=("prn","name","room","seat","bench"), show="headings", height=14)
        self.seat_tree.pack(fill="both", expand=True, padx=5, pady=5)
        for ci,(c,h,w) in enumerate([("prn","PRN",120),("name","Student Name",220),("room","Room",100),
                                       ("seat","Seat No",80),("bench","Bench No",80)]):
            self.seat_tree.heading(c, text=h); self.seat_tree.column(c, width=w)

    def refresh(self):
        subjs = query("SELECT DISTINCT nl.subject_code, s.name FROM namelist nl LEFT JOIN subjects s ON nl.subject_code=s.code")
        self.seat_subject["values"] = [f"{r['subject_code']} - {r['name'] or r['subject_code']}" for r in subjs]
        sessions = get_all("exam_sessions")
        self.seat_session["values"] = [f"{s['id']} - {s['name']} ({s['start_time']}-{s['end_time']})" for s in sessions]
        if sessions:
            self.seat_session.set(f"{sessions[0]['id']} - {sessions[0]['name']} ({sessions[0]['start_time']}-{sessions[0]['end_time']})")

    def _get_subj_code(self):
        val = self.seat_subject.get()
        return val.split(" - ")[0] if " - " in val else val

    def _get_session_id(self):
        val = self.seat_session.get()
        return int(val.split(" - ")[0]) if val else 1

    def _check_count(self):
        code = self._get_subj_code()
        count = query("SELECT COUNT(*) as cnt FROM namelist WHERE subject_code=?", (code,))
        self.seat_students.config(text=str(count[0]["cnt"] if count else 0))

    def _generate_seating(self):
        code = self._get_subj_code()
        edate = self.seat_date.get().strip()
        sess_id = self._get_session_id()
        if not code or not edate:
            return messagebox.showwarning("Missing", "Select subject and enter exam date")

        students = query("SELECT prn, student_name FROM namelist WHERE subject_code=? ORDER BY prn", (code,))
        if not students:
            return messagebox.showwarning("None", "No students in namelist for this subject")

        rooms = get_all("rooms", "name")
        if not rooms:
            return messagebox.showwarning("None", "No rooms defined. Add rooms in Master Setup.")

        # Clear existing seating for this subject+date+session
        execute("DELETE FROM seating WHERE subject_code=? AND exam_date=? AND session_id=?",
                (code, edate, sess_id))

        total = len(students)
        self.seat_result.delete(*self.seat_result.get_children())
        self.seat_students.config(text=str(total))

        allocated = 0
        seat_counter = 1
        for room in rooms:
            if allocated >= total:
                break
            room_cap = room["capacity"]
            to_allot = min(room_cap, total - allocated)
            if to_allot <= 0:
                continue

            from_seat = seat_counter
            to_seat = seat_counter + to_allot - 1
            occ = round(to_allot / room_cap * 100, 1)

            self.seat_result.insert("", "end", values=(
                room["name"], "Block", room_cap, to_allot, from_seat, to_seat, f"{occ}%"
            ))

            for i in range(to_allot):
                si = allocated + i
                if si >= len(students):
                    break
                bench_no = (i // 2) + 1  # alternate: 2 students per bench idea (actual: 1 per bench)
                row_num = int(bench_no)
                seat_label = f"{room['name'][:3]}{row_num:03d}"
                insert("seating", {
                    "prn": students[si]["prn"],
                    "subject_code": code,
                    "exam_date": edate,
                    "session_id": sess_id,
                    "room_id": room["id"],
                    "seat_no": seat_label,
                    "bench_no": bench_no,
                })

            allocated += to_allot
            seat_counter += to_allot

        self._refresh_seat_tree(code, edate, sess_id)
        messagebox.showinfo("Done", f"Seating generated: {total} students in {len(rooms)} rooms")

    def _refresh_seat_tree(self, code, edate, sess_id):
        self.seat_tree.delete(*self.seat_tree.get_children())
        rows = query("""
            SELECT s.prn, n.student_name, r.name as room, s.seat_no, s.bench_no
            FROM seating s
            JOIN namelist n ON s.prn = n.prn AND s.subject_code = n.subject_code
            JOIN rooms r ON s.room_id = r.id
            WHERE s.subject_code=? AND s.exam_date=? AND s.session_id=?
            ORDER BY s.room_id, s.seat_no
        """, (code, edate, sess_id))
        for r in rows:
            self.seat_tree.insert("", "end", values=(r["prn"],r["student_name"],r["room"],r["seat_no"],r["bench_no"]))

    def _clear_subject_seating(self):
        code = self._get_subj_code()
        edate = self.seat_date.get().strip()
        sess_id = self._get_session_id()
        execute("DELETE FROM seating WHERE subject_code=? AND exam_date=? AND session_id=?", (code, edate, sess_id))
        self.seat_result.delete(*self.seat_result.get_children())
        self.seat_tree.delete(*self.seat_tree.get_children())
        self.seat_students.config(text="0")
        messagebox.showinfo("Done", "Seating cleared")

    def _generate_all(self):
        if messagebox.askyesno("Confirm", "Generate seating for ALL subjects in timetable?"):
            tt_entries = query("SELECT DISTINCT subject_code, exam_date, session_id FROM timetable ORDER BY exam_date, session_id")
            if not tt_entries:
                return messagebox.showwarning("None", "No timetable entries")
            total_gen = 0
            for tt in tt_entries:
                students = query("SELECT prn, student_name FROM namelist WHERE subject_code=? AND exam_date=? ORDER BY prn",
                                 (tt["subject_code"], tt["exam_date"]))
                if not students:
                    continue
                rooms = get_all("rooms", "name")
                if not rooms:
                    continue
                execute("DELETE FROM seating WHERE subject_code=? AND exam_date=? AND session_id=?",
                        (tt["subject_code"], tt["exam_date"], tt["session_id"]))
                allocated = 0
                for room in rooms:
                    if allocated >= len(students):
                        break
                    to_allot = min(room["capacity"], len(students) - allocated)
                    for i in range(to_allot):
                        si = allocated + i
                        if si >= len(students):
                            break
                        bench = (i // 2) + 1
                        insert("seating", {
                            "prn": students[si]["prn"], "subject_code": tt["subject_code"],
                            "exam_date": tt["exam_date"], "session_id": tt["session_id"],
                            "room_id": room["id"], "seat_no": f"{room['name'][:3]}{bench:03d}",
                            "bench_no": bench
                        })
                    allocated += to_allot
                total_gen += min(allocated, len(students))
            messagebox.showinfo("Done", f"Generated seating for {total_gen} students across all subjects")

    def _print_chart(self):
        code = self._get_subj_code()
        edate = self.seat_date.get().strip()
        sess_id = self._get_session_id()
        rows = query("""
            SELECT r.name as room, r.capacity, COUNT(s.id) as allotted
            FROM seating s JOIN rooms r ON s.room_id=r.id
            WHERE s.subject_code=? AND s.exam_date=? AND s.session_id=?
            GROUP BY r.name
        """, (code, edate, sess_id))
        if not rows:
            return messagebox.showwarning("None", "No seating data to print")
        from utils import export_to_excel
        import tkinter.filedialog as fd
        fp = fd.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel","*.xlsx")],
                                  initialfile=f"Seating_Chart_{code}.xlsx")
        if fp:
            export_to_excel(rows, ["room", "capacity", "allotted"], fp, "Seating Chart")
            messagebox.showinfo("Done", f"Saved to {fp}")
