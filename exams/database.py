"""
SPPU Exam Management System - Database Layer
SQLite database setup and all CRUD operations
"""

import sqlite3
import os
import shutil
import time

DB_PATH = os.path.join(os.path.dirname(__file__), "sppu_exam.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA cache_size = -64000")
    conn.execute("PRAGMA mmap_size = 268435456")
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS academic_years (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            start_date TEXT,
            end_date TEXT,
            is_active INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS terms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            acad_year_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            code TEXT NOT NULL,
            FOREIGN KEY (acad_year_id) REFERENCES academic_years(id) ON DELETE CASCADE,
            UNIQUE(acad_year_id, code)
        );

        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            faculty TEXT NOT NULL,
            duration_years INTEGER DEFAULT 3,
            is_active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS semesters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            semester_no INTEGER NOT NULL,
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
            UNIQUE(course_id, semester_no)
        );

        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            course_id INTEGER NOT NULL,
            sem_id INTEGER,
            paper_no INTEGER DEFAULT 1,
            type TEXT NOT NULL CHECK(type IN ('Theory','Practical','Oral','Project','Internal','Termwork')),
            credits INTEGER DEFAULT 4,
            max_internal INTEGER DEFAULT 15,
            max_external INTEGER DEFAULT 70,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
            FOREIGN KEY (sem_id) REFERENCES semesters(id)
        );

        CREATE TABLE IF NOT EXISTS blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            floor TEXT
        );

        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            block_id INTEGER NOT NULL,
            floor TEXT,
            capacity INTEGER NOT NULL,
            bench_count INTEGER NOT NULL,
            FOREIGN KEY (block_id) REFERENCES blocks(id)
        );

        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            designation TEXT,
            department TEXT,
            mobile TEXT,
            email TEXT,
            role TEXT NOT NULL CHECK(role IN ('Principal','CEO','Senior Supervisor','Junior Supervisor','Peon','HOD','Clerk','Other')),
            is_active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS exam_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_code TEXT NOT NULL,
            exam_date TEXT NOT NULL,
            session_id INTEGER NOT NULL,
            acad_year_id INTEGER NOT NULL,
            FOREIGN KEY (session_id) REFERENCES exam_sessions(id),
            FOREIGN KEY (acad_year_id) REFERENCES academic_years(id)
        );

        CREATE TABLE IF NOT EXISTS namelist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prn TEXT NOT NULL,
            student_name TEXT NOT NULL,
            course_id INTEGER,
            sem_id INTEGER,
            subject_code TEXT NOT NULL,
            exam_date TEXT,
            session_id INTEGER,
            FOREIGN KEY (course_id) REFERENCES courses(id),
            FOREIGN KEY (sem_id) REFERENCES semesters(id)
        );

        CREATE TABLE IF NOT EXISTS seating (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prn TEXT NOT NULL,
            subject_code TEXT NOT NULL,
            exam_date TEXT NOT NULL,
            session_id INTEGER NOT NULL,
            room_id INTEGER NOT NULL,
            seat_no TEXT NOT NULL,
            bench_no INTEGER NOT NULL,
            FOREIGN KEY (room_id) REFERENCES rooms(id)
        );

        CREATE TABLE IF NOT EXISTS staff_duty (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            room_id INTEGER,
            block_id INTEGER,
            subject_code TEXT NOT NULL,
            exam_date TEXT NOT NULL,
            session_id INTEGER NOT NULL,
            FOREIGN KEY (staff_id) REFERENCES staff(id),
            FOREIGN KEY (room_id) REFERENCES rooms(id),
            FOREIGN KEY (block_id) REFERENCES blocks(id)
        );

        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seating_id INTEGER NOT NULL,
            status TEXT DEFAULT 'Present' CHECK(status IN ('Present','Absent','UFM')),
            qp_serial TEXT,
            remarks TEXT,
            FOREIGN KEY (seating_id) REFERENCES seating(id)
        );

        CREATE TABLE IF NOT EXISTS qp_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_code TEXT NOT NULL,
            exam_date TEXT NOT NULL,
            session_id INTEGER NOT NULL,
            total_received INTEGER DEFAULT 0,
            sealed_packs INTEGER DEFAULT 0,
            opened_packs INTEGER DEFAULT 0,
            distributed INTEGER DEFAULT 0,
            balance INTEGER DEFAULT 0,
            remarks TEXT
        );

        CREATE TABLE IF NOT EXISTS qp_distribution (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            qp_id INTEGER NOT NULL,
            room_id INTEGER NOT NULL,
            student_count INTEGER DEFAULT 0,
            qp_issued INTEGER DEFAULT 0,
            qp_returned INTEGER DEFAULT 0,
            supervisor_sign INTEGER DEFAULT 0,
            FOREIGN KEY (qp_id) REFERENCES qp_inventory(id),
            FOREIGN KEY (room_id) REFERENCES rooms(id)
        );

        CREATE TABLE IF NOT EXISTS internal_marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prn TEXT NOT NULL,
            subject_code TEXT NOT NULL,
            theory_ia INTEGER DEFAULT 0,
            practical INTEGER DEFAULT 0,
            oral INTEGER DEFAULT 0,
            project INTEGER DEFAULT 0,
            termwork INTEGER DEFAULT 0,
            attendance_pct REAL DEFAULT 0,
            eligible INTEGER DEFAULT 1,
            remarks TEXT
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            full_name TEXT,
            role TEXT DEFAULT 'Clerk'
        );

        CREATE TABLE IF NOT EXISTS duty_heads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS remuneration_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            duty_head_id INTEGER NOT NULL,
            session_type TEXT NOT NULL CHECK(session_type IN ('Morning','Afternoon','Full Day','Per Paper','Per Answer Sheet','Per Visit')),
            rate_per_unit REAL NOT NULL DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (duty_head_id) REFERENCES duty_heads(id) ON DELETE CASCADE,
            UNIQUE(duty_head_id, session_type)
        );

        CREATE TABLE IF NOT EXISTS staff_remuneration (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id INTEGER NOT NULL,
            duty_head_id INTEGER NOT NULL,
            exam_date TEXT NOT NULL,
            session_type TEXT NOT NULL,
            units REAL DEFAULT 1,
            rate REAL NOT NULL,
            amount REAL NOT NULL,
            payment_status TEXT DEFAULT 'Pending' CHECK(payment_status IN ('Pending','Paid','Cancelled')),
            paid_date TEXT,
            remarks TEXT,
            FOREIGN KEY (staff_id) REFERENCES staff(id),
            FOREIGN KEY (duty_head_id) REFERENCES duty_heads(id)
        );
    """)

    cursor.execute("SELECT COUNT(*) FROM exam_sessions")
    if cursor.fetchone()[0] == 0:
        cursor.executescript("""
            INSERT INTO exam_sessions (name, start_time, end_time) VALUES
                ('Morning', '10:00', '13:00'),
                ('Afternoon', '14:00', '17:00');
            INSERT INTO users (username, password, full_name, role) VALUES
                ('admin', 'admin123', 'Administrator', 'CEO'),
                ('ceo', 'ceo123', 'Exam Officer', 'CEO'),
                ('clerk', 'clerk123', 'Exam Clerk', 'Clerk');
            INSERT INTO academic_years (name, is_active) VALUES ('2025-26', 1);
            INSERT INTO terms (acad_year_id, name, code) VALUES
                (1, 'Winter (Oct-Nov)', 'WINTER'),
                (1, 'Summer (Mar-Apr)', 'SUMMER');
        """)

    cursor.execute("SELECT COUNT(*) FROM duty_heads")
    if cursor.fetchone()[0] == 0:
        cursor.executescript("""
            INSERT INTO duty_heads (name, description) VALUES
                ('CEO / Chief Conductor', 'Overall exam centre in-charge'),
                ('Senior Supervisor', 'Block / Floor supervisor'),
                ('Junior Supervisor', 'Room invigilator'),
                ('Peon', 'Helper / Messenger'),
                ('Reliever', 'Backup staff for breaks'),
                ('Flying Squad', 'Surprise inspection visits'),
                ('QP Distribution', 'Question paper distribution staff'),
                ('Paper Setting', 'Setting question papers'),
                ('Assessment', 'Answer sheet assessment');
            INSERT INTO remuneration_rates (duty_head_id, session_type, rate_per_unit) VALUES
                (1, 'Full Day', 2000),
                (2, 'Morning', 600), (2, 'Afternoon', 600),
                (3, 'Morning', 500), (3, 'Afternoon', 500),
                (4, 'Morning', 350), (4, 'Afternoon', 350),
                (5, 'Morning', 450), (5, 'Afternoon', 450),
                (6, 'Per Visit', 500),
                (7, 'Morning', 400), (7, 'Afternoon', 400),
                (8, 'Per Paper', 3000),
                (9, 'Per Answer Sheet', 10);
        """)

    cursor.executescript("""
        CREATE INDEX IF NOT EXISTS idx_namelist_prn ON namelist(prn);
        CREATE INDEX IF NOT EXISTS idx_namelist_course ON namelist(course_id);
        CREATE INDEX IF NOT EXISTS idx_seating_date ON seating(exam_date);
        CREATE INDEX IF NOT EXISTS idx_seating_prn ON seating(prn);
        CREATE INDEX IF NOT EXISTS idx_seating_room ON seating(room_id);
        CREATE INDEX IF NOT EXISTS idx_staff_duty_date ON staff_duty(exam_date);
        CREATE INDEX IF NOT EXISTS idx_staff_duty_staff ON staff_duty(staff_id);
        CREATE INDEX IF NOT EXISTS idx_attendance_seating ON attendance(seating_id);
        CREATE INDEX IF NOT EXISTS idx_internal_marks_prn ON internal_marks(prn);
        CREATE INDEX IF NOT EXISTS idx_internal_marks_subj ON internal_marks(subject_code);
        CREATE INDEX IF NOT EXISTS idx_subjects_course ON subjects(course_id);
        CREATE INDEX IF NOT EXISTS idx_rooms_block ON rooms(block_id);
        CREATE INDEX IF NOT EXISTS idx_timetable_date ON timetable(exam_date);
        CREATE INDEX IF NOT EXISTS idx_qp_inventory_date ON qp_inventory(exam_date);
        CREATE INDEX IF NOT EXISTS idx_staff_remuneration_staff ON staff_remuneration(staff_id);
        CREATE INDEX IF NOT EXISTS idx_staff_remuneration_date ON staff_remuneration(exam_date);
    """)

    conn.commit()
    conn.close()


# ---------- CRUD Operations ----------

def get_all(table, order_by="id"):
    conn = get_connection()
    rows = conn.execute(f"SELECT * FROM {table} ORDER BY {order_by}").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_by_id(table, id_val):
    conn = get_connection()
    row = conn.execute(f"SELECT * FROM {table} WHERE id=?", (id_val,)).fetchone()
    conn.close()
    return dict(row) if row else None


def insert(table, data):
    conn = get_connection()
    cols = ", ".join(data.keys())
    placeholders = ", ".join(["?" for _ in data])
    sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
    cur = conn.execute(sql, list(data.values()))
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id


def update(table, data, id_val):
    conn = get_connection()
    sets = ", ".join([f"{k}=?" for k in data])
    sql = f"UPDATE {table} SET {sets} WHERE id=?"
    conn.execute(sql, list(data.values()) + [id_val])
    conn.commit()
    conn.close()


def delete(table, id_val):
    conn = get_connection()
    conn.execute(f"DELETE FROM {table} WHERE id=?", (id_val,))
    conn.commit()
    conn.close()


def query(sql, params=None):
    conn = get_connection()
    rows = conn.execute(sql, params or []).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def execute(sql, params=None):
    conn = get_connection()
    conn.execute(sql, params or [])
    conn.commit()
    conn.close()


# ---------- Backup & Restore ----------
BACKUP_DIR = os.path.join(os.path.dirname(__file__), "backups")

def backup_db(tag=""):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    fname = f"backup_{ts}{'_'+tag if tag else ''}.db"
    dest = os.path.join(BACKUP_DIR, fname)
    shutil.copy2(DB_PATH, dest)
    return dest

def restore_db(backup_path):
    if not os.path.exists(backup_path):
        return False
    shutil.copy2(backup_path, DB_PATH)
    return True

def list_backups():
    if not os.path.exists(BACKUP_DIR):
        return []
    files = sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith('.db')], reverse=True)
    return [{"name": f, "path": os.path.join(BACKUP_DIR, f),
             "size_kb": round(os.path.getsize(os.path.join(BACKUP_DIR, f))/1024, 1),
             "modified": time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(os.path.join(BACKUP_DIR, f))))} for f in files]

def db_stats():
    conn = get_connection()
    tables = ["academic_years","terms","courses","subjects","blocks","rooms","staff",
              "exam_sessions","timetable","namelist","seating","staff_duty","attendance",
              "qp_inventory","qp_distribution","internal_marks","duty_heads","remuneration_rates","staff_remuneration","users"]
    stats = {"total_rows": 0, "db_size_kb": round(os.path.getsize(DB_PATH)/1024, 1),
             "wal_mode": conn.execute("PRAGMA journal_mode").fetchone()[0],
             "tables": {}}
    for t in tables:
        try:
            cnt = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            stats["tables"][t] = cnt
            stats["total_rows"] += cnt
        except:
            stats["tables"][t] = 0
    conn.close()
    return stats
