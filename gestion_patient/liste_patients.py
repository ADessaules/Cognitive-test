from PyQt6.QtWidgets import QVBoxLayout, QDialog, QMessageBox, QListWidget
import sqlite3
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from constant import DB_FILE, DOSSIER_PATIENTS
from gestion_patient.detail_patient import PatientDetailsWindow

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
        patient_name = self.patients[index][1]  # 👈 ajoute cette ligne
        self.details_fenetre = DetailsPatient(patient_id, patient_name)
        self.details_fenetre.show()
