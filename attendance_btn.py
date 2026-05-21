import cv2
import os
import cvzone
import pickle
import face_recognition
import numpy as np
import sqlite3
from datetime import datetime
import threading
import time
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "app_config.json")
DB_FILE     = os.path.join(BASE_DIR, "attendance.db")


def load_config() -> dict:
    """Return config dict from JSON file, or empty dict if absent."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def get_image_folder() -> str:
    config = load_config()
    folder = config.get("image_folder", "")
    if folder and os.path.isdir(folder):
        return folder
    fallback = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
    os.makedirs(fallback, exist_ok=True)
    return fallback


def get_db_connection() -> sqlite3.Connection:
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


def encodeList(encodeFile: str, folderPath: str):
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("SELECT id FROM student")
        rows = cur.fetchall()
        db_student_ids = {str(row["id"]) for row in rows}
        conn.close()
    except Exception as e:
        print(f"[Encoding] DB connection failed: {e}")
        print("[Encoding] Proceeding without DB verification — encoding from images only.")
        db_student_ids = None

    
    if os.path.exists(encodeFile):
        with open(encodeFile, "rb") as f:
            encodeListKnown, studentIds = pickle.load(f)
        print("Old encodings loaded")
    else:
        encodeListKnown = []
        studentIds      = []
        print("No old encodings found")

    pathList          = os.listdir(folderPath)
    image_ids_in_folder = {os.path.splitext(p)[0] for p in pathList}

    if db_student_ids is not None:
        for db_id in db_student_ids:
            if db_id not in image_ids_in_folder:
                print(f"Image not available for student ID: {db_id}")

    for path in pathList:
        student_id = os.path.splitext(path)[0]
        if student_id in studentIds:
            continue
        if db_student_ids is not None and student_id not in db_student_ids:
            print(f"Skipping '{path}' — ID '{student_id}' not in database.")
            continue

        img = cv2.imread(os.path.join(folderPath, path))
        if img is None:
            continue
        img       = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(img)
        if encodings:
            encodeListKnown.append(encodings[0])
            studentIds.append(student_id)
        else:
            print(f"No face found in {student_id}")

    with open(encodeFile, "wb") as f:
        pickle.dump([encodeListKnown, studentIds], f)

    print("Encoding update complete")
    return encodeListKnown, studentIds


def showMissingImagesWindow(missing_ids: list):
    win_w       = 500
    line_height = 40
    header_lines = 3
    win_h = header_lines * line_height + len(missing_ids) * line_height + 60

    canvas = np.zeros((win_h, win_w, 3), dtype=np.uint8)
    canvas[:] = (30, 30, 30)

    cv2.putText(canvas, "Images Not Available:", (30, 50),
                cv2.FONT_HERSHEY_COMPLEX, 0.8, (0, 0, 255), 2)
    cv2.line(canvas, (30, 65), (win_w - 30, 65), (100, 100, 100), 1)

    y = 105
    for sid in missing_ids:
        cv2.putText(canvas, str(sid), (60, y),
                    cv2.FONT_HERSHEY_COMPLEX, 0.65, (255, 255, 255), 1)
        y += line_height

    cv2.putText(canvas, "Press any key to continue...", (30, win_h - 20),
                cv2.FONT_HERSHEY_COMPLEX, 0.5, (150, 150, 150), 1)

    cv2.imshow("Missing Student Images", canvas)
    cv2.waitKey(0)
    cv2.destroyWindow("Missing Student Images")


def recognitionWorker(encodeListKnown, studentIds,
                      inputFrameHolder, inputFrameLock,
                      recognitionResult, recognitionLock,
                      stop_event):
    while not stop_event.is_set():
        with inputFrameLock:
            frame = inputFrameHolder["frame"]
            inputFrameHolder["frame"] = None

        if frame is None:
            time.sleep(0.005)
            continue

        faceCurrFrame   = face_recognition.face_locations(frame)
        encodeCurrFrame = face_recognition.face_encodings(frame, faceCurrFrame)

        matchedIds = []
        for encodeFace in encodeCurrFrame:
            faceDist = face_recognition.face_distance(encodeListKnown, encodeFace)
            if len(faceDist) > 0:
                matchIdx = np.argmin(faceDist)
                matchedIds.append(studentIds[matchIdx] if faceDist[matchIdx] < 0.5 else None)
            else:
                matchedIds.append(None)

        with recognitionLock:
            recognitionResult["faceLocs"]   = faceCurrFrame
            recognitionResult["matchedIds"] = matchedIds


def run(stop_event: threading.Event):
    init_db()
    folderPath = get_image_folder()
    encodeFile = os.path.join(BASE_DIR, "EncodeFile.p")

    counter      = 0
    modeType     = 0
    frameCounter = 0
    department   = ""
    name         = ""
    current_id   = ""

    recognitionResult = {"faceLocs": [], "matchedIds": []}
    recognitionLock   = threading.Lock()
    inputFrameHolder  = {"frame": None}
    inputFrameLock    = threading.Lock()

    conn = get_db_connection()
    cur  = conn.cursor()

    cur.execute("SELECT id FROM student")
    db_student_ids = {str(row["id"]) for row in cur.fetchall()}

    image_ids_in_folder = {os.path.splitext(f)[0] for f in os.listdir(folderPath)}
    missing_ids = sorted(db_student_ids - image_ids_in_folder)
    if missing_ids:
        showMissingImagesWindow(missing_ids)

    encodeListKnown, studentIds = encodeList(encodeFile, folderPath)
    print("Encodings Loaded Successfully")

    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    imgbackgroundMaster = cv2.imread(os.path.join(BASE_DIR, "Resources", "background.png"))
    folderModePath      = os.path.join(BASE_DIR, "Resources", "Modes")

    imgModeList         = [
        cv2.imread(os.path.join(folderModePath, p))
        for p in sorted(os.listdir(folderModePath))
    ]

    recThread = threading.Thread(
        target=recognitionWorker,
        args=(encodeListKnown, studentIds,
              inputFrameHolder, inputFrameLock,
              recognitionResult, recognitionLock,
              stop_event),
        daemon=True,
    )
    recThread.start()

    while not stop_event.is_set():
        success, img = cap.read()
        if not success:
            break

        frameCounter += 1

        if frameCounter % 3 == 0:
            imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
            imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
            with inputFrameLock:
                inputFrameHolder["frame"] = imgS

        with recognitionLock:
            faceCurrFrame = list(recognitionResult["faceLocs"])
            matchedIds    = list(recognitionResult["matchedIds"])

        imgbackground = imgbackgroundMaster.copy()
        imgbackground[162:162 + 480, 55:55 + 640] = img

        if faceCurrFrame:
            for faceLoc, sid in zip(faceCurrFrame, matchedIds):
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4

                if sid is not None:
                    bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1
                    imgbackground = cvzone.cornerRect(imgbackground, bbox, rt=0)

                    if counter == 0:
                        counter    = 1
                        modeType   = 1
                        current_id = sid

                else:
                    cv2.putText(imgbackground, "Unknown Face", (890, 330),
                                cv2.FONT_HERSHEY_COMPLEX, 0.7, (0, 0, 0), 2)
                    cv2.putText(imgbackground, "Please Register First", (890, 370),
                                cv2.FONT_HERSHEY_COMPLEX, 0.6, (0, 0, 0), 1)

            if counter != 0:
                if counter == 1:
                    now             = datetime.now()
                    attendance_date = now.strftime("%Y-%m-%d")   # ISO string for SQLite
                    attendance_time = now.strftime("%H:%M:%S")
                    state           = 1

                    # Check if attendance already marked today
                    cur.execute(
                        "SELECT student_id FROM attendance "
                        "WHERE student_id = ? AND attendance_date = ?",
                        (current_id, attendance_date),
                    )
                    already_marked = cur.fetchone()

                    if already_marked is None:
                        cur.execute(
                            "UPDATE attendance "
                            "SET attendance_date = ?, attendance_time = ?, state = ? "
                            "WHERE student_id = ?",
                            (attendance_date, attendance_time, state, current_id),
                        )
                        conn.commit()

                        cur.execute(
                            "SELECT Department, name FROM student WHERE id = ?",
                            (current_id,),
                        )
                        result = cur.fetchone()
                        if result:
                            department = result["Department"]
                            name       = result["name"]
                        else:
                            department = ""
                            name       = ""

                    else:
                        modeType = 3
                        counter  = 0
                        imgbackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]
                        cv2.imshow("Face Attendance", imgbackground)
                        cv2.waitKey(1)
                        cv2.waitKey(2000)
                        modeType   = 0
                        department = ""
                        name       = ""

                if counter != 0:
                    if 10 < counter < 20:
                        modeType = 2

                    imgbackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

                    if counter <= 10:
                        cv2.putText(imgbackground, str(current_id), (1006, 493),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.5, (50, 50, 50), 1)
                        cv2.putText(imgbackground, str(department), (1006, 550),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.50, (255, 255, 255), 1)

                        (w, _), _ = cv2.getTextSize(name, cv2.FONT_HERSHEY_COMPLEX, 1, 1)
                        offset = (414 - w) // 2
                        cv2.putText(imgbackground, str(name), (808 + offset, 445),
                                    cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 0), 1)

                        # Use dynamic folder for displaying photo
                        image_show = cv2.imread(
                            os.path.join(folderPath, f"{current_id}.jpg")
                        )
                        if image_show is not None:
                            image_show = cv2.resize(image_show, (216, 216))
                            imgbackground[175:175 + 216, 909:909 + 216] = image_show
                        else:
                            print("No image detected")

                    counter += 1

                    if counter >= 20:
                        counter    = 0
                        modeType   = 0
                        department = ""
                        name       = ""

        else:
            modeType = 0
            counter  = 0
            imgbackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

        cv2.imshow("Face Attendance", imgbackground)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            stop_event.set()
            break

    conn.close()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    stop = threading.Event()
    run(stop)