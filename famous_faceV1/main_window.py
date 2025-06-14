from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QInputDialog, QMessageBox
from PyQt6.QtGui import QGuiApplication
import os
import sys
import sqlite3
import subprocess
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from constant import DB_FILE, DOSSIER_PATIENTS
from gestion_patient.liste_patients import ListePatients
from preselection_celeb import SelectionCelebrites
from dialogs import SelectionPatientDialog
from bisection_test.bisection_test import BisectionTest
from gestion_patient.creation_patient import creer_patient

class MainApp(QWidget):
    """
Fenêtre principale de lancement de l’application.

Permet de naviguer entre :
- l’interface principale (autre module),
- le test Famous Face,
- la présélection de célébrités pour un patient,
- la liste des patients existants.

C’est l’écran d’accueil central de l'application.
    """
    def __init__(self):
        """
    Initialise la fenêtre d’accueil avec tous les boutons de navigation.
    Configure les actions liées à chaque bouton pour ouvrir les modules correspondants.
        """
        super().__init__()
        self.setWindowTitle("Reconnaissance de célébrités")
        self.setGeometry(100, 100, 600, 700)
        
        self.layout = QVBoxLayout()

        self.btn_interface_principale = QPushButton("Aller à l'interface principale")
        self.btn_interface_principale.clicked.connect(self.go_to_main_interface)
        
        self.btn_test_famous_face = QPushButton("Aller au test Famous Face")
        self.btn_test_famous_face.clicked.connect(self.go_to_famous_face_test)

        self.btn_liste_patients = QPushButton("Voir Patients")
        self.btn_liste_patients.setFixedHeight(60)
        self.btn_liste_patients.setStyleSheet("font-size: 18px;")

        self.btn_selection_celeb = QPushButton("Sélectionner Célébrités pour un Patient")
        self.btn_selection_celeb.setFixedHeight(60)
        self.btn_selection_celeb.setStyleSheet("font-size: 18px;")

        self.btn_selection_celeb.clicked.connect(self.selectionner_patient_pour_celebrite) 
        self.btn_liste_patients.clicked.connect(self.afficher_liste_patients)

        self.layout.addWidget(self.btn_interface_principale)
        self.layout.addWidget(self.btn_test_famous_face)
        self.layout.addWidget(self.btn_selection_celeb)
        self.layout.addWidget(self.btn_liste_patients)
        self.setLayout(self.layout)

    def go_to_main_interface(self):
        """
    Ferme la fenêtre actuelle et lance l’interface principale via `interface.py`.
    Gérée comme un nouveau processus.
        """
        try:
            self.close()
            subprocess.Popen(["python", "interface.py"])
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'ouverture de l'interface principale : {e}")

    def go_to_famous_face_test(self):
        """
    Ferme la fenêtre actuelle et lance le script du test Famous Face.
    Appelle le fichier `famous_faceV1.py` comme un nouveau processus.
        """
        try:
            self.close()
            subprocess.Popen(["python", "famous_faceV1/famous_faceV1.py"])
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'ouverture du test Famous Face : {e}")

    def afficher_liste_patients(self):
        """
    Affiche la fenêtre contenant la liste des patients enregistrés.
    Utilise la classe `ListePatients` provenant du module `gestion_patient`.
        """
        self.liste_patients_fenetre = ListePatients()
        self.liste_patients_fenetre.show()
    
    def selectionner_patient_pour_celebrite(self):
        """
    Ouvre une boîte de dialogue permettant de sélectionner un patient.
    Une fois un patient choisi, on appelle `lancer_selection_celebrite`.
        """
        self.selection_patient_fenetre = SelectionPatientDialog(self.lancer_selection_celebrite)
        self.selection_patient_fenetre.show()

    def lancer_selection_celebrite(self, patient_id, patient_name):
        """
    Lance la fenêtre de sélection des célébrités pour le patient choisi.

    - Si une présélection existe déjà dans la base, affiche une alerte.
    - Sinon, ouvre la fenêtre de présélection avec la classe `SelectionCelebrites`.

    Args:
        patient_id (int): ID du patient sélectionné.
        patient_name (str): Nom du patient sélectionné.
        """
        self.selection_fenetre = SelectionCelebrites(patient_id, patient_name)
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM selections WHERE patient_id = ?", (patient_id,))
        count = cursor.fetchone()[0]
        conn.close()

        if count > 0:
            QMessageBox.information(self, "Déjà sélectionné", "Ce patient a déjà effectué la préselection.")
        else:
            self.selection_fenetre = SelectionCelebrites(patient_id, patient_name)
            self.selection_fenetre.show()
