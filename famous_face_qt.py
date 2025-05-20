import sys
import os
import random
import uuid
import time
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QLineEdit, QMessageBox, QComboBox
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QTimer, Qt
import pandas as pd

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

        self.image_folder = "image_famous_faceV1"
        self.test_name = "famous_face"
        self.results_file = "resultats_test.xlsx"

        all_images = [img for img in os.listdir(self.image_folder) if img.lower().endswith((".png", ".jpg", ".jpeg"))]
        triplet_dict = {}
        for img in all_images:
            try:
                prefix = img.split("_")[1]
                if prefix not in triplet_dict:
                    triplet_dict[prefix] = []
                triplet_dict[prefix].append(img)
            except IndexError:
                continue

        self.all_triplets = [
            sorted(images, key=lambda name: int(name.split("_")[2].split(".")[0]))
            for _, images in sorted(triplet_dict.items(), key=lambda item: int(item[0]))
            if len(images) == 3
        ]

        random.shuffle(self.all_triplets)
        self.current_triplets = self.all_triplets[:]

        self.current_index = 0
        self.click_times = []
        self.error_indices = []
        self.start_time = None
        self.session_active = False
        self.participant_name = ""

        self.mode = "click"
        self.timer_duration = 3
        self.space_mode = False
        self.selected_index = None
        self.experimenter_labels = []

        self.timer = QTimer()
        self.timer.timeout.connect(self.handle_timeout)

        self.patient_window = PatientWindow()
        self.waiting_screen = WaitingScreen()
        self.init_ui()

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout()

        self.config_layout = QVBoxLayout()
        self.prenom_input = QLineEdit()
        self.prenom_input.setPlaceholderText("Prénom")
        self.nom_input = QLineEdit()
        self.nom_input.setPlaceholderText("Nom")

        self.mode_label = QLabel("Mode d'affichage des images :")
        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["Image au clic", "Temps imparti", "Barre espace"])
        self.mode_selector.currentTextChanged.connect(self.toggle_timer_input)

        self.timer_input = QLineEdit()
        self.timer_input.setPlaceholderText("Temps (en secondes)")
        self.timer_input.setVisible(False)

        self.start_btn = QPushButton("Valider et Préparer le test")
        self.start_btn.clicked.connect(self.prepare_test)

        self.stop_btn = QPushButton("Arrêter et sauvegarder")
        self.stop_btn.clicked.connect(self.end_session)

        self.config_layout.addWidget(self.prenom_input)
        self.config_layout.addWidget(self.nom_input)
        self.config_layout.addWidget(self.mode_label)
        self.config_layout.addWidget(self.mode_selector)
        self.config_layout.addWidget(self.timer_input)
        self.config_layout.addWidget(self.start_btn)
        self.config_layout.addWidget(self.stop_btn)

        self.image_layout = QHBoxLayout()
        self.image_panel = QWidget()
        self.image_panel.setLayout(self.image_layout)

        self.main_layout.addLayout(self.config_layout)
        self.main_layout.addWidget(self.image_panel)

        self.central_widget.setLayout(self.main_layout)

    def toggle_timer_input(self):
        self.timer_input.setVisible(self.mode_selector.currentText() == "Temps imparti")

    def keyPressEvent(self, event):
        if self.space_mode and event.key() == Qt.Key.Key_Space:
            self.handle_click(self.flags[self.selected_index])

    def prepare_test(self):
        prenom = self.prenom_input.text().strip()
        nom = self.nom_input.text().strip()
        if not prenom or not nom:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer un nom et prénom.")
            return

        self.participant_name = f"{prenom} {nom}"
        mode_text = self.mode_selector.currentText()
        self.mode = "timer" if mode_text == "Temps imparti" else "click" if mode_text == "Image au clic" else "space"
        self.space_mode = self.mode == "space"

        try:
            self.timer_duration = int(self.timer_input.text()) if self.mode == "timer" else 0
        except ValueError:
            self.timer_duration = 3

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()
        self.waiting_screen.show()

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_Space and not self.session_active and self.waiting_screen.isVisible():
            self.waiting_screen.hide()
            self.session_active = True
            self.current_index = 0
            self.click_times = []
            self.error_indices = []
            self.current_triplets = self.all_triplets[:]
            random.shuffle(self.current_triplets)
            self.patient_window.show()
            self.show_triplet()

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
            QMessageBox.critical(self, "Erreur", "Impossible de trouver l'image _0 pour ce triplet.")
            return

        shuffled = images[:]
        random.shuffle(shuffled)
        self.flags = [img == famous_img for img in shuffled]
        self.selected_index = None
        self.start_time = time.time()

        for idx, (img_name, is_famous) in enumerate(zip(shuffled, self.flags)):
            img_path = os.path.join(self.image_folder, img_name)
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

        if self.mode == "timer":
            self.timer.start(self.timer_duration * 1000)

    def make_click_handler(self, is_famous, index):
        def handler(event):
            self.selected_index = index
            self.handle_click(is_famous)
        return handler

    def handle_click(self, is_famous):
        if not self.session_active:
            return

        if self.timer.isActive():
            self.timer.stop()

        reaction_time = round(time.time() - self.start_time, 3)
        self.click_times.append(reaction_time)

        if not is_famous:
            self.error_indices.append(self.current_index)

        # Visual feedback on experimenter screen
        for i, label in enumerate(self.experimenter_labels):
            if i == self.selected_index:
                color = "green" if self.flags[i] else "red"
                label.setStyleSheet(f"border: 4px solid {color}; margin: 5px;")

        self.current_index += 1
        QTimer.singleShot(500, self.show_triplet)

    def handle_timeout(self):
        self.timer.stop()
        self.click_times.append(self.timer_duration)
        self.error_indices.append(self.current_index)
        self.current_index += 1
        self.show_triplet()

    def end_session(self):
        if not self.session_active:
            return

        self.session_active = False
        self.patient_window.hide()

        session_id = str(uuid.uuid4())
        session_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result_dict = {
            "id_client": session_id,
            "nom_prenom": self.participant_name,
            "date_test": session_time,
            "nom_test": self.test_name,
            "choix_affichage": self.mode,
            "temps": self.timer_duration if self.mode == "timer" else "NA",
            "nombre_erreurs": len(self.error_indices),
            "clics_temps": self.click_times,
            "moyenne_temps_clic": round(sum(self.click_times)/len(self.click_times), 3) if self.click_times else "NA"
        }

        df_new = pd.DataFrame([result_dict])
        path = Path(self.results_file)
        if path.exists():
            try:
                df_old = pd.read_excel(path)
                df_full = pd.concat([df_old, df_new], ignore_index=True)
            except Exception:
                df_full = df_new
        else:
            df_full = df_new

        try:
            df_full.to_excel(path, index=False, engine='openpyxl')
            QMessageBox.information(self, "Fin", f"Test terminé. Résultats sauvegardés dans {self.results_file}.")
        except PermissionError:
            QMessageBox.critical(self, "Erreur", "Le fichier Excel est ouvert. Fermez-le puis relancez.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FamousFaceTest()
    window.show()
    sys.exit(app.exec())
