import sqlite3
from PyQt6.QtWidgets import QVBoxLayout, QDialog, QListWidget
from constant import DB_FILE

class SelectionPatientDialog(QDialog):
    def __init__(self, callback):
        super().__init__()
        self.setWindowTitle("Choisir un patient")
        self.setGeometry(200, 200, 400, 400)
        self.callback = callback
        
        self.layout = QVBoxLayout()
        self.liste_widget = QListWidget()
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, nom FROM patients")
        self.patients = cursor.fetchall()
        conn.close()
        
        for patient in self.patients:
            self.liste_widget.addItem(f"{patient[1]}")
        
        self.liste_widget.itemClicked.connect(self.patient_selectionne)
        self.layout.addWidget(self.liste_widget)
        self.setLayout(self.layout)

    def patient_selectionne(self, item):
        index = self.liste_widget.row(item)
        patient_id = self.patients[index][0]
        self.callback(patient_id, patient_name)
        self.close()
