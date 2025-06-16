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

        # Titre dynamique selon qu’on veut afficher ou supprimer un patient
        self.setWindowTitle("Liste des patients" if not supprimer else "Supprimer un Patient")
        self.setGeometry(200, 200, 400, 500)

        self.layout = QVBoxLayout()

        self.liste_widget = QListWidget()  # Liste des noms de patients

        # Connexion à la base de données pour récupérer les patients
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, nom FROM patients")  # Récupère l'ID et le nom de tous les patients
        self.patients = cursor.fetchall()               # Stocke les résultats dans une liste
        conn.close()

        # Ajoute chaque nom de patient à la liste visuelle
        for patient in self.patients:
            self.liste_widget.addItem(f"{patient[1]}")  # patient[1] = nom du patient

        self.layout.addWidget(self.liste_widget)
        self.setLayout(self.layout)

        # Connecte le clic à la bonne méthode selon si on est en mode suppression ou affichage
        self.liste_widget.itemClicked.connect(
            self.supprimer_patient if supprimer else self.afficher_details_patient
        )

    # --- Méthode pour afficher les détails d’un patient sélectionné ---
    def afficher_details_patient(self, item):
        patient_name = item.text()  # Récupère le nom du patient sélectionné
        patient_id = None

        # Recherche l'ID correspondant au nom du patient
        for p_id, p_name in self.patients:
            if p_name == patient_name:
                patient_id = p_id
                break

        if patient_id is not None:
            # Ouvre une fenêtre de détails (affiche les tests réalisés)
            self.details_fenetre = PatientDetailsWindow()
            self.details_fenetre.exec()

    # --- Méthode pour supprimer un patient ---
    def supprimer_patient(self, item):
        index = self.liste_widget.row(item)        # Index de l'élément sélectionné
        patient_id, patient_nom = self.patients[index]  # Récupère ID et nom du patient

        # Supprime le patient et ses sélections de la base de données
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM selections WHERE patient_id = ?", (patient_id,))
        cursor.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
        conn.commit()
        conn.close()

        # Supprime le dossier contenant les données du patient (fichiers de tests, etc.)
        dossier_patient = os.path.join(DOSSIER_PATIENTS, patient_nom)
        if os.path.exists(dossier_patient):
            shutil.rmtree(dossier_patient)  # Suppression récursive du dossier
            print(f"Dossier {dossier_patient} supprimé avec succès.")
        else:
            print(f"Dossier {dossier_patient} introuvable.")

        # Affiche un message de confirmation à l'utilisateur
        QMessageBox.information(self, "Supprimé", "Le patient a été supprimé avec succès.")

        # Retire le patient de l'affichage dans la liste
        self.liste_widget.takeItem(index)
