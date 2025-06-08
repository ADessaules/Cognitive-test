import sys
import os
import random
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


class PatientWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test en cours - Écran patient")
        self.setGeometry(920, 100, 800, 600)
        self.top_label = QLabel()
        self.bottom_layout = QHBoxLayout()
        layout = QVBoxLayout()
        layout.addWidget(self.top_label)
        layout.addLayout(self.bottom_layout)
        self.setLayout(layout)

    def show_triplet(self, top_image_path, bottom_images, handlers):
        pixmap_top = QPixmap(top_image_path).scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio)
        self.top_label.setPixmap(pixmap_top)
        for i in reversed(range(self.bottom_layout.count())):
            w = self.bottom_layout.itemAt(i).widget()
            if w:
                w.setParent(None)
        for path, handler in zip(bottom_images, handlers):
            label = QLabel()
            pixmap = QPixmap(path).scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio)
            label.setPixmap(pixmap)
            label.mousePressEvent = handler
            self.bottom_layout.addWidget(label)


class MatchingUnknownTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Matching Unknown Test - Expérimentateur")
        self.setGeometry(100, 100, 1200, 600)

        self.image_folder = os.path.join(os.path.dirname(__file__), "image_unknown_faceV1")
        self.test_name = "matching_unknown"

        self.patient_window = PatientWindow()
        self.patient_window.show()
        self.timer = QTimer()

        self.init_data()
        self.init_ui()

    def init_data(self):
        self.triplets = {}
        for file in os.listdir(self.image_folder):
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                prefix = "_".join(file.split("_")[:2])
                self.triplets.setdefault(prefix, []).append(file)

        self.all_triplets = [v for v in self.triplets.values() if len(v) == 3]
        self.session_results = []

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()

        self.patient_selector = QComboBox()
        self.patient_selector.addItem("-- Aucun --")
        for folder in Path("Patients").iterdir():
            if folder.is_dir():
                self.patient_selector.addItem(folder.name)

        self.contact_input = QLineEdit("Contacts de stimulation")
        self.intensite_input = QLineEdit("Intensité (mA)")
        self.duree_input = QLineEdit("Durée (ms)")

        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["Image au clic", "Temps imparti", "Barre espace"])
        self.timer_input = QLineEdit("Temps (en secondes)")
        self.timer_input.setVisible(False)

        self.mode_selector.currentTextChanged.connect(lambda x: self.timer_input.setVisible(x == "Temps imparti"))

        start_btn = QPushButton("Valider et Préparer le test")
        start_btn.clicked.connect(self.start_test)

        stop_btn = QPushButton("Arrêter et sauvegarder")
        stop_btn.clicked.connect(self.save_results)

        layout.addWidget(QLabel("Sélectionner un patient :"))
        layout.addWidget(self.patient_selector)
        layout.addWidget(self.contact_input)
        layout.addWidget(self.intensite_input)
        layout.addWidget(self.duree_input)
        layout.addWidget(QLabel("Mode d'affichage des images :"))
        layout.addWidget(self.mode_selector)
        layout.addWidget(self.timer_input)
        layout.addWidget(start_btn)
        layout.addWidget(stop_btn)

        central.setLayout(layout)

    def start_test(self):
        if self.patient_selector.currentText() == "-- Aucun --":
            QMessageBox.warning(self, "Erreur", "Veuillez choisir un patient.")
            return

        self.contact = self.contact_input.text().strip()
        self.intensite = self.intensite_input.text().strip()
        self.duree = self.duree_input.text().strip()

        self.mode = self.mode_selector.currentText()
        self.timer_duration = int(self.timer_input.text()) if self.mode == "Temps imparti" else 0

        self.shuffled_triplets = random.sample(self.all_triplets, len(self.all_triplets))
        self.index = 0
        self.show_next_triplet()

    def show_next_triplet(self):
        if self.index >= len(self.shuffled_triplets):
            self.save_results()
            return

        triplet = self.shuffled_triplets[self.index]
        prefix = "_".join(triplet[0].split("_")[:2])
        top = next(f for f in triplet if f.endswith("_0.jpg") or f.endswith("_0.png"))
        correct = next(f for f in triplet if f.endswith("_1.jpg") or f.endswith("_1.png"))
        distractor = next(f for f in triplet if f.endswith("_2.jpg") or f.endswith("_2.png"))

        options = [correct, distractor]
        random.shuffle(options)
        is_correct_map = {img: (img == correct) for img in options}

        start_time = time.time()

        def make_handler(selected_img):
            def handler(event):
                rt = round(time.time() - start_time, 3)
                self.session_results.append({
                    "id_essai": self.index + 1,
                    "temps_reponse": rt,
                    "image_choisie": "correct" if is_correct_map[selected_img] else "distracteur",
                    "correct": is_correct_map[selected_img],
                    "triplet_nom": prefix,
                    "participant": self.patient_selector.currentText(),
                    "contact_stimulation": self.contact,
                    "intensité": self.intensite,
                    "durée": self.duree,
                    "horodatage": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                self.index += 1
                QTimer.singleShot(500, self.show_next_triplet)
            return handler

        top_path = os.path.join(self.image_folder, top)
        options_path = [os.path.join(self.image_folder, opt) for opt in options]
        handlers = [make_handler(opt) for opt in options]

        self.patient_window.show_triplet(top_path, options_path, handlers)

    def save_results(self):
        df = pd.DataFrame(self.session_results)
        if df.empty:
            return
        now = datetime.now().strftime("%Y_%m_%d_%H%M")
        name = self.patient_selector.currentText().replace(" ", "_")
        filename = f"{name}_{now}_{self.contact}-{self.intensite}-{self.duree}_{self.test_name}.xlsx"
        df.to_excel(filename, index=False)
        QMessageBox.information(self, "Fin", f"Test terminé. Fichier sauvegardé : {filename}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MatchingUnknownTest()
    window.show()
    sys.exit(app.exec())
