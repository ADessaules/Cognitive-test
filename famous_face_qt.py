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
from PyQt6.QtCore import QTimer
import pandas as pd

class FamousFaceTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Famous Face Test")
        self.setGeometry(100, 100, 800, 600)

        self.image_folder = "image_famous_faceV1"
        self.test_name = "famous_face"
        self.results_file = "resultats_test.xlsx"

        # Construction des triplets par groupe de X (0, 1, 2)
        all_images = [img for img in os.listdir(self.image_folder) if img.lower().endswith((".png", ".jpg", ".jpeg"))]
        triplet_dict = {}
        for img in all_images:
            try:
                prefix = img.split("_")[1]  # ex: "4" dans "image_4_0"
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

        self.current_triplets = self.all_triplets[:]
        self.current_index = 0
        self.click_times = []
        self.error_indices = []
        self.start_time = None
        self.session_active = False
        self.participant_name = ""

        self.mode = "click"
        self.timer_duration = 3

        self.timer = QTimer()
        self.timer.timeout.connect(self.handle_timeout)

        self.init_ui()

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()

        self.prenom_input = QLineEdit()
        self.prenom_input.setPlaceholderText("Prénom")
        self.nom_input = QLineEdit()
        self.nom_input.setPlaceholderText("Nom")

        self.mode_label = QLabel("Mode d'affichage des images :")
        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["Image au clic", "Temps imparti"])
        self.mode_selector.currentTextChanged.connect(self.toggle_timer_input)

        self.timer_input = QLineEdit()
        self.timer_input.setPlaceholderText("Temps (en secondes)")
        self.timer_input.setVisible(False)

        self.validate_btn = QPushButton("Valider")
        self.validate_btn.clicked.connect(self.start_configuration)

        self.layout.addWidget(self.prenom_input)
        self.layout.addWidget(self.nom_input)
        self.layout.addWidget(self.mode_label)
        self.layout.addWidget(self.mode_selector)
        self.layout.addWidget(self.timer_input)
        self.layout.addWidget(self.validate_btn)

        self.image_layout = QHBoxLayout()
        self.layout.addLayout(self.image_layout)

        self.info_label = QLabel("")
        self.layout.addWidget(self.info_label)

        self.feedback_label = QLabel("")
        self.layout.addWidget(self.feedback_label)

        self.central_widget.setLayout(self.layout)

    def toggle_timer_input(self):
        self.timer_input.setVisible(self.mode_selector.currentText() == "Temps imparti")

    def start_configuration(self):
        prenom = self.prenom_input.text().strip()
        nom = self.nom_input.text().strip()
        if not prenom or not nom:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer un nom et prénom.")
            return

        self.participant_name = f"{prenom} {nom}"
        self.mode = "timer" if self.mode_selector.currentText() == "Temps imparti" else "click"
        try:
            self.timer_duration = int(self.timer_input.text()) if self.mode == "timer" else 0
        except ValueError:
            self.timer_duration = 3

        self.session_active = True
        self.current_index = 0
        self.click_times = []
        self.error_indices = []
        self.show_triplet()

    def show_triplet(self):
        for i in reversed(range(self.image_layout.count())):
            widget = self.image_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        self.feedback_label.clear()

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
        flags = [img == famous_img for img in shuffled]

        self.start_time = time.time()
        for img_name, is_famous in zip(shuffled, flags):
            img_path = os.path.join(self.image_folder, img_name)
            pixmap = QPixmap(img_path).scaled(200, 200)
            label = QLabel()
            label.setPixmap(pixmap)

            btn = QPushButton("Choisir")
            btn.clicked.connect(self.make_click_handler(is_famous))

            box = QVBoxLayout()
            box_widget = QWidget()
            box.addWidget(label)
            box.addWidget(btn)
            box_widget.setLayout(box)
            self.image_layout.addWidget(box_widget)

        if self.mode == "timer":
            self.timer.start(self.timer_duration * 1000)

    def make_click_handler(self, is_famous):
        def handler():
            self.handle_click(is_famous)
        return handler

    def handle_click(self, is_famous):
        if not self.session_active:
            return
        if self.timer.isActive():
            self.timer.stop()

        reaction_time = round(time.time() - self.start_time, 3)
        self.click_times.append(reaction_time)

        if is_famous:
            self.feedback_label.setText("<span style='color: green; font-size: 24px;'>✔️</span>")
        else:
            self.feedback_label.setText("<span style='color: red; font-size: 24px;'>❌</span>")
            self.error_indices.append(self.current_index)

        self.current_index += 1
        QTimer.singleShot(500, self.show_triplet)

    def handle_timeout(self):
        self.timer.stop()
        self.click_times.append(self.timer_duration)
        self.error_indices.append(self.current_index)
        self.current_index += 1
        self.show_triplet()

    def end_session(self):
        self.session_active = False
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
