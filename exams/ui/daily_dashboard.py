"""
Daily Exam Summary Dashboard - Aaj kiti papers, kiti sessions, kiti students
"""

import tkinter as tk
from tkinter import ttk, messagebox
from database import get_all, query


class DailyDashboardFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        ttk.Label(self, text="Dashboard - Daily Exam Summary", style="Header.TLabel").pack(anchor="w", pady=(10, 5))

        self.dash_text = tk.Text(self, font=("Segoe UI", 11), wrap="word", bg="white", fg="#333",
                                  padx=15, pady=15, relief="flat", borderwidth=1)
        self.dash_text.pack(fill="both", expand=True, padx=10, pady=10)

        btnf = ttk.Frame(self)
        btnf.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(btnf, text="Refresh Dashboard", command=self.refresh).pack(side="left", padx=5)
        ttk.Button(btnf, text="Print Dashboard", command=self._print_dashboard).pack(side="left", padx=5)

    def refresh(self):
        self.dash_text.delete("1.0", "end")

        dates = query("SELECT DISTINCT exam_date FROM timetable ORDER BY exam_date")
        if not dates:
            self.dash_text.insert("end", "No exam timetable data. Please import timetable first.\n")
            self.dash_text.insert("end", "\nGo to: Import SPPU Data → Load Demo Timetable")
            return

        self.dash_text.insert("end", "═══════════════════════════════════════════════════════\n")
        self.dash_text.insert("end", "  SPPU EXAM MANAGEMENT - DAILY SUMMARY DASHBOARD\n")
        self.dash_text.insert("end", "═══════════════════════════════════════════════════════\n\n")

        grand_papers = 0
        grand_students = 0

        for d in dates:
            date_str = d["exam_date"]
            self.dash_text.insert("end", f"📅  EXAM DATE: {date_str}\n")
            self.dash_text.insert("end", "───────────────────────────────────────────────────────\n")

            day_papers = 0
            day_students = 0

            for sess in get_all("exam_sessions"):
                papers = query("""
                    SELECT DISTINCT t.subject_code, s.name as sname
                    FROM timetable t
                    LEFT JOIN subjects s ON t.subject_code = s.code
                    WHERE t.exam_date=? AND t.session_id=?
                    ORDER BY t.subject_code
                """, (date_str, sess["id"]))

                if not papers:
                    continue

                self.dash_text.insert("end", f"\n  🕐 {sess['name'].upper()} SESSION ({sess['start_time']} - {sess['end_time']})\n")
                self.dash_text.insert("end", "  ┌──────────┬──────────────────────────────────┬────────┬──────────────────────┐\n")
                self.dash_text.insert("end", "  │ Sub Code │ Subject                          │  Stu   │ Rooms                │\n")
                self.dash_text.insert("end", "  ├──────────┼──────────────────────────────────┼────────┼──────────────────────┤\n")

                for p in papers:
                    code = p["subject_code"]
                    sname = p["sname"] or code

                    student_count = query("SELECT COUNT(*) as cnt FROM namelist WHERE subject_code=? AND exam_date=?",
                                          (code, date_str))
                    stu = student_count[0]["cnt"] if student_count else 0

                    rooms_data = query("""
                        SELECT r.name FROM seating s JOIN rooms r ON s.room_id=r.id
                        WHERE s.subject_code=? AND s.exam_date=? AND s.session_id=?
                        GROUP BY r.name ORDER BY r.name
                    """, (code, date_str, sess["id"]))

                    room_list = ",".join([r["name"] for r in rooms_data]) if rooms_data else "Not assigned"

                    self.dash_text.insert("end",
                        f"  │ {code:<8} │ {sname:<32} │ {stu:<6} │ {room_list:<20} │\n")

                    day_students += stu
                    day_papers += 1

                self.dash_text.insert("end", "  └──────────┴──────────────────────────────────┴────────┴──────────────────────┘\n")

            if day_papers > 0:
                self.dash_text.insert("end", f"\n  ➤ {date_str} TOTAL: {day_papers} Papers | {day_students} Students\n\n")

            grand_papers += day_papers
            grand_students += day_students

        self.dash_text.insert("end", "═══════════════════════════════════════════════════════\n")
        self.dash_text.insert("end", f"  GRAND TOTAL: {grand_papers} Papers | {grand_students} Students\n")
        self.dash_text.insert("end", "═══════════════════════════════════════════════════════\n")

    def _print_dashboard(self):
        from tkinter import filedialog
        fp = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text", "*.txt")],
                                          initialfile="Daily_Exam_Summary.txt")
        if fp:
            with open(fp, "w", encoding="utf-8") as f:
                f.write(self.dash_text.get("1.0", "end"))
            messagebox.showinfo("Done", f"Saved to {fp}")
