# VERSION ADAPTÉE DU TEST SÉMANTIQUE PAR IMAGES
# Ce script suit la même structure que matching_unknown_faceV1.py


import sys
import os
import random
import time
import datetime
import pandas as pd
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QLineEdit, QMessageBox, QComboBox, QGridLayout
)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt, QTimer, QEvent

class WaitingScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("\u00c9cran d'attente")
        self.setGeometry(920, 100, 800, 600)
        layout = QVBoxLayout()
        label = QLabel("Appuyez sur Espace pour d\u00e9marrer le test")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)

class PatientWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Appariement S\u00e9mantique - Patient")
        self.setGeometry(920, 100, 800, 600)
        self.top_label = QLabel()
        self.top_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bottom_layout = QHBoxLayout()
        layout = QVBoxLayout()
        layout.addWidget(self.top_label)
        layout.addLayout(self.bottom_layout)
        self.setLayout(layout)

    def show_triplet(self, top_image_path, options, handlers):
        pixmap_top = QPixmap(top_image_path).scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio)
        self.top_label.setPixmap(pixmap_top)

        for i in reversed(range(self.bottom_layout.count())):
            w = self.bottom_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        for path, handler in zip(options, handlers):
            btn = QPushButton()
            btn.setIcon(QIcon(path))
            btn.setIconSize(pixmap_top.size())
            btn.setFixedSize(220, 220)
            btn.clicked.connect(handler)
            self.bottom_layout.addWidget(btn)

