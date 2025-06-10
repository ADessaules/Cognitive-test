from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QMessageBox, QLabel, QApplication, QHBoxLayout, QComboBox, QLineEdit, QGroupBox, QFormLayout
from PyQt6.QtGui import QPainter, QPen
from PyQt6.QtCore import Qt, QTimer
import sqlite3
import random
import time
import pandas as pd
from datetime import datetime
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from constant import DB_FILE, DOSSIER_PATIENTS

class BisectionTest(QWidget):
    def __init__(self, patient_id, screen_patient, screen_experimenter):
        super().__init__()
        self.screen_patient = screen_patient  # <-- À ajouter
        self.screen_experimenter = screen_experimenter  # <-- À ajouter
        self.setWindowTitle("Contrôle du Test de Bisection")
        self.patient_id = patient_id
        self.attempt = 0
        self.total_attempts = 10
        self.trial_data = []
        self.stimulation_active = False

        self.start_time = None
        self.trial_start_time = None

        self.setGeometry(screen_experimenter.geometry())
        self.move(screen_experimenter.geometry().topLeft())

        # --- Boutons principaux ---
        self.btn_start = QPushButton("Démarrer le test")
        self.btn_stop = QPushButton("Arrêter et sauvegarder")
        self.btn_toggle_stimulation = QPushButton("Activer la stimulation")

        # Connexion des signaux
        self.btn_start.clicked.connect(self.start_test)
        self.btn_stop.clicked.connect(self.stop_test)
        self.btn_toggle_stimulation.clicked.connect(self.toggle_stimulation)

        self.label_stimulation = QLabel("Stimulation: inactive")
        self.label_stimulation.setStyleSheet("font-size: 16px; color: blue;")

        self.preview = PreviewWidget()

        layout = QVBoxLayout()

        # --- Sélection du patient ---
        self.patient_selector = QComboBox()
        self.populate_patient_list()
        layout.addWidget(QLabel("Sélectionnez un patient :"))
        layout.addWidget(self.patient_selector)

        # --- Section Stimulation ---
        stimulation_group = QGroupBox("Paramètres de stimulation :")
        stimulation_layout = QFormLayout()
        self.input_contacts = QLineEdit()
        self.input_intensity = QLineEdit()
        self.input_duration = QLineEdit()
        stimulation_layout.addRow("Contacts de stimulation", self.input_contacts)
        stimulation_layout.addRow("Intensité (mA)", self.input_intensity)
        stimulation_layout.addRow("Durée (ms)", self.input_duration)
        stimulation_group.setLayout(stimulation_layout)
        layout.addWidget(stimulation_group)

        # --- Section Contrôle Test ---
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.btn_start)
        controls_layout.addWidget(self.btn_stop)
        layout.addLayout(controls_layout)

        # --- Section Stimulation active/inactive ---
        stimulation_state_layout = QHBoxLayout()
        stimulation_state_layout.addWidget(self.btn_toggle_stimulation)
        stimulation_state_layout.addWidget(self.label_stimulation)
        layout.addLayout(stimulation_state_layout)

        # --- Section Preview ---
        hbox = QHBoxLayout()
        hbox.addStretch()
        hbox.addWidget(self.preview)
        hbox.addStretch()
        layout.addLayout(hbox)

        # --- Section Validation ---
        bottom_buttons_layout = QHBoxLayout()
        bottom_buttons_layout.addWidget(self.btn_start)
        bottom_buttons_layout.addWidget(self.btn_stop)
        layout.addLayout(bottom_buttons_layout)

        self.setLayout(layout)

    def toggle_stimulation(self):
        self.stimulation_active = not self.stimulation_active
        if self.stimulation_active:
            self.label_stimulation.setText("Stimulation: ACTIVE")
            self.label_stimulation.setStyleSheet("font-size: 16px; color: red;")
            self.btn_toggle_stimulation.setText("Désactiver la stimulation")
        else:
            self.label_stimulation.setText("Stimulation: inactive")
            self.label_stimulation.setStyleSheet("font-size: 16px; color: blue;")
            self.btn_toggle_stimulation.setText("Activer la stimulation")

    def start_test(self):
        selected_id = self.patient_selector.currentData()
        if selected_id is None:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un patient avant de démarrer le test.")
            return

        self.patient_id = selected_id
        self.patient_selector.setEnabled(False)
        self.btn_start.setEnabled(False)

        # Créer et afficher la fenêtre patient maintenant que l'ID est choisi
        self.patient_window = PatientWindow(self)
        self.patient_window.setGeometry(self.screen_patient.geometry())
        self.patient_window.move(self.screen_patient.geometry().topLeft())
        self.patient_window.show()
        self.patient_window.setFocus()
        self.patient_window.setMouseTracking(True)

        self.start_trial()

    def start_trial(self):
        if self.attempt == 0:
            self.start_time = time.time()
        self.trial_start_time = time.time()
        self.patient_window.generate_new_bar()

        self.preview.update_bar(
            self.patient_window.x1,
            self.patient_window.y1,
            self.patient_window.x2,
            self.patient_window.y2,
            self.patient_window.width(),
            self.patient_window.height()
        )

    def populate_patient_list(self):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, nom FROM patients")
        self.patients = cursor.fetchall()
        conn.close()

        self.patient_selector.addItem("Sélectionnez un patient", None)
        for pid, name in self.patients:
            self.patient_selector.addItem(name, pid)


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
            "Clic Y": round(clic_y, 2) if clic_y is not None else "NA",
            "Stimulation": "active" if self.stimulation_active else "inactive",
            "Contact stimulation": self.input_contacts.text(),
            "Intensité (mA)": self.input_intensity.text(),
            "Durée (ms)": self.input_duration.text()
        })

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
        self.waiting_for_input = True
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
        if not hasattr(self, 'x1') or not self.waiting_for_input:
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

class PreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(300, 300)
        self.x1 = self.y1 = self.x2 = self.y2 = None

        self.frame_width = 280
        self.frame_height = 160
        self.frame_x = (self.width() - self.frame_width) // 2
        self.frame_y = 20

    def update_bar(self, x1, y1, x2, y2, width_real, height_real):
        scale_x = self.frame_width / width_real
        scale_y = self.frame_height / height_real

        self.x1 = x1 * scale_x
        self.y1 = y1 * scale_y
        self.x2 = x2 * scale_x
        self.y2 = y2 * scale_y

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        pen_frame = QPen(Qt.GlobalColor.black, 3)
        painter.setPen(pen_frame)
        painter.drawRect(self.frame_x, self.frame_y, self.frame_width, self.frame_height)

        if None not in (self.x1, self.y1, self.x2, self.y2):
            pen_line = QPen(Qt.GlobalColor.red, 3)
            painter.setPen(pen_line)

            bar_x1 = self.x1 + self.frame_x
            bar_y1 = self.y1 + self.frame_y
            bar_x2 = self.x2 + self.frame_x
            bar_y2 = self.y2 + self.frame_y

            painter.drawLine(int(bar_x1), int(bar_y1), int(bar_x2), int(bar_y2))

if __name__ == "__main__":
    app = QApplication(sys.argv)

    screens = QApplication.screens()


    screen_experimenter = screens[0]
    screen_patient = screens[1]

    app_window = {}
    app_window["main"] = BisectionTest(patient_id=None, screen_patient=screen_patient, screen_experimenter=screen_experimenter)
    app_window["main"].show()

    sys.exit(app.exec())