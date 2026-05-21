from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from PIL import Image, ImageTk
from tkinter import messagebox
import sqlite3
import os
import csv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE  = os.path.join(BASE_DIR, "attendance.db")

def get_db_connection() -> sqlite3.Connection:
    """Return a new SQLite connection with Row factory."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


class files:

    def __init__(self, root):
        self.root = root
        self.root.geometry("700x500+420+120")
        self.root.title("Export Center")
        self.root.config(bg="#0f172a")

        title_lbl = Label(self.root, text="EXPORT  CENTER",font=("Segoe UI", 28, "bold"), bg="#0f172a", fg="white")
        title_lbl.pack(pady=35)

        main_frame = Frame(self.root, bg="#1e293b", bd=0, relief=RIDGE)
        main_frame.place(x=70, y=140, width=560, height=300)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Custom.TButton",font=("Segoe UI", 14, "bold"), padding=15,foreground="white", background="#2563eb", borderwidth=0)
        style.map("Custom.TButton", background=[("active", "#1d4ed8")])

        self.export_icon = Label(self.root, text="📁",font=("Segoe UI Emoji", 40), bg="#0f172a", fg="white")
        self.export_icon.place(x=315, y=90)

        attend_btn = ttk.Button(main_frame, text="📊  Export Attendance File",style="Custom.TButton", cursor="hand2",command=self.attendance_file)
        attend_btn.place(x=70, y=70, width=420, height=55)

        detail_btn = ttk.Button(main_frame, text="🧾  Export Student Details",style="Custom.TButton", cursor="hand2",command=self.detail_file)
        detail_btn.place(x=70, y=170, width=420, height=55)

        footer_lbl = Label(self.root, text="Face Recognition Attendance System",font=("Segoe UI", 10), bg="#0f172a", fg="#94a3b8")
        footer_lbl.pack(side=BOTTOM, pady=10)

    def attendance_file(self):
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute(
            "SELECT student_id, attendance_date, attendance_time, state "
            "FROM attendance"
        )
        data = cur.fetchall()
        conn.close()

        if not data:
            messagebox.showerror("Error", "No data found", parent=self.root)
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV File", "*.csv")],
            title="Save CSV File",
        )
        if not file_path:
            return

        try:
            with open(file_path, mode="w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Student Id", "Date", "Time", "Status"])
                for row in data:
                    writer.writerow([
                        str(row["student_id"]),
                        str(row["attendance_date"]) if row["attendance_date"] else "",
                        str(row["attendance_time"]) if row["attendance_time"] else "",
                        str(row["state"]),
                    ])
            messagebox.showinfo("Success", "CSV file exported successfully",
                                parent=self.root)
        except Exception as es:
            messagebox.showerror("Error", str(es), parent=self.root)


    def detail_file(self):
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("SELECT * FROM student")
        data = cur.fetchall()
        conn.close()

        if not data:
            messagebox.showerror("Error", "No data found", parent=self.root)
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV File", "*.csv")],
            title="Save CSV File",
        )
        if not file_path:
            return

        try:
            with open(file_path, mode="w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Department", "Course", "Year", "Semester",
                    "ID", "Name", "Email", "Phone", "Image",
                ])
                for row in data:
                    writer.writerow(list(row))
            messagebox.showinfo("Success", "CSV file exported successfully",
                                parent=self.root)
        except Exception as es:
            messagebox.showerror("Error", str(es), parent=self.root)


if __name__ == "__main__":
    root = Tk()
    obj = files(root)
    root.mainloop()