from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QLineEdit, QMessageBox, QComboBox
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QTimer, Qt
from pathlib import Path
from datetime import datetime
import sys, os, random, time
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
        self.top_label = QLabel()
        self.top_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.top_label)
        layout.addLayout(self.bottom_layout)
        self.setLayout(layout)

    def show_triplet(self, top_image_path, bottom_images, handlers):
        pixmap_top = QPixmap(top_image_path).scaled(
            250, 250, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self.top_label.setPixmap(pixmap_top)

        for i in reversed(range(self.bottom_layout.count())):
            w = self.bottom_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        for path, handler in zip(bottom_images, handlers):
            label = QLabel()
            pixmap = QPixmap(path).scaled(
                250, 250, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            label.setPixmap(pixmap)
            label.mousePressEvent = handler
            self.bottom_layout.addWidget(label)


class MatchingUnknownTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Matching Unknown Test - Expérimentateur")
        self.setGeometry(100, 100, 1200, 600)
        self.image_folder = os.path.join(os.path.dirname(__file__), "image_matching_unknown_faceV1")
        self.test_name = "matching_unknown"

        self.patient_window = PatientWindow()
        self.patient_window.show()
        self.waiting_screen = WaitingScreen()
        self.timer = QTimer()
        self.session_active = False

        self.init_data()
        self.init_ui()

    def init_data(self):
        self.triplets = {}
        for file in os.listdir(self.image_folder):
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                prefix = file.rsplit("_", 1)[0]
                self.triplets.setdefault(prefix, []).append(file)
    
        # Ne garder que les triplets complets : un _0, un _1 et un _2
        self.all_triplets = [
            files for files in self.triplets.values()
            if any("_0" in f for f in files) and
               any("_1" in f for f in files) and
               any("_2" in f for f in files)
        ]
    
        self.session_results = []

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout()

        left_layout = QVBoxLayout()

        self.patient_selector = QComboBox()
        self.patient_selector.addItem("-- Aucun --")
        patients_path = Path(__file__).resolve().parent.parent / "Patients"
        if patients_path.exists():
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
        start_btn.clicked.connect(self.start_test)
        stop_btn = QPushButton("Arrêter et sauvegarder")
        stop_btn.clicked.connect(self.save_results)

        for w in [
            QLabel("Sélectionner un patient :"), self.patient_selector,
            self.contact_input, self.intensite_input, self.duree_input,
            QLabel("Mode d'affichage des images :"), self.mode_selector,
            self.timer_input, start_btn, stop_btn
        ]:
            left_layout.addWidget(w)

        # Expérimentateur layout (triangle : top + bottom)
        self.image_layout = QVBoxLayout()
        self.top_exp_label = QLabel()
        self.top_exp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.bottom_exp_layout = QHBoxLayout()
        self.bottom_exp_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.image_layout.addWidget(self.top_exp_label)
        self.image_layout.addLayout(self.bottom_exp_layout)

        right_panel = QWidget()
        right_panel.setLayout(self.image_layout)

        layout.addLayout(left_layout)
        layout.addWidget(right_panel)
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

        self.waiting_screen.show()
        self.patient_window.show()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_Space and self.waiting_screen.isVisible():
            self.waiting_screen.hide()
            self.session_active = True
            self.index = 0
            self.show_next_triplet()

    def show_next_triplet(self):
        for layout in [self.image_layout, self.bottom_exp_layout]:
            for i in reversed(range(layout.count())):
                w = layout.itemAt(i).widget()
                if w:
                    w.setParent(None)

        if self.index >= len(self.shuffled_triplets):
            self.save_results()
            return

        triplet = self.shuffled_triplets[self.index]
        prefix = "_".join(triplet[0].split("_")[:2])
        
        top_list = [f for f in triplet if "_0" in f]
        if not top_list:
            print(f"❌ Triplet mal formé ignoré (haut manquant): {triplet}")
            self.index += 1
            self.show_next_triplet()
            return
        top = top_list[0]
        
        bottom = [f for f in triplet if "_1" in f or "_2" in f]
        if len(bottom) != 2:
            print(f"❌ Triplet mal formé ignoré (bas): {triplet}")
            self.index += 1
            self.show_next_triplet()
            return

        def make_handler(selected_img):
            def handler(event):
                rt = round(time.time() - self.start_time, 3)
                self.session_results.append({
                    "id_essai": self.index + 1,
                    "temps_reponse": rt,
                    "image_choisie": "correct" if "_1" in selected_img else "distracteur",
                    "correct": "_1" in selected_img,
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

        top_path = os.path.join(self.image_folder, top)
        options_path = [os.path.join(self.image_folder, opt) for opt in bottom]
        handlers = [make_handler(opt) for opt in bottom]

        # Affichage patient
        self.patient_window.show_triplet(top_path, options_path, handlers)

        # Affichage expérimentateur
        self.top_exp_label.setPixmap(QPixmap(top_path).scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio))
        for path in options_path:
            lbl = QLabel()
            lbl.setPixmap(QPixmap(path).scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio))
            self.bottom_exp_layout.addWidget(lbl)

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