class ImageSemanticMatchingTest(QMainWindow):
    def __init__(self, test_triplets):
        super().__init__()
        self.setWindowTitle("Test Appariement S\u00e9mantique - Images")
        self.setGeometry(100, 100, 1200, 600)
        self.test_triplets = test_triplets
        self.test_name = "matching_images"
        self.timer = QTimer()
        self.timer.timeout.connect(self.advance_by_timer)
        self.init_ui()
        self.installEventFilter(self)

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout()
        left_layout = QVBoxLayout()

        self.patient_selector = QComboBox()
        self.patient_selector.addItem("-- Aucun --")
        patients_path = Path(__file__).resolve().parent / "Patients"
        if patients_path.exists():
            for folder in patients_path.iterdir():
                if folder.is_dir():
                    self.patient_selector.addItem(folder.name)

        self.contact_input = QLineEdit()
        self.contact_input.setPlaceholderText("Contacts de stimulation")
        self.intensite_input = QLineEdit()
        self.intensite_input.setPlaceholderText("Intensit\u00e9 (mA)")
        self.duree_input = QLineEdit()
        self.duree_input.setPlaceholderText("Dur\u00e9e (ms)")

        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["Image au clic", "Temps imparti", "Barre espace"])
        self.timer_input = QLineEdit()
        self.timer_input.setPlaceholderText("Temps (en secondes)")
        self.timer_input.setVisible(False)
        self.mode_selector.currentTextChanged.connect(lambda x: self.timer_input.setVisible(x == "Temps imparti"))

        start_btn = QPushButton("Valider et Pr\u00e9parer le test")
        start_btn.clicked.connect(self.prepare_test)
        stop_btn = QPushButton("Arr\u00eater et sauvegarder")
        stop_btn.clicked.connect(self.save_results)

        for w in [QLabel("S\u00e9lectionner un patient :"), self.patient_selector,
                  self.contact_input, self.intensite_input, self.duree_input,
                  QLabel("Mode de test :"), self.mode_selector,
                  self.timer_input, start_btn, stop_btn]:
            left_layout.addWidget(w)

        self.status_label = QLabel("En attente du d\u00e9marrage du test…")
        left_layout.addWidget(self.status_label)

        self.image_layout = QVBoxLayout()
        layout.addLayout(left_layout)
        layout.addLayout(self.image_layout)
        central.setLayout(layout)

    def prepare_test(self):
        if self.patient_selector.currentText() == "-- Aucun --" or not all([
            self.contact_input.text().strip(),
            self.intensite_input.text().strip(),
            self.duree_input.text().strip()
        ]):
            QMessageBox.warning(self, "Erreur", "Veuillez remplir tous les champs et choisir un patient.")
            return

        if self.mode_selector.currentText() == "Temps imparti" and not self.timer_input.text().isdigit():
            QMessageBox.warning(self, "Erreur", "Veuillez entrer un temps valide en secondes.")
            return

        self.contact = self.contact_input.text().strip()
        self.intensite = self.intensite_input.text().strip()
        self.duree = self.duree_input.text().strip()
        self.mode = self.mode_selector.currentText()
        self.timer_duration = int(self.timer_input.text()) if self.mode == "Temps imparti" else 0

        self.shuffled_triplets = random.sample(self.test_triplets, len(self.test_triplets))
        self.index = 0
        self.session_results = []
        self.session_active = False

        self.patient_window = PatientWindow()
        self.waiting_screen = WaitingScreen()
        self.waiting_screen.show()
        self.patient_window.show()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyRelease and event.key() == Qt.Key.Key_Space:
            if not self.session_active and self.waiting_screen.isVisible():
                self.waiting_screen.hide()
                self.session_active = True
                self.show_next_triplet()
            elif self.session_active and self.mode == "Barre espace":
                self.index += 1
                self.show_next_triplet()
        return super().eventFilter(obj, event)

    def advance_by_timer(self):
        self.index += 1
        self.show_next_triplet()

    def show_next_triplet(self):
        for i in reversed(range(self.image_layout.count())):
            w = self.image_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        if self.index >= len(self.shuffled_triplets):
            self.save_results()
            return

        test_path, correct_path, distractor_path = self.shuffled_triplets[self.index]
        options = [correct_path, distractor_path]
        random.shuffle(options)
        is_correct_map = {opt: opt == correct_path for opt in options}
        self.start_time = time.time()

        def make_handler(selected_img, btn):
            def handler():
                rt = round(time.time() - self.start_time, 3)
                self.session_results.append({
                    "id_essai": self.index + 1,
                    "temps_reponse": rt,
                    "image_choisie": os.path.basename(selected_img),
                    "correct": is_correct_map[selected_img],
                    "image_testee": os.path.basename(test_path),
                    "participant": self.patient_selector.currentText(),
                    "contact_stimulation": self.contact,
                    "intensité": self.intensite,
                    "durée": self.duree,
                    "mode": self.mode,
                    "horodatage": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "test_name": self.test_name
                })
                for b in buttons:
                    b.setEnabled(False)
                color = "green" if is_correct_map[selected_img] else "red"
                btn.setStyleSheet(f"border: 4px solid {color}; margin: 5px;")
                self.index += 1
                QTimer.singleShot(500, self.show_next_triplet)
            return handler

        buttons = []
        top_label = QLabel()
        top_label.setPixmap(QPixmap(test_path).scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio))
        self.image_layout.addWidget(top_label, alignment=Qt.AlignmentFlag.AlignCenter)

        option_layout = QHBoxLayout()
        handlers = []
        for path in options:
            btn = QPushButton()
            btn.setIcon(QIcon(path))
            btn.setIconSize(top_label.pixmap().size())
            btn.setFixedSize(220, 220)
            handler = make_handler(path, btn)
            btn.clicked.connect(handler)
            option_layout.addWidget(btn)
            buttons.append(btn)
            handlers.append(handler)

        self.image_layout.addLayout(option_layout)
        self.patient_window.show_triplet(test_path, options, handlers)

        if self.mode == "Temps imparti":
            self.timer.start(self.timer_duration * 1000)

    def save_results(self):
        self.timer.stop()
        df = pd.DataFrame(self.session_results)
        if df.empty:
            QMessageBox.information(self, "Fin", "Aucun résultat à enregistrer.")
            return

        now = datetime.datetime.now().strftime("%Y_%m_%d_%H%M")
        name = self.patient_selector.currentText().replace(" ", "_")
        filename = f"{name}_{now}_{self.contact}-{self.intensite}-{self.duree}_{self.test_name}.xlsx"
        df.to_excel(filename, index=False)
        QMessageBox.information(self, "Fin", f"Test terminé. Résultats enregistrés dans :\n{filename}")
        if self.patient_window:
            self.patient_window.close()
        if self.waiting_screen:
            self.waiting_screen.close()
        self.session_active = False

