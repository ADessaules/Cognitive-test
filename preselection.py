from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QDialog, QInputDialog, QMessageBox, QListWidget, QGridLayout
from PyQt6.QtGui import QPixmap
import sqlite3
import os
import glob


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
        self.btn_liste_patients = QPushButton("Voir Patients")
        self.btn_supprimer_patient = QPushButton("Supprimer Patient")
        
        self.btn_creer_patient.clicked.connect(self.creer_patient)
        self.btn_liste_patients.clicked.connect(self.afficher_liste_patients)
        self.btn_supprimer_patient.clicked.connect(self.afficher_liste_patients_supprimer)
        
        self.layout.addWidget(self.btn_creer_patient)
        self.layout.addWidget(self.btn_liste_patients)
        self.layout.addWidget(self.btn_supprimer_patient)
        
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
            
            self.selection_fenetre = SelectionCelebrites(patient_id)
            self.selection_fenetre.show()

    def afficher_liste_patients(self):
        self.liste_patients_fenetre = ListePatients()
        self.liste_patients_fenetre.show()
    
    def afficher_liste_patients_supprimer(self):
        self.supprimer_patients_fenetre = ListePatients(supprimer=True)
        self.supprimer_patients_fenetre.show()

# --- Fenêtre de sélection des célébrités ---
class SelectionCelebrites(QDialog):
    def __init__(self, patient_id):
        super().__init__()
        self.setWindowTitle("Sélection des célébrités")
        self.setGeometry(200, 200, 500, 600)
        self.patient_id = patient_id
        
        self.layout = QVBoxLayout()
        self.nom_label = QLabel("")
        self.image_label = QLabel()
        self.btn_connu = QPushButton("Connu")
        self.btn_inconnu = QPushButton("Inconnu")
        
        self.btn_connu.clicked.connect(self.enregistrer_connu)
        self.btn_inconnu.clicked.connect(self.passer)
        
        self.layout.addWidget(self.image_label)
        self.layout.addWidget(self.nom_label)
        self.layout.addWidget(self.btn_connu)
        self.layout.addWidget(self.btn_inconnu)
        
        self.setLayout(self.layout)
        
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
        self.layout = QGridLayout()
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT nom, image FROM selections WHERE patient_id = ?", (patient_id,))
        celebrites = cursor.fetchall()
        conn.close()
        
        row, col = 0, 0
        for celeb in celebrites:
            nom, image_path = celeb
            label = QLabel(nom)
            img_label = QLabel()
            if os.path.exists(image_path):
                pixmap = QPixmap(image_path).scaled(150, 150)
                img_label.setPixmap(pixmap)
            self.layout.addWidget(img_label, row, col)
            self.layout.addWidget(label, row+1, col)
            col += 1
            if col >= 3:
                col = 0
                row += 2
        
        self.setLayout(self.layout)

# --- Exécution de l'application ---
if __name__ == "__main__":
    creer_base()
    app = QApplication([])
    main_window = MainApp()
    main_window.show()
    app.exec()
