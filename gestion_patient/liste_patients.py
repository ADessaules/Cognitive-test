from PyQt6.QtWidgets import QVBoxLayout, QDialog, QMessageBox, QListWidget
import sqlite3
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from constant import DB_FILE, DOSSIER_PATIENTS
from gestion_patient.detail_patient import PatientDetailsWindow
import shutil

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
        
    def afficher_details_patient(self, item):
        patient_name = item.text()
        patient_id = None
        for p_id, p_name in self.patients:
            if p_name == patient_name:
                patient_id = p_id
                break
    
        if patient_id is not None:
            self.details_fenetre = PatientDetailsWindow(patient_id, patient_name)
            self.details_fenetre.exec()
            
    def supprimer_patient(self, item):
        index = self.liste_widget.row(item)
        patient_id, patient_nom = self.patients[index]

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM selections WHERE patient_id = ?", (patient_id,))
        cursor.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
        conn.commit()
        conn.close()

        dossier_patient = os.path.join(DOSSIER_PATIENTS, patient_nom)
        if os.path.exists(dossier_patient):
            shutil.rmtree(dossier_patient)
            print(f"Dossier {dossier_patient} supprimé avec succès.")
        else:
            print(f"Dossier {dossier_patient} introuvable.")

        QMessageBox.information(self, "Supprimé", "Le patient a été supprimé avec succès.")
        self.liste_widget.takeItem(index)
