from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
from give_details import details
from export_files import files
import attendance_btn
import threading


class Face_recognition_system:

    def __init__(self, root):

        self.root = root
        self.root.geometry("700x550+420+100")
        self.root.title("Face Recognition Attendance System")
        self.root.config(bg="#0f172a")

        self._att_thread = None
        self._stop_event = None

        title_lbl = Label(self.root,text="FACE RECOGNITION",font=("Segoe UI", 28, "bold"),bg="#0f172a",fg="white")
        title_lbl.pack(pady=(25, 0))

        subtitle_lbl = Label(self.root,text="Attendance Management System",font=("Segoe UI", 13),bg="#0f172a",fg="#94a3b8")
        subtitle_lbl.pack(pady=(0, 20))

        main_frame = Frame(self.root,bg="#1e293b",bd=0,relief=RIDGE)
        main_frame.place(x=70, y=170, width=560, height=320)


        self.export_icon = Label(self.root,text="🧠",font=("Segoe UI Emoji", 35),bg="#0f172a",fg="white")
        self.export_icon.place(x=315, y=120)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Custom.TButton",font=("Segoe UI", 14, "bold"),padding=15,foreground="white",background="#2563eb",borderwidth=0)
        style.map("Custom.TButton",background=[("active", "#1d4ed8")])

        self.b1_lbl = ttk.Button(main_frame,text="🧾  Register Student",style="Custom.TButton",cursor="hand2",command=self.student_details)
        self.b1_lbl.place(x=70, y=40, width=420, height=55)

        self.b2_lbl = ttk.Button(main_frame,text="📁  Export Files",style="Custom.TButton",cursor="hand2",command=self.export_details)
        self.b2_lbl.place(x=70, y=130, width=420, height=55)

        self.b3_lbl = ttk.Button(main_frame,text="🎥  Start Attendance",style="Custom.TButton",cursor="hand2",command=self.start_attendance)
        self.b3_lbl.place(x=70, y=220, width=420, height=55)

        footer_lbl = Label(self.root,text="Powered by OpenCV • Face Recognition • SQLite",font=("Segoe UI", 10),bg="#0f172a",fg="#94a3b8")
        footer_lbl.pack(side=BOTTOM, pady=15)

    def student_details(self):

        self.new_window = Toplevel(self.root)
        self.app = details(self.new_window)

    def export_details(self):

        self.new_window = Toplevel(self.root)
        self.app = files(self.new_window)

    def start_attendance(self):

        if self._att_thread and self._att_thread.is_alive():
            return

        self._stop_event = threading.Event()

        self._att_thread = threading.Thread(
            target=attendance_btn.run,
            args=(self._stop_event,),
            daemon=True
        )

        self._att_thread.start()

        self.b3_lbl.config(
            text="⛔  Stop Attendance",
            command=self.stop_attendance
        )

    def stop_attendance(self):

        if self._stop_event:
            self._stop_event.set()

        self.b3_lbl.config(
            text="🎥  Start Attendance",
            command=self.start_attendance
        )


if __name__ == "__main__":
    root = Tk()
    obj = Face_recognition_system(root)
    root.mainloop()