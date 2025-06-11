from constant import DB_FILE
import sqlite3


# --- Création de la base de données ---
def creer_base():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS selections (
            patient_id INTEGER,
            nom TEXT,
            image TEXT,
            FOREIGN KEY(patient_id) REFERENCES patients(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bisection (
            patient_id INTEGER,
            x1 REAL, y1 REAL,
            x2 REAL, y2 REAL,
            clic_x REAL, clic_y REAL,
            FOREIGN KEY(patient_id) REFERENCES patients(id)
        )
    """)
    conn.commit()
    conn.close()