"""
Exam Management Pro - Flask Web Application
BJ College, Ale - Affiliated to SPPU
Run: python main.py  →  http://localhost:5000
"""

import sys, os, io, webbrowser, threading, time
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, get_all, query, insert, update, delete, execute, backup_db, restore_db, list_backups, db_stats
from utils import export_to_excel
import analytics

app = Flask(__name__)
init_db()

# ==================== ROUTES ====================

@app.route("/")
def index():
    return render_template("dashboard.html")

# ---- Masters (Unified) ----
@app.route("/masters")
def masters_page():
    return render_template("masters.html")

# ---- Academic Years & Terms ----
@app.route("/api/acadyears")
def api_acadyears():
    rows = query("""
        SELECT a.id, a.name, a.start_date, a.end_date, a.is_active,
               GROUP_CONCAT(t.name) as terms_list
        FROM academic_years a LEFT JOIN terms t ON a.id = t.acad_year_id
        GROUP BY a.id ORDER BY a.name DESC
    """)
    return jsonify(rows)

@app.route("/api/acadyears/save", methods=["POST"])
def api_acadyears_save():
    d = request.json
    try:
        if d.get("id"):
            update("academic_years", {"name": d["name"], "start_date": d.get("start_date", ""), "end_date": d.get("end_date", ""), "is_active": d.get("is_active", 0)}, int(d["id"]))
        else:
            insert("academic_years", {"name": d["name"], "start_date": d.get("start_date", ""), "end_date": d.get("end_date", ""), "is_active": 0})
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route("/api/acadyears/delete/<int:aid>", methods=["DELETE"])
def api_acadyears_delete(aid):
    delete("academic_years", aid)
    return jsonify({"ok": True})

@app.route("/api/acadyears/activate/<int:aid>", methods=["POST"])
def api_acadyears_activate(aid):
    execute("UPDATE academic_years SET is_active=0")
    execute("UPDATE academic_years SET is_active=1 WHERE id=?", (aid,))
    return jsonify({"ok": True})

@app.route("/api/terms")
def api_terms():
    aid = request.args.get("acadyear_id", "")
    if aid:
        rows = query("SELECT t.*, a.name as year_name FROM terms t JOIN academic_years a ON t.acad_year_id=a.id WHERE t.acad_year_id=? ORDER BY t.code", (aid,))
    else:
        rows = query("SELECT t.*, a.name as year_name FROM terms t JOIN academic_years a ON t.acad_year_id=a.id ORDER BY a.name, t.code")
    return jsonify(rows)

@app.route("/api/terms/save", methods=["POST"])
def api_terms_save():
    d = request.json
    try:
        if d.get("id"):
            update("terms", {"name": d["name"], "code": d["code"], "acad_year_id": int(d["acad_year_id"])}, int(d["id"]))
        else:
            insert("terms", {"name": d["name"], "code": d["code"], "acad_year_id": int(d["acad_year_id"])})
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route("/api/terms/delete/<int:tid>", methods=["DELETE"])
def api_terms_delete(tid):
    delete("terms", tid)
    return jsonify({"ok": True})
@app.route("/api/courses")
def api_courses():
    return jsonify(get_all("courses"))

@app.route("/api/courses/save", methods=["POST"])
def api_courses_save():
    d = request.json
    try:
        if d.get("id"):
            update("courses", {"code": d["code"], "name": d["name"], "faculty": d["faculty"], "duration_years": int(d["duration_years"])}, int(d["id"]))
        else:
            insert("courses", {"code": d["code"], "name": d["name"], "faculty": d["faculty"], "duration_years": int(d["duration_years"])})
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route("/api/courses/delete/<int:cid>", methods=["DELETE"])
def api_courses_delete(cid):
    delete("courses", cid)
    return jsonify({"ok": True})
@app.route("/api/subjects")
def api_subjects():
    rows = query("SELECT s.id, s.code, s.name, c.name as course_name, c.code as course_code, s.type, s.credits, s.paper_no, s.max_internal, s.max_external FROM subjects s JOIN courses c ON s.course_id=c.id ORDER BY s.code")
    return jsonify(rows)

@app.route("/api/subjects/save", methods=["POST"])
def api_subjects_save():
    d = request.json
    try:
        cid = query("SELECT id FROM courses WHERE code=?", (d["course_code"],))[0]["id"]
        data = {"code": d["code"], "name": d["name"], "course_id": cid,
                "paper_no": int(d.get("paper_no", 1)), "type": d["type"],
                "credits": int(d.get("credits", 4)),
                "max_internal": int(d.get("max_internal", 15)),
                "max_external": int(d.get("max_external", 70))}
        if d.get("id"):
            update("subjects", data, int(d["id"]))
        else:
            insert("subjects", data)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route("/api/subjects/delete/<int:sid>", methods=["DELETE"])
def api_subjects_delete(sid):
    delete("subjects", sid)
    return jsonify({"ok": True})
@app.route("/api/blocks")
def api_blocks():
    return jsonify(get_all("blocks"))

@app.route("/api/blocks/save", methods=["POST"])
def api_blocks_save():
    d = request.json
    try:
        if d.get("id"):
            update("blocks", {"name": d["name"], "floor": d.get("floor", "")}, int(d["id"]))
        else:
            insert("blocks", {"name": d["name"], "floor": d.get("floor", "")})
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route("/api/blocks/delete/<int:bid>", methods=["DELETE"])
def api_blocks_delete(bid):
    delete("blocks", bid)
    return jsonify({"ok": True})

@app.route("/api/rooms")
def api_rooms():
    rows = query("SELECT r.id, r.name, b.name as block_name, b.id as block_id, r.capacity, r.bench_count, b.floor FROM rooms r JOIN blocks b ON r.block_id=b.id ORDER BY b.name, r.name")
    return jsonify(rows)

@app.route("/api/rooms/save", methods=["POST"])
def api_rooms_save():
    d = request.json
    try:
        blk = query("SELECT id FROM blocks WHERE name=?", (d["block_name"],))[0]["id"]
        data = {"name": d["name"], "block_id": blk, "capacity": int(d["capacity"]), "bench_count": int(d["bench_count"])}
        if d.get("id"):
            update("rooms", data, int(d["id"]))
        else:
            insert("rooms", data)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route("/api/rooms/delete/<int:rid>", methods=["DELETE"])
def api_rooms_delete(rid):
    delete("rooms", rid)
    return jsonify({"ok": True})
@app.route("/api/staff")
def api_staff():
    return jsonify(get_all("staff"))

@app.route("/api/staff/save", methods=["POST"])
def api_staff_save():
    d = request.json
    try:
        data = {"name": d["name"], "designation": d.get("designation", ""), "department": d.get("department", ""),
                "mobile": d.get("mobile", ""), "email": d.get("email", ""), "role": d["role"]}
        if d.get("id"):
            update("staff", data, int(d["id"]))
        else:
            insert("staff", data)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route("/api/staff/delete/<int:sid>", methods=["DELETE"])
def api_staff_delete(sid):
    delete("staff", sid)
    return jsonify({"ok": True})

# ---- Import (Namelist + Timetable) ----
@app.route("/import")
def import_page():
    return render_template("import.html")

@app.route("/api/namelist")
def api_namelist():
    rows = query("SELECT id, prn, student_name, subject_code, exam_date FROM namelist ORDER BY subject_code, prn LIMIT 200")
    return jsonify(rows)

@app.route("/api/namelist/upload", methods=["POST"])
def api_namelist_upload():
    import pandas as pd
    f = request.files.get("file")
    if not f:
        return jsonify({"ok": False, "error": "No file"}), 400
    try:
        df = pd.read_csv(f) if f.filename.endswith(".csv") else pd.read_excel(f)
        count = 0
        for _, row in df.iterrows():
            insert("namelist", {"prn": str(row.get("PRN", "")).strip(), "student_name": str(row.get("Student Name", "")).strip(),
                                "subject_code": str(row.get("Subject Code", "")).strip(), "exam_date": str(row.get("Exam Date", "")).strip(), "session_id": 1})
            count += 1
        return jsonify({"ok": True, "count": count})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route("/api/namelist/clear", methods=["POST"])
def api_namelist_clear():
    execute("DELETE FROM namelist")
    return jsonify({"ok": True})

@app.route("/api/timetable")
def api_timetable():
    rows = query("SELECT t.id, t.subject_code, t.exam_date, s.name as session_name, t.session_id FROM timetable t JOIN exam_sessions s ON t.session_id=s.id ORDER BY t.exam_date, s.start_time")
    return jsonify(rows)

@app.route("/api/timetable/save", methods=["POST"])
def api_timetable_save():
    d = request.json
    try:
        insert("timetable", {"subject_code": d["subject_code"], "exam_date": d["exam_date"], "session_id": int(d["session_id"]), "acad_year_id": 1})
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route("/api/timetable/delete/<int:tid>", methods=["DELETE"])
def api_timetable_delete(tid):
    delete("timetable", tid)
    return jsonify({"ok": True})

@app.route("/api/timetable/upload", methods=["POST"])
def api_timetable_upload():
    import pandas as pd
    f = request.files.get("file")
    if not f:
        return jsonify({"ok": False, "error": "No file"}), 400
    try:
        df = pd.read_csv(f) if f.filename.endswith(".csv") else pd.read_excel(f)
        session_id = int(request.form.get("session_id", 1))
        count = 0
        for _, row in df.iterrows():
            insert("timetable", {"subject_code": str(row.get("Subject Code", "")).strip(), "exam_date": str(row.get("Exam Date", "")).strip(), "session_id": session_id, "acad_year_id": 1})
            count += 1
        return jsonify({"ok": True, "count": count})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route("/api/timetable/clear", methods=["POST"])
def api_timetable_clear():
    execute("DELETE FROM timetable")
    return jsonify({"ok": True})

# ---- Seating ----
@app.route("/seating")
def seating_page():
    return render_template("seating.html")

@app.route("/api/seating/subjects")
def api_seating_subjects():
    rows = query("SELECT DISTINCT t.subject_code, s.name as subject_name FROM timetable t LEFT JOIN subjects s ON t.subject_code=s.code ORDER BY t.subject_code")
    return jsonify(rows)

@app.route("/api/seating/generate", methods=["POST"])
def api_seating_generate():
    d = request.json
    code = d["subject_code"]
    edate = d["exam_date"]
    sess_id = int(d.get("session_id", 1))

    students = query("SELECT prn, student_name FROM namelist WHERE subject_code=? ORDER BY prn", (code,))
    if not students:
        return jsonify({"ok": False, "error": "No students in namelist"}), 400

    rooms = get_all("rooms", "name")
    if not rooms:
        return jsonify({"ok": False, "error": "No rooms defined"}), 400

    execute("DELETE FROM seating WHERE subject_code=? AND exam_date=? AND session_id=?", (code, edate, sess_id))

    total = len(students)
    result = []
    allocated = 0
    for room in rooms:
        if allocated >= total:
            break
        to_allot = min(room["capacity"], total - allocated)
        if to_allot <= 0:
            continue
        for i in range(to_allot):
            si = allocated + i
            if si >= total:
                break
            bench = (i // 2) + 1
            insert("seating", {"prn": students[si]["prn"], "subject_code": code, "exam_date": edate,
                               "session_id": sess_id, "room_id": room["id"],
                               "seat_no": f"{room['name'][:3]}{bench:03d}", "bench_no": bench})
        result.append({"room": room["name"], "capacity": room["capacity"], "allotted": to_allot,
                       "occ_pct": round(to_allot / room["capacity"] * 100, 1)})
        allocated += to_allot

    return jsonify({"ok": True, "total": total, "rooms": result})

@app.route("/api/seating/view")
def api_seating_view():
    code = request.args.get("code")
    edate = request.args.get("date")
    sess_id = request.args.get("session", 1)
    rows = query("""
        SELECT s.prn, n.student_name, r.name as room, s.seat_no, s.bench_no
        FROM seating s JOIN namelist n ON s.prn=n.prn AND s.subject_code=n.subject_code
        JOIN rooms r ON s.room_id=r.id
        WHERE s.subject_code=? AND s.exam_date=? AND s.session_id=?
        ORDER BY r.name, s.bench_no
    """, (code, edate, sess_id))
    return jsonify(rows)

@app.route("/api/seating/generate_all", methods=["POST"])
def api_seating_generate_all():
    tt = query("SELECT DISTINCT subject_code, exam_date, session_id FROM timetable")
    if not tt:
        return jsonify({"ok": False, "error": "No timetable"}), 400
    rooms = get_all("rooms", "name")
    total_gen = 0
    for t in tt:
        students = query("SELECT prn FROM namelist WHERE subject_code=? AND exam_date=? ORDER BY prn", (t["subject_code"], t["exam_date"]))
        if not students:
            continue
        execute("DELETE FROM seating WHERE subject_code=? AND exam_date=? AND session_id=?", (t["subject_code"], t["exam_date"], t["session_id"]))
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
                insert("seating", {"prn": students[si]["prn"], "subject_code": t["subject_code"],
                                   "exam_date": t["exam_date"], "session_id": t["session_id"],
                                   "room_id": room["id"], "seat_no": f"{room['name'][:3]}{bench:03d}", "bench_no": bench})
            allocated += to_allot
        total_gen += allocated
    return jsonify({"ok": True, "total": total_gen})

@app.route("/api/seating/clear", methods=["POST"])
def api_seating_clear():
    d = request.json
    execute("DELETE FROM seating WHERE subject_code=? AND exam_date=? AND session_id=?", (d["subject_code"], d["exam_date"], int(d.get("session_id", 1))))
    return jsonify({"ok": True})

# ---- Staff Duty ----
@app.route("/duty")
def duty_page():
    return render_template("duty.html")

@app.route("/api/duty/view")
def api_duty_view():
    edate = request.args.get("date", "")
    sess_id = request.args.get("session", 1)
    from collections import defaultdict
    duties = query("""
        SELECT r.name as room, b.name as block, sd.subject_code, sd.role, s.name as staff_name
        FROM staff_duty sd JOIN rooms r ON sd.room_id=r.id
        JOIN blocks b ON r.block_id=b.id LEFT JOIN staff s ON sd.staff_id=s.id
        WHERE sd.exam_date=? AND sd.session_id=?
    """, (edate, sess_id))
    room_data = defaultdict(dict)
    for d in duties:
        room_data[d["room"]]["room"] = d["room"]
        room_data[d["room"]]["block"] = d["block"]
        room_data[d["room"]]["subject"] = d["subject_code"]
        room_data[d["room"]][d["role"]] = d["staff_name"] or ""
    return jsonify(list(room_data.values()))

@app.route("/api/duty/assign", methods=["POST"])
def api_duty_assign():
    d = request.json
    edate = d["date"]
    sess_id = int(d.get("session_id", 1))
    execute("DELETE FROM staff_duty WHERE exam_date=? AND session_id=?", (edate, sess_id))

    rooms = get_all("rooms", "name")
    jr_staff = query("SELECT id, name FROM staff WHERE role IN ('Junior Supervisor','Other','HOD') AND is_active=1")
    sr_staff = query("SELECT id, name FROM staff WHERE role IN ('Senior Supervisor','HOD','Other') AND is_active=1")
    peons = query("SELECT id, name FROM staff WHERE role='Peon' AND is_active=1")

    if not jr_staff:
        jr_staff = query("SELECT id, name FROM staff WHERE is_active=1")
    if not sr_staff:
        sr_staff = [{"id": 0, "name": "TBA"}]
    if not peons:
        peons = [{"id": 0, "name": "TBA"}]

    for i, room in enumerate(rooms):
        subjs = query("SELECT DISTINCT subject_code FROM seating WHERE room_id=? AND exam_date=? AND session_id=?",
                       (room["id"], edate, sess_id))
        scode = subjs[0]["subject_code"] if subjs else "N/A"
        blk = query("SELECT block_id FROM rooms WHERE id=?", (room["id"],))[0]["block_id"]

        for role, staff, idx in [("Junior Supervisor", jr_staff, i), ("Senior Supervisor", sr_staff, i // 3), ("Peon", peons, i // 5)]:
            insert("staff_duty", {"staff_id": staff[idx % len(staff)]["id"], "role": role,
                                  "room_id": room["id"], "block_id": blk, "subject_code": scode,
                                  "exam_date": edate, "session_id": sess_id})
    return jsonify({"ok": True})

@app.route("/api/duty/clear", methods=["POST"])
def api_duty_clear():
    d = request.json
    execute("DELETE FROM staff_duty WHERE exam_date=? AND session_id=?", (d["date"], int(d.get("session_id", 1))))
    return jsonify({"ok": True})

# ---- Duty Heads & Remuneration ----
@app.route("/api/duty-heads")
def api_duty_heads():
    rows = query("""
        SELECT d.id, d.name, d.description,
               GROUP_CONCAT(r.session_type||':'||r.rate_per_unit) as rates_str,
               GROUP_CONCAT(r.id) as rate_ids
        FROM duty_heads d LEFT JOIN remuneration_rates r ON d.id=r.duty_head_id AND r.is_active=1
        GROUP BY d.id ORDER BY d.id
    """)
    return jsonify(rows)

@app.route("/api/duty-heads/rates/<int:dh_id>")
def api_duty_head_rates(dh_id):
    rows = query("SELECT * FROM remuneration_rates WHERE duty_head_id=? AND is_active=1", (dh_id,))
    return jsonify(rows)

@app.route("/api/duty-heads/save", methods=["POST"])
def api_duty_heads_save():
    d = request.json
    try:
        if d.get("id"):
            update("duty_heads", {"name": d["name"], "description": d.get("description", "")}, int(d["id"]))
            did = int(d["id"])
        else:
            did = insert("duty_heads", {"name": d["name"], "description": d.get("description", "")})
        execute("UPDATE remuneration_rates SET is_active=0 WHERE duty_head_id=?", (did,))
        for rate in d.get("rates", []):
            insert("remuneration_rates", {"duty_head_id": did, "session_type": rate["session_type"], "rate_per_unit": float(rate["rate"]), "is_active": 1})
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route("/api/duty-heads/delete/<int:dh_id>", methods=["DELETE"])
def api_duty_heads_delete(dh_id):
    delete("duty_heads", dh_id)
    return jsonify({"ok": True})

# ---- Staff Remuneration Calculation ----
@app.route("/api/remuneration")
def api_remuneration():
    date_from = request.args.get("from", "")
    date_to = request.args.get("to", "")
    staff_id = request.args.get("staff_id", "")
    sql = """SELECT sr.id, s.name as staff_name, dh.name as duty_name, sr.exam_date,
             sr.session_type, sr.units, sr.rate, sr.amount, sr.payment_status, sr.paid_date
             FROM staff_remuneration sr
             JOIN staff s ON sr.staff_id=s.id
             JOIN duty_heads dh ON sr.duty_head_id=dh.id WHERE 1=1"""
    params = []
    if date_from: sql += " AND sr.exam_date>=?"; params.append(date_from)
    if date_to: sql += " AND sr.exam_date<=?"; params.append(date_to)
    if staff_id: sql += " AND sr.staff_id=?"; params.append(int(staff_id))
    sql += " ORDER BY sr.exam_date, s.name"
    return jsonify(query(sql, params))

@app.route("/api/remuneration/calculate", methods=["POST"])
def api_remuneration_calculate():
    d = request.json
    edate = d.get("date", "")
    sess_id = int(d.get("session_id", 1))
    sess_name = "Morning" if sess_id == 1 else "Afternoon"
    execute("DELETE FROM staff_remuneration WHERE exam_date=? AND session_type=?", (edate, sess_name))
    duties = query("""
        SELECT sd.staff_id, sd.role, s.name, bl.name as block_name, r.name as room_name
        FROM staff_duty sd JOIN staff s ON sd.staff_id=s.id
        LEFT JOIN rooms r ON sd.room_id=r.id
        LEFT JOIN blocks bl ON sd.block_id=bl.id
        WHERE sd.exam_date=? AND sd.session_id=?
    """, (edate, sess_id))
    head_map = {}
    for h in query("SELECT d.id, d.name, rr.session_type, rr.rate_per_unit FROM duty_heads d JOIN remuneration_rates rr ON d.id=rr.duty_head_id WHERE rr.is_active=1"):
        key = (h["name"], h["session_type"])
        head_map[key] = {"head_id": h["id"], "rate": h["rate_per_unit"]}
    count = 0
    for duty in duties:
        role = duty["role"]
        key = (role, sess_name)
        if key in head_map:
            head = head_map[key]
            try:
                insert("staff_remuneration", {"staff_id": duty["staff_id"], "duty_head_id": head["head_id"],
                    "exam_date": edate, "session_type": sess_name, "units": 1, "rate": head["rate"],
                    "amount": head["rate"], "payment_status": "Pending"})
                count += 1
            except: pass
    return jsonify({"ok": True, "calculated": count})

@app.route("/api/remuneration/save", methods=["POST"])
def api_remuneration_save():
    d = request.json
    try:
        if d.get("id"):
            update("staff_remuneration", {"payment_status": d["payment_status"], "paid_date": d.get("paid_date", ""), "remarks": d.get("remarks", "")}, int(d["id"]))
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route("/api/remuneration/delete/<int:rid>", methods=["DELETE"])
def api_remuneration_delete(rid):
    delete("staff_remuneration", rid)
    return jsonify({"ok": True})

@app.route("/api/remuneration/summary")
def api_remuneration_summary():
    rows = query("""
        SELECT s.id, s.name, s.designation, s.department,
               COUNT(sr.id) as total_sessions,
               SUM(sr.amount) as total_amount,
               SUM(CASE WHEN sr.payment_status='Paid' THEN sr.amount ELSE 0 END) as paid_amount,
               SUM(CASE WHEN sr.payment_status='Pending' THEN sr.amount ELSE 0 END) as pending_amount
        FROM staff s LEFT JOIN staff_remuneration sr ON s.id=sr.staff_id
        GROUP BY s.id ORDER BY total_amount DESC
    """)
    return jsonify(rows)

# ---- Students (Namelist) CRUD ----
@app.route("/api/students")
def api_students():
    course = request.args.get("course", "")
    sql = "SELECT n.id, n.prn, n.student_name, c.code as course_code, c.name as course_name, n.subject_code, n.exam_date FROM namelist n JOIN courses c ON n.course_id=c.id"
    params = []
    if course:
        sql += " WHERE c.code=?"
        params.append(course)
    sql += " ORDER BY n.id DESC LIMIT 500"
    return jsonify(query(sql, params))

@app.route("/api/students/save", methods=["POST"])
def api_students_save():
    d = request.json
    try:
        course = query("SELECT id FROM courses WHERE code=?", (d["course_code"],))
        if not course: return jsonify({"ok": False, "error": "Course not found"}), 400
        cid = course[0]["id"]
        if d.get("id"):
            update("namelist", {"prn": d["prn"], "student_name": d["name"], "course_id": cid,
                "subject_code": d.get("subject_code", ""), "exam_date": d.get("exam_date", "")}, int(d["id"]))
        else:
            insert("namelist", {"prn": d["prn"], "student_name": d["name"], "course_id": cid,
                "subject_code": d.get("subject_code", ""), "exam_date": d.get("exam_date", "")})
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route("/api/students/delete/<int:sid>", methods=["DELETE"])
def api_students_delete(sid):
    delete("namelist", sid)
    return jsonify({"ok": True})

@app.route("/api/students/bulk", methods=["POST"])
def api_students_bulk():
    d = request.json
    try:
        course = query("SELECT id FROM courses WHERE code=?", (d["course_code"],))
        if not course: return jsonify({"ok": False, "error": "Course not found"}), 400
        cid = course[0]["id"]
        count = 0
        for row in d.get("students", []):
            try:
                insert("namelist", {"prn": row["prn"], "student_name": row["name"], "course_id": cid,
                    "subject_code": row.get("subject_code", ""), "exam_date": row.get("exam_date", "")})
                count += 1
            except: pass
        return jsonify({"ok": True, "inserted": count})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

# ---- Attendance ----
@app.route("/attendance")
def attendance_page():
    return render_template("attendance.html")

@app.route("/api/attendance/rooms")
def api_attendance_rooms():
    edate = request.args.get("date", "")
    rows = query("SELECT DISTINCT r.name FROM seating s JOIN rooms r ON s.room_id=r.id WHERE s.exam_date=?", (edate,))
    return jsonify([r["name"] for r in rows])

@app.route("/api/attendance/load")
def api_attendance_load():
    edate = request.args.get("date", "")
    room = request.args.get("room", "")
    rows = query("""
        SELECT s.id, s.prn, n.student_name, s.seat_no, COALESCE(a.status,'Present') as status
        FROM seating s JOIN namelist n ON s.prn=n.prn AND s.subject_code=n.subject_code
        JOIN rooms r ON s.room_id=r.id LEFT JOIN attendance a ON a.seating_id=s.id
        WHERE s.exam_date=? AND r.name=? ORDER BY s.bench_no
    """, (edate, room))
    return jsonify(rows)

@app.route("/api/attendance/save", methods=["POST"])
def api_attendance_save():
    data = request.json.get("attendance", [])
    for item in data:
        sid = item["id"]
        status = item["status"]
        existing = query("SELECT id FROM attendance WHERE seating_id=?", (sid,))
        if existing:
            execute("UPDATE attendance SET status=? WHERE seating_id=?", (status, sid))
        else:
            insert("attendance", {"seating_id": sid, "status": status})
    return jsonify({"ok": True, "count": len(data)})

# ---- QP Management ----
@app.route("/qp")
def qp_page():
    return render_template("qp.html")

@app.route("/api/qp")
def api_qp():
    return jsonify(get_all("qp_inventory"))

@app.route("/api/qp/save", methods=["POST"])
def api_qp_save():
    d = request.json
    try:
        insert("qp_inventory", {"subject_code": d["subject_code"], "exam_date": d["exam_date"],
                                "session_id": int(d.get("session_id", 1)),
                                "total_received": int(d["total_received"]),
                                "sealed_packs": int(d.get("sealed_packs", 0)),
                                "opened_packs": 0, "distributed": 0,
                                "balance": int(d["total_received"])})
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route("/api/qp/distribute/<int:qid>", methods=["POST"])
def api_qp_distribute(qid):
    qp = query("SELECT * FROM qp_inventory WHERE id=?", (qid,))
    if not qp:
        return jsonify({"ok": False, "error": "Not found"}), 404
    qp = qp[0]
    rooms = query("SELECT DISTINCT r.id, r.name, COUNT(s.id) as cnt FROM seating s JOIN rooms r ON s.room_id=r.id WHERE s.subject_code=? AND s.exam_date=? AND s.session_id=? GROUP BY r.name", (qp["subject_code"], qp["exam_date"], qp["session_id"]))
    if not rooms:
        return jsonify({"ok": False, "error": "No seating data"}), 400
    execute("DELETE FROM qp_distribution WHERE qp_id=?", (qid,))
    total_dist = 0
    for room in rooms:
        insert("qp_distribution", {"qp_id": qid, "room_id": room["id"], "student_count": room["cnt"], "qp_issued": room["cnt"]})
        total_dist += room["cnt"]
    execute("UPDATE qp_inventory SET distributed=?, balance=total_received-? WHERE id=?", (total_dist, total_dist, qid))
    return jsonify({"ok": True, "rooms": len(rooms), "distributed": total_dist})

@app.route("/api/qp/delete/<int:qid>", methods=["DELETE"])
def api_qp_delete(qid):
    delete("qp_inventory", qid)
    return jsonify({"ok": True})

# ---- Internal Marks ----
@app.route("/marks")
def marks_page():
    return render_template("marks.html")

@app.route("/api/marks/load")
def api_marks_load():
    code = request.args.get("code", "")
    students = query("SELECT DISTINCT prn, student_name FROM namelist WHERE subject_code=? ORDER BY prn", (code,))
    result = []
    for st in students:
        e = query("SELECT * FROM internal_marks WHERE prn=? AND subject_code=?", (st["prn"], code))
        e = e[0] if e else {"theory_ia": 0, "practical": 0, "oral": 0, "project": 0, "termwork": 0, "attendance_pct": 75, "eligible": 1, "id": 0}
        result.append({"id": e["id"], "prn": st["prn"], "student_name": st["student_name"],
                       "theory_ia": e["theory_ia"], "practical": e["practical"], "oral": e["oral"],
                       "project": e["project"], "termwork": e["termwork"], "attendance_pct": e["attendance_pct"],
                       "eligible": "Yes" if e["eligible"] else "No"})
    return jsonify(result)

@app.route("/api/marks/save", methods=["POST"])
def api_marks_save():
    data = request.json.get("marks", [])
    for item in data:
        if item.get("id") and int(item["id"]) > 0:
            update("internal_marks", {"theory_ia": int(item.get("theory_ia", 0)), "practical": int(item.get("practical", 0)),
                                       "oral": int(item.get("oral", 0)), "project": int(item.get("project", 0)),
                                       "termwork": int(item.get("termwork", 0)), "attendance_pct": float(item.get("attendance_pct", 75)),
                                       "eligible": 1 if item.get("eligible") == "Yes" else 0}, int(item["id"]))
        else:
            insert("internal_marks", {"prn": item["prn"], "subject_code": item.get("subject_code", ""),
                                       "theory_ia": int(item.get("theory_ia", 0)), "practical": int(item.get("practical", 0)),
                                       "oral": int(item.get("oral", 0)), "project": int(item.get("project", 0)),
                                       "termwork": int(item.get("termwork", 0)), "attendance_pct": float(item.get("attendance_pct", 75)),
                                       "eligible": 1 if item.get("eligible") == "Yes" else 0})
    return jsonify({"ok": True})

# ---- Reports ----
@app.route("/reports")
def reports_page():
    return render_template("reports.html")

@app.route("/api/reports/subject_summary")
def api_reports_subject_summary():
    rows = query("""
        SELECT nl.subject_code, s.name as sname, COUNT(DISTINCT nl.prn) as total,
               COUNT(DISTINCT se.prn) as seated
        FROM namelist nl LEFT JOIN subjects s ON nl.subject_code=s.code
        LEFT JOIN seating se ON nl.prn=se.prn AND nl.subject_code=se.subject_code
        GROUP BY nl.subject_code ORDER BY nl.subject_code
    """)
    result = []
    for r in rows:
        rooms = query("SELECT DISTINCT r.name FROM seating s JOIN rooms r ON s.room_id=r.id WHERE s.subject_code=?", (r["subject_code"],))
        result.append({**r, "seated": r["seated"] or 0, "unseated": (r["total"] or 0) - (r["seated"] or 0),
                       "rooms": ", ".join([x["name"] for x in rooms]) if rooms else "None"})
    return jsonify(result)

@app.route("/api/reports/day_summary")
def api_reports_day_summary():
    rows = query("""
        SELECT t.exam_date, es.name as session_name, COUNT(DISTINCT t.subject_code) as papers,
               COUNT(DISTINCT s.prn) as students, COUNT(DISTINCT s.room_id) as rooms
        FROM timetable t LEFT JOIN seating s ON t.subject_code=s.subject_code AND t.exam_date=s.exam_date AND t.session_id=s.session_id
        JOIN exam_sessions es ON t.session_id=es.id
        GROUP BY t.exam_date, t.session_id ORDER BY t.exam_date, t.session_id
    """)
    return jsonify(rows)

@app.route("/api/reports/duty_summary")
def api_reports_duty_summary():
    rows = query("""
        SELECT s.name as staff_name, sd.role, sd.exam_date, es.name as session_name, r.name as room, sd.subject_code
        FROM staff_duty sd LEFT JOIN staff s ON sd.staff_id=s.id
        JOIN exam_sessions es ON sd.session_id=es.id
        JOIN rooms r ON sd.room_id=r.id
        ORDER BY sd.exam_date, es.start_time, sd.role, s.name
    """)
    return jsonify(rows)

@app.route("/api/reports/export/<rpt_type>")
def api_reports_export(rpt_type):
    buf = io.BytesIO()
    if rpt_type == "subject_summary":
        data = query("""
            SELECT nl.subject_code, COUNT(DISTINCT nl.prn) as total, COUNT(DISTINCT se.prn) as seated
            FROM namelist nl LEFT JOIN seating se ON nl.prn=se.prn AND nl.subject_code=se.subject_code
            GROUP BY nl.subject_code
        """)
        cols = ["subject_code", "total", "seated"]
    elif rpt_type == "namelist":
        data = query("SELECT prn, student_name, subject_code, exam_date FROM namelist")
        cols = ["prn", "student_name", "subject_code", "exam_date"]
    elif rpt_type == "seating":
        data = query("""
            SELECT s.subject_code, s.exam_date, r.name as room, s.prn, n.student_name, s.seat_no
            FROM seating s JOIN rooms r ON s.room_id=r.id JOIN namelist n ON s.prn=n.prn AND s.subject_code=n.subject_code
        """)
        cols = ["subject_code", "exam_date", "room", "prn", "student_name", "seat_no"]
    elif rpt_type == "marks":
        data = query("SELECT prn, subject_code, theory_ia, practical, oral, project, termwork, attendance_pct, eligible FROM internal_marks")
        cols = ["prn", "subject_code", "theory_ia", "practical", "oral", "project", "termwork", "attendance_pct", "eligible"]
    elif rpt_type == "staff":
        data = get_all("staff")
        cols = ["id", "name", "designation", "department", "mobile", "email", "role"]
    else:
        return jsonify({"ok": False, "error": "Invalid type"}), 400

    if rpt_type == "namelist" and not data:
        data = query("SELECT prn, student_name, subject_code, exam_date FROM namelist ORDER BY subject_code, prn")
    export_to_excel(data, cols, buf if hasattr(buf, 'write') else buf)
    buf.seek(0)
    return send_file(buf, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                     as_attachment=True, download_name=f"{rpt_type}.xlsx")

# ---- Dashboard API ----
@app.route("/api/dashboard")
def api_dashboard():
    dates = query("SELECT DISTINCT exam_date FROM timetable ORDER BY exam_date")
    sessions = get_all("exam_sessions")
    result = {"dates": [], "grand_total_papers": 0, "grand_total_students": 0}
    for d in dates:
        day = {"date": d["exam_date"], "sessions": [], "day_papers": 0, "day_students": 0}
        for sess in sessions:
            papers = query("SELECT DISTINCT t.subject_code, s.name as sname FROM timetable t LEFT JOIN subjects s ON t.subject_code=s.code WHERE t.exam_date=? AND t.session_id=? ORDER BY t.subject_code", (d["exam_date"], sess["id"]))
            if not papers:
                continue
            session_papers = []
            for p in papers:
                stu = query("SELECT COUNT(*) as cnt FROM namelist WHERE subject_code=? AND exam_date=?", (p["subject_code"], d["exam_date"]))[0]["cnt"]
                rooms = query("SELECT DISTINCT r.name FROM seating s JOIN rooms r ON s.room_id=r.id WHERE s.subject_code=? AND s.exam_date=? AND s.session_id=?", (p["subject_code"], d["exam_date"], sess["id"]))
                session_papers.append({"code": p["subject_code"], "name": p["sname"] or p["subject_code"], "students": stu, "rooms": ",".join([r["name"] for r in rooms]) if rooms else "Not assigned"})
                day["day_students"] += stu
                day["day_papers"] += 1
            day["sessions"].append({"name": sess["name"], "time": f"{sess['start_time']}-{sess['end_time']}", "papers": session_papers, "paper_count": len(session_papers), "student_count": sum(p["students"] for p in session_papers)})
        result["dates"].append(day)
        result["grand_total_papers"] += day["day_papers"]
        result["grand_total_students"] += day["day_students"]
    return jsonify(result)

# ---- Demo Data ----
@app.route("/api/demo/subjects", methods=["POST"])
def api_demo_subjects():
    courses_data = [("BSC", "Bachelor of Science", "Science & Technology", 3), ("BCOM", "Bachelor of Commerce", "Commerce & Management", 3), ("BA", "Bachelor of Arts", "Humanities", 3)]
    subjects_data = [
        ("MTC-301","Mathematics Paper 1","BSC",1,"Theory"),("CH-301","Chemistry Paper 1","BSC",1,"Theory"),
        ("PHY-301","Physics Paper 1","BSC",1,"Theory"),("BOT-301","Botany Paper 1","BSC",1,"Theory"),
        ("ZOO-301","Zoology Paper 1","BSC",1,"Theory"),("COMP-101","Accountancy Paper 1","BCOM",1,"Theory"),
        ("COMP-201","Business Economics","BCOM",1,"Theory"),("BA-ENG-101","English Literature","BA",1,"Theory"),
        ("BA-ECO-201","Economics","BA",1,"Theory"),("CH-303","Chemistry Practical","BSC",1,"Practical"),
    ]
    for code, name, fac, dur in courses_data:
        if not query("SELECT id FROM courses WHERE code=?", (code,)):
            insert("courses", {"code": code, "name": name, "faculty": fac, "duration_years": dur})
    for scode, sname, ccode, pno, stype in subjects_data:
        if not query("SELECT id FROM subjects WHERE code=?", (scode,)):
            crs = query("SELECT id FROM courses WHERE code=?", (ccode,))
            if crs:
                insert("subjects", {"code": scode, "name": sname, "course_id": crs[0]["id"], "paper_no": pno, "type": stype, "credits": 4})
    return jsonify({"ok": True})

@app.route("/api/demo/rooms", methods=["POST"])
def api_demo_rooms():
    blocks = [("Block A", "Ground"), ("Block B", "Ground"), ("Block C", "First")]
    rooms = [("A-101", "Block A", 40, 20), ("A-102", "Block A", 40, 20), ("A-103", "Block A", 40, 20),
             ("A-104", "Block A", 40, 20), ("B-101", "Block B", 60, 30), ("B-102", "Block B", 60, 30),
             ("B-103", "Block B", 60, 30), ("Seminar Hall", "Block C", 100, 50)]
    for bname, bfloor in blocks:
        if not query("SELECT id FROM blocks WHERE name=?", (bname,)):
            insert("blocks", {"name": bname, "floor": bfloor})
    for rname, blk, cap, bench in rooms:
        if not query("SELECT id FROM rooms WHERE name=?", (rname,)):
            b = query("SELECT id FROM blocks WHERE name=?", (blk,))
            if b:
                insert("rooms", {"name": rname, "block_id": b[0]["id"], "capacity": cap, "bench_count": bench})
    return jsonify({"ok": True})

@app.route("/api/demo/staff", methods=["POST"])
def api_demo_staff():
    demo = [("Dr. Anil Patil","Principal","Admin","9876543201","Principal"),("Prof. Sunil Joshi","Assoc Prof","Math","9876543202","CEO"),
            ("Dr. Meena More","HOD","Physics","9876543203","Senior Supervisor"),("Prof. Ramesh Kulkarni","Asst Prof","Chemistry","9876543204","Senior Supervisor"),
            ("Prof. Smita Desai","Asst Prof","Botany","9876543205","Junior Supervisor"),("Prof. Amit Bhosale","Asst Prof","Zoology","9876543206","Junior Supervisor"),
            ("Prof. Neha Sharma","Asst Prof","English","9876543207","Junior Supervisor"),("Mr. Raju Jadhav","Peon","General","9876543208","Peon"),
            ("Mr. Mahesh Shinde","Peon","General","9876543209","Peon")]
    for sname, desig, dept, mob, role in demo:
        if not query("SELECT id FROM staff WHERE name=?", (sname,)):
            insert("staff", {"name": sname, "designation": desig, "department": dept, "mobile": mob, "role": role})
    return jsonify({"ok": True})

@app.route("/api/demo/timetable", methods=["POST"])
def api_demo_timetable():
    theory = [r["code"] for r in query("SELECT code FROM subjects WHERE type='Theory'")]
    if not theory:
        return jsonify({"ok": False, "error": "Load subjects first"}), 400
    dates = ["15-11-2025", "16-11-2025", "17-11-2025"]
    import itertools
    subjs = list(itertools.islice(itertools.cycle(theory), len(dates) * 5))
    for i, sc in enumerate(subjs):
        insert("timetable", {"subject_code": sc, "exam_date": dates[i // 5], "session_id": (i % 2) + 1, "acad_year_id": 1})
    return jsonify({"ok": True, "count": len(subjs)})

@app.route("/api/demo/namelist", methods=["POST"])
def api_demo_namelist():
    theory = query("SELECT code FROM subjects WHERE type='Theory'")
    if not theory:
        return jsonify({"ok": False, "error": "Load subjects first"}), 400
    names = ["Rahul","Priya","Amit","Neha","Sachin","Pooja","Vikas","Anjali","Rohit","Deepa"] * 4
    count = 0
    for tt in query("SELECT subject_code, exam_date FROM timetable ORDER BY exam_date LIMIT 5"):
        for i in range(40):
            insert("namelist", {"prn": f"72BSC{i+100:04d}", "student_name": f"{names[i]} {i+1}", "subject_code": tt["subject_code"], "exam_date": tt["exam_date"], "session_id": 1})
            count += 1
    return jsonify({"ok": True, "count": count})

@app.route("/api/demo/full", methods=["POST"])
def api_demo_full():
    # Run all demo data generators
    # Courses + Subjects
    courses_data = [("BSC","Bachelor of Science","Science & Technology",3),("BCOM","Bachelor of Commerce","Commerce & Management",3),("BA","Bachelor of Arts","Humanities",3)]
    subjects_data = [("MTC-301","Mathematics Paper 1","BSC",1),("CH-301","Chemistry Paper 1","BSC",1),("PHY-301","Physics Paper 1","BSC",1),("BOT-301","Botany Paper 1","BSC",1),("ZOO-301","Zoology Paper 1","BSC",1),("COMP-101","Accountancy Paper 1","BCOM",1),("COMP-201","Business Economics","BCOM",1),("BA-ENG-101","English Literature","BA",1),("BA-ECO-201","Economics","BA",1)]
    for code,name,fac,dur in courses_data:
        if not query("SELECT id FROM courses WHERE code=?",(code,)):
            insert("courses",{"code":code,"name":name,"faculty":fac,"duration_years":dur})
    for scode,sname,ccode,pno in subjects_data:
        if not query("SELECT id FROM subjects WHERE code=?",(scode,)):
            crs=query("SELECT id FROM courses WHERE code=?",(ccode,))
            if crs: insert("subjects",{"code":scode,"name":sname,"course_id":crs[0]["id"],"paper_no":pno,"type":"Theory","credits":4})

    # Rooms
    blocks=[("Block A","Ground"),("Block B","Ground"),("Block C","First")]
    for bn,bf in blocks:
        if not query("SELECT id FROM blocks WHERE name=?",(bn,)): insert("blocks",{"name":bn,"floor":bf})
    rooms=[("A-101","Block A",40,20),("A-102","Block A",40,20),("A-103","Block A",40,20),("A-104","Block A",40,20),("B-101","Block B",60,30),("B-102","Block B",60,30),("B-103","Block B",60,30),("Seminar Hall","Block C",100,50)]
    for rn,blk,cap,bench in rooms:
        if not query("SELECT id FROM rooms WHERE name=?",(rn,)):
            b=query("SELECT id FROM blocks WHERE name=?",(blk,))
            if b: insert("rooms",{"name":rn,"block_id":b[0]["id"],"capacity":cap,"bench_count":bench})

    # Staff
    demo_s=[("Dr. Anil Patil","Principal","Admin","9876543201","Principal"),("Prof. Sunil Joshi","Assoc Prof","Math","9876543202","CEO"),
            ("Dr. Meena More","HOD","Physics","9876543203","Senior Supervisor"),("Prof. Ramesh Kulkarni","Asst Prof","Chemistry","9876543204","Senior Supervisor"),
            ("Prof. Smita Desai","Asst Prof","Botany","9876543205","Junior Supervisor"),("Prof. Amit Bhosale","Asst Prof","Zoology","9876543206","Junior Supervisor"),
            ("Prof. Neha Sharma","Asst Prof","English","9876543207","Junior Supervisor"),("Mr. Raju Jadhav","Peon","General","9876543208","Peon"),
            ("Mr. Mahesh Shinde","Peon","General","9876543209","Peon")]
    for sn,sd,sdep,smob,sr in demo_s:
        if not query("SELECT id FROM staff WHERE name=?",(sn,)):
            insert("staff",{"name":sn,"designation":sd,"department":sdep,"mobile":smob,"role":sr})

    # Timetable
    theory=[r["code"] for r in query("SELECT code FROM subjects WHERE type='Theory'")]
    dates=["15-11-2025","16-11-2025","17-11-2025"]
    import itertools
    for i,sc in enumerate(list(itertools.islice(itertools.cycle(theory),len(dates)*5))):
        insert("timetable",{"subject_code":sc,"exam_date":dates[i//5],"session_id":(i%2)+1,"acad_year_id":1})

    # Namelist
    namepool=["Rahul","Priya","Amit","Neha","Sachin","Pooja","Vikas","Anjali"]*5
    for tt in query("SELECT subject_code, exam_date FROM timetable ORDER BY exam_date LIMIT 5"):
        for i in range(40):
            insert("namelist",{"prn":f"72BSC{i+100:04d}","student_name":f"{namepool[i]} {i+1}","subject_code":tt["subject_code"],"exam_date":tt["exam_date"],"session_id":1})

    return jsonify({"ok":True,"msg":"All demo data loaded. Restart server to see changes."})

# ---- Utility ----
@app.route("/api/util/dates")
def api_util_dates():
    dates = query("SELECT DISTINCT exam_date FROM timetable ORDER BY exam_date")
    return jsonify([d["exam_date"] for d in dates])

@app.route("/api/util/sessions")
def api_util_sessions():
    return jsonify(get_all("exam_sessions"))

# ---- Database Backup & Health ----
@app.route("/api/backup", methods=["POST"])
def api_backup():
    tag = request.json.get("tag", "") if request.is_json else ""
    path = backup_db(tag)
    return jsonify({"ok": True, "file": os.path.basename(path), "path": path})

@app.route("/api/backups")
def api_backups():
    return jsonify(list_backups())

@app.route("/api/restore", methods=["POST"])
def api_restore():
    path = request.json.get("path", "")
    if not path or not os.path.exists(path):
        return jsonify({"ok": False, "error": "Backup file not found"}), 400
    restore_db(path)
    return jsonify({"ok": True})

@app.route("/api/db-stats")
def api_db_stats():
    return jsonify(db_stats())

# ---- DuckDB Analytics ----
@app.route("/api/analytics/exam-summary")
def api_analytics_exam():
    return jsonify(analytics.exam_summary())

@app.route("/api/analytics/course-stats")
def api_analytics_course():
    return jsonify(analytics.course_wise_stats())

@app.route("/api/analytics/staff-workload")
def api_analytics_workload():
    return jsonify(analytics.staff_workload())

@app.route("/api/analytics/room-utilization")
def api_analytics_room():
    return jsonify(analytics.room_utilization())

@app.route("/api/analytics/attendance")
def api_analytics_attendance():
    return jsonify(analytics.attendance_summary())

@app.route("/api/analytics/remuneration")
def api_analytics_remuneration():
    return jsonify(analytics.remuneration_summary())


def open_browser():
    time.sleep(1)
    webbrowser.open("http://localhost:5000")


if __name__ == "__main__":
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=True)
