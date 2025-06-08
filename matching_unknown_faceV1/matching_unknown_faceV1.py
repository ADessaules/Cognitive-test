import sys, os, random, time
from datetime import datetime
from pathlib import Path
import pandas as pd

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QLineEdit, QMessageBox, QComboBox
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QTimer, Qt, QEvent


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
        self.top_label = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        self.bottom_layout = QHBoxLayout(alignment=Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout(alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.top_label)
        layout.addLayout(self.bottom_layout)
        self.setLayout(layout)

    def show_triplet(self, top_image, bottom_images, handlers):
        pixmap_top = QPixmap(top_image).scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio)
        self.top_label.setPixmap(pixmap_top)

        for i in reversed(range(self.bottom_layout.count())):
            w = self.bottom_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        for img, handler in zip(bottom_images, handlers):
            label = QLabel()
            label.setPixmap(QPixmap(img).scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio))
            label.mousePressEvent = handler
            self.bottom_layout.addWidget(label)


class MatchingUnknownTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Matching Unknown Test - Expérimentateur")
        self.setGeometry(100, 100, 1200, 600)

        self.image_folder = os.path.join(os.path.dirname(__file__), "image_matching_unknown_faceV1")
        self.test_name = "matching_unknown"

        self.waiting_screen = WaitingScreen()
        self.patient_window = PatientWindow()
        self.timer = QTimer()

        self.init_data()
        self.init_ui()

    def init_data(self):
        self.triplets = {}
        for file in os.listdir(self.image_folder):
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                prefix = "_".join(file.split("_")[:2])
                self.triplets.setdefault(prefix, []).append(file)

        self.all_triplets = [
            sorted(v, key=lambda x: int(x.split("_")[-1].split(".")[0]))
            for v in self.triplets.values() if len(v) == 3
        ]
        self.session_results = []

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout()

        config_layout = QVBoxLayout()
        self.patient_selector = QComboBox()
        self.patient_selector.addItem("-- Aucun --")
        patients_path = Path(__file__).resolve().parent.parent / "Patients"
        for folder in patients_path.iterdir():
            if folder.is_dir():
                self.patient_selector.addItem(folder.name)

        self.contact_input = QLineEdit()
        self.contact_input.setPlaceholderText("Contacts de stimulation")
        self.intensite_input = QLineEdit()
        self.intensite_input.setPlaceholderText("Intensité (mA)")
        self.duree_input = QLineEdit()
        self.duree_input.setPlaceholderText("Durée (ms)")

        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["Image au clic", "Temps imparti", "Barre espace"])
        self.timer_input = QLineEdit()
        self.timer_input.setPlaceholderText("Temps (en secondes)")
        self.timer_input.setVisible(False)
        self.mode_selector.currentTextChanged.connect(lambda x: self.timer_input.setVisible(x == "Temps imparti"))

        start_btn = QPushButton("Valider et Préparer le test")
        start_btn.clicked.connect(self.prepare_test)
        stop_btn = QPushButton("Arrêter et sauvegarder")
        stop_btn.clicked.connect(self.save_results)

        for w in [
            QLabel("Sélectionner un patient :"), self.patient_selector,
            self.contact_input, self.intensite_input, self.duree_input,
            QLabel("Mode d'affichage des images :"), self.mode_selector,
            self.timer_input, start_btn, stop_btn
        ]:
            config_layout.addWidget(w)

        self.image_layout = QVBoxLayout()
        self.top_img = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        self.bottom_layout = QHBoxLayout(alignment=Qt.AlignmentFlag.AlignCenter)
        self.image_layout.addWidget(self.top_img)
        self.image_layout.addLayout(self.bottom_layout)

        layout.addLayout(config_layout)
        layout.addLayout(self.image_layout)
        central.setLayout(layout)

    def prepare_test(self):
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
        self.session_active = False
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()
        self.waiting_screen.show()
        self.patient_window.show()

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_Space and not self.session_active and self.waiting_screen.isVisible():
            self.waiting_screen.hide()
            self.session_active = True
            self.show_next_triplet()

    def show_next_triplet(self):
        for layout in (self.bottom_layout, self.patient_window.bottom_layout):
            for i in reversed(range(layout.count())):
                widget = layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)

        if self.index >= len(self.shuffled_triplets):
            self.save_results()
            return

        triplet = self.shuffled_triplets[self.index]
        top_file = next(f for f in triplet if "_0" in f)
        bottom_files = [f for f in triplet if "_1" in f or "_2" in f]
        random.shuffle(bottom_files)

        prefix = "_".join(top_file.split("_")[:2])
        start_time = time.time()
        correct_img = next(f for f in bottom_files if "_1" in f)
        is_correct_map = {img: (img == correct_img) for img in bottom_files}

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
                    "mode": self.mode,
                    "horodatage": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                self.index += 1
                QTimer.singleShot(500, self.show_next_triplet)
            return handler

        top_path = os.path.join(self.image_folder, top_file)
        bottom_paths = [os.path.join(self.image_folder, f) for f in bottom_files]
        handlers = [make_handler(img) for img in bottom_files]

        # Patient
        self.patient_window.show_triplet(top_path, bottom_paths, handlers)

        # Expérimentateur
        self.top_img.setPixmap(QPixmap(top_path).scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio))
        for i, path in enumerate(bottom_paths):
            label = QLabel()
            label.setPixmap(QPixmap(path).scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio))
            self.bottom_layout.addWidget(label)

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
