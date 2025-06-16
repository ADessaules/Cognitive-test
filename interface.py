import sys
import subprocess
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QWidget, QPushButton, QStackedWidget, QListWidget
from PyQt6.QtCore import Qt
from gestion_patient.creation_patient import creer_patient
from constant import DB_FILE, DOSSIER_PATIENTS
from gestion_patient.detail_patient import PatientDetailsWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Titre et taille de la fenêtre
        self.setWindowTitle("Cognitive Test")
        self.setGeometry(100, 100, 400, 600)

        # Utilisation d'un QStackedWidget pour gérer les différentes pages de l'interface
        self.stack = QStackedWidget()

        # Création des pages
        self.page_acceuil = self.create_home_page()
        self.page_choix_test = self.create_tests_page()

        # Ajout des pages à la pile
        self.stack.addWidget(self.page_acceuil)      # Index 0 : page d'accueil
        self.stack.addWidget(self.page_choix_test)   # Index 1 : page des tests

         # Définition de la pile comme widget central
        self.setCentralWidget(self.stack)

    # Création de la page d'accueil
    def create_home_page(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Titre de la page
        title = QLabel("Cognitive Test")
        title.setStyleSheet("font-size: 24px; padding: 15px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Bouton pour accéder aux tests
        btn_tests = QPushButton("Faire un test cognitif")
        btn_tests.setStyleSheet("font-size: 20px; padding: 15px;")
        btn_tests.clicked.connect(lambda: self.stack.setCurrentIndex(1))  # Affiche la page des tests

        # Bouton pour créer un nouveau patient
        btn_creer_patient = QPushButton("Créer un patient")
        btn_creer_patient.setStyleSheet("font-size: 20px; padding: 15px;")
        btn_creer_patient.clicked.connect(lambda: creer_patient(self))

        # Bouton pour consulter les détails d’un patient
        btn_detail_patient = QPushButton("Détail patient")
        btn_detail_patient.setStyleSheet("font-size: 20px; padding: 15px;")
        btn_detail_patient.clicked.connect(self.show_patient_details)

        # Bouton pour supprimer un patient
        btn_supprimer_patient = QPushButton("Supprimer un patient")
        btn_supprimer_patient.setStyleSheet("font-size: 20px; padding: 15px;")
        btn_supprimer_patient.clicked.connect(self.delete_patient)

        # Ajout des éléments au layout
        layout.addWidget(title)
        layout.addWidget(btn_creer_patient)
        layout.addWidget(btn_tests)
        layout.addWidget(btn_detail_patient)
        layout.addWidget(btn_supprimer_patient)

        # Création et retour du widget
        page = QWidget()
        page.setLayout(layout)
        return page

    # Création de la page de sélection des tests
    def create_tests_page(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Label d'instruction
        label = QLabel("Choisissez un test")
        label.setStyleSheet("font-size: 20px; padding: 10px;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Liste des tests disponibles
        self.list_tests = QListWidget()
        self.list_tests.addItem("famous_faceV1")
        self.list_tests.addItem("matching_unknow_face")
        self.list_tests.addItem("famous_name")
        self.list_tests.addItem("appareiment_semantique_mots")
        self.list_tests.addItem("appareiment_semantique_image")
        self.list_tests.addItem("bisection_test")

        # Connexion de l'événement de clic sur un test
        self.list_tests.itemClicked.connect(self.launch_test)

        # Bouton de retour à l'accueil
        btn_back = QPushButton("Retour")
        btn_back.setStyleSheet("font-size: 18px; padding: 10px;")
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        # Ajout des widgets au layout
        layout.addWidget(label)
        layout.addWidget(self.list_tests)
        layout.addWidget(btn_back)

        # Création et retour du widget
        page = QWidget()
        page.setLayout(layout)
        return page
    
    # Méthode pour lancer un test sélectionné dans la liste
    def launch_test(self, item):
        test_name = item.text()

        # Chaque condition tente de lancer un test via subprocess
        if test_name == "famous_faceV1":
            try:
                self.hide() 
                subprocess.Popen(["python", "./famous_faceV1/famous_faceV1.py"])
            except Exception as e:
                print(f"Erreur lors du lancement du test : {e}")
        elif test_name == "matching_unknow_face":
            try:
                self.hide()
                subprocess.Popen(["python", "./matching_unknown_faceV1/matching_unknown_faceV1.py"])
            except Exception as e:
                print(f"Erreur lors du lancement du test : {e}")
        elif test_name == "famous_name":
            try:
                self.hide()
                subprocess.Popen(["python", "./famous_name/famous_name.py"])
            except Exception as e:
                print(f"Erreur lors du lancement du test : {e}")
        elif test_name == "appareiment_semantique_mots":
            try:
                self.hide()
                subprocess.Popen(["python", "./test_appariement_semantique_mots/test_appareiment_semantique_mots.py"])
            except Exception as e:
                print(f"Erreur lors du lancement du test : {e}")
        elif test_name == "appareiment_semantique_image":
            try:
                self.hide()
                subprocess.Popen(["python", "./test_appariement_semantique_image/test_appariement_semantique_image.py"])
            except Exception as e:
                print(f"Erreur lors du lancement du test : {e}")
        elif test_name == "bisection_test":
            try:
                self.hide()
                subprocess.Popen(["python", "./bisection_test/bisection_test.py"])
            except Exception as e:
                print(f"Erreur lors du lancement du test : {e}")
    
    # Méthode pour afficher les détails d’un patient
    def show_patient_details(self):
        self.details_window = PatientDetailsWindow(self)
        self.details_window.exec()

    # Méthode pour supprimer un patient (ouvre une fenêtre dédiée)
    def delete_patient(self):
        from gestion_patient.liste_patients import ListePatients
        self.supprimer_window = ListePatients(supprimer=True)
        self.supprimer_window.exec()

# Point d’entrée principal de l’application
if __name__ == "__main__":
    app = QApplication(sys.argv)     # Création de l'application Qt
    window = MainWindow()            # Instanciation de la fenêtre principale
    window.show()                    # Affichage de la fenêtre
    sys.exit(app.exec())            # Boucle d'événements Qt