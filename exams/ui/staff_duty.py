"""
Staff Duty Assignment & Exam Order Generation
SPPU Hierarchy: Principal → CEO → Senior Supervisor → Junior Supervisor → Peon
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from database import get_all, insert, query, execute


class StaffDutyFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        ttk.Label(self, text="Staff Duty - Exam Order", style="Header.TLabel").pack(anchor="w", pady=(10, 5))

        topf = ttk.LabelFrame(self, text="Assign Staff Duty", padding=10)
        topf.pack(fill="x", padx=5, pady=5)

        r1 = ttk.Frame(topf)
        r1.pack(fill="x", pady=3)
        ttk.Label(r1, text="Exam Date:").pack(side="left")
        self.dt_date = ttk.Combobox(r1, width=15)
        self.dt_date.pack(side="left", padx=5)
        ttk.Label(r1, text="Session:").pack(side="left", padx=(20, 0))
        self.dt_session = ttk.Combobox(r1, width=20)
        self.dt_session.pack(side="left", padx=5)

        r2 = ttk.Frame(topf)
        r2.pack(fill="x", pady=5)
        ttk.Button(r2, text="Auto-Assign Duties", command=self._auto_assign).pack(side="left", padx=5)
        ttk.Button(r2, text="Refresh View", command=self._refresh_view).pack(side="left", padx=5)
        ttk.Button(r2, text="Clear Duties for Date", command=self._clear_duties).pack(side="left", padx=5)
        ttk.Button(r2, text="Print Exam Order", command=self._print_exam_order).pack(side="left", padx=5)

        # Staff duty tree
        self.dtree = ttk.Treeview(self, columns=("room","block","subject","junior","senior","peon"), show="headings", height=15)
        self.dtree.pack(fill="both", expand=True, padx=5, pady=5)
        for ci,(c,h,w) in enumerate([("room","Room",100),("block","Block",100),("subject","Subject",200),
                                       ("junior","Junior Supervisor",180),("senior","Senior Supervisor",180),("peon","Peon",150)]):
            self.dtree.heading(c, text=h); self.dtree.column(c, width=w)

    def refresh(self):
        dates = query("SELECT DISTINCT exam_date FROM timetable ORDER BY exam_date")
        self.dt_date["values"] = [d["exam_date"] for d in dates]
        sessions = get_all("exam_sessions")
        self.dt_session["values"] = [f"{s['id']} - {s['name']} ({s['start_time']}-{s['end_time']})" for s in sessions]
        if dates:
            self.dt_date.set(dates[0]["exam_date"])
        if sessions:
            self.dt_session.set(f"{sessions[0]['id']} - {sessions[0]['name']} ({sessions[0]['start_time']}-{sessions[0]['end_time']})")
        self._refresh_view()

    def _get_sess_id(self):
        val = self.dt_session.get()
        return int(val.split(" - ")[0]) if val else 1

    def _refresh_view(self):
        self.dtree.delete(*self.dtree.get_children())
        edate = self.dt_date.get()
        if not edate:
            return
        sess_id = self._get_sess_id()

        duties = query("""
            SELECT r.name as room, b.name as block, sd.subject_code,
                   sd.role, sd.staff_id, s.name as staff_name
            FROM staff_duty sd
            JOIN rooms r ON sd.room_id = r.id
            JOIN blocks b ON r.block_id = b.id
            LEFT JOIN staff s ON sd.staff_id = s.id
            WHERE sd.exam_date = ? AND sd.session_id = ?
            ORDER BY b.name, r.name
        """, (edate, sess_id))

        # Group by room
        from collections import defaultdict
        room_data = defaultdict(lambda: {"block":"", "subject":"", "junior":"", "senior":"", "peon":""})
        for d in duties:
            room_data[d["room"]]["block"] = d["block"]
            room_data[d["room"]]["subject"] = d.get("subject_code","")
            if d["role"] == "Junior Supervisor":
                room_data[d["room"]]["junior"] = d["staff_name"] or f"Staff#{d['staff_id']}"
            elif d["role"] == "Senior Supervisor":
                room_data[d["room"]]["senior"] = d["staff_name"] or f"Staff#{d['staff_id']}"
            elif d["role"] == "Peon":
                room_data[d["room"]]["peon"] = d["staff_name"] or f"Staff#{d['staff_id']}"

        for room, data in sorted(room_data.items()):
            self.dtree.insert("", "end", values=(room, data["block"], data["subject"],
                                                  data["junior"], data["senior"], data["peon"]))

    def _auto_assign(self):
        edate = self.dt_date.get()
        sess_id = self._get_sess_id()
        if not edate:
            return messagebox.showwarning("Missing", "Select exam date")

        if messagebox.askyesno("Confirm", "Auto-assign staff duties for all rooms on this date+session?\nExisting duties will be replaced."):
            execute("DELETE FROM staff_duty WHERE exam_date=? AND session_id=?", (edate, sess_id))

            rooms = get_all("rooms", "name")
            jr_staff = query("SELECT id, name FROM staff WHERE role IN ('Junior Supervisor','Other') AND is_active=1 ORDER BY name")
            sr_staff = query("SELECT id, name FROM staff WHERE role IN ('Senior Supervisor','HOD','Other') AND is_active=1 ORDER BY name")
            peons = query("SELECT id, name FROM staff WHERE role='Peon' AND is_active=1 ORDER BY name")

            if not jr_staff:
                jr_staff = query("SELECT id, name FROM staff WHERE is_active=1 ORDER BY name")
            if not sr_staff:
                sr_staff = [{"id":0,"name":"(To Assign)"}]
            if not peons:
                peons = [{"id":0,"name":"(To Assign)"}]

            # Get subjects for each room from seating
            for i, room in enumerate(rooms):
                subjs = query("SELECT DISTINCT subject_code FROM seating WHERE room_id=? AND exam_date=? AND session_id=?",
                              (room["id"], edate, sess_id))
                scode = subjs[0]["subject_code"] if subjs else "N/A"

                jr = jr_staff[i % len(jr_staff)]
                sr = sr_staff[i // 3 % len(sr_staff)]
                pn = peons[i // 5 % len(peons)]

                blk = query("SELECT block_id FROM rooms WHERE id=?", (room["id"],))
                blk_id = blk[0]["block_id"] if blk else 1

                for role, staff in [("Junior Supervisor", jr), ("Senior Supervisor", sr), ("Peon", pn)]:
                    insert("staff_duty", {
                        "staff_id": staff["id"],
                        "role": role,
                        "room_id": room["id"],
                        "block_id": blk_id,
                        "subject_code": scode,
                        "exam_date": edate,
                        "session_id": sess_id,
                    })

            self._refresh_view()
            messagebox.showinfo("Done", f"Duties assigned for {len(rooms)} rooms")

    def _clear_duties(self):
        edate = self.dt_date.get()
        sess_id = self._get_sess_id()
        if messagebox.askyesno("Confirm", "Clear all duties for this date+session?"):
            execute("DELETE FROM staff_duty WHERE exam_date=? AND session_id=?", (edate, sess_id))
            self._refresh_view()

    def _print_exam_order(self):
        edate = self.dt_date.get()
        sess_id = self._get_sess_id()
        if not edate:
            return

        # Get CEO and Principal
        principal = query("SELECT name FROM staff WHERE role='Principal' LIMIT 1")
        ceo = query("SELECT name FROM staff WHERE role='CEO' LIMIT 1")

        room_duties = self._get_room_duty_data(edate, sess_id)
        if not room_duties:
            return messagebox.showwarning("None", "No duties assigned")

        fp = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text","*.txt")],
                                          initialfile=f"Exam_Order_{edate}.txt")
        if not fp:
            return

        with open(fp, "w", encoding="utf-8") as f:
            f.write("=" * 85 + "\n")
            f.write(f"{'SPPU AFFILIATED COLLEGE - EXAM ORDER':^85}\n")
            f.write("=" * 85 + "\n\n")
            f.write(f"  Exam Date     : {edate}\n")
            f.write(f"  Session       : {self.dt_session.get()}\n")
            f.write(f"  Principal     : {principal[0]['name'] if principal else '_______________'}\n")
            f.write(f"  CEO           : {ceo[0]['name'] if ceo else '_______________'}\n")
            f.write("\n" + "-" * 85 + "\n")
            f.write(f"{'Room':<12}{'Subject':<22}{'Junior Supervisor':<22}{'Senior Supervisor':<22}{'Peon':<12}\n")
            f.write("-" * 85 + "\n")

            for rd in room_duties:
                f.write(f"{rd['room']:<12}{rd['subject'][:20]:<22}{rd['junior'][:20]:<22}{rd['senior'][:20]:<22}{rd['peon'][:10]:<12}\n")

            f.write("-" * 85 + "\n\n")
            f.write("  Principal Signature: ______________     CEO Signature: ______________\n")
            f.write(f"\n  Generated on: {edate}\n")

        messagebox.showinfo("Done", f"Exam Order saved to {fp}")

    def _get_room_duty_data(self, edate, sess_id):
        from collections import defaultdict
        duties = query("""
            SELECT r.name as room, sd.subject_code, sd.role, s.name as staff_name
            FROM staff_duty sd
            JOIN rooms r ON sd.room_id = r.id
            LEFT JOIN staff s ON sd.staff_id = s.id
            WHERE sd.exam_date = ? AND sd.session_id = ?
            ORDER BY r.name
        """, (edate, sess_id))
        room_data = defaultdict(lambda: {"room":"","subject":"","junior":"","senior":"","peon":""})
        for d in duties:
            room_data[d["room"]]["room"] = d["room"]
            room_data[d["room"]]["subject"] = d["subject_code"]
            if d["role"] == "Junior Supervisor":
                room_data[d["room"]]["junior"] = d["staff_name"] or ""
            elif d["role"] == "Senior Supervisor":
                room_data[d["room"]]["senior"] = d["staff_name"] or ""
            elif d["role"] == "Peon":
                room_data[d["room"]]["peon"] = d["staff_name"] or ""
        return [v for v in room_data.values()]
