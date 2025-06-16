# patient_details.py

import os
import sys
import subprocess
from PyQt6.QtWidgets import QDialog, QListWidget, QVBoxLayout, QListWidgetItem, QMessageBox
from PyQt6.QtCore import Qt
from constant import DOSSIER_PATIENTS

# Fenêtre principale pour afficher la liste des patients et leurs tests
class PatientDetailsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Détail des patients")              # Titre de la fenêtre
        self.setGeometry(150, 150, 500, 400)                    # Dimensions de la fenêtre

        layout = QVBoxLayout()                                  # Layout vertical principal
        self.list_widget = QListWidget()                        # Liste qui contiendra les patients
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

        self.list_widget.itemClicked.connect(self.afficher_tests_patient)  # Action sur clic

        self.load_patient_data()                                # Chargement initial des patients

    # Fonction de chargement des données patients depuis le dossier
    def load_patient_data(self):
        # Vérifie si le dossier des patients existe
        if not os.path.exists(DOSSIER_PATIENTS):
            QMessageBox.warning(self, "Erreur", "Dossier patients introuvable.")
            return

        # Parcours des sous-dossiers, un par patient
        for nom_patient in os.listdir(DOSSIER_PATIENTS):
            chemin_dossier = os.path.join(DOSSIER_PATIENTS, nom_patient)
            if os.path.isdir(chemin_dossier):
                detail = f"🧑 {nom_patient}"     # Affiche le nom du patient
                tests_trouves = False

                # Recherche des fichiers de test (.xlsx ou .csv)
                for fichier in os.listdir(chemin_dossier):
                    if fichier.endswith(".xlsx") or fichier.endswith(".csv"):
                        nom_test = os.path.splitext(fichier)[0]  # Nom sans extension
                        detail += f"\n   📋 {nom_test}"           # Ajoute dans la vue
                        tests_trouves = True

                # Si aucun test trouvé
                if not tests_trouves:
                    detail += "\n   ❌ Aucun test trouvé"

                # Ajoute l'entrée à la liste avec le chemin associé
                item = QListWidgetItem(detail)
                item.setData(Qt.ItemDataRole.UserRole, chemin_dossier)
                self.list_widget.addItem(item)

    # Fonction appelée lors du clic sur un patient
    def afficher_tests_patient(self, item):
        chemin_dossier = item.data(Qt.ItemDataRole.UserRole)
        nom_patient = os.path.basename(chemin_dossier)
        if os.path.exists(chemin_dossier):
            # Ouvre une nouvelle fenêtre pour afficher les tests du patient
            self.test_window = PatientTestEditorDialog(nom_patient, chemin_dossier, self)
            self.test_window.exec()


# Fenêtre pour afficher les tests d’un patient donné
class PatientTestEditorDialog(QDialog):
    def __init__(self, patient_name, dossier_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Tests de {patient_name}")     # Titre dynamique avec le nom du patient
        self.setGeometry(200, 200, 500, 300)

        layout = QVBoxLayout()
        self.list_widget = QListWidget()                    # Liste des fichiers de test
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

        self.dossier_path = dossier_path                    # Chemin du répertoire patient
        self.patient_name = patient_name                    # Nom du patient

        self.list_widget.itemDoubleClicked.connect(self.ouvrir_test)  # Action double clic

        self.load_tests()                                   # Chargement initial des tests

    # Recherche et ajoute à la liste les fichiers de test disponibles
    def load_tests(self):
        for fichier in os.listdir(self.dossier_path):
            if fichier.endswith(".csv") or fichier.endswith(".xlsx"):
                item = QListWidgetItem(fichier)
                chemin_fichier = os.path.join(self.dossier_path, fichier)
                item.setData(Qt.ItemDataRole.UserRole, chemin_fichier)
                self.list_widget.addItem(item)

    # Ouvre un fichier de test avec l’application par défaut selon l’OS
    def ouvrir_test(self, item):
        chemin = item.data(Qt.ItemDataRole.UserRole)
        if os.path.exists(chemin):
            try:
                if sys.platform == "win32":
                    os.startfile(chemin)                            # Windows
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", chemin])              # macOS
                else:
                    subprocess.Popen(["xdg-open", chemin])          # Linux
            except Exception as e:
                QMessageBox.warning(self, "Erreur", f"Impossible d’ouvrir le fichier : {e}")
        else:
            QMessageBox.warning(self, "Erreur", "Le fichier n'existe pas.")