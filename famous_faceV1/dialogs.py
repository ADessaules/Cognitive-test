import sqlite3
import inspect
from PyQt6.QtWidgets import QVBoxLayout, QDialog, QListWidget
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from constant import DB_FILE, DOSSIER_PATIENTS

class SelectionPatientDialog(QDialog):
    """
Fenêtre de dialogue permettant de sélectionner un patient depuis la base de données.

Une fois un patient sélectionné dans la liste, un rappel (`callback`) est appelé
avec son identifiant et éventuellement son nom. Cette classe est utile pour intégrer
la sélection de patients dans d'autres interfaces.
    """
    def __init__(self, callback):
        """
    Initialise la boîte de dialogue et affiche la liste des patients.

    Args:
        callback (function): Fonction à appeler lorsqu’un patient est sélectionné.
                             Elle peut accepter soit un argument (id), soit deux (id, nom).
        """
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
        """
    Appelée lorsqu’un patient est cliqué dans la liste.

    Elle récupère l'ID et le nom du patient sélectionné, puis appelle la fonction
    `callback` fournie, avec le bon nombre d’arguments selon ce qu’elle accepte.

    Args:
        item (QListWidgetItem): Élément cliqué représentant un patient.
        """
        index = self.liste_widget.row(item)
        patient_id = self.patients[index][0]
        patient_name = self.patients[index][1]
    
        # Détermine combien d'arguments la fonction attend
        arg_count = len(inspect.signature(self.callback).parameters)
    
        if arg_count == 1:
            self.callback(patient_id)
        else:
            self.callback(patient_id, patient_name)
    
        self.close()
