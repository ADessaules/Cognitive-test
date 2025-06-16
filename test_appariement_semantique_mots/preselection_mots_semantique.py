from PyQt6.QtWidgets import (
    QWidget, QPushButton, QLabel, QVBoxLayout, QDialog, QMessageBox, QGridLayout, QScrollArea
)
from PyQt6.QtCore import Qt
import sqlite3
import os

# À adapter à ton système
from constant import DB_FILE, DOSSIER_PATIENTS



class SelectionMots(QDialog):
    def __init__(self, patient_id, patient_name, liste_mots):
        super().__init__()
        self.setWindowTitle("Sélection des mots")
        self.setGeometry(100, 100, 800, 600)
        self.patient_id = patient_id
        self.patient_name = patient_name
        self.selections = {}

        self.liste_mots = liste_mots

        self.layout = QVBoxLayout()

        scroll = QScrollArea()
        scroll_widget = QWidget()
        self.grid_layout = QGridLayout()
        scroll_widget.setLayout(self.grid_layout)
        scroll.setWidgetResizable(True)
        scroll.setWidget(scroll_widget)
        self.layout.addWidget(scroll)

        self.btn_valider = QPushButton("Valider la sélection")
        self.btn_valider.setStyleSheet("font-size: 18px; padding: 10px;")
        self.btn_valider.clicked.connect(self.valider_selection)
        self.layout.addWidget(self.btn_valider)

        self.btn_stop = QPushButton("Stopper le test")
        self.btn_stop.setStyleSheet("font-size: 18px; padding: 10px; background-color: red; color: white;")
        self.btn_stop.clicked.connect(self.stop_test)
        self.layout.addWidget(self.btn_stop)

        self.setLayout(self.layout)
        self.afficher_mots_grid()

    def afficher_mots_grid(self):
        row = col = 0
        for mot in self.liste_mots:
            label = QLabel(mot)
            label.setFixedSize(150, 40)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("border: 2px solid black; font-size: 16px; padding: 5px; background-color: lightgreen;")

            label.mousePressEvent = self.generer_toggle_handler(label, mot)
            self.grid_layout.addWidget(label, row, col)
            self.selections[label] = {"selected": True, "mot": mot}

            col += 1
            if col >= 4:
                col = 0
                row += 1

    def generer_toggle_handler(self, label, mot):
        def handler(event):
            current = self.selections[label]
            current["selected"] = not current["selected"]
            if current["selected"]:
                label.setStyleSheet("border: 2px solid black; font-size: 16px; padding: 5px; background-color: lightgreen;")
            else:
                label.setStyleSheet("border: 2px solid black; font-size: 16px; padding: 5px; background-color: lightgray;")
        return handler

    def enregistrer_selection_txt(self):
        selected_mots = [info["mot"] for info in self.selections.values() if info["selected"]]
        patient_folder = os.path.join("Patients", self.patient_name)
        os.makedirs(patient_folder, exist_ok=True)
        with open(os.path.join(patient_folder, "selection_mots.txt"), "w", encoding="utf-8") as f:
            f.write(",".join(selected_mots))

    def valider_selection(self):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM selection_mots WHERE patient_id = ?", (self.patient_id,))
        for info in self.selections.values():
            if info["selected"]:
                cursor.execute(
                    "INSERT INTO selection_mots (patient_id, mot) VALUES (?, ?)",
                    (self.patient_id, info["mot"])
                )
        conn.commit()
        conn.close()
        self.enregistrer_selection_txt()
        QMessageBox.information(self, "Enregistré", "Sélection mise à jour avec succès.")
        self.close()

    def table_selection_mots():
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS selection_mots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                mot TEXT NOT NULL
            )
        ''')

        conn.commit()
        conn.close()
        print("✅ Table 'selection_mots' vérifiée/créée avec succès.")

    def stop_test(self):
        self.valider_selection()
        QMessageBox.information(self, "Test interrompu", "Test arrêté. Sélections sauvegardées.")
        self.close()

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    # ⚠️ Remplacer par des valeurs de test ou récupérer dynamiquement
    patient_id = 1
    patient_name = "Test_Patient"
    Triplet_de_mot = [
    ("souris", "chien", "chat"),
    ("balais", "aspirateur", "cintre"),
    ("âne", "carotte", "banane"),
    ("chameau", "désert", "forêt"),
    ("piano", "partition", "roman"),
    ("sifflet", "maçon", "gendarme"),
    ("château", "chevalier", "pirate"),
    ("chauve-souris", "nuit", "jour"),
    ("serpent", "banquise", "désert"),
    ("flèche", "arc", "fusil"), 
    ("moulin à vent", "campagne", "ville"),
    ("fraise", "poêle", "sucre"),
    ("arrosoir", "arbre", "fleur"),
    ("tortue", "salade", "gland"),
    ("scie", "tarte", "branche"),
    ("maïs", "forêt", "champs"),
    ("perroquet", "perchoir", "cheminée"),
    ("tulipe", "jardinier", "cuisinier"),
    ("brouette", "ciseaux", "pelle"),
    ("vin", "tasse", "bouteille"),
    ("compas", "sac à main", "cartable"),
    ("luge", "rames", "skis"),
    ("tambour", "baquettes", "louche"),
    ("pyjama", "chaussures", "pantoufles"),
    ("lapin", "carotte", "os"),
    ("lézard", "lune", "soleil"),
    ("cravate", "chemise", "robe"),
    ("flûte", "pipe", "trompette"),
    ("chapeau", "tête", "main"),
    ("ananas", "tronçonneuse", "couteaux"),
    ("mouton", "loup", "lion"),
    ("aigle", "mer", "montagne"),
    ("toupie", "main", "pied"),
    ("ours", "vodka", "miel"),
    ("singe", "salade", "banane"),
    ("hache", "bûche", "pain"),
    ("zèbre", "ferme", "savane"),
    ("cygne", "forêt", "étang"),
    ("lunettes", "oeil", "bouche"),
    ("mains", "gants", "chaussures"),
    ("selle", "mouton", "cheval"),
    ("ancre", "pirogue", "paquebot"),
    ("oreillers", "lit", "chaise"),
    ("allumettes", "ampoule", "bougie"),
    ("pyramide", "palmier", "sapin"),
    ("tente", "feu de camp", "radiateur"),
    ("gruyère", "lapin", "souris"),
    ("niche", "chien", "chat"),
    ("rideau", "porte", "fenêtre"),
    ("ventilateur", "lune", "soleil"),
    ("antivol", "vélo", "voiture"),
    ("masque", "clown", "homme d'affaire"),
    ("tableau", "table de ping pong", "bureau"),
    ("vin", "raisin", "cerise"),
    ("cactus", "désert", "littoral"),
    ("clou", "marteau", "hache"),
    ("orange", "jus", "vin"),
    ("avion", "oiseau", "requin"),
    ("camion", "panier", "carton"),
    ("canard", "étang", "mer"),
    ("grenouille", "tournesol", "nénuphar"),
    ("crocodile", "panier", "sac à main"),
    ("brosse à dent", "nez", "bouche"),
    ("éléphant", "cirque", "église"),
    ("groupe de gens", "bus", "cabane"),
    ("ciseaux", "feuille de papier", "planche de bois"),
    ("clé", "porte", "fenêtre"),
    ("pomme", "scarabée", "ver"),
    ("poubelle", "brosse", "balai"),
    ("pile", "bougie", "lampe torche"),
    ("chien", "nichoir", "niche"),
    ("marteau", "vis", "clou"),
    ("rhinocéros", "lion", "chat"),
    ("moto", "costume", "blouson"),
    ("écureuil", "maïs", "gland")
    ]
    # Aplatir et supprimer les doublons
    liste_mots = sorted(set([mot for triplet in Triplet_de_mot for mot in triplet]))
    window = SelectionMots(patient_id, patient_name, liste_mots)
    window.show()
    sys.exit(app.exec())
