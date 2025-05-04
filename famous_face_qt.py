import sys
import os
import random
import uuid
import time
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QFileDialog, QLineEdit, QMessageBox
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QTimer
import pandas as pd

class FamousFaceTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Famous Face Test")
        self.setGeometry(100, 100, 800, 600)

        # === CONFIGURATION ===
        self.image_folder = "images_extraites_famous_faceV1"
        self.test_name = "famous_face"
        self.results_file = "resultats_test.xlsx"

        # === VARIABLES ===
        self.all_images = sorted([
            img for img in os.listdir(self.image_folder) if img.endswith(".png")
        ], key=lambda x: int(x.split("_")[1].split(".")[0]))

        self.all_triplets = [
            self.all_images[i:i + 3] for i in range(0, len(self.all_images), 3) if i + 2 < len(self.all_images)
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

        # Nom/prenom
        self.prenom_input = QLineEdit()
        self.prenom_input.setPlaceholderText("Prénom")
        self.nom_input = QLineEdit()
        self.nom_input.setPlaceholderText("Nom")
        self.validate_btn = QPushButton("Valider")
        self.validate_btn.clicked.connect(self.start_configuration)

        self.layout.addWidget(self.prenom_input)
        self.layout.addWidget(self.nom_input)
        self.layout.addWidget(self.validate_btn)

        self.image_layout = QHBoxLayout()
        self.layout.addLayout(self.image_layout)

        self.info_label = QLabel("")
        self.layout.addWidget(self.info_label)

        self.central_widget.setLayout(self.layout)

    def start_configuration(self):
        prenom = self.prenom_input.text().strip()
        nom = self.nom_input.text().strip()
        if not prenom or not nom:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer un nom et prénom.")
            return

        self.participant_name = f"{prenom} {nom}"
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

        if self.current_index >= len(self.current_triplets):
            self.end_session()
            return

        images = self.current_triplets[self.current_index]
        famous_img = images[0]
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
            btn.clicked.connect(lambda _, f=is_famous: self.handle_click(f))

            box = QVBoxLayout()
            box_widget = QWidget()
            box.addWidget(label)
            box.addWidget(btn)
            box_widget.setLayout(box)
            self.image_layout.addWidget(box_widget)

        if self.mode == "timer":
            self.timer.start(self.timer_duration * 1000)

    def handle_click(self, is_famous):
        if not self.session_active:
            return
        if self.timer.isActive():
            self.timer.stop()

        reaction_time = round(time.time() - self.start_time, 3)
        self.click_times.append(reaction_time)

        if not is_famous:
            self.error_indices.append(self.current_index)

        self.current_index += 1
        self.show_triplet()

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
