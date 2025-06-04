from PyQt6.QtWidgets import QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QDialog, QGridLayout, QScrollArea, QWidget
from PyQt6.QtGui import QPixmap
import sqlite3
import os
from constant import DB_FILE
from preselection_celeb import SelectionCelebrites
from bisection_test import BisectionTest

class DetailsPatient(QDialog):
    def __init__(self, patient_id):
        super().__init__()
        self.setWindowTitle("Détails du Patient")
        self.setGeometry(250, 250, 500, 500)
        self.patient_id = patient_id
        
        self.layout = QVBoxLayout()
        self.btn_layout = QHBoxLayout()

        self.btn_selections = QPushButton("Sélections")
        self.btn_bisection = QPushButton("Bisection")

        self.btn_selections.clicked.connect(self.afficher_selections)
        self.btn_bisection.clicked.connect(self.afficher_bisection)

        self.btn_layout.addWidget(self.btn_selections)
        self.btn_layout.addWidget(self.btn_bisection)

        self.layout.addLayout(self.btn_layout)
        self.contenu = QVBoxLayout()
        self.layout.addLayout(self.contenu)

        self.setLayout(self.layout)
        self.afficher_selections()

    def clear_contenu(self):
        def clear_layout(layout):
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    clear_layout(item.layout())

        clear_layout(self.contenu)

    def afficher_selections(self):
        self.clear_contenu()
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT nom, image FROM selections WHERE patient_id = ?", (self.patient_id,))
        celebrites = cursor.fetchall()
        conn.close()

        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        grid = QGridLayout(scroll_content)

        row, col = 0, 0
        for nom, image_path in celebrites:
            label = QLabel(nom)
            img_label = QLabel()
            if os.path.exists(image_path):
                pixmap = QPixmap(image_path).scaled(150, 150)
                img_label.setPixmap(pixmap)
            grid.addWidget(img_label, row, col)
            grid.addWidget(label, row + 1, col)
            col += 1
            if col >= 3:
                col = 0
                row += 2

        scroll.setWidget(scroll_content)
        self.contenu.addWidget(scroll)

        btn_revoir_selection = QPushButton("Modifier la Sélection")
        btn_revoir_selection.setStyleSheet("font-size: 16px; padding: 5px; background-color: orange; color: white;")
        btn_revoir_selection.clicked.connect(self.revoir_selection)
        self.contenu.addWidget(btn_revoir_selection)

    def revoir_selection(self):
        self.selection_fenetre = SelectionCelebrites(self.patient_id)
        self.selection_fenetre.show()

    def afficher_bisection(self):
        self.clear_contenu()

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT x1, y1, x2, y2, clic_x, clic_y
            FROM bisection
            WHERE patient_id = ?
        """, (self.patient_id,))
        resultats = cursor.fetchall()
        conn.close()

        if not resultats:
            self.contenu.addWidget(QLabel("Aucun test de bisection enregistré pour ce patient."))
            return

        resultats_text = ""
        dpi = self.logicalDpiX()
        pixels_per_cm = dpi / 2.54

        for i, (x1, y1, x2, y2, clic_x, clic_y) in enumerate(resultats, 1):
            mx = (x1 + x2) / 2
            if clic_x is None:
                resultats_text += f"Essai {i} : non fait (skippé)\n"
            else:
                delta_cm = (clic_x - mx) / pixels_per_cm
                resultats_text += f"Essai {i} : Erreur = {delta_cm:+.2f} cm\n"

        label = QLabel(resultats_text)
        label.setStyleSheet("font-size: 16px;")
        self.contenu.addWidget(label)

        btn_rejouer = QPushButton("Revoir ou Continuer le Test")
        btn_rejouer.setStyleSheet("font-size: 16px; padding: 5px; background-color: #007BFF; color: white;")
        btn_rejouer.clicked.connect(self.relancer_bisection)
        self.contenu.addWidget(btn_rejouer)

    def relancer_bisection(self):
        self.bisection_fenetre = BisectionTest(self.patient_id)
        self.bisection_fenetre.show()
