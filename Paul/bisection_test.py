from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QMessageBox, QLabel
from PyQt6.QtGui import QPainter, QPen, QFont
import sqlite3
from PyQt6.QtCore import Qt
import random
from constant import DB_FILE, DOSSIER_PATIENTS
import time
import pandas as pd
from datetime import datetime
import os

class BisectionTest(QWidget):
    def __init__(self, patient_id):
        super().__init__()
        self.setWindowTitle("Test de Bisection")
        self.setGeometry(300, 300, 600, 600)
        self.patient_id = patient_id
        self.attempt = 0
        self.total_attempts = 10
        self.setMouseTracking(True)

        self.waiting_for_space = True
        self.waiting_for_input = False
        self.start_time = None
        self.trial_start_time = None
        self.trial_data = []

        self.generate_new_bar() 

        self.btn_stop = QPushButton("Stopper le test")
        self.btn_stop.setStyleSheet("font-size: 18px; background-color: red; color: white; padding: 5px;")
        self.btn_stop.clicked.connect(self.stop_test)
        self.btn_stop.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        layout = QVBoxLayout()
        layout.addWidget(self.btn_stop)
        layout.addStretch()
        self.setLayout(layout)

        self.label_message = QLabel("Appuyez sur ESPACE pour commencer le test", self)
        self.label_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_message.setFont(QFont("Arial", 16))
        self.label_message.setGeometry(50, 250, 500, 100)
        self.label_message.show()

    def generate_new_bar(self):
        dpi = self.logicalDpiX()
        pixels_per_cm = dpi / 2.54
        length = 20 * pixels_per_cm

        margin = length / 2 + 10
        cx = random.uniform(margin, self.width() - margin)
        cy = random.uniform(margin, self.height() - margin)

        
        self.x1, self.y1 = cx - length / 2, cy
        self.x2, self.y2 = cx + length / 2, cy

        self.bar_cx = cx  
        self.bar_cy = cy

        self.fake_click_position = None
        self.waiting_for_input = True
        self.update()

        if self.attempt == 0 and self.start_time is None:
            self.start_time = time.time()  

        self.trial_start_time = time.time()

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.waiting_for_space:
            return  

        pen = QPen(Qt.GlobalColor.black, 5)
        painter.setPen(pen)
        painter.drawLine(int(self.x1), int(self.y1), int(self.x2), int(self.y2))

    def mousePressEvent(self, event):
        if not self.waiting_for_input or self.attempt >= self.total_attempts:
            return
        self.record_click(event.position().x(), event.position().y())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            if self.waiting_for_space:
                self.label_message.hide()
                self.waiting_for_space = False
                self.generate_new_bar()
            elif self.waiting_for_input and self.fake_click_position is None:
                self.record_click(None, None)

    def record_click(self, clic_x, clic_y):

        now = time.time()
        response_time = now - self.trial_start_time if self.trial_start_time else None
        elapsed_since_start = now - self.start_time if self.start_time else None

        if clic_x is not None and clic_y is not None:
            ecart_cm = (clic_x - self.bar_cx) / (self.logicalDpiX() / 2.54)
            reponse = round(ecart_cm, 2)
        else:
            reponse = "non fait"

        now_datetime=datetime.now()

        self.trial_data.append({
            "Essai": self.attempt + 1,
            "Date": now_datetime.strftime("%Y-%m-%d"),
            "Heure": now_datetime.strftime("%H:%M:%S"),
            "Temps total (s)": round(elapsed_since_start, 2) if elapsed_since_start else "NA",
            "Réponse (écart en cm)": reponse,
            "Temps de réponse (s)": round(response_time, 2) if response_time else "NA",
            "x1": round(self.x1, 2), 
            "y1": round(self.y1, 2), 
            "x2": round(self.x2, 2), 
            "y2": round(self.y2, 2),
            "Centre X (cx)": round(self.bar_cx, 2),
            "Centre Y (cy)": round(self.bar_cy, 2),
            "Clic X": round(clic_x, 2) if clic_x is not None else "NA",
            "Clic Y": round(clic_y, 2) if clic_y is not None else "NA"
        })


        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO bisection (patient_id, x1, y1, x2, y2, clic_x, clic_y)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (self.patient_id, self.x1, self.y1, self.x2, self.y2, clic_x, clic_y))
        conn.commit()
        conn.close()

        self.attempt += 1
        self.fake_click_position  = False

        if self.attempt < self.total_attempts:
            self.generate_new_bar()
        else:
            QMessageBox.information(self, "Terminé", "Test de bisection terminé.")
            self.export_results()
            self.close()

    def stop_test(self):
        QMessageBox.information(self, "Test interrompu", "Test de bisection arrêté prématurément.")
        self.export_results()
        self.close()

    def export_results(self):
        if not self.trial_data:
            return

        patient_name = self.get_patient_name()
        date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        parametres = "20cm"
        nom_test = "Bisection"
        nom_fichier = f"{patient_name}_{date_str}_{parametres}_{nom_test}.xlsx"

        dossier_patient = os.path.join(DOSSIER_PATIENTS, patient_name)
        os.makedirs(dossier_patient, exist_ok=True)

        df = pd.DataFrame(self.trial_data)
        chemin = os.path.join(dossier_patient, nom_fichier)
        df.to_excel(chemin, index=False)

    def get_patient_name(self):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT nom FROM patients WHERE id = ?", (self.patient_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else f"patient_{self.patient_id}"
