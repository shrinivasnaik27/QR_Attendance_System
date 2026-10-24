
import csv
import json
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk

import cv2
import qrcode


# ---------- FILES AND FOLDERS ----------

BASE_DIR = Path(__file__).resolve().parent
QR_DIR = BASE_DIR / "qr_codes"
STUDENTS_FILE = BASE_DIR / "students.csv"
ATTENDANCE_FILE = BASE_DIR / "attendance.csv"

QR_DIR.mkdir(exist_ok=True)


def normalize_csv_field_name(value):
    if value is None:
        return ""
    return (
        str(value)
        .strip()
        .lstrip("\ufeff")
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )


def ensure_csv_headers(path, required_columns):
    if not path.exists():
        with path.open("w", newline="", encoding="utf-8") as file:
            csv.writer(file).writerow(required_columns)
        return

    with path.open("r", newline="", encoding="utf-8-sig") as file:
        rows = list(csv.reader(file))

    if not rows:
        rows = [list(required_columns)]
    else:
        header = [normalize_csv_field_name(column) for column in rows[0]]
        if header != list(required_columns):
            rows = [list(required_columns)] + rows[1:]

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerows(rows)


def initialize_files():
    ensure_csv_headers(STUDENTS_FILE, ["student_id", "name"])
    ensure_csv_headers(
        ATTENDANCE_FILE,
        ["student_id", "name", "date", "time", "status"],
    )


def load_students():
    with STUDENTS_FILE.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        normalized_rows = []
        for row in reader:
            if not row:
                continue
            normalized_row = {}
            for key, value in row.items():
                if key is None:
                    continue
                normalized_row[normalize_csv_field_name(key)] = value
            normalized_rows.append(normalized_row)

    return {
        str(row["student_id"]).strip(): str(row["name"]).strip()
        for row in normalized_rows
        if row.get("student_id") not in (None, "")
    }


def load_attendance():
    with ATTENDANCE_FILE.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        normalized_rows = []
        for row in reader:
            if not row:
                continue
            normalized_row = {}
            for key, value in row.items():
                if key is None:
                    continue
                normalized_row[normalize_csv_field_name(key)] = value
            normalized_rows.append(normalized_row)

    return normalized_rows


# ---------- STUDENT REGISTRATION ----------

def add_student():
    student_id = simpledialog.askstring(
        "Add Student", "Enter student ID:", parent=root
    )
    if student_id is None:
        return

    student_id = student_id.strip()
    if not student_id:
        messagebox.showwarning("Invalid ID", "Student ID cannot be empty.")
        return

    students = load_students()
    if student_id in students:
        messagebox.showwarning("Already Exists", "This student ID is registered.")
        return

    name = simpledialog.askstring(
        "Add Student", "Enter student name:", parent=root
    )
    if name is None:
        return

    name = name.strip()
    if not name:
        messagebox.showwarning("Invalid Name", "Student name cannot be empty.")
        return

    with STUDENTS_FILE.open("a", newline="", encoding="utf-8") as file:
        csv.writer(file).writerow([student_id, name])

    refresh_student_list()
    messagebox.showinfo("Success", f"Registered {name} ({student_id}).")


# ---------- QR CODE GENERATION ----------

def generate_qr(student_id, name):
    # QR contains structured data identifying the registered student.
    payload = json.dumps(
        {"student_id": student_id},
        separators=(",", ":")
    )

    image = qrcode.make(payload)
    image.save(QR_DIR / f"{student_id}.png")


def generate_all_qr():
    students = load_students()
    if not students:
        messagebox.showwarning(
            "No Students", "Register at least one student first."
        )
        return

    for student_id, name in students.items():
        generate_qr(student_id, name)

    messagebox.showinfo(
        "QR Codes Created",
        f"Generated {len(students)} QR code(s).\nSaved in:\n{QR_DIR}"
    )


# ---------- ATTENDANCE RECORDING ----------

def mark_attendance(student_id):
    students = load_students()

    # Only registered students are accepted.
    if student_id not in students:
        return False, "Unknown student ID."

    now = datetime.now()
    today = now.strftime("%Y-%m-%d")

    # Prevent duplicate attendance for the same student on the same day.
    for record in load_attendance():
        if (
            record["student_id"] == student_id
            and record["date"] == today
        ):
            return False, f"{students[student_id]} is already marked present today."

    with ATTENDANCE_FILE.open("a", newline="", encoding="utf-8") as file:
        csv.writer(file).writerow([
            student_id,
            students[student_id],
            today,
            now.strftime("%H:%M:%S"),
            "Present",
        ])

    return True, f"Attendance marked for {students[student_id]}!"


# ---------- WEBCAM QR SCANNER ----------