if __name__ == "__main__":
    test_triplets =     [
        ("./image_test_appariement/Image1.jpg", "./image_test_appariement/Image2.jpg", "./image_test_appariement/Image3.jpg"),
        ("./image_test_appariement/Image4.jpg", "./image_test_appariement/Image5.jpg", "./image_test_appariement/Image6.jpg"),
        ("./image_test_appariement/Image7.jpg", "./image_test_appariement/Image8.jpg", "./image_test_appariement/Image9.jpg"),
        ("./image_test_appariement/Image10.jpg", "./image_test_appariement/Image11.jpg", "./image_test_appariement/Image12.jpg"),
        ("./image_test_appariement/Image13.jpg", "./image_test_appariement/Image14.jpg", "./image_test_appariement/Image15.jpg"),
        ("./image_test_appariement/Image16.jpg", "./image_test_appariement/Image17.jpg", "./image_test_appariement/Image18.jpg"),
        ("./image_test_appariement/Image19.jpg", "./image_test_appariement/Image20.jpg", "./image_test_appariement/Image21.jpg"),
        ("./image_test_appariement/Image22.jpg", "./image_test_appariement/Image23.jpg", "./image_test_appariement/Image24.jpg"),
        ("./image_test_appariement/Image25.jpg", "./image_test_appariement/Image26.jpg", "./image_test_appariement/Image27.jpg"),
        ("./image_test_appariement/Image28.jpg", "./image_test_appariement/Image29.jpg", "./image_test_appariement/Image30.jpg"),
        ("./image_test_appariement/Image31.jpg", "./image_test_appariement/Image32.jpg", "./image_test_appariement/Image33.jpg"),
        ("./image_test_appariement/Image34.jpg", "./image_test_appariement/Image35.jpg", "./image_test_appariement/Image36.jpg"),
        ("./image_test_appariement/Image37.jpg", "./image_test_appariement/Image38.jpg", "./image_test_appariement/Image39.jpg"),
        ("./image_test_appariement/Image40.jpg", "./image_test_appariement/Image41.jpg", "./image_test_appariement/Image42.jpg"),
        ("./image_test_appariement/Image43.jpg", "./image_test_appariement/Image44.jpg", "./image_test_appariement/Image45.jpg"),
        ("./image_test_appariement/Image46.jpg", "./image_test_appariement/Image47.jpg", "./image_test_appariement/Image48.jpg"),
        ("./image_test_appariement/Image49.jpg", "./image_test_appariement/Image50.jpg", "./image_test_appariement/Image51.jpg"),
        ("./image_test_appariement/Image52.jpg", "./image_test_appariement/Image53.jpg", "./image_test_appariement/Image54.jpg"),
        ("./image_test_appariement/Image55.jpg", "./image_test_appariement/Image56.jpg", "./image_test_appariement/Image57.jpg"),
        ("./image_test_appariement/Image58.jpg", "./image_test_appariement/Image59.jpg", "./image_test_appariement/Image60.jpg"),
        ("./image_test_appariement/Image61.jpg", "./image_test_appariement/Image62.jpg", "./image_test_appariement/Image63.jpg"),
        ("./image_test_appariement/Image64.jpg", "./image_test_appariement/Image65.jpg", "./image_test_appariement/Image66.jpg"),
        ("./image_test_appariement/Image67.jpg", "./image_test_appariement/Image68.jpg", "./image_test_appariement/Image69.jpg"),
        ("./image_test_appariement/Image70.jpg", "./image_test_appariement/Image71.jpg", "./image_test_appariement/Image72.jpg"),
        ("./image_test_appariement/Image73.jpg", "./image_test_appariement/Image74.jpg", "./image_test_appariement/Image75.jpg"),
        ("./image_test_appariement/Image76.jpg", "./image_test_appariement/Image77.jpg", "./image_test_appariement/Image78.jpg"),
        ("./image_test_appariement/Image79.jpg", "./image_test_appariement/Image80.jpg", "./image_test_appariement/Image81.jpg"),
        ("./image_test_appariement/Image82.jpg", "./image_test_appariement/Image83.jpg", "./image_test_appariement/Image84.jpg"),
        ("./image_test_appariement/Image85.jpg", "./image_test_appariement/Image86.jpg", "./image_test_appariement/Image87.jpg"),
        ("./image_test_appariement/Image88.jpg", "./image_test_appariement/Image89.jpg", "./image_test_appariement/Image90.jpg"),
    ]
    app = QApplication(sys.argv)
    window = ImageSemanticMatchingTest(test_triplets)
    window.show()
    sys.exit(app.exec())
