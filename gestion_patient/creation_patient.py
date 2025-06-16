import os
import sqlite3
import re
from PyQt6.QtWidgets import QInputDialog, QMessageBox
from constant import DB_FILE, DOSSIER_PATIENTS

# Fonction pour créer un nouveau patient
def creer_patient(parent_widget):
    # Affiche une boîte de dialogue demandant le nom du patient
    nom, ok = QInputDialog.getText(parent_widget, "Nouveau Patient", "Entrez le nom du patient :")

    # Vérifie si l'utilisateur a cliqué sur OK et que le nom n'est pas vide
    if ok and nom:
        # Nettoyage du nom : suppression des caractères interdits pour un nom de dossier
        nom_dossier = re.sub(r'[\\/*?:"<>|]', "_", nom).strip()

        # Vérifie que le nom nettoyé n'est pas vide
        if not nom_dossier:
            QMessageBox.warning(parent_widget, "Erreur", "Nom de patient invalide.")
            return

        try:
            # Connexion à la base de données SQLite
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()

            # Insertion du nom du patient dans la table "patients"
            cursor.execute("INSERT INTO patients (nom) VALUES (?)", (nom,))
            conn.commit()
            conn.close()
        except Exception as e:
            # Affiche une erreur si l'insertion échoue
            QMessageBox.critical(parent_widget, "Erreur BDD", f"Erreur d'insertion : {e}")
            return

        # Création du dossier du patient
        dossier_patient = os.path.join(DOSSIER_PATIENTS, nom_dossier)
        try:
            # Crée le dossier si celui-ci n'existe pas déjà
            os.makedirs(dossier_patient, exist_ok=True)
        except Exception as e:
            # Affiche une erreur si la création du dossier échoue
            QMessageBox.critical(parent_widget, "Erreur Dossier", f"Erreur lors de la création du dossier : {e}")
            return

        # Affiche un message de succès si tout s'est bien passé
        QMessageBox.information(parent_widget, "Succès", f"Le patient « {nom} » a été créé.")
