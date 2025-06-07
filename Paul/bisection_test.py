from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QMessageBox, QLabel, QApplication
from PyQt6.QtGui import QPainter, QPen, QFont
from PyQt6.QtCore import Qt, QTimer
import sqlite3
import random
import time
import pandas as pd
from datetime import datetime
import os
from constant import DB_FILE, DOSSIER_PATIENTS

class BisectionTest(QWidget):
    def __init__(self, patient_id, screen_patient, screen_experimenter):
        super().__init__()
        self.setWindowTitle("Contrôle du Test de Bisection")
        self.patient_id = patient_id
        self.attempt = 0
        self.total_attempts = 10
        self.trial_data = []

        self.start_time = None
        self.trial_start_time = None

        # Fenêtre expérimentateur 
        self.setGeometry(screen_experimenter.geometry())
        self.move(screen_experimenter.geometry().topLeft())

        self.btn_stop = QPushButton("Stopper le test")
        self.btn_stop.setStyleSheet("font-size: 18px; background-color: red; color: white; padding: 5px;")
        self.btn_stop.clicked.connect(self.stop_test)

        layout = QVBoxLayout()
        layout.addWidget(self.btn_stop)
        self.setLayout(layout)

        # Fenêtre patient sur l'autre écran
        self.patient_window = PatientWindow(self)
        self.patient_window.setGeometry(screen_patient.geometry())
        self.patient_window.move(screen_patient.geometry().topLeft())
        self.patient_window.show()

        self.label_message = QLabel("Appuyez sur ESPACE pour commencer le test", self.patient_window)
        self.label_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_message.setFont(QFont("Arial", 20))
        self.label_message.setGeometry(100, screen_patient.geometry().height() // 2 - 50,
                                       screen_patient.geometry().width() - 200, 100)
        self.label_message.show()

        self.patient_window.setFocus()
        self.patient_window.setMouseTracking(True)

    def start_trial(self):
        if self.attempt == 0:
            self.start_time = time.time()
        self.trial_start_time = time.time()
        self.patient_window.generate_new_bar()

    def record_click(self, clic_x, clic_y):
        now = time.time()
        response_time = now - self.trial_start_time
        elapsed_since_start = now - self.start_time if self.start_time else None

        if clic_x is not None:
            ecart_cm = (clic_x - self.patient_window.bar_cx) / (self.logicalDpiX() / 2.54)
            reponse = round(ecart_cm, 2)
        else:
            reponse = "non fait"

        now_datetime = datetime.now()

        self.trial_data.append({
            "Essai": self.attempt + 1,
            "Date": now_datetime.strftime("%Y-%m-%d"),
            "Heure": now_datetime.strftime("%H:%M:%S"),
            "Temps total (s)": round(elapsed_since_start, 2),
            "Réponse (écart en cm)": reponse,
            "Temps de réponse (s)": round(response_time, 2),
            "x1": round(self.patient_window.x1, 2),
            "y1": round(self.patient_window.y1, 2),
            "x2": round(self.patient_window.x2, 2),
            "y2": round(self.patient_window.y2, 2),
            "Centre X (cx)": round(self.patient_window.bar_cx, 2),
            "Centre Y (cy)": round(self.patient_window.bar_cy, 2),
            "Clic X": round(clic_x, 2) if clic_x is not None else "NA",
            "Clic Y": round(clic_y, 2) if clic_y is not None else "NA"
        })

        # Sauvegarde en base
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO bisection (patient_id, x1, y1, x2, y2, clic_x, clic_y)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (self.patient_id, self.patient_window.x1, self.patient_window.y1,
             self.patient_window.x2, self.patient_window.y2, clic_x, clic_y))
        conn.commit()
        conn.close()

        self.attempt += 1
        if self.attempt < self.total_attempts:
            QTimer.singleShot(500, self.start_trial)
        else:
            QMessageBox.information(self, "Terminé", "Test de bisection terminé.")
            self.export_results()
            self.patient_window.close()
            self.close()

    def stop_test(self):
        QMessageBox.information(self, "Test interrompu", "Test de bisection arrêté prématurément.")
        self.export_results()
        self.patient_window.close()
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


class PatientWindow(QWidget):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.waiting_for_space = True
        self.waiting_for_input = False
        self.bar_cx = 0
        self.bar_cy = 0

    def generate_new_bar(self):
        dpi = self.logicalDpiX()
        pixels_per_cm = dpi / 2.54
        length = 20 * pixels_per_cm
        margin = length / 2 + 10
        cx = random.uniform(margin, self.width() - margin)
        cy = random.uniform(margin, self.height() - margin)

        self.x1 = cx - length / 2
        self.y1 = cy
        self.x2 = cx + length / 2
        self.y2 = cy
        self.bar_cx = cx
        self.bar_cy = cy
        self.waiting_for_input = True
        self.update()

    def paintEvent(self, event):
        if self.waiting_for_space:
            return
        painter = QPainter(self)
        pen = QPen(Qt.GlobalColor.black, 5)
        painter.setPen(pen)
        painter.drawLine(int(self.x1), int(self.y1), int(self.x2), int(self.y2))

    def mousePressEvent(self, event):
        if not self.waiting_for_input:
            return
        self.waiting_for_input = False
        self.main_app.record_click(event.position().x(), event.position().y())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space and self.waiting_for_space:
            self.waiting_for_space = False
            self.main_app.label_message.hide()
            self.main_app.start_trial()
