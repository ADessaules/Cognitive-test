from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QDialog, QInputDialog, QMessageBox, QListWidget, QGridLayout
from PyQt6.QtGui import QPixmap, QPainter, QPen
import sqlite3
import os
import glob
from PyQt6.QtCore import Qt
import math
import random


# --- Configuration ---
DB_FILE = "patients.db"
DOSSIER_IMAGES = "C:\\Users\\Paul\\Downloads\\Pyth\\image"

# --- Création de la base de données ---
def creer_base():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS selections (
            patient_id INTEGER,
            nom TEXT,
            image TEXT,
            FOREIGN KEY(patient_id) REFERENCES patients(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bisection (
            patient_id INTEGER,
            x1 REAL, y1 REAL,
            x2 REAL, y2 REAL,
            clic_x REAL, clic_y REAL,
            FOREIGN KEY(patient_id) REFERENCES patients(id)
        )
    """)
    conn.commit()
    conn.close()

# --- Classe principale ---
class MainApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reconnaissance de célébrités")
        self.setGeometry(100, 100, 600, 700)
        
        self.layout = QVBoxLayout()
        self.btn_creer_patient = QPushButton("Créer Patient")
        self.btn_creer_patient.setFixedHeight(60)
        self.btn_creer_patient.setStyleSheet("font-size: 18px;")

        self.btn_liste_patients = QPushButton("Voir Patients")
        self.btn_liste_patients.setFixedHeight(60)
        self.btn_liste_patients.setStyleSheet("font-size: 18px;")

        self.btn_supprimer_patient = QPushButton("Supprimer Patient")
        self.btn_supprimer_patient.setFixedHeight(60)
        self.btn_supprimer_patient.setStyleSheet("font-size: 18px;")


        self.btn_selection_celeb = QPushButton("Sélectionner Célébrités pour un Patient")
        self.btn_selection_celeb.setFixedHeight(60)
        self.btn_selection_celeb.setStyleSheet("font-size: 18px;")
        
        self.btn_bisection = QPushButton("Bisection")
        self.btn_bisection.setFixedHeight(60)
        self.btn_bisection.setStyleSheet("font-size: 18px;")        


        self.btn_selection_celeb.clicked.connect(self.selectionner_patient_pour_celebrite) 
        self.btn_creer_patient.clicked.connect(self.creer_patient)
        self.btn_liste_patients.clicked.connect(self.afficher_liste_patients)
        self.btn_supprimer_patient.clicked.connect(self.afficher_liste_patients_supprimer)
        self.btn_bisection.clicked.connect(self.selectionner_patient_pour_bisection)        


        self.layout.addWidget(self.btn_creer_patient)
        self.layout.addWidget(self.btn_selection_celeb)
        self.layout.addWidget(self.btn_liste_patients)
        self.layout.addWidget(self.btn_supprimer_patient)
        self.layout.addWidget(self.btn_bisection)

        
        self.setLayout(self.layout)
    
    def creer_patient(self):
        nom, ok = QInputDialog.getText(self, "Nouveau Patient", "Entrez l'ID du patient :")
        if ok and nom:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO patients (nom) VALUES (?)", (nom,))
            conn.commit()
            patient_id = cursor.lastrowid
            conn.close()
            QMessageBox.information(self, "Patient créé", f"Le patient « {nom} » a bien été créé.")


    def afficher_liste_patients(self):
        self.liste_patients_fenetre = ListePatients()
        self.liste_patients_fenetre.show()
    
    def afficher_liste_patients_supprimer(self):
        self.supprimer_patients_fenetre = ListePatients(supprimer=True)
        self.supprimer_patients_fenetre.show()

    def selectionner_patient_pour_celebrite(self):
        self.selection_patient_fenetre = SelectionPatientDialog(self.lancer_selection_celebrite)
        self.selection_patient_fenetre.show()

    def selectionner_patient_pour_bisection(self):
        self.selection_patient_fenetre = SelectionPatientDialog(self.lancer_bisection)
        self.selection_patient_fenetre.show()

    def lancer_selection_celebrite(self, patient_id):
        # Vérifier si ce patient a déjà fait une sélection
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM selections WHERE patient_id = ?", (patient_id,))
        count = cursor.fetchone()[0]
        conn.close()

        if count > 0:
            QMessageBox.information(self, "Déjà sélectionné", "Ce patient a déjà effectué la préselection.")
        else:
            self.selection_fenetre = SelectionCelebrites(patient_id)
            self.selection_fenetre.show()

    def lancer_bisection(self, patient_id):
        self.bisection_fenetre = BisectionTest(patient_id)
        self.bisection_fenetre.show()


# --- Fenêtre de test Bisection ---
class BisectionTest(QWidget):
    def __init__(self, patient_id):
        super().__init__()
        self.setWindowTitle("Test de Bisection")
        self.setGeometry(300, 300, 600, 600)
        self.patient_id = patient_id
        self.attempt = 0
        self.total_attempts = 10
        self.setMouseTracking(True)
        self.generate_new_bar()

    def generate_new_bar(self):
        cx, cy = self.width() // 2, self.height() // 2
        length = 200
        angle = random.uniform(0, math.pi)
        dx = length / 2 * math.cos(angle)
        dy = length / 2 * math.sin(angle)
        self.x1, self.y1 = cx - dx + random.randint(-100, 100), cy - dy + random.randint(-100, 100)
        self.x2, self.y2 = cx + dx + random.randint(-100, 100), cy + dy + random.randint(-100, 100)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        pen = QPen(Qt.GlobalColor.black, 5)
        painter.setPen(pen)
        painter.drawLine(int(self.x1), int(self.y1), int(self.x2), int(self.y2))

    def mousePressEvent(self, event):
        if self.attempt >= self.total_attempts:
            return

        clic_x, clic_y = event.position().x(), event.position().y()

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO bisection (patient_id, x1, y1, x2, y2, clic_x, clic_y)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (self.patient_id, self.x1, self.y1, self.x2, self.y2, clic_x, clic_y))
        conn.commit()
        conn.close()

        self.attempt += 1
        if self.attempt < self.total_attempts:
            self.generate_new_bar()
        else:
            QMessageBox.information(self, "Terminé", "Test de bisection terminé.")
            self.close()

class SelectionPatientDialog(QDialog):
    def __init__(self, callback):
        super().__init__()
        self.setWindowTitle("Choisir un patient")
        self.setGeometry(200, 200, 400, 400)
        self.callback = callback
        
        self.layout = QVBoxLayout()
        self.liste_widget = QListWidget()
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, nom FROM patients")
        self.patients = cursor.fetchall()
        conn.close()
        
        for patient in self.patients:
            self.liste_widget.addItem(f"{patient[1]}")
        
        self.liste_widget.itemClicked.connect(self.patient_selectionne)
        self.layout.addWidget(self.liste_widget)
        self.setLayout(self.layout)

    def patient_selectionne(self, item):
        index = self.liste_widget.row(item)
        patient_id = self.patients[index][0]
        self.callback(patient_id)
        self.close()


# --- Fenêtre de sélection des célébrités ---
class SelectionCelebrites(QDialog):
    def __init__(self, patient_id):
        super().__init__()
        self.setWindowTitle("Sélection des célébrités")
        self.setGeometry(200, 200, 500, 600)
        self.patient_id = patient_id

        self.layout = QVBoxLayout()

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.image_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.nom_label = QLabel("")
        self.nom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.nom_label, alignment=Qt.AlignmentFlag.AlignCenter)

        btn_layout = QHBoxLayout()
        self.btn_connu = QPushButton("Connu")
        self.btn_inconnu = QPushButton("Inconnu")
        btn_layout.addWidget(self.btn_connu)
        btn_layout.addWidget(self.btn_inconnu)
        self.layout.addLayout(btn_layout)

        self.btn_connu.clicked.connect(self.enregistrer_connu)
        self.btn_inconnu.clicked.connect(self.passer)

        self.setLayout(self.layout)

        # Chargement des célébrités
        self.celebrites = [{"nom": os.path.splitext(os.path.basename(f))[0].replace("_", " "), "image": f}
                           for f in glob.glob(os.path.join(DOSSIER_IMAGES, "*.webp"))]

        self.afficher_celebrite()


    
    def afficher_celebrite(self):
        if not self.celebrites:
            QMessageBox.information(self, "Terminé", "Sélection terminée.")
            self.close()
            return
        
        self.current_celebrite = self.celebrites.pop(0)
        self.nom_label.setText(self.current_celebrite["nom"])
        
        image_path = self.current_celebrite["image"]
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path).scaled(200, 200)
            self.image_label.setPixmap(pixmap)
        else:
            self.passer()

    def enregistrer_connu(self):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO selections (patient_id, nom, image) VALUES (?, ?, ?)", 
                       (self.patient_id, self.current_celebrite["nom"], self.current_celebrite["image"]))
        conn.commit()
        conn.close()
        self.afficher_celebrite()
    
    def passer(self):
        self.afficher_celebrite()

# --- Fenêtre de liste des patients ---
class ListePatients(QDialog):
    def __init__(self, supprimer=False):
        super().__init__()
        self.setWindowTitle("Liste des patients" if not supprimer else "Supprimer un Patient")
        self.setGeometry(200, 200, 400, 500)
        self.layout = QVBoxLayout()
        
        self.liste_widget = QListWidget()
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, nom FROM patients")
        self.patients = cursor.fetchall()
        conn.close()
        
        for patient in self.patients:
            self.liste_widget.addItem(f"{patient[1]}")
        
        self.layout.addWidget(self.liste_widget)
        self.setLayout(self.layout)
        
        self.liste_widget.itemClicked.connect(self.supprimer_patient if supprimer else self.afficher_details_patient)
    
    def supprimer_patient(self, item):
        index = self.liste_widget.row(item)
        patient_id = self.patients[index][0]
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM selections WHERE patient_id = ?", (patient_id,))
        cursor.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
        conn.commit()
        conn.close()
        QMessageBox.information(self, "Supprimé", "Le patient a été supprimé avec succès.")
        self.liste_widget.takeItem(index)
    
    def afficher_details_patient(self, item):
        index = self.liste_widget.row(item)
        patient_id = self.patients[index][0]
        self.details_fenetre = DetailsPatient(patient_id)
        self.details_fenetre.show()

# --- Fenêtre des détails d'un patient ---
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
        self.afficher_selections()  # Affiche par défaut les sélections

    def clear_contenu(self):
        while self.contenu.count():
            item = self.contenu.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def afficher_selections(self):
        self.clear_contenu()
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT nom, image FROM selections WHERE patient_id = ?", (self.patient_id,))
        celebrites = cursor.fetchall()
        conn.close()

        grid = QGridLayout()
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
        self.contenu.addLayout(grid)

    def afficher_bisection(self):
        self.clear_contenu()
    
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT x1, y1, x2, y2, clic_x, clic_y
            FROM bisection
            WHERE patient_id = ?
        """, (self.patient_id,))
        essais = cursor.fetchall()
        conn.close()

        if not essais:
            self.contenu.addWidget(QLabel("Aucun test de bisection trouvé."))
            return

        total_distance = 0
        total_precision = 0
        essais_valides = 0
        max_distance = 100.0  # distance maximale pour calculer un pourcentage de précision

        resultats_layout = QVBoxLayout()

        for i, (x1, y1, x2, y2, clic_x, clic_y) in enumerate(essais, 1):
            if None in (x1, y1, x2, y2, clic_x, clic_y):
                print(f"⚠️ Donnée manquante à l'essai {i}, ignoré.")
                continue

            mx = (x1 + x2) / 2
            my = (y1 + y2) / 2
            distance = math.sqrt((clic_x - mx) ** 2 + (clic_y - my) ** 2)
            precision = max(0, 100 - (distance / max_distance) * 100)

            total_distance += distance
            total_precision += precision
            essais_valides += 1

            label = QLabel(f"Essai {i} : Distance = {distance:.2f} px | Précision = {precision:.1f} %")
            resultats_layout.addWidget(label)

        if essais_valides == 0:
            self.contenu.addWidget(QLabel("Aucune donnée exploitable pour les essais de bisection."))
            return

        moyenne_distance = total_distance / essais_valides
        moyenne_precision = total_precision / essais_valides

        resultats_layout.addSpacing(10)
        resultats_layout.addWidget(QLabel(f"📏 Distance moyenne : {moyenne_distance:.2f} px"))
        resultats_layout.addWidget(QLabel(f"🎯 Précision moyenne : {moyenne_precision:.1f} %"))

        self.contenu.addLayout(resultats_layout)


# --- Exécution de l'application ---
if __name__ == "__main__":
    creer_base()
    app = QApplication([])
    main_window = MainApp()
    main_window.show()
    app.exec()
