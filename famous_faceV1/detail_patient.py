# patient_details.py

import os
import sys
import subprocess
from PyQt6.QtWidgets import QDialog, QListWidget, QVBoxLayout, QListWidgetItem, QMessageBox
from PyQt6.QtCore import Qt
from constant import DOSSIER_PATIENTS

class PatientDetailsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Détail des patients")
        self.setGeometry(150, 150, 500, 400)

        layout = QVBoxLayout()
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

        self.list_widget.itemClicked.connect(self.afficher_tests_patient)

        self.load_patient_data()

    def load_patient_data(self):
        if not os.path.exists(DOSSIER_PATIENTS):
            QMessageBox.warning(self, "Erreur", "Dossier patients introuvable.")
            return

        for nom_patient in os.listdir(DOSSIER_PATIENTS):
            chemin_dossier = os.path.join(DOSSIER_PATIENTS, nom_patient)
            if os.path.isdir(chemin_dossier):
                detail = f"🧑 {nom_patient}"
                tests_trouves = False

                for fichier in os.listdir(chemin_dossier):
                    if fichier.endswith(".xlsx") or fichier.endswith(".csv"):
                        nom_test = os.path.splitext(fichier)[0]
                        detail += f"\n   📋 {nom_test}"
                        tests_trouves = True

                if not tests_trouves:
                    detail += "\n   ❌ Aucun test trouvé"

                item = QListWidgetItem(detail)
                item.setData(Qt.ItemDataRole.UserRole, chemin_dossier)
                self.list_widget.addItem(item)

    def afficher_tests_patient(self, item):
        chemin_dossier = item.data(Qt.ItemDataRole.UserRole)
        nom_patient = os.path.basename(chemin_dossier)
        if os.path.exists(chemin_dossier):
            self.test_window = PatientTestEditorDialog(nom_patient, chemin_dossier, self)
            self.test_window.exec()

class PatientTestEditorDialog(QDialog):
    def __init__(self, patient_name, dossier_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Tests de {patient_name}")
        self.setGeometry(200, 200, 500, 300)

        layout = QVBoxLayout()
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

        self.dossier_path = dossier_path
        self.patient_name = patient_name

        self.list_widget.itemDoubleClicked.connect(self.ouvrir_test)

        self.load_tests()

    def load_tests(self):
        for fichier in os.listdir(self.dossier_path):
            if fichier.endswith(".csv") or fichier.endswith(".xlsx"):
                item = QListWidgetItem(fichier)
                chemin_fichier = os.path.join(self.dossier_path, fichier)
                item.setData(Qt.ItemDataRole.UserRole, chemin_fichier)
                self.list_widget.addItem(item)

    def ouvrir_test(self, item):
        chemin = item.data(Qt.ItemDataRole.UserRole)
        if os.path.exists(chemin):
            try:
                if sys.platform == "win32":
                    os.startfile(chemin)
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", chemin])
                else:
                    subprocess.Popen(["xdg-open", chemin])
            except Exception as e:
                QMessageBox.warning(self, "Erreur", f"Impossible d’ouvrir le fichier : {e}")
        else:
            QMessageBox.warning(self, "Erreur", "Le fichier n'existe pas.")