def scan_attendance():
    students = load_students()
    if not students:
        messagebox.showwarning(
            "No Students", "Register students and generate QR codes first."
        )
        return

    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        camera.release()
        messagebox.showerror(
            "Camera Error",
            "Could not open your webcam. Close other apps using it and try again."
        )
        return

    detector = cv2.QRCodeDetector()
    last_payload = None
    status_text = "Show a student QR code. Press Q to quit."

    try:
        while True:
            success, frame = camera.read()
            if not success:
                messagebox.showerror(
                    "Camera Error", "Could not read a webcam frame."
                )
                break

            decoded_text, points, _ = detector.detectAndDecode(frame)

            # Re-arm after the QR is removed from view.
            if not decoded_text:
                last_payload = None

            if decoded_text and decoded_text != last_payload:
                last_payload = decoded_text

                try:
                    data = json.loads(decoded_text)
                    student_id = str(data["student_id"]).strip()
                    was_marked, result_message = mark_attendance(student_id)
                except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                    was_marked = False
                    result_message = "Invalid QR code."

                status_text = result_message
                print(result_message)

                if was_marked:
                    print(f"Saved to: {ATTENDANCE_FILE}")

            cv2.putText(
                frame,
                status_text[:75],
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 180, 0) if "marked" in status_text.lower() else (0, 0, 255),
                2,
            )
            cv2.putText(
                frame,
                "Press Q to close scanner",
                (10, frame.shape[0] - 15),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
            )

            cv2.imshow("QR Attendance Scanner", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        camera.release()
        cv2.destroyAllWindows()

    refresh_attendance()
    messagebox.showinfo(
        "Scanner Closed",
        f"Attendance records are saved in:\n{ATTENDANCE_FILE}"
    )


# ---------- DISPLAY DATA ----------

def refresh_student_list():
    for item in student_table.get_children():
        student_table.delete(item)

    for student_id, name in load_students().items():
        student_table.insert("", "end", values=(student_id, name))


def refresh_attendance():
    for item in attendance_table.get_children():
        attendance_table.delete(item)

    for record in load_attendance():
        attendance_table.insert(
            "",
            "end",
            values=(
                record["student_id"],
                record["name"],
                record["date"],
                record["time"],
                record["status"],
            ),
        )


# ---------- MAIN WINDOW ----------

if __name__ == "__main__":
    initialize_files()

    root = tk.Tk()
    root.title("QR Attendance System")
    root.geometry("850x650")
    root.minsize(700, 520)
    root.configure(bg="#f3f6fb")

    title = tk.Label(
        root,
        text="QR Attendance System",
        font=("Segoe UI", 22, "bold"),
        bg="#f3f6fb",
        fg="#17365d",
    )
    title.pack(pady=(18, 4))

    subtitle = tk.Label(
        root,
        text="Register students • Generate QR codes • Track attendance",
        font=("Segoe UI", 10),
        bg="#f3f6fb",
        fg="#526176",
    )
    subtitle.pack(pady=(0, 14))

    button_frame = tk.Frame(root, bg="#f3f6fb")
    button_frame.pack(pady=5)

    button_style = {
        "font": ("Segoe UI", 10, "bold"),
        "bg": "#2457c5",
        "fg": "white",
        "activebackground": "#173f94",
        "activeforeground": "white",
        "relief": "flat",
        "cursor": "hand2",
        "padx": 12,
        "pady": 9,
    }

    tk.Button(
        button_frame, text="Add Student", command=add_student, **button_style
    ).grid(row=0, column=0, padx=5, pady=5)

    tk.Button(
        button_frame, text="Generate QR Codes",
        command=generate_all_qr, **button_style
    ).grid(row=0, column=1, padx=5, pady=5)

    tk.Button(
        button_frame, text="Scan Attendance",
        command=scan_attendance, **button_style
    ).grid(row=0, column=2, padx=5, pady=5)

    tk.Button(
        button_frame, text="Refresh Records",
        command=lambda: (refresh_student_list(), refresh_attendance()),
        **button_style
    ).grid(row=0, column=3, padx=5, pady=5)

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=18, pady=15)

    student_tab = ttk.Frame(notebook, padding=10)
    attendance_tab = ttk.Frame(notebook, padding=10)

    notebook.add(student_tab, text="Registered Students")
    notebook.add(attendance_tab, text="Attendance History")

    student_table = ttk.Treeview(
        student_tab,
        columns=("student_id", "name"),
        show="headings",
    )
    student_table.heading("student_id", text="Student ID")
    student_table.heading("name", text="Student Name")
    student_table.column("student_id", width=180, anchor="center")
    student_table.column("name", width=350, anchor="w")
    student_table.pack(fill="both", expand=True)

    attendance_table = ttk.Treeview(
        attendance_tab,
        columns=("student_id", "name", "date", "time", "status"),
        show="headings",
    )
    for column, heading in [
        ("student_id", "Student ID"),
        ("name", "Name"),
        ("date", "Date"),
        ("time", "Time"),
        ("status", "Status"),
    ]:
        attendance_table.heading(column, text=heading)
        attendance_table.column(column, width=130, anchor="center")

    attendance_table.pack(fill="both", expand=True)

    footer = tk.Label(
        root,
        text="Records are stored locally in CSV files.",
        font=("Segoe UI", 9),
        bg="#f3f6fb",
        fg="#526176",
    )
    footer.pack(pady=(0, 12))

    refresh_student_list()
    refresh_attendance()

    root.mainloop()
