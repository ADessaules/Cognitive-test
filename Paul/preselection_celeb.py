from PyQt6.QtWidgets import QWidget, QPushButton, QLabel, QVBoxLayout, QDialog, QMessageBox, QGridLayout
from PyQt6.QtGui import QPixmap, QPainter
import sqlite3
import os
import glob
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QScrollArea
from constant import DOSSIER_IMAGES, DB_FILE

class SelectionCelebrites(QDialog):
    def __init__(self, patient_id):
        super().__init__()
        self.setWindowTitle("Sélection des célébrités")
        self.setGeometry(100, 100, 800, 600)
        self.patient_id = patient_id
        self.selections = {}

        # Chargement des célébrités
        self.celebrites = [{"nom": os.path.splitext(os.path.basename(f))[0].replace("_", " "), "image": f}
                           for f in glob.glob(os.path.join(DOSSIER_IMAGES, "*.webp"))]

        self.layout = QVBoxLayout()

        scroll = QScrollArea()
        scroll_widget = QWidget()
        self.grid_layout = QGridLayout()
        scroll_widget.setLayout(self.grid_layout)
        scroll.setWidgetResizable(True)
        scroll.setWidget(scroll_widget)

        self.layout.addWidget(scroll)

        self.btn_valider = QPushButton("Valider la sélection")
        self.btn_valider.setStyleSheet("font-size: 18px; padding: 10px;")
        self.btn_valider.clicked.connect(self.valider_selection)
        self.layout.addWidget(self.btn_valider)

        self.btn_stop = QPushButton("Stopper le test")
        self.btn_stop.setStyleSheet("font-size: 18px; padding: 10px; background-color: red; color: white;")
        self.btn_stop.clicked.connect(self.stop_test)
        self.layout.addWidget(self.btn_stop)


        self.setLayout(self.layout)

        self.afficher_celebrite_grid()

    def afficher_celebrite_grid(self):
        row = col = 0
        for celebrité in self.celebrites:
            nom = celebrité["nom"]
            image_path = celebrité["image"]

            img_label = QLabel()
            img_label.setFixedSize(150, 150)
            img_label.setScaledContents(True)

            if os.path.exists(image_path):
                pixmap = QPixmap(image_path).scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio)
                img_label.setPixmap(pixmap)

            img_label.mousePressEvent = self.generer_toggle_handler(img_label, nom, image_path)
            self.grid_layout.addWidget(img_label, row, col)
            self.selections[img_label] = {"selected": True, "nom": nom, "image": image_path, "pixmap": pixmap}

            col += 1
            if col >= 4:
                col = 0
                row += 1

    def generer_toggle_handler(self, label, nom, image_path):
        def handler(event):
            current = self.selections[label]
            current["selected"] = not current["selected"]
            opacity = 0.3 if not current["selected"] else 1.0
            pixmap = QPixmap(current["image"]).scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio)
            transparent = QPixmap(pixmap.size())
            transparent.fill(Qt.GlobalColor.transparent)

            painter = QPainter(transparent)
            painter.setOpacity(opacity)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()

            label.setPixmap(transparent)
        return handler

    def valider_selection(self):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
    
        # Supprimer les anciennes sélections du patient
        cursor.execute("DELETE FROM selections WHERE patient_id = ?", (self.patient_id,))
    
        # Insérer les nouvelles sélections
        for info in self.selections.values():
            if info["selected"]:
                cursor.execute(
                    "INSERT INTO selections (patient_id, nom, image) VALUES (?, ?, ?)",
                    (self.patient_id, info["nom"], info["image"])
                )
    
        conn.commit()
        conn.close()
        QMessageBox.information(self, "Enregistré", "Sélection mise à jour avec succès.")
        self.close()

    def stop_test(self):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
    
        # Supprimer les anciennes sélections du patient
        cursor.execute("DELETE FROM selections WHERE patient_id = ?", (self.patient_id,))
    
        # Insérer les nouvelles sélections
        for info in self.selections.values():
            if info["selected"]:
                cursor.execute(
                    "INSERT INTO selections (patient_id, nom, image) VALUES (?, ?, ?)",
                    (self.patient_id, info["nom"], info["image"])
                )
    
        conn.commit()
        conn.close()

        QMessageBox.information(self, "Test interrompu", "Test arrêté. Sélections sauvegardées.")
        self.close()
