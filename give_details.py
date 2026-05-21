from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
from tkinter import messagebox
import sqlite3
import cv2
import face_recognition
import os
from tkinter import filedialog
import pickle
import json

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "app_config.json")
DB_FILE     = os.path.join(BASE_DIR, "attendance.db")


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config(data: dict):
    """Persist config dict to JSON file."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_image_folder(root_window) -> str:
    config = load_config()
    folder = config.get("image_folder", "")

    if folder and os.path.isdir(folder):
        return folder

    messagebox.showinfo(
        "Image Folder Setup",
        "Please select or create a folder where student images will be stored.\n\n"
        "This will only be asked once.",
        parent=root_window,
    )

    chosen = filedialog.askdirectory(
        title="Select / Create Image Folder",
        parent=root_window,
        mustexist=False,
    )

    if not chosen:
        chosen = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
        messagebox.showwarning(
            "Default folder used",
            f"No folder was selected.\nUsing default:\n{chosen}",
            parent=root_window,
        )

    os.makedirs(chosen, exist_ok=True)
    config["image_folder"] = chosen
    save_config(config)
    return chosen


def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db():

    conn = get_db_connection()
    cur  = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS student (
            Department  TEXT NOT NULL,
            Course      TEXT NOT NULL,
            year        TEXT NOT NULL,
            sem         TEXT NOT NULL,
            id          TEXT PRIMARY KEY NOT NULL,
            name        TEXT NOT NULL,
            email       TEXT NOT NULL,
            phone       TEXT NOT NULL,
            image       TEXT
        )
    """)

    # attendance table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id       TEXT NOT NULL,
            attendance_date  TEXT,
            attendance_time  TEXT,
            state            INTEGER DEFAULT 0,
            FOREIGN KEY (student_id) REFERENCES student(id)
        )
    """)

    conn.commit()
    conn.close()


class details:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1530x790+0+0")
        self.root.title("Student Details")
        self.root.config(bg="#0f172a")

        init_db()
        self.IMAGE_FOLDER = get_image_folder(self.root)

        self.Department_var  = StringVar()
        self.Course_var      = StringVar()
        self.year_var        = StringVar()
        self.sem_var         = StringVar()
        self.id_var          = StringVar()
        self.name_var        = StringVar()
        self.email_var       = StringVar()
        self.phone_var       = StringVar()
        self.image_var       = StringVar()
        self.search_var      = StringVar()
        self.search_bar_var  = StringVar()

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground="white", background="white",
                        foreground="black", padding=5)
        style.configure("Treeview", background="#f8fafc", foreground="black",
                        rowheight=28, fieldbackground="#f8fafc",
                        font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background="#2563eb", foreground="white",
                        font=("Segoe UI", 11, "bold"))
        style.map("Treeview", background=[("selected", "#3b82f6")])

        main_lbl = Label(self.root, text="STUDENT  MANAGEMENT  SYSTEM",
                         font=("Segoe UI", 30, "bold"), bg="#0f172a", fg="white")
        main_lbl.place(x=0, y=50, width=1530, height=45)

        footer_lbl = Label(self.root, text="face recognition attendance system",
                           font=("Segoe UI", 12), bg="gray", fg="white")
        footer_lbl.place(x=1230, y=740, width=270, height=25)

        main_frame = Frame(self.root, bd=0, bg="#1e293b")
        main_frame.place(x=20, y=125, width=1480, height=600)

        left_frame = LabelFrame(main_frame, text="Student Details",
                                font=("Segoe UI", 14, "bold"),
                                bg="#1e293b", fg="white", bd=3)
        left_frame.place(x=10, y=10, width=730, height=580)

        img1 = Image.open(os.path.join(BASE_DIR, "banner.png"))
        img1 = img1.resize((400, 190), Image.LANCZOS)
        self.photoimg1 = ImageTk.PhotoImage(img1)
        f_lbl1 = Label(left_frame, image=self.photoimg1)
        f_lbl1.place(x=40, y=8, width=650, height=190)

        curr_course_frame = LabelFrame(left_frame, bd=2, relief=RIDGE,
                                       text="Current Course Details",
                                       font=("Segoe UI", 12, "bold"), bg="#334155")
        curr_course_frame.place(x=5, y=210, width=720, height=135)

        dept_lbl = Label(curr_course_frame, text="Department",
                         font=("Segoe UI", 12, "bold"), bg="#334155", fg="white")
        dept_lbl.grid(row=0, column=0, padx=10, sticky=W)
        dept_comb = ttk.Combobox(curr_course_frame, font=("Segoe UI", 12, "bold"),
                                 textvariable=self.Department_var, width=17, state="readonly")
        dept_comb["values"] = ("Select department", "Computer", "IT", "Civil",
                               "Mechanical", "ECE", "Electrical", "IP", "BME")
        dept_comb.current(0)
        dept_comb.grid(row=0, column=1, padx=2, pady=10, sticky=W)

        course_lbl = Label(curr_course_frame, text="Course",
                           font=("Segoe UI", 12, "bold"), fg="white", bg="#334155")
        course_lbl.grid(row=0, column=2, padx=10, sticky=W)
        course_comb = ttk.Combobox(curr_course_frame, font=("Segoe UI", 12, "bold"),
                                   textvariable=self.Course_var, width=17, state="readonly")
        course_comb["values"] = ("Select course", "B Tech", "M Tech", "Reasearch")
        course_comb.current(0)
        course_comb.grid(row=0, column=3, padx=2, pady=10, sticky=W)

        semester_lbl = Label(curr_course_frame, text="Semester",
                             font=("Segoe UI", 12, "bold"), fg="white", bg="#334155")
        semester_lbl.grid(row=1, column=0, padx=10, sticky=W)
        semester_comb = ttk.Combobox(curr_course_frame, font=("Segoe UI", 12, "bold"),
                                     width=17, state="readonly", textvariable=self.sem_var)
        semester_comb["values"] = ("Select Semester", "1", "2", "3", "4", "5", "6", "7", "8")
        semester_comb.current(0)
        semester_comb.grid(row=1, column=1, padx=2, pady=10, sticky=W)

        year_lbl = Label(curr_course_frame, text="Year",
                         font=("Segoe UI", 12, "bold"), bg="#334155", fg="white")
        year_lbl.grid(row=1, column=2, padx=10, sticky=W)
        year_comb = ttk.Combobox(curr_course_frame, font=("Segoe UI", 12, "bold"),
                                 width=17, state="readonly", textvariable=self.year_var)
        year_comb["values"] = ("Select Year", "1", "2", "3", "4")
        year_comb.current(0)
        year_comb.grid(row=1, column=3, padx=2, pady=10, sticky=W)

        # Student Details
        class_frame = LabelFrame(left_frame, bd="2", relief=RIDGE,
                                 text="Student Details",
                                 font=("Segoe UI", 12, "bold"), bg="#334155")
        class_frame.place(x=5, y=350, width=720, height=200)

        label_style = {"font": ("Segoe UI", 11, "bold"), "bg": "#334155", "fg": "white"}

        student_id_lbl = Label(class_frame, text="Student Id", **label_style)
        student_id_lbl.grid(row=0, column=0, padx=10, pady=5, sticky=W)
        student_id_entry = ttk.Entry(class_frame, font=("Segoe UI", 10),
                                     width=25, textvariable=self.id_var)
        student_id_entry.grid(row=0, column=1, padx=15, pady=5, sticky=W)

        name_lbl = Label(class_frame, text="Name", **label_style)
        name_lbl.grid(row=0, column=2, padx=10, pady=5, sticky=W)
        name_entry = ttk.Entry(class_frame, font=("Segoe UI", 10),
                               width=25, textvariable=self.name_var)
        name_entry.grid(row=0, column=3, padx=15, pady=5, sticky=W)

        phone_lbl = Label(class_frame, text="Phone No.", **label_style)
        phone_lbl.grid(row=1, column=0, padx=10, pady=5, sticky=W)
        phone_entry = ttk.Entry(class_frame, font=("Segoe UI", 10),
                                width=25, textvariable=self.phone_var)
        phone_entry.grid(row=1, column=1, padx=15, pady=5, sticky=W)

        email_lbl = Label(class_frame, text="Email", **label_style)
        email_lbl.grid(row=1, column=2, padx=10, pady=5, sticky=W)
        email_entry = ttk.Entry(class_frame, font=("Segoe UI", 10),
                                width=25, textvariable=self.email_var)
        email_entry.grid(row=1, column=3, padx=15, pady=5, sticky=W)

        self.image_entry = Entry(class_frame, font=("Segoe UI", 10),
                                 textvariable=self.image_var)

        btn_style = {
            "bg": "#2563eb", "fg": "white", "cursor": "hand2", "bd": 0,
            "activebackground": "#1d4ed8", "activeforeground": "white",
        }

        btn_frame = Frame(class_frame, bd=2, relief=RIDGE, bg="white")
        btn_frame.place(x=0, y=100, width=715, height=70)

        reset_btn = Button(btn_frame, text="Reset", width=23, command=self.reset,
                           **btn_style, font=("Segoe UI", 13, "bold"))
        reset_btn.grid(row=0, column=0)

        update_btn = Button(btn_frame, text="Update", width=23, command=self.update,
                            **btn_style, font=("Segoe UI", 13, "bold"))
        update_btn.grid(row=0, column=1, padx=1)

        delete_btn = Button(btn_frame, text="Delete", width=24, command=self.delete,
                            **btn_style, font=("Segoe UI", 13, "bold"))
        delete_btn.grid(row=0, column=2)

        btn_frame1 = Frame(class_frame, bd=2, relief=RIDGE, bg="white")
        btn_frame1.place(x=0, y=135, width=715, height=35)

        take_photo_btn = Button(btn_frame1, text="Take photo sample and Save", width=32,
                                command=self.take_image, **btn_style,
                                font=("Segoe UI", 14, "bold"))
        take_photo_btn.grid(row=1, column=0)

        update_photo_btn = Button(btn_frame1, text="Update photo", width=32,
                                  command=self.update_image, **btn_style,
                                  font=("Segoe UI", 14, "bold"))
        update_photo_btn.grid(row=1, column=1, padx=1)

        right_frame = LabelFrame(main_frame, text="Student Database",
                                 font=("Segoe UI", 14, "bold"),
                                 bg="#1e293b", fg="white", bd=3)
        right_frame.place(x=750, y=10, width=720, height=580)

        self.image_lbl = Label(right_frame,
                               text="No image\n (Click on any field to get it image)",
                               font=("Segoe UI", 12), bg="#475569", fg="white",
                               relief=RIDGE, bd=3)
        self.image_lbl.place(x=135, y=3, width=450, height=220)

        search_frame = LabelFrame(right_frame, text="Search Student",
                                  font=("Segoe UI", 10, "bold"),
                                  bg="#334155", fg="white", bd=2)
        search_frame.place(x=5, y=225, width=710, height=70)

        search_label = Label(search_frame, text="Search",
                             font=("Segoe UI", 13, "bold"), bg="#334155", fg="white")
        search_label.grid(row=0, column=0, padx=10, sticky=W)

        self.search_combo = ttk.Combobox(search_frame, textvariable=self.search_var,
                                         width=18, state="readonly",
                                         font=("Segoe UI", 10))
        self.search_combo["values"] = ("Select", "Department", "Course", "year",
                                       "sem", "id", "email", "name", "phone")
        self.search_combo.current(0)
        self.search_combo.grid(row=0, column=1, pady=10, sticky=W)

        self.search_entry = ttk.Entry(search_frame, font=("Segoe UI", 13),
                                      width=25, textvariable=self.search_bar_var)
        self.search_entry.grid(row=0, column=2, padx=10, sticky=W)

        self.search_btn = Button(search_frame, text="Search", width=11,
                                 font=("Segoe UI", 12), command=self.search_row,
                                 **btn_style)
        self.search_btn.grid(row=0, column=3)

        self.show_all_btn = Button(search_frame, text="Show all", width=11,
                                   font=("Segoe UI", 12), **btn_style,
                                   command=self.show_all)
        self.show_all_btn.grid(row=0, column=4, padx=5, pady=5, sticky=W)

        table_frame = LabelFrame(right_frame, bd=2, bg="white")
        table_frame.place(x=5, y=300, width=710, height=250)

        scroll_x = ttk.Scrollbar(table_frame, orient=HORIZONTAL)
        scroll_y = ttk.Scrollbar(table_frame, orient=VERTICAL)

        self.student_table = ttk.Treeview(
            table_frame,
            columns=("dep", "course", "year", "sem", "id", "name", "email", "phone"),
            xscrollcommand=scroll_x.set,
            yscrollcommand=scroll_y.set,
        )
        scroll_x.pack(side=BOTTOM, fill=X)
        scroll_y.pack(side=RIGHT, fill=Y)
        scroll_x.config(command=self.student_table.xview)
        scroll_y.config(command=self.student_table.yview)

        self.student_table.heading("dep",    text="department")
        self.student_table.heading("course", text="course")
        self.student_table.heading("year",   text="year")
        self.student_table.heading("sem",    text="semester")
        self.student_table.heading("id",     text="id")
        self.student_table.heading("name",   text="Name")
        self.student_table.heading("email",  text="email")
        self.student_table.heading("phone",  text="Phone")
        self.student_table["show"] = "headings"

        for col in ("dep", "course", "year", "sem", "id", "name", "email", "phone"):
            self.student_table.column(col, width=100)

        self.student_table.pack(fill=BOTH, expand=1)
        self.student_table.bind("<ButtonRelease>", self.get_cursor)
        self.fetch_data()

    def _img_path(self, filename: str) -> str:
        return os.path.join(self.IMAGE_FOLDER, filename)

    def remove_encoding_for_id(self, student_id):
        encode_file = os.path.join(BASE_DIR, "EncodeFile.p")
        if not os.path.exists(encode_file):
            return
        try:
            with open(encode_file, "rb") as f:
                encodeListKnown, studentIds = pickle.load(f)
            if student_id not in studentIds:
                return
            idx = studentIds.index(student_id)
            encodeListKnown.pop(idx)
            studentIds.pop(idx)
            with open(encode_file, "wb") as f:
                pickle.dump([encodeListKnown, studentIds], f)
            print(f"Encoding removed for student ID: {student_id}")
        except Exception as e:
            print(f"Warning: Could not update encoding file — {e}")

    def validate_fields(self):
        if not self.id_var.get().isdigit() or len(self.id_var.get()) != 6:
            messagebox.showerror("Error", "Student ID must be exactly 6 digits",
                                 parent=self.root)
            return False
        if not self.phone_var.get().isdigit() or len(self.phone_var.get()) != 10:
            messagebox.showerror("Error", "Phone number must be exactly 10 digits",
                                 parent=self.root)
            return False
        email = self.email_var.get()
        if "@" not in email or "." not in email:
            messagebox.showerror("Error", "Enter a valid email address",
                                 parent=self.root)
            return False
        return True

    def add_data(self):
        if (self.Department_var.get() == "Select department"
                or self.Course_var.get()  == "Select course"
                or self.year_var.get()    == "Select Year"
                or self.sem_var.get()     == "Select Semester"
                or self.id_var.get()    == ""
                or self.name_var.get()  == ""
                or self.email_var.get() == ""
                or self.phone_var.get() == ""
                or self.image_var.get() == ""):
            messagebox.showerror("Error", "All fields are required", parent=self.root)
            return

        if not self.validate_fields():
            return

        conn = get_db_connection()
        cur  = conn.cursor()

        cur.execute("SELECT id FROM student WHERE id = ?", (self.id_var.get(),))
        if cur.fetchone():
            messagebox.showerror("Error", "Student ID already exists", parent=self.root)
            conn.close()
            return

        cur.execute(
            "INSERT INTO student VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                self.Department_var.get(), self.Course_var.get(),
                self.year_var.get(),       self.sem_var.get(),
                self.id_var.get(),         self.name_var.get(),
                self.email_var.get(),      self.phone_var.get(),
                self.image_var.get(),
            ),
        )
        cur.execute("INSERT INTO attendance (student_id) VALUES (?)", (self.id_var.get(),))

        conn.commit()
        conn.close()
        self.fetch_data()
        self.image_lbl.config(image="")
        self.image_lbl.config(text="No image found\n Click on any row to see any image")
        self.student_table.selection_remove(self.student_table.selection())
        messagebox.showinfo("Success", "Image and details are successfully saved.",
                            parent=self.root)

    def fetch_data(self):
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("SELECT Department, Course, year, sem, id, name, email, phone "
                    "FROM student")
        data = cur.fetchall()
        conn.close()

        self.student_table.delete(*self.student_table.get_children())
        for row in data:
            self.student_table.insert("", END, values=tuple(row))

    def get_cursor(self, event):
        cursor_focus = self.student_table.focus()
        content = self.student_table.item(cursor_focus)
        data = content["values"]
        if not data:
            return

        self.Department_var.set(data[0])
        self.Course_var.set(data[1])
        self.year_var.set(data[2])
        self.sem_var.set(data[3])
        self.id_var.set(data[4])
        self.name_var.set(data[5])
        self.email_var.set(data[6])
        self.phone_var.set(data[7])

        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("SELECT image FROM student WHERE id = ?", (data[4],))
        row = cur.fetchone()
        conn.close()
        img_name = row["image"] if row else ""
        self.image_var.set(img_name if img_name else "")

        file_path = self._img_path(f"{self.id_var.get()}.jpg")
        try:
            img = Image.open(file_path)
            img = img.resize((450, 220), Image.LANCZOS)
            self.student_photo = ImageTk.PhotoImage(img)
            self.image_lbl.config(image=self.student_photo, text="")
        except Exception:
            self.image_lbl.config(image="")
            self.image_lbl.config(text="No image found\n Click on any row to see any image")

    def reset(self):
        self.Department_var.set("Select department")
        self.Course_var.set("Select course")
        self.year_var.set("Select Year")
        self.sem_var.set("Select Semester")
        self.id_var.set("")
        self.email_var.set("")
        self.name_var.set("")
        self.phone_var.set("")
        self.image_var.set("")
        self.image_lbl.config(image="")
        self.image_lbl.config(text="No image found\n Click on any row to see any image")
        self.student_table.selection_remove(self.student_table.selection())

    def update(self):
        if (self.Department_var.get() == "Select department"
                or self.Course_var.get()  == "Select course"
                or self.year_var.get()    == "Select Year"
                or self.sem_var.get()     == "Select Semester"
                or self.id_var.get()    == ""
                or self.name_var.get()  == ""
                or self.email_var.get() == ""
                or self.phone_var.get() == ""
                or self.image_var.get() == ""):
            messagebox.showerror("Error", "All fields are required", parent=self.root)
            return

        if not self.validate_fields():
            return

        try:
            if not messagebox.askyesno("Update", "Confirm Update", parent=self.root):
                return

            conn = get_db_connection()
            cur  = conn.cursor()
            cur.execute("SELECT id FROM student WHERE id = ?", (self.id_var.get(),))
            if not cur.fetchone():
                messagebox.showerror("Error", "Please first save the details",
                                     parent=self.root)
                conn.close()
                return

            cur.execute(
                "UPDATE student SET Department=?, Course=?, year=?, sem=?, "
                "email=?, name=?, phone=? WHERE id=?",
                (
                    self.Department_var.get(), self.Course_var.get(),
                    self.year_var.get(),       self.sem_var.get(),
                    self.email_var.get(),      self.name_var.get(),
                    self.phone_var.get(),      self.id_var.get(),
                ),
            )
            conn.commit()
            conn.close()
            self.fetch_data()
            messagebox.showinfo("Success", "Successfully Updated the field",
                                parent=self.root)
        except Exception as es:
            messagebox.showerror("Error", str(es), parent=self.root)

    def delete(self):
        if (self.Department_var.get() == "Select department"
                or self.Course_var.get()  == "Select course"
                or self.year_var.get()    == "Select Year"
                or self.sem_var.get()     == "Select Semester"
                or self.id_var.get()    == ""
                or self.name_var.get()  == ""
                or self.email_var.get() == ""
                or self.phone_var.get() == ""):
            messagebox.showerror("Error", "All fields are required", parent=self.root)
            return

        try:
            if not messagebox.askyesno(
                "Delete",
                f"Confirm Deleting details for id: {self.id_var.get()}",
                parent=self.root,
            ):
                return

            conn = get_db_connection()
            cur  = conn.cursor()
            cur.execute("DELETE FROM attendance WHERE student_id = ?", (self.id_var.get(),))
            cur.execute("DELETE FROM student WHERE id = ?", (self.id_var.get(),))

            img_path = self._img_path(f"{self.id_var.get()}.jpg")
            if os.path.exists(img_path):
                os.remove(img_path)
                self.image_var.set("")
                self.image_lbl.config(image="")
                self.image_lbl.config(text="No image found\nClick on any row to see its image")

            conn.commit()
            conn.close()
            self.remove_encoding_for_id(self.id_var.get())
            self.fetch_data()
            messagebox.showinfo("Success", "Deleted the field", parent=self.root)
        except Exception as es:
            messagebox.showerror("Error", f"Due to {str(es)}", parent=self.root)

    def take_image(self):
        if (self.Department_var.get() == "Select department"
                or self.Course_var.get()  == "Select course"
                or self.year_var.get()    == "Select Year"
                or self.sem_var.get()     == "Select Semester"
                or self.id_var.get()    == ""
                or self.name_var.get()  == ""
                or self.email_var.get() == ""
                or self.phone_var.get() == ""):
            messagebox.showerror("Error", "Please first fill all other fields",
                                 parent=self.root)
            return

        if not self.validate_fields():
            return

        if self.image_var.get():
            check     = self.image_var.get().split(".")[0]
            file_path = self._img_path(f"{self.id_var.get()}.jpg")
            old_path  = self._img_path(self.image_var.get())

            if check != self.id_var.get() and os.path.exists(old_path):
                os.remove(old_path)
            elif check == self.id_var.get() and os.path.exists(file_path):
                messagebox.showinfo(
                    "Already saved",
                    "Your photo is already taken. Press update to update the photo.",
                    parent=self.root,
                )
                return
            self.image_var.set("")

        conn = get_db_connection()
        cur  = conn.cursor()
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            messagebox.showerror("Error", "Unable to access camera", parent=self.root)
            conn.close()
            return
        cap.set(3, 640)
        cap.set(4, 480)
        for _ in range(10):
            cap.read()

        while True:
            ret, img = cap.read()
            if not ret:
                break
            cv2.putText(img, "Press 's' to Save Photo", (20, 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(img, "Press 'q' to Abort", (20, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            cv2.imshow("Camera", img)
            key = cv2.waitKey(1)

            if key == ord("s"):
                file_path = self._img_path(f"{self.id_var.get()}.jpg")
                self.image_var.set(f"{self.id_var.get()}.jpg")
                try:
                    self.add_data()
                except Exception as es:
                    print(str(es))
                    self.image_var.set("")
                    messagebox.showerror("Error", str(es), parent=self.root)
                    cap.release()
                    cv2.destroyAllWindows()
                    conn.close()
                    return
                cv2.imwrite(file_path, img)
                break
            elif key == ord("q"):
                break

        cap.release()
        cv2.destroyAllWindows()
        conn.commit()
        conn.close()

    def update_image(self):
        if (self.Department_var.get() == "Select department"
                or self.Course_var.get()  == "Select course"
                or self.year_var.get()    == "Select Year"
                or self.sem_var.get()     == "Select Semester"
                or self.id_var.get()    == ""
                or self.name_var.get()  == ""
                or self.email_var.get() == ""
                or self.phone_var.get() == ""):
            messagebox.showerror("Error", "Please first fill all other fields",
                                 parent=self.root)
            return

        if not self.validate_fields():
            return

        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("SELECT id FROM student WHERE id = ?", (self.id_var.get(),))
        if not cur.fetchone():
            messagebox.showerror("Error", "No field exists with the given id",
                                 parent=self.root)
            conn.close()
            return

        if not messagebox.askyesno("Update", "Confirm Updation of image", parent=self.root):
            conn.close()
            return

        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            messagebox.showerror("Error", "Unable to access camera", parent=self.root)
            conn.close()
            return
        cap.set(3, 640)
        cap.set(4, 480)
        for _ in range(10):
            cap.read()

        while True:
            ret, img = cap.read()
            if not ret:
                break
            cv2.putText(img, "Press 's' to Save Updated Photo", (20, 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(img, "Press 'q' to Abort", (20, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            cv2.imshow("Camera", img)
            key = cv2.waitKey(1)

            if key == ord("s"):
                file_path   = self._img_path(f"{self.id_var.get()}.jpg")
                saving_name = f"{self.id_var.get()}.jpg"
                cv2.imwrite(file_path, img)
                cur.execute("UPDATE student SET image=? WHERE id=?",
                            (saving_name, self.id_var.get()))
                self.image_var.set(saving_name)
                messagebox.showinfo("Success",
                                    "Image updated and saved successfully",
                                    parent=self.root)
                break
            elif key == ord("q"):
                break

        cap.release()
        cv2.destroyAllWindows()
        conn.commit()
        conn.close()

    _VALID_SEARCH_COLS = {
        "Department", "Course", "year", "sem",
        "id", "email", "name", "phone",
    }

    def search_row(self):
        col = self.search_var.get()

        if col not in self._VALID_SEARCH_COLS:
            messagebox.showerror("Error",
                                 "Please select a valid search column",
                                 parent=self.root)
            return

        conn = get_db_connection()
        cur  = conn.cursor()
        try:
            cur.execute(
                f"SELECT Department, Course, year, sem, id, name, email, phone "
                f"FROM student WHERE {col} = ?",
                (self.search_bar_var.get(),),
            )
        except Exception:
            messagebox.showerror("Error",
                                 "No value exists in the chosen field",
                                 parent=self.root)
            self.search_entry.delete(0, END)
            conn.close()
            return

        data = cur.fetchall()
        conn.close()

        if data:
            self.student_table.delete(*self.student_table.get_children())
            for row in data:
                self.student_table.insert("", END, values=tuple(row))
            self.search_combo.current(0)
            self.search_entry.delete(0, END)
        else:
            messagebox.showerror("Error",
                                 "No value exists in the chosen field",
                                 parent=self.root)
            self.search_combo.current(0)
            self.search_entry.delete(0, END)

    def show_all(self):
        self.search_combo.current(0)
        self.search_entry.delete(0, END)
        self.fetch_data()


if __name__ == "__main__":
    root = Tk()
    obj  = details(root)
    root.mainloop()