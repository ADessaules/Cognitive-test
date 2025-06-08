import sys
import os
import random
import hashlib
import time
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QLineEdit, QMessageBox, QComboBox
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QTimer, Qt, QEvent
import pandas as pd


def hash_image(path):
    """Génère un hash MD5 d'une image pour vérifier l'unicité visuelle."""
    pixmap = QPixmap(path)
    image_bytes = pixmap.toImage().bits().asstring(pixmap.width() * pixmap.height() * 4)
    return hashlib.md5(image_bytes).hexdigest()


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
        self.top_label = QLabel()
        self.top_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.top_label)
        layout.addLayout(self.bottom_layout)
        self.setLayout(layout)

    def show_triplet(self, top_image_path, bottom_images, handlers):
        self.top_label.setPixmap(QPixmap(top_image_path).scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio))

        for i in reversed(range(self.bottom_layout.count())):
            widget = self.bottom_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        for path, handler in zip(bottom_images, handlers):
            label = QLabel()
            label.setPixmap(QPixmap(path).scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio))
            label.mousePressEvent = handler
            self.bottom_layout.addWidget(label)


class MatchingUnknownTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Matching Unknown Test - Expérimentateur")
        self.setGeometry(100, 100, 1200, 600)

        self.image_folder = os.path.join(os.path.dirname(__file__), "image_matching_unknown_faceV1")
        self.test_name = "matching_unknown"
        self.triplet_widgets = []

        self.patient_window = PatientWindow()
        self.waiting_screen = WaitingScreen()
        self.timer = QTimer()
        self.installEventFilter(self)

        self.init_data()
        self.init_ui()

    def init_data(self):
        triplets = {}
        for file in os.listdir(self.image_folder):
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                prefix = file.rsplit("_", 1)[0]
                triplets.setdefault(prefix, []).append(file)

        self.all_triplets = []
        for group in triplets.values():
            if len(group) == 3:
                paths = [os.path.join(self.image_folder, f) for f in group]
                hashes = {hash_image(p) for p in paths}
                if len(hashes) == 3:
                    self.all_triplets.append(group)

        self.session_results = []

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout()

        left = QVBoxLayout()

        self.patient_selector = QComboBox()
        self.patient_selector.addItem("-- Aucun --")
        patients_path = Path(__file__).resolve().parent.parent / "Patients"
        if patients_path.exists():
            for folder in patients_path.iterdir():
                if folder.is_dir():
                    self.patient_selector.addItem(folder.name)

        self.contact_input = QLineEdit("C1-C2")
        self.intensite_input = QLineEdit("1.5")
        self.duree_input = QLineEdit("500")

        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["Image au clic", "Temps imparti", "Barre espace"])
        self.timer_input = QLineEdit("5")
        self.timer_input.setVisible(False)
        self.mode_selector.currentTextChanged.connect(lambda x: self.timer_input.setVisible(x == "Temps imparti"))

        start_btn = QPushButton("Valider et Préparer le test")
        start_btn.clicked.connect(self.start_test)
        stop_btn = QPushButton("Arrêter et sauvegarder")
        stop_btn.clicked.connect(self.save_results)

        for w in [
            QLabel("Sélectionner un patient :"), self.patient_selector,
            self.contact_input, self.intensite_input, self.duree_input,
            QLabel("Mode d'affichage des images :"), self.mode_selector,
            self.timer_input, start_btn, stop_btn
        ]:
            left.addWidget(w)

        self.image_layout = QVBoxLayout()
        self.top_layout = QHBoxLayout()
        self.bottom_layout = QHBoxLayout()
        self.image_layout.addLayout(self.top_layout)
        self.image_layout.addLayout(self.bottom_layout)

        right = QWidget()
        right.setLayout(self.image_layout)

        layout.addLayout(left)
        layout.addWidget(right)
        central.setLayout(layout)

    def start_test(self):
        if self.patient_selector.currentText() == "-- Aucun --":
            QMessageBox.warning(self, "Erreur", "Veuillez choisir un patient.")
            return

        self.contact = self.contact_input.text()
        self.intensite = self.intensite_input.text()
        self.duree = self.duree_input.text()
        self.mode = self.mode_selector.currentText()
        self.timer_duration = int(self.timer_input.text()) if self.mode == "Temps imparti" else 0

        self.shuffled_triplets = random.sample(self.all_triplets, len(self.all_triplets))
        self.index = 0
        self.waiting_screen.show()
        self.patient_window.show()
        self.setFocus()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyRelease and event.key() == Qt.Key.Key_Space and self.waiting_screen.isVisible():
            self.waiting_screen.hide()
            self.show_next_triplet()
        return super().eventFilter(obj, event)

    def show_next_triplet(self):
        for layout in (self.top_layout, self.bottom_layout):
            for i in reversed(range(layout.count())):
                widget = layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)

        if self.index >= len(self.shuffled_triplets):
            self.save_results()
            return

        triplet = self.shuffled_triplets[self.index]
        top = next((f for f in triplet if "_0" in f), None)
        bottom = [f for f in triplet if f != top]
        random.shuffle(bottom)

        top_path = os.path.join(self.image_folder, top)
        bottom_paths = [os.path.join(self.image_folder, f) for f in bottom]
        is_correct = {path: "_1" in os.path.basename(path) for path in bottom_paths}

        self.start_time = time.time()

        def make_handler(img_path):
            def handler(event):
                rt = round(time.time() - self.start_time, 3)
                self.session_results.append({
                    "id_essai": self.index + 1,
                    "temps_reponse": rt,
                    "image_choisie": "correct" if is_correct[img_path] else "distracteur",
                    "correct": is_correct[img_path],
                    "triplet_nom": top.rsplit("_", 1)[0],
                    "participant": self.patient_selector.currentText(),
                    "contact_stimulation": self.contact,
                    "intensité": self.intensite,
                    "durée": self.duree,
                    "mode": self.mode,
                    "horodatage": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

                for i, path in enumerate(bottom_paths):
                    label = self.bottom_layout.itemAt(i).widget()
                    color = "green" if is_correct[path] else "red"
                    if path == img_path:
                        label.setStyleSheet(f"border: 4px solid {color}; margin: 5px;")
                self.index += 1
                QTimer.singleShot(500, self.show_next_triplet)
            return handler

        handlers = [make_handler(p) for p in bottom_paths]

        self.patient_window.show_triplet(top_path, bottom_paths, handlers)

        top_lbl = QLabel()
        top_lbl.setPixmap(QPixmap(top_path).scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio))
        self.top_layout.addWidget(top_lbl)

        for p in bottom_paths:
            lbl = QLabel()
            lbl.setPixmap(QPixmap(p).scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio))
            self.bottom_layout.addWidget(lbl)

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
