import json
import os
import sys
import time
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QHBoxLayout
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QTimer, Qt

SHARED_COMMAND_FILE = "commande.json"
RESPONSE_FILE = "reponse_patient.json"
IMAGE_FOLDER = "image_famous_faceV1"

class PatientWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Interface Patient")
        self.setGeometry(100, 100, 800, 600)
        self.image_layout = QHBoxLayout()
        self.setLayout(self.image_layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.verifier_nouvelle_commande)
        self.timer.start(1000)  # Vérifie toutes les secondes

        self.current_triplet = []
        self.start_time = None

    def verifier_nouvelle_commande(self):
        print("[DEBUG] Vérification du fichier commande.json...")

        if not os.path.exists(SHARED_COMMAND_FILE):
            print("[DEBUG] Aucun fichier de commande trouvé.")
            return

        try:
            with open(SHARED_COMMAND_FILE, "r") as f:
                data = json.load(f)
                print("[DEBUG] Commande chargée :", data)
        except json.JSONDecodeError as e:
            print("[ERREUR] Fichier commande illisible :", e)
            return
        except Exception as e:
            print("[ERREUR] Problème à l'ouverture du fichier commande.json :", e)
            return

        self.afficher_images(data)

        try:
            os.remove(SHARED_COMMAND_FILE)
            print("[DEBUG] commande.json supprimé après lecture.")
        except Exception as e:
            print("[ERREUR] Impossible de supprimer commande.json :", e)

    def afficher_images(self, data):
        for i in reversed(range(self.image_layout.count())):
            widget = self.image_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        self.current_triplet = data.get("triplet", [])
        self.start_time = time.time()
        self.nom = data.get("nom", "")
        self.prenom = data.get("prenom", "")

        if not self.current_triplet:
            print("[ERREUR] Triplet vide ou manquant dans les données de commande.")
            return

        print(f"[DEBUG] Affichage de {len(self.current_triplet)} images pour {self.prenom} {self.nom}.")

        for img_name in self.current_triplet:
            img_path = os.path.join(IMAGE_FOLDER, img_name)
            if not os.path.exists(img_path):
                print(f"[ERREUR] Image non trouvée : {img_path}")
                continue

            label = QLabel()
            pixmap = QPixmap(img_path).scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio)
            label.setPixmap(pixmap)
            label.mousePressEvent = self.make_click_handler(img_name)
            self.image_layout.addWidget(label)

    def make_click_handler(self, img_name):
        def handler(event):
            reaction_time = round(time.time() - self.start_time, 3)
            reponse = {
                "prenom": self.prenom,
                "nom": self.nom,
                "image_choisie": img_name,
                "temps_reponse": reaction_time,
                "horodatage": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            try:
                with open(RESPONSE_FILE, "a") as f:
                    f.write(json.dumps(reponse) + "\n")
                print("[DEBUG] Réponse enregistrée :", reponse)
            except Exception as e:
                print("[ERREUR] Impossible d'enregistrer la réponse :", e)

            # Nettoyer l'écran après réponse
            for i in reversed(range(self.image_layout.count())):
                widget = self.image_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)

        return handler

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PatientWindow()
    window.showFullScreen()
    sys.exit(app.exec())
