import sys
import os
import random
import time
import sqlite3
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QComboBox, QMessageBox
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QTimer, Qt, QEvent
import pandas as pd

DB_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Paul", "patients.db"))
IMAGE_FOLDER = os.path.join("famous_faceV1", "image_famous_faceV1")

class WaitingScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Écran d'attente")
        self.setGeometry(920, 100, 800, 600)
        layout = QVBoxLayout()
        label = QLabel("Appuyez sur Espace pour démarrer le test")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)

class PatientWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test en cours - Écran patient")
        self.setGeometry(920, 100, 800, 600)
        self.image_layout = QHBoxLayout()
        self.setLayout(self.image_layout)

    def show_images(self, triplet, click_handlers):
        for i in reversed(range(self.image_layout.count())):
            widget = self.image_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        for img_path, handler in zip(triplet, click_handlers):
            pixmap = QPixmap(img_path).scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio)
            label = QLabel()
            label.setPixmap(pixmap)
            label.mousePressEvent = handler
            self.image_layout.addWidget(label)

class FamousFaceTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Famous Face Test - Expérimentateur")
        self.setGeometry(100, 100, 1200, 600)

        self.timer = QTimer()
        self.timer.timeout.connect(self.handle_timeout)
        self.patient_window = PatientWindow()
        self.waiting_screen = WaitingScreen()

        self.session_active = False
        self.click_times = []
        self.error_indices = []
        self.trial_results = []
        self.nurse_clicks = []
        self.experimenter_labels = []
        self.selected_index = None
        self.current_index = 0
        self.participant_name = ""
        self.mode = "click"
        self.timer_duration = 3

        self.init_ui()
        self.installEventFilter(self)

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout()
        self.config_layout = QVBoxLayout()

        self.patient_selector = QComboBox()
        self.load_patients()
        self.patient_selector.currentIndexChanged.connect(self.select_patient)

        self.start_btn = QPushButton("Démarrer le test")
        self.start_btn.clicked.connect(self.prepare_test)

        self.stop_btn = QPushButton("Arrêter et sauvegarder")
        self.stop_btn.clicked.connect(self.end_session)

        self.config_layout.addWidget(QLabel("Choisir un patient :"))
        self.config_layout.addWidget(self.patient_selector)
        self.config_layout.addWidget(self.start_btn)
        self.config_layout.addWidget(self.stop_btn)

        self.image_layout = QHBoxLayout()
        self.image_panel = QWidget()
        self.image_panel.setLayout(self.image_layout)

        self.main_layout.addLayout(self.config_layout)
        self.main_layout.addWidget(self.image_panel)

        self.central_widget.setLayout(self.main_layout)

    def load_patients(self):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""SELECT DISTINCT p.id, p.nom FROM patients p JOIN selections s ON p.id = s.patient_id ORDER BY p.nom;""")
        self.patients = cursor.fetchall()
        conn.close()
        for _, nom in self.patients:
            self.patient_selector.addItem(nom)

    def select_patient(self):
        self.current_index = 0
        self.trial_results = []
        self.patient_id = self.patients[self.patient_selector.currentIndex()][0]
        self.participant_name = self.patients[self.patient_selector.currentIndex()][1]

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT image FROM selections WHERE patient_id = ?", (self.patient_id,))
        images = [row[0] for row in cursor.fetchall()]
        conn.close()

        # Group by prefix for triplets
        triplets = {}
        for img in images:
            prefix = os.path.basename(img).split("_")[1]
            if prefix not in triplets:
                triplets[prefix] = []
            triplets[prefix].append(img)

        self.current_triplets = [triplet for triplet in triplets.values() if len(triplet) == 3]
        random.shuffle(self.current_triplets)

    def prepare_test(self):
        if not hasattr(self, "current_triplets") or not self.current_triplets:
            QMessageBox.warning(self, "Erreur", "Aucun triplet sélectionné pour ce patient.")
            return
        self.session_active = True
        self.waiting_screen.show()
        self.patient_window.show()
        self.session_start_time = time.time()
        self.show_triplet()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress and self.session_active:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.nurse_clicks.append({"evenement": "clic_infirmiere", "horodatage": now})
        return super().eventFilter(obj, event)

    def show_triplet(self):
        for layout in (self.image_layout, self.patient_window.image_layout):
            for i in reversed(range(layout.count())):
                widget = layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)

        self.experimenter_labels.clear()

        if self.current_index >= len(self.current_triplets):
            self.end_session()
            return

        images = self.current_triplets[self.current_index]
        famous_img = next((img for img in images if "_0." in img), None)
        if not famous_img:
            QMessageBox.critical(self, "Erreur", "Image _0 non trouvée pour ce triplet.")
            return

        shuffled = images[:]
        random.shuffle(shuffled)
        self.flags = [img == famous_img for img in shuffled]
        self.selected_index = None
        self.start_time = time.time()

        for idx, (img_path, is_famous) in enumerate(zip(shuffled, self.flags)):
            pixmap = QPixmap(img_path).scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio)

            label_patient = QLabel()
            label_patient.setPixmap(pixmap)
            label_patient.mousePressEvent = self.make_click_handler(is_famous, idx)
            self.patient_window.image_layout.addWidget(label_patient)

            label_mirror = QLabel()
            label_mirror.setPixmap(pixmap)
            label_mirror.setStyleSheet("border: 2px solid transparent; margin: 5px;")
            self.image_layout.addWidget(label_mirror)
            self.experimenter_labels.append(label_mirror)

    def make_click_handler(self, is_famous, index):
        def handler(event):
            self.selected_index = index
            self.handle_click(is_famous)
        return handler

    def handle_click(self, is_famous):
        if not self.session_active:
            return

        now = time.time()
        reaction_time = round(now - self.start_time, 3)
        elapsed_since_start = round(now - self.session_start_time, 3)

        self.click_times.append(reaction_time)
        if not is_famous:
            self.error_indices.append(self.current_index)

        self.trial_results.append({
            "id_essai": self.current_index + 1,
            "temps_total_depuis_debut": elapsed_since_start,
            "image_choisie": "famous" if is_famous else "distracteur",
            "correct": is_famous,
            "temps_reponse": reaction_time,
            "horodatage_stimulation": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "participant": self.participant_name
        })

        for i, label in enumerate(self.experimenter_labels):
            if i == self.selected_index:
                color = "green" if self.flags[i] else "red"
                label.setStyleSheet(f"border: 4px solid {color}; margin: 5px;")

        self.current_index += 1
        QTimer.singleShot(500, self.show_triplet)

    def handle_timeout(self):
        self.timer.stop()
        now = time.time()
        elapsed_since_start = round(now - self.session_start_time, 3)

        self.click_times.append(self.timer_duration)
        self.error_indices.append(self.current_index)

        self.trial_results.append({
            "id_essai": self.current_index + 1,
            "temps_total_depuis_debut": elapsed_since_start,
            "image_choisie": "aucune",
            "correct": False,
            "temps_reponse": self.timer_duration,
            "horodatage_stimulation": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "participant": self.participant_name
        })

        self.current_index += 1
        self.show_triplet()

    def end_session(self):
        if not self.session_active:
            return

        self.session_active = False
        self.patient_window.hide()

        df_trials = pd.DataFrame(self.trial_results)
        df_clicks = pd.DataFrame(self.nurse_clicks)
        full_df = pd.concat([df_trials, df_clicks], ignore_index=True)

        now = datetime.now()
        timestamp = now.strftime("%Y_%m_%d_%H%M")
        nom_fichier = f"{self.participant_name}_{timestamp}_famous_face.xlsx"

        try:
            full_df.to_excel(nom_fichier, index=False, engine='openpyxl')
            QMessageBox.information(self, "Fin", f"Test terminé. Résultats sauvegardés dans {nom_fichier}.")
        except PermissionError:
            QMessageBox.critical(self, "Erreur", "Fichier Excel ouvert. Fermez-le et réessayez.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FamousFaceTest()
    window.show()
    sys.exit(app.exec())
