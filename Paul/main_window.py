from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QInputDialog, QMessageBox
from PyQt6.QtGui import QGuiApplication
import os
import sqlite3
from constant import DB_FILE, DOSSIER_PATIENTS
from liste_patients import ListePatients
from preselection_celeb import SelectionCelebrites
from dialogs import SelectionPatientDialog
from bisection_test import BisectionTest

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
        nom, ok = QInputDialog.getText(self, "Nouveau Patient", "Entrez le nom du patient :")
        if ok and nom:
            # Nettoyage du nom pour qu'il soit valide comme nom de dossier
            import re
            nom_dossier = re.sub(r'[\\/*?:"<>|]', "_", nom).strip()

            if not nom_dossier:
                QMessageBox.warning(self, "Erreur", "Nom de patient invalide.")
                return

            # Insère dans la base de données
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO patients (nom) VALUES (?)", (nom,))
            conn.commit()
            conn.close()

            # Créer le dossier du patient dans DOSSIER_PATIENTS
            dossier_patient = os.path.join(DOSSIER_PATIENTS, nom_dossier)
            try:
                os.makedirs(dossier_patient, exist_ok=True)
            except Exception as e:
                QMessageBox.warning(self, "Erreur", f"Erreur lors de la création du dossier : {e}")
                return

            QMessageBox.information(self, "Patient créé", f"Le patient « {nom} » a bien été créé avec un dossier nommé « {nom_dossier} »")



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

    def lancer_selection_celebrite(self, patient_id, patient_name):
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

    def lancer_bisection(self, patient_id):
        screens = QGuiApplication.screens()

        if len(screens) >= 2:
            screen_experimenter = screens[0]
            screen_patient = screens[1]
        else:
            screen_experimenter = screen_patient = screens[0]

        self.bisection_fenetre = BisectionTest(patient_id, screen_patient, screen_experimenter)
        self.bisection_fenetre.show()
