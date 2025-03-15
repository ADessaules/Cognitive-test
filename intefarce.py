import sys

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QWidget, QPushButton, QStackedWidget
from PyQt6.QtCore import Qt
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cognitive Test") #Titre de la page 
        self.setGeometry(100, 100, 400, 600) #Taille de base de la page

        self.stack = QStackedWidget() #Widgets empilés pour gérer les pages 

        #Pages
        self.page_acceuil = self.create_home_page()
        self.page_tests = self.create_tests_page()
        self.page_patients = self.create_patients_page()
        self.page_listes_patients = self.create_listes_patients_page()
        self.page_nouveau_patient = self.create_nouveau_patient_page()

        #Ajouter les pages au stack
        self.stack.addWidget(self.page_acceuil)#Ajouter à l'Index 0
        self.stack.addWidget(self.page_tests)#Ajouter à l'Index 1
        self.stack.addWidget(self.page_patients)#Ajouter à l'Index 2
        self.stack.addWidget(self.page_listes_patients)#Ajouter à l'Index 3
        self.stack.addWidget(self.page_nouveau_patient)#Ajouter à l'Index 4

        self.setCentralWidget(self.stack)

    def create_home_page(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        #Titre
        title = QLabel("Cognitive Test")
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        title.setStyleSheet("font-size: 24px; padding: 15px;")

        #Boutons
        btn_tests = QPushButton("Les tests Cognitifs")
        btn_tests.setStyleSheet("font-size: 24px; padding: 15px;")
        btn_tests.clicked.connect(lambda: self.stack.setCurrentIndex(1))

        btn_patients =  QPushButton("Les patients")
        btn_patients.setStyleSheet("font-size: 24px; padding: 15px;")
        btn_patients.clicked.connect(lambda: self.stack.setCurrentIndex(2))

        #Ajout au layout
        layout.addWidget(title)
        layout.addWidget(btn_tests)
        layout.addWidget(btn_patients)

        #Retourner la page
        page = QWidget()
        page.setLayout(layout)
        return page
    
    def create_tests_page(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel("Pages des tests cognitifs")
        label.setStyleSheet("font-size: 32px;")

        btn_back = QPushButton("Retour")
        btn_back.setStyleSheet("font-size: 20px; padding: 10px;")
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        layout.addWidget(label)
        layout.addWidget(btn_back)

        page = QWidget()
        page.setLayout(layout)
        return page
    
    def create_patients_page(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel("Pages des Patients")
        label.setStyleSheet("font-size: 32px;")

        btn_nouveau_patients =  QPushButton("Nouveau Patient")
        btn_nouveau_patients.setStyleSheet("font-size: 25px; padding: 15px;")
        btn_nouveau_patients.clicked.connect(lambda: self.stack.setCurrentIndex(4))

        btn_listes_patients = QPushButton("Listes des Patients")
        btn_listes_patients.setStyleSheet("font-size: 25px; padding: 15px;")
        btn_listes_patients.clicked.connect(lambda: self.stack.setCurrentIndex(3))

        btn_back = QPushButton("Retour")
        btn_back.setStyleSheet("font-size: 20px; padding: 10px;")
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        layout.addWidget(label)
        layout.addWidget(btn_nouveau_patients)
        layout.addWidget(btn_listes_patients)
        layout.addWidget(btn_back)

        page = QWidget()
        page.setLayout(layout)
        return page
    
    def create_listes_patients_page(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel("Listes des Patients")
        label.setStyleSheet("font-size: 32px;")

        btn_back = QPushButton("Retour")
        btn_back.setStyleSheet("font-size: 20px; padding: 10px;")
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(2))

        layout.addWidget(label)
        layout.addWidget(btn_back)

        page = QWidget()
        page.setLayout(layout)
        return page
    
    def create_nouveau_patient_page(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel("Nouveau Patients")
        label.setStyleSheet("font-size: 32px;")

        btn_back = QPushButton("Retour")
        btn_back.setStyleSheet("font-size: 20px; padding: 10px;")
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(2))

        layout.addWidget(label)
        layout.addWidget(btn_back)
        
        page = QWidget()
        page.setLayout(layout)
        return page



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()
else :
    print("ERROR")
