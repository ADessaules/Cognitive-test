import sys
import os
import sqlite3
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QDialog, QLabel, QVBoxLayout, QScrollArea,
    QWidget, QGridLayout, QPushButton, QMessageBox
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

from constant import DB_FILE, DOSSIER_PATIENTS

base_path = Path(__file__).resolve().parent / "image_test_appariement"
TRIPLETS = [
        (base_path/"Image1.jpg", base_path/"Image2.jpg", base_path/"Image3.jpg"),
        (base_path/"Image4.jpg", base_path/"Image5.jpg", base_path/"Image6.jpg"),
        (base_path/"Image7.jpg", base_path/"Image8.jpg", base_path/"Image9.jpg"),
        (base_path/"Image10.jpg", base_path/"Image11.jpg", base_path/"Image12.jpg"),
        (base_path/"Image13.jpg", base_path/"Image14.jpg", base_path/"Image15.jpg"),
        (base_path/"Image16.jpg", base_path/"Image17.jpg", base_path/"Image18.jpg"),
        (base_path/"Image19.jpg", base_path/"Image20.jpg", base_path/"Image21.jpg"),
        (base_path/"Image22.jpg", base_path/"Image23.jpg", base_path/"Image24.jpg"),
        (base_path/"Image25.jpg", base_path/"Image26.jpg", base_path/"Image27.jpg"),
        (base_path/"Image28.jpg", base_path/"Image29.jpg", base_path/"Image30.jpg"),
        (base_path/"Image31.jpg", base_path/"Image32.jpg", base_path/"Image33.jpg"),
        (base_path/"Image34.jpg", base_path/"Image35.jpg", base_path/"Image36.jpg"),
        (base_path/"Image37.jpg", base_path/"Image38.jpg", base_path/"Image39.jpg"),
        (base_path/"Image40.jpg", base_path/"Image41.jpg", base_path/"Image42.jpg"),
        (base_path/"Image43.jpg", base_path/"Image44.jpg", base_path/"Image45.jpg"),
        (base_path/"Image46.jpg", base_path/"Image47.jpg", base_path/"Image48.jpg"),
        (base_path/"Image49.jpg", base_path/"Image50.jpg", base_path/"Image51.jpg"),
        (base_path/"Image52.jpg", base_path/"Image53.jpg", base_path/"Image54.jpg"),
        (base_path/"Image55.jpg", base_path/"Image56.jpg", base_path/"Image57.jpg"),
        (base_path/"Image58.jpg", base_path/"Image59.jpg", base_path/"Image60.jpg"),
        (base_path/"Image61.jpg", base_path/"Image62.jpg", base_path/"Image63.jpg"),
        (base_path/"Image64.jpg", base_path/"Image65.jpg", base_path/"Image66.jpg"),
        (base_path/"Image67.jpg", base_path/"Image68.jpg", base_path/"Image69.jpg"),
        (base_path/"Image70.jpg", base_path/"Image71.jpg", base_path/"Image72.jpg"),
        (base_path/"Image73.jpg", base_path/"Image74.jpg", base_path/"Image75.jpg"),
        (base_path/"Image76.jpg", base_path/"Image77.jpg", base_path/"Image78.jpg"),
        (base_path/"Image79.jpg", base_path/"Image80.jpg", base_path/"Image81.jpg"),
        (base_path/"Image82.jpg", base_path/"Image83.jpg", base_path/"Image84.jpg"),
        (base_path/"Image85.jpg", base_path/"Image86.jpg", base_path/"Image87.jpg"),
        (base_path/"Image88.jpg", base_path/"Image89.jpg", base_path/"Image90.jpg"),
    ]

TRIPLETS =  [(str(a), str(b), str(c)) for (a, b, c) in TRIPLETS]

class SelectionImages(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sélection des images")
        self.setGeometry(100, 100, 900, 700)

        self.selections = {}
        self.layout = QVBoxLayout()

        scroll = QScrollArea()
        scroll_widget = QWidget()
        self.grid_layout = QGridLayout()
        scroll_widget.setLayout(self.grid_layout)
        scroll.setWidgetResizable(True)
        scroll.setWidget(scroll_widget)
        self.layout.addWidget(scroll)

        self.btn_valider = QPushButton("Valider la sélection")
        self.btn_valider.clicked.connect(self.valider_selection)
        self.layout.addWidget(self.btn_valider)

        self.setLayout(self.layout)
        self.afficher_images()

    # Affiche tout les images disponibles pour la préselection
    def afficher_images(self):
        images = sorted(set(img for triplet in TRIPLETS for img in triplet))
        row = col = 0
        for img_name in images:
            path = os.path.join(base_path, img_name)
            label = QLabel()
            pixmap = QPixmap(path).scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio)
            label.setPixmap(pixmap)
            label.setFixedSize(130, 130)
            label.setStyleSheet("border: 2px solid green;")
            label.mousePressEvent = self.generer_toggle_handler(label, img_name)
            self.grid_layout.addWidget(label, row, col)
            self.selections[label] = {"selected": True, "path": img_name}
            col += 1
            if col >= 5:
                col = 0
                row += 1

    # Définie l'affichage quand on sélectionne une image dans la présélection
    def generer_toggle_handler(self, label, img_name):
        def handler(event):
            current = self.selections[label]
            current["selected"] = not current["selected"]
            label.setStyleSheet("border: 2px solid green;" if current["selected"] else "border: 2px solid gray;")
        return handler
    
    # Enregistre la présélection dans un txt
    def enregistrer_selection_txt(self):
        selected_image = [info["image"] for info in self.selections.values() if info["selected"]]
        patient_folder = os.path.join("Patients", self.patient_name)
        os.makedirs(patient_folder, exist_ok=True)
        with open(os.path.join(patient_folder, "selection_image_semantique.txt"), "w", encoding="utf-8") as f:
            f.write(",".join(selected_image))

    # Enregistre la présélection dans la BDD
    def valider_selection(self):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM selection_image_semantique WHERE patient_id = ?", (self.patient_id,))
        for info in self.selections.values():
            if info["selected"]:
                cursor.execute(
                    "INSERT INTO selection_image_semantique (patient_id, mot) VALUES (?, ?)",
                    (self.patient_id, info["mot"])
                )
        conn.commit()
        conn.close()
        self.enregistrer_selection_txt()
        QMessageBox.information(self, "Enregistré", "Sélection mise à jour avec succès.")
        self.close()

    # Creer un table dans la BDD si elle n'est pas déjà présente 
    def creer_table_selection_image():
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS selection_image_semantique (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                mot TEXT NOT NULL
            )
        ''')

        conn.commit()
        conn.close()
        print("✅ Table 'selection_image_semantique' vérifiée/créée avec succès.")

    # Enregistre le txt avec les infos de présélection
    def valider_selection(self):
        selected = [info["path"] for info in self.selections.values() if info["selected"]]
        os.makedirs("Patients", exist_ok=True)
        with open("Patients/selection_images_semantique.txt", "w", encoding="utf-8") as f:
            f.write(",".join(selected))
        QMessageBox.information(self, "Enregistré", "Sélection sauvegardée.")
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SelectionImages()
    window.show()
    sys.exit(app.exec())