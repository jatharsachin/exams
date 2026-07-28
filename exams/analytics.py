"""
Analytics Engine - DuckDB for high-performance reports
"""
import duckdb
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "sppu_exam.db")


def get_analytics():
    return duckdb.connect(DB_PATH, read_only=True)


def exam_summary():
    con = get_analytics()
    try:
        df = con.execute("""
            SELECT t.exam_date, es.name as session,
                   COUNT(DISTINCT s.prn) as students,
                   COUNT(DISTINCT s.room_id) as rooms,
                   COUNT(DISTINCT sd.staff_id) as staff_assigned,
                   SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) as present,
                   SUM(CASE WHEN a.status='Absent' THEN 1 ELSE 0 END) as absent,
                   SUM(CASE WHEN a.status='UFM' THEN 1 ELSE 0 END) as ufm
            FROM timetable t
            JOIN exam_sessions es ON t.session_id=es.id
            LEFT JOIN seating s ON s.exam_date=t.exam_date AND s.session_id=t.session_id
            LEFT JOIN attendance a ON a.seating_id=s.id
            LEFT JOIN staff_duty sd ON sd.exam_date=t.exam_date AND sd.session_id=t.session_id
            GROUP BY t.exam_date, es.name ORDER BY t.exam_date
        """).fetchdf()
        return df.to_dict(orient="records")
    finally:
        con.close()


def course_wise_stats():
    con = get_analytics()
    try:
        df = con.execute("""
            SELECT c.name as course, c.code,
                   COUNT(DISTINCT n.prn) as students,
                   COUNT(DISTINCT s.code) as subjects
            FROM courses c
            LEFT JOIN namelist n ON n.course_id=c.id
            LEFT JOIN subjects s ON s.course_id=c.id
            GROUP BY c.id, c.name, c.code ORDER BY students DESC
        """).fetchdf()
        return df.to_dict(orient="records")
    finally:
        con.close()


def staff_workload():
    con = get_analytics()
    try:
        df = con.execute("""
            SELECT s.name, s.designation, s.role,
                   COUNT(sd.id) as sessions,
                   COALESCE(SUM(sr.amount), 0) as total_remuneration
            FROM staff s
            LEFT JOIN staff_duty sd ON sd.staff_id=s.id
            LEFT JOIN staff_remuneration sr ON sr.staff_id=s.id
            GROUP BY s.id, s.name, s.designation, s.role
            ORDER BY sessions DESC
        """).fetchdf()
        return df.to_dict(orient="records")
    finally:
        con.close()


def room_utilization():
    con = get_analytics()
    try:
        df = con.execute("""
            SELECT r.name as room, b.name as block, r.capacity,
                   COUNT(DISTINCT s.exam_date) as exam_days,
                   AVG(s_cnt.cnt) as avg_students_per_exam
            FROM rooms r
            JOIN blocks b ON r.block_id=b.id
            LEFT JOIN seating s ON s.room_id=r.id
            LEFT JOIN (SELECT room_id, exam_date, COUNT(*) as cnt FROM seating GROUP BY room_id, exam_date) s_cnt
                ON s_cnt.room_id=r.id
            GROUP BY r.id, r.name, b.name, r.capacity
            ORDER BY r.name
        """).fetchdf()
        return df.to_dict(orient="records")
    finally:
        con.close()


def attendance_summary():
    con = get_analytics()
    try:
        df = con.execute("""
            SELECT su.code as subject_code, su.name as subject_name,
                   COUNT(a.id) as total,
                   SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) as present,
                   SUM(CASE WHEN a.status='Absent' THEN 1 ELSE 0 END) as absent,
                   SUM(CASE WHEN a.status='UFM' THEN 1 ELSE 0 END) as ufm,
                   ROUND(100.0*SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END)/COUNT(a.id),1) as pct
            FROM attendance a
            JOIN seating s ON a.seating_id=s.id
            JOIN subjects su ON s.subject_code=su.code
            GROUP BY su.code, su.name ORDER BY su.code
        """).fetchdf()
        return df.to_dict(orient="records")
    finally:
        con.close()


def remuneration_summary():
    con = get_analytics()
    try:
        df = con.execute("""
            SELECT dh.name as duty_head,
                   COUNT(sr.id) as entries,
                   SUM(sr.amount) as total_amount,
                   SUM(CASE WHEN sr.payment_status='Paid' THEN sr.amount ELSE 0 END) as paid,
                   SUM(CASE WHEN sr.payment_status='Pending' THEN sr.amount ELSE 0 END) as pending
            FROM staff_remuneration sr
            JOIN duty_heads dh ON sr.duty_head_id=dh.id
            GROUP BY dh.id, dh.name ORDER BY total_amount DESC
        """).fetchdf()
        return df.to_dict(orient="records")
    finally:
        con.close()
