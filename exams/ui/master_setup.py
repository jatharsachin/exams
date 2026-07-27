"""
Master Setup Module - Courses, Subjects, Blocks/Rooms, Staff
"""

import tkinter as tk
from tkinter import ttk, messagebox
from database import get_all, insert, update, delete, query


class MasterSetupFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        ttk.Label(self, text="Master Setup", style="Header.TLabel").pack(anchor="w", pady=(10, 5))

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        self._tab_courses()
        self._tab_subjects()
        self._tab_rooms()
        self._tab_staff()

    def refresh(self):
        pass

    def _tab_courses(self):
        f = ttk.Frame(self.notebook)
        self.notebook.add(f, text="Courses & Semesters")

        # Input frame
        inp = ttk.LabelFrame(f, text="Add / Edit Course", padding=10)
        inp.pack(fill="x", padx=5, pady=5)

        ttk.Label(inp, text="Course Code:").grid(row=0, col=0, sticky="w", pady=3)
        self.ccode = ttk.Entry(inp, width=20)
        self.ccode.grid(row=0, col=1, padx=5, pady=3)

        ttk.Label(inp, text="Course Name:").grid(row=0, col=2, sticky="w", pady=3)
        self.cname = ttk.Entry(inp, width=30)
        self.cname.grid(row=0, col=3, padx=5, pady=3)

        ttk.Label(inp, text="Faculty:").grid(row=1, col=0, sticky="w", pady=3)
        self.cfaculty = ttk.Combobox(inp, values=["Science & Technology", "Commerce & Management", "Humanities", "Inter-Disciplinary"], width=28)
        self.cfaculty.grid(row=1, col=1, padx=5, pady=3)

        ttk.Label(inp, text="Duration (Years):").grid(row=1, col=2, sticky="w", pady=3)
        self.cdur = ttk.Combobox(inp, values=["2", "3", "4", "5"], width=8)
        self.cdur.grid(row=1, col=3, padx=5, pady=3)
        self.cdur.set("3")

        btnf = ttk.Frame(inp)
        btnf.grid(row=2, col=0, columnspan=4, pady=10)
        ttk.Button(btnf, text="Add Course", command=self._add_course).pack(side="left", padx=5)
        ttk.Button(btnf, text="Update Selected", command=self._update_course).pack(side="left", padx=5)
        ttk.Button(btnf, text="Delete Selected", command=self._delete_course).pack(side="left", padx=5)

        # Course tree
        self.ctree = ttk.Treeview(f, columns=("id", "code", "name", "faculty", "dur"), show="headings", height=10)
        self.ctree.pack(fill="both", expand=True, padx=5, pady=5)
        for col, hdr in [("id","ID"), ("code","Code"), ("name","Name"), ("faculty","Faculty"), ("dur","Years")]:
            self.ctree.heading(col, text=hdr)
            self.ctree.column(col, width=100 if col != "name" else 250)
        self.ctree.column("id", width=40)

        self.ctree.bind("<<TreeviewSelect>>", self._on_course_select)
        self._refresh_courses()

    def _refresh_courses(self):
        self.ctree.delete(*self.ctree.get_children())
        for c in get_all("courses"):
            self.ctree.insert("", "end", values=(c["id"], c["code"], c["name"], c["faculty"], c["duration_years"]))

    def _on_course_select(self, evt):
        sel = self.ctree.selection()
        if sel:
            vals = self.ctree.item(sel[0], "values")
            self.ccode.delete(0, "end"); self.ccode.insert(0, vals[1])
            self.cname.delete(0, "end"); self.cname.insert(0, vals[2])
            self.cfaculty.set(vals[3])
            self.cdur.set(vals[4])

    def _add_course(self):
        code, name, fac, dur = self.ccode.get().strip(), self.cname.get().strip(), self.cfaculty.get(), self.cdur.get()
        if not code or not name:
            messagebox.showwarning("Validation", "Code and Name required")
            return
        try:
            insert("courses", {"code": code, "name": name, "faculty": fac, "duration_years": int(dur)})
            self._refresh_courses()
            messagebox.showinfo("Success", "Course added")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _update_course(self):
        sel = self.ctree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a course first")
            return
        cid = self.ctree.item(sel[0], "values")[0]
        update("courses", {"code": self.ccode.get().strip(), "name": self.cname.get().strip(),
                           "faculty": self.cfaculty.get(), "duration_years": int(self.cdur.get())}, cid)
        self._refresh_courses()
        messagebox.showinfo("Success", "Course updated")

    def _delete_course(self):
        sel = self.ctree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a course to delete")
            return
        if messagebox.askyesno("Confirm", "Delete this course? Related subjects will also be deleted."):
            delete("courses", self.ctree.item(sel[0], "values")[0])
            self._refresh_courses()

    def _tab_subjects(self):
        f = ttk.Frame(self.notebook)
        self.notebook.add(f, text="Subjects")

        inp = ttk.LabelFrame(f, text="Add / Edit Subject", padding=10)
        inp.pack(fill="x", padx=5, pady=5)

        r = 0
        ttk.Label(inp, text="Subject Code:").grid(row=r, col=0, sticky="w", pady=3)
        self.scode = ttk.Entry(inp, width=20)
        self.scode.grid(row=r, col=1, padx=5, pady=3)

        ttk.Label(inp, text="Subject Name:").grid(row=r, col=2, sticky="w", pady=3)
        self.sname = ttk.Entry(inp, width=30)
        self.sname.grid(row=r, col=3, padx=5, pady=3)

        r = 1
        ttk.Label(inp, text="Course:").grid(row=r, col=0, sticky="w", pady=3)
        self.scourse = ttk.Combobox(inp, width=28)
        self.scourse.grid(row=r, col=1, padx=5, pady=3)
        self._populate_courses_combo(self.scourse)

        ttk.Label(inp, text="Paper No:").grid(row=r, col=2, sticky="w", pady=3)
        self.spaper = ttk.Entry(inp, width=8)
        self.spaper.grid(row=r, col=3, padx=5, pady=3)
        self.spaper.insert(0, "1")

        r = 2
        ttk.Label(inp, text="Type:").grid(row=r, col=0, sticky="w", pady=3)
        self.stype = ttk.Combobox(inp, values=["Theory", "Practical", "Oral", "Project", "Internal", "Termwork"], width=28)
        self.stype.grid(row=r, col=1, padx=5, pady=3)
        self.stype.set("Theory")

        ttk.Label(inp, text="Credits:").grid(row=r, col=2, sticky="w", pady=3)
        self.scredits = ttk.Entry(inp, width=8)
        self.scredits.grid(row=r, col=3, padx=5, pady=3)
        self.scredits.insert(0, "4")

        r = 3
        ttk.Label(inp, text="Max Internal:").grid(row=r, col=0, sticky="w", pady=3)
        self.sint = ttk.Entry(inp, width=8)
        self.sint.grid(row=r, col=1, padx=5, pady=3)
        self.sint.insert(0, "15")

        ttk.Label(inp, text="Max External:").grid(row=r, col=2, sticky="w", pady=3)
        self.sext = ttk.Entry(inp, width=8)
        self.sext.grid(row=r, col=3, padx=5, pady=3)
        self.sext.insert(0, "70")

        btnf = ttk.Frame(inp)
        btnf.grid(row=4, col=0, columnspan=4, pady=8)
        ttk.Button(btnf, text="Add Subject", command=self._add_subject).pack(side="left", padx=5)
        ttk.Button(btnf, text="Update Selected", command=self._update_subject).pack(side="left", padx=5)
        ttk.Button(btnf, text="Delete Selected", command=self._delete_subject).pack(side="left", padx=5)

        self.stree = ttk.Treeview(f, columns=("id","code","name","course","type","credits"), show="headings", height=10)
        self.stree.pack(fill="both", expand=True, padx=5, pady=5)
        for ci, (c, h, w) in enumerate([("id","ID",40),("code","Code",100),("name","Subject",250),
                                         ("course","Course",200),("type","Type",80),("credits","Cred",50)]):
            self.stree.heading(c, text=h); self.stree.column(c, width=w)
        self.stree.bind("<<TreeviewSelect>>", self._on_subj_select)
        self._refresh_subjects()

    def _populate_courses_combo(self, combo):
        courses = get_all("courses")
        combo["values"] = [f"{c['code']} - {c['name']}" for c in courses]

    def _refresh_subjects(self):
        self.stree.delete(*self.stree.get_children())
        rows = query("SELECT s.id, s.code, s.name, c.name as cname, s.type, s.credits "
                     "FROM subjects s JOIN courses c ON s.course_id=c.id ORDER BY s.code")
        for r in rows:
            self.stree.insert("", "end", values=(r["id"],r["code"],r["name"],r["cname"],r["type"],r["credits"]))

    def _on_subj_select(self, evt):
        sel = self.stree.selection()
        if sel:
            vals = self.stree.item(sel[0], "values")
            self.scode.delete(0,"end"); self.scode.insert(0, vals[1])
            self.sname.delete(0,"end"); self.sname.insert(0, vals[2])
            self.scourse.set("")
            self.stype.set(vals[4])
            self.spaper.delete(0,"end"); self.spaper.insert(0, "1")
            self.scredits.delete(0,"end"); self.scredits.insert(0, str(vals[5]))
            row = query("SELECT c.code||' - '||c.name as fullname FROM subjects s JOIN courses c ON s.course_id=c.id WHERE s.id=?", (vals[0],))
            if row:
                self.scourse.set(row[0]["fullname"])

    def _get_course_id(self, val):
        if " - " in val:
            code = val.split(" - ")[0]
            r = query("SELECT id FROM courses WHERE code=?", (code,))
            return r[0]["id"] if r else None
        return None

    def _add_subject(self):
        try:
            cid = self._get_course_id(self.scourse.get())
            insert("subjects", {
                "code": self.scode.get().strip(), "name": self.sname.get().strip(),
                "course_id": cid, "paper_no": int(self.spaper.get()),
                "type": self.stype.get(), "credits": int(self.scredits.get()),
                "max_internal": int(self.sint.get()), "max_external": int(self.sext.get())
            })
            self._refresh_subjects()
            messagebox.showinfo("Success", "Subject added")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _update_subject(self):
        sel = self.stree.selection()
        if not sel: return
        sid = self.stree.item(sel[0], "values")[0]
        cid = self._get_course_id(self.scourse.get())
        update("subjects", {
            "code": self.scode.get().strip(), "name": self.sname.get().strip(),
            "course_id": cid, "paper_no": int(self.spaper.get()),
            "type": self.stype.get(), "credits": int(self.scredits.get()),
            "max_internal": int(self.sint.get()), "max_external": int(self.sext.get())
        }, sid)
        self._refresh_subjects()
        messagebox.showinfo("Success", "Subject updated")

    def _delete_subject(self):
        sel = self.stree.selection()
        if not sel: return
        if messagebox.askyesno("Confirm", "Delete this subject?"):
            delete("subjects", self.stree.item(sel[0], "values")[0])
            self._refresh_subjects()

    def _tab_rooms(self):
        f = ttk.Frame(self.notebook)
        self.notebook.add(f, text="Rooms & Blocks")

        panes = ttk.PanedWindow(f, orient="horizontal")
        panes.pack(fill="both", expand=True, padx=5, pady=5)

        # Left: Blocks
        blf = ttk.LabelFrame(panes, text="Blocks", padding=8)
        panes.add(blf, weight=1)

        ttk.Label(blf, text="Block Name:").pack(anchor="w")
        self.blkname = ttk.Entry(blf)
        self.blkname.pack(fill="x", pady=2)
        ttk.Label(blf, text="Floor:").pack(anchor="w")
        self.blkfloor = ttk.Entry(blf)
        self.blkfloor.pack(fill="x", pady=2)

        bf = ttk.Frame(blf)
        bf.pack(fill="x", pady=5)
        ttk.Button(bf, text="Add Block", command=self._add_block).pack(side="left", padx=2)
        ttk.Button(bf, text="Delete Block", command=self._delete_block).pack(side="left", padx=2)

        self.blktree = ttk.Treeview(blf, columns=("id","name","floor"), show="headings", height=6)
        self.blktree.pack(fill="both", expand=True, pady=5)
        self.blktree.heading("id", text="ID"); self.blktree.column("id", width=40)
        self.blktree.heading("name", text="Name"); self.blktree.column("name", width=120)
        self.blktree.heading("floor", text="Floor"); self.blktree.column("floor", width=80)
        self._refresh_blocks()

        # Right: Rooms
        rmf = ttk.LabelFrame(panes, text="Rooms", padding=8)
        panes.add(rmf, weight=2)

        ttk.Label(rmf, text="Room Name:").pack(anchor="w")
        self.rmname = ttk.Entry(rmf)
        self.rmname.pack(fill="x", pady=2)

        ttk.Label(rmf, text="Block:").pack(anchor="w")
        self.rmblock = ttk.Combobox(rmf)
        self.rmblock.pack(fill="x", pady=2)

        ttk.Label(rmf, text="Capacity (Students):").pack(anchor="w")
        self.rmcap = ttk.Entry(rmf)
        self.rmcap.pack(fill="x", pady=2)

        ttk.Label(rmf, text="Bench Count:").pack(anchor="w")
        self.rmbench = ttk.Entry(rmf)
        self.rmbench.pack(fill="x", pady=2)

        rf = ttk.Frame(rmf)
        rf.pack(fill="x", pady=5)
        ttk.Button(rf, text="Add Room", command=self._add_room).pack(side="left", padx=2)
        ttk.Button(rf, text="Update Room", command=self._update_room).pack(side="left", padx=2)
        ttk.Button(rf, text="Delete Room", command=self._delete_room).pack(side="left", padx=2)

        self.rmtree = ttk.Treeview(rmf, columns=("id","name","block","capacity","bench"), show="headings", height=10)
        self.rmtree.pack(fill="both", expand=True, pady=5)
        self.rmtree.heading("id", text="ID"); self.rmtree.column("id", width=40)
        self.rmtree.heading("name", text="Room"); self.rmtree.column("name", width=100)
        self.rmtree.heading("block", text="Block"); self.rmtree.column("block", width=100)
        self.rmtree.heading("capacity", text="Capacity"); self.rmtree.column("capacity", width=70)
        self.rmtree.heading("bench", text="Benches"); self.rmtree.column("bench", width=70)
        self.rmtree.bind("<<TreeviewSelect>>", self._on_room_select)
        self._refresh_rooms()

    def _refresh_blocks(self):
        self.blktree.delete(*self.blktree.get_children())
        for b in get_all("blocks"):
            self.blktree.insert("", "end", values=(b["id"], b["name"], b["floor"] or ""))
        blocks = get_all("blocks")
        self.rmblock["values"] = [b["name"] for b in blocks]

    def _refresh_rooms(self):
        self.rmtree.delete(*self.rmtree.get_children())
        rows = query("SELECT r.id, r.name, b.name as bname, r.capacity, r.bench_count "
                     "FROM rooms r JOIN blocks b ON r.block_id=b.id ORDER BY b.name, r.name")
        for r in rows:
            self.rmtree.insert("", "end", values=(r["id"],r["name"],r["bname"],r["capacity"],r["bench_count"]))

    def _on_room_select(self, evt):
        sel = self.rmtree.selection()
        if sel:
            vals = self.rmtree.item(sel[0], "values")
            self.rmname.delete(0,"end"); self.rmname.insert(0, vals[1])
            self.rmblock.set(vals[2])
            self.rmcap.delete(0,"end"); self.rmcap.insert(0, str(vals[3]))
            self.rmbench.delete(0,"end"); self.rmbench.insert(0, str(vals[4]))

    def _add_block(self):
        name = self.blkname.get().strip()
        if not name: return
        try:
            insert("blocks", {"name": name, "floor": self.blkfloor.get().strip()})
            self._refresh_blocks()
            self.blkname.delete(0,"end"); self.blkfloor.delete(0,"end")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _delete_block(self):
        sel = self.blktree.selection()
        if sel and messagebox.askyesno("Confirm", "Delete block and its rooms?"):
            delete("blocks", self.blktree.item(sel[0],"values")[0])
            self._refresh_blocks()
            self._refresh_rooms()

    def _add_room(self):
        try:
            blk = query("SELECT id FROM blocks WHERE name=?", (self.rmblock.get(),))
            if not blk: return messagebox.showwarning("Error", "Select a block")
            insert("rooms", {"name": self.rmname.get().strip(), "block_id": blk[0]["id"],
                             "capacity": int(self.rmcap.get()), "bench_count": int(self.rmbench.get())})
            self._refresh_rooms()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _update_room(self):
        sel = self.rmtree.selection()
        if not sel: return
        rid = self.rmtree.item(sel[0],"values")[0]
        blk = query("SELECT id FROM blocks WHERE name=?", (self.rmblock.get(),))
        if not blk: return
        update("rooms", {"name": self.rmname.get().strip(), "block_id": blk[0]["id"],
                         "capacity": int(self.rmcap.get()), "bench_count": int(self.rmbench.get())}, rid)
        self._refresh_rooms()

    def _delete_room(self):
        sel = self.rmtree.selection()
        if sel and messagebox.askyesno("Confirm", "Delete this room?"):
            delete("rooms", self.rmtree.item(sel[0],"values")[0])
            self._refresh_rooms()

    def _tab_staff(self):
        f = ttk.Frame(self.notebook)
        self.notebook.add(f, text="Staff")

        inp = ttk.LabelFrame(f, text="Add / Edit Staff", padding=10)
        inp.pack(fill="x", padx=5, pady=5)

        fields = [
            ("Name:", "st_name", 0, 0),
            ("Designation:", "st_desig", 0, 2),
            ("Department:", "st_dept", 1, 0),
            ("Mobile:", "st_mob", 1, 2),
            ("Role:", "st_role", 2, 0),
            ("Email:", "st_email", 2, 2),
        ]
        for lbl, attr, r, c in fields:
            ttk.Label(inp, text=lbl).grid(row=r, column=c, sticky="w", pady=3)
            ent = ttk.Entry(inp, width=25) if "role" not in attr else ttk.Combobox(inp,
                values=["Principal","CEO","Senior Supervisor","Junior Supervisor","Peon","HOD","Clerk","Other"], width=23)
            ent.grid(row=r, column=c+1, padx=5, pady=3)
            setattr(self, attr, ent)
        if hasattr(self, "st_role") and isinstance(self.st_role, ttk.Combobox):
            self.st_role.set("Junior Supervisor")

        bf = ttk.Frame(inp)
        bf.grid(row=3, col=0, columnspan=4, pady=8)
        ttk.Button(bf, text="Add Staff", command=self._add_staff).pack(side="left", padx=5)
        ttk.Button(bf, text="Update Selected", command=self._update_staff).pack(side="left", padx=5)
        ttk.Button(bf, text="Delete Selected", command=self._delete_staff).pack(side="left", padx=5)
        ttk.Button(bf, text="Add 8 Demo Staff", command=self._add_demo_staff).pack(side="left", padx=5)

        self.stftree = ttk.Treeview(f, columns=("id","name","designation","dept","mobile","role"), show="headings", height=10)
        self.stftree.pack(fill="both", expand=True, padx=5, pady=5)
        for ci, (c,h,w) in enumerate([("id","ID",40),("name","Name",200),("designation","Designation",150),
                                        ("dept","Dept",100),("mobile","Mobile",100),("role","Role",140)]):
            self.stftree.heading(c, text=h); self.stftree.column(c, width=w)
        self.stftree.bind("<<TreeviewSelect>>", self._on_staff_select)
        self._refresh_staff()

    def _refresh_staff(self):
        self.stftree.delete(*self.stftree.get_children())
        for s in get_all("staff"):
            self.stftree.insert("", "end", values=(s["id"],s["name"],s["designation"] or "",s["department"] or "",
                                                    s["mobile"] or "",s["role"]))

    def _on_staff_select(self, evt):
        sel = self.stftree.selection()
        if sel:
            vals = self.stftree.item(sel[0], "values")
            for attr, idx in [("st_name",1),("st_desig",2),("st_dept",3),("st_mob",4),("st_role",5),("st_email",6)]:
                ent = getattr(self, attr, None)
                if ent:
                    ent.delete(0,"end")
                    ent.insert(0, vals[idx] if idx < len(vals) and vals[idx] else "")
                    if idx == 5 and isinstance(ent, ttk.Combobox):
                        ent.set(vals[idx] if vals[idx] else "")

    def _add_staff(self):
        try:
            insert("staff", {
                "name": self.st_name.get().strip(), "designation": self.st_desig.get().strip(),
                "department": self.st_dept.get().strip(), "mobile": self.st_mob.get().strip(),
                "email": self.st_email.get().strip(), "role": self.st_role.get()
            })
            self._refresh_staff()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _update_staff(self):
        sel = self.stftree.selection()
        if not sel: return
        sid = self.stftree.item(sel[0], "values")[0]
        update("staff", {"name":self.st_name.get().strip(), "designation":self.st_desig.get().strip(),
                         "department":self.st_dept.get().strip(), "mobile":self.st_mob.get().strip(),
                         "email":self.st_email.get().strip(), "role":self.st_role.get()}, sid)
        self._refresh_staff()

    def _delete_staff(self):
        sel = self.stftree.selection()
        if sel and messagebox.askyesno("Confirm", "Delete this staff?"):
            delete("staff", self.stftree.item(sel[0],"values")[0])
            self._refresh_staff()

    def _add_demo_staff(self):
        demo = [
            ("Dr. Anil Patil","Principal","Administration","9876543201","Principal"),
            ("Prof. Sunil Joshi","Associate Prof","Mathematics","9876543202","CEO"),
            ("Dr. Meena More","HOD","Physics","9876543203","Senior Supervisor"),
            ("Prof. Ramesh Kulkarni","Asst Prof","Chemistry","9876543204","Senior Supervisor"),
            ("Prof. Smita Desai","Asst Prof","Botany","9876543205","Junior Supervisor"),
            ("Prof. Amit Bhosale","Asst Prof","Zoology","9876543206","Junior Supervisor"),
            ("Prof. Neha Sharma","Asst Prof","English","9876543207","Junior Supervisor"),
            ("Mr. Raju Jadhav","Peon","General","9876543208","Peon"),
            ("Mr. Mahesh Shinde","Peon","General","9876543209","Peon"),
        ]
        for name, desig, dept, mob, role in demo:
            try:
                insert("staff", {"name":name,"designation":desig,"department":dept,"mobile":mob,"role":role})
            except:
                pass
        self._refresh_staff()
        messagebox.showinfo("Done", "Demo staff added successfully")
