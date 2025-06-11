# famous_faceV1/creation_patient.py

import os
import sqlite3
import re
from PyQt6.QtWidgets import QInputDialog, QMessageBox
from constant import DB_FILE, DOSSIER_PATIENTS

def creer_patient(parent_widget):
    nom, ok = QInputDialog.getText(parent_widget, "Nouveau Patient", "Entrez le nom du patient :")
    if ok and nom:
        nom_dossier = re.sub(r'[\\/*?:"<>|]', "_", nom).strip()
        if not nom_dossier:
            QMessageBox.warning(parent_widget, "Erreur", "Nom de patient invalide.")
            return

        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO patients (nom) VALUES (?)", (nom,))
            conn.commit()
            conn.close()
        except Exception as e:
            QMessageBox.critical(parent_widget, "Erreur BDD", f"Erreur d'insertion : {e}")
            return

        dossier_patient = os.path.join(DOSSIER_PATIENTS, nom_dossier)
        try:
            os.makedirs(dossier_patient, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(parent_widget, "Erreur Dossier", f"Erreur lors de la création du dossier : {e}")
            return

        QMessageBox.information(parent_widget, "Succès", f"Le patient « {nom} » a été créé.")
