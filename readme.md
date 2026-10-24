# QR Attendance System

A Python-based attendance management application that generates student-specific QR codes, scans them using a webcam, and records attendance with automatic timestamps.

## Features

- Register students with unique student IDs
- Generate individual QR codes for registered students
- Scan QR codes through a webcam
- Record attendance with date and time
- Prevent duplicate attendance entries on the same day
- View registered students and attendance history
- Store records locally in CSV files

## Tech Stack

- Python
- Tkinter for the graphical user interface
- OpenCV for webcam-based QR scanning
- qrcode and Pillow for QR code generation
- CSV for data storage

## Project Structure

```text
QR-Attendance-System/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
└── students.csv
```

The application creates the `qr_codes/` folder and `attendance.csv` automatically when needed.

## Requirements

- Python 3.10 or later recommended
- Webcam for scanning QR codes
- Internet connection to install dependencies

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/QR-Attendance-System.git
cd QR-Attendance-System
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the application:

```bash
python app.py
```

## How to Use

1. Click **Add Student** and enter a unique student ID and name.
2. Click **Generate QR Codes**.
3. Find the generated student QR images inside `qr_codes/`.
4. Click **Scan Attendance** and show a registered student's QR code to the webcam.
5. Press `Q` in the scanner window to stop scanning.
6. View the saved records under **Attendance History**.

## Data Storage

- `students.csv` stores registered student details.
- `attendance.csv` stores attendance date, time, and status.
- `qr_codes/` contains generated QR images.

## Limitations

This is a local prototype for learning and small demonstrations. It does not provide authentication or tamper-resistant attendance verification. A copied QR code could be used by another person, and CSV files can be edited manually. Use authenticated student verification for a production attendance system.

## Future Improvements

- Admin login and authentication
- Daily attendance summaries and percentage reports
- Export attendance reports for selected dates
- Database integration using SQLite or MySQL
- A web-based dashboard

## Author

Shrinivas Naik

GitHub: https://github.com/shrinivasnaik25