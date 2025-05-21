import json
import os
import time
import random
import sys
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QLineEdit, QMessageBox)
from PyQt6.QtCore import Qt

SHARED_COMMAND_FILE = "commande.json"
IMAGE_FOLDER = "image_famous_faceV1"

class ExperimentateurWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Interface Expérimentateur")
        self.setGeometry(100, 100, 400, 300)

        self.prenom_input = QLineEdit()
        self.prenom_input.setPlaceholderText("Prénom")
        self.nom_input = QLineEdit()
        self.nom_input.setPlaceholderText("Nom")
        self.start_button = QPushButton("Lancer un essai")
        self.start_button.clicked.connect(self.envoyer_essai)

        self.status_label = QLabel("Aucun essai en cours.")

        layout = QVBoxLayout()
        layout.addWidget(self.prenom_input)
        layout.addWidget(self.nom_input)
        layout.addWidget(self.start_button)
        layout.addWidget(self.status_label)
        self.setLayout(layout)

        self.triplets = self.charger_triplets()

    def charger_triplets(self):
        images = [img for img in os.listdir(IMAGE_FOLDER) if img.endswith(('jpg', 'jpeg', 'png'))]
        triplet_dict = {}
        for img in images:
            try:
                key = img.split("_")[1]
                triplet_dict.setdefault(key, []).append(img)
            except IndexError:
                continue
        triplets = [group for group in triplet_dict.values() if len(group) == 3]
        random.shuffle(triplets)
        return triplets

    def envoyer_essai(self):
        if not self.triplets:
            QMessageBox.warning(self, "Erreur", "Aucun triplet d'image disponible.")
            return

        prenom = self.prenom_input.text().strip()
        nom = self.nom_input.text().strip()
        if not prenom or not nom:
            QMessageBox.warning(self, "Erreur", "Remplissez le prénom et le nom.")
            return

        triplet = self.triplets.pop()
        ordre = {
            "prenom": prenom,
            "nom": nom,
            "start_time": time.time(),
            "triplet": triplet
        }

        with open(SHARED_COMMAND_FILE, "w") as f:
            json.dump(ordre, f)

        self.status_label.setText("Essai envoyé au patient.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ExperimentateurWindow()
    window.show()
    sys.exit(app.exec())

