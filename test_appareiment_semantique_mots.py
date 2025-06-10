import sys
import random
import time
import datetime
import pandas as pd
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QComboBox, QLineEdit, QGridLayout, QApplication, QWidget, QLabel,
    QPushButton, QVBoxLayout, QMessageBox, QHBoxLayout
)
from PyQt6.QtCore import Qt, QTimer, QEvent

# === Triplets de test ===
tests = [
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

class WaitingScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("\u00c9cran d'attente")
        self.setGeometry(920, 100, 800, 600)
        layout = QVBoxLayout()
        label = QLabel("Appuyez sur Espace pour d\u00e9marrer le test")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)

class SemanticMatchingPatient(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Appariement S\u00e9mantique - Patient")
        self.setGeometry(920, 100, 800, 600)
        self.word_label = QLabel("", alignment=Qt.AlignmentFlag.AlignCenter)
        self.word_label.setStyleSheet("font-size: 28px; margin: 20px;")

        self.btn1 = QPushButton("")
        self.btn2 = QPushButton("")
        for btn in (self.btn1, self.btn2):
            btn.setStyleSheet("font-size: 20px; padding: 15px;")

        layout = QVBoxLayout()
        layout.addWidget(self.word_label)
        layout.addWidget(self.btn1)
        layout.addWidget(self.btn2)
        self.setLayout(layout)

    def show_triplet(self, test_word, options, handlers):
        self.word_label.setText(test_word)
        self.btn1.setText(options[0])
        self.btn2.setText(options[1])

        self.btn1.clicked.disconnect()
        self.btn2.clicked.disconnect()

        self.btn1.clicked.connect(handlers[0])
        self.btn2.clicked.connect(handlers[1])

class SemanticMatchingExaminateur(QMainWindow):
    def __init__(self, test_triplets):
        super().__init__()
        self.setWindowTitle("Test Appariement S\u00e9mantique - Exp\u00e9rimentateur")
        self.setGeometry(100, 100, 1200, 600)
        self.test_triplets = test_triplets
        self.test_name = "matching_words"
        self.timer = QTimer()
        self.timer.timeout.connect(self.advance_by_timer)

        self.init_ui()
        self.installEventFilter(self)

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout()
        left_layout = QVBoxLayout()

        self.patient_selector = QComboBox()
        self.patient_selector.addItem("-- Aucun --")
        patients_path = Path(__file__).resolve().parent / "Patients"
        if patients_path.exists():
            for folder in patients_path.iterdir():
                if folder.is_dir():
                    self.patient_selector.addItem(folder.name)

        self.contact_input = QLineEdit()
        self.contact_input.setPlaceholderText("Contacts de stimulation")
        self.intensite_input = QLineEdit()
        self.intensite_input.setPlaceholderText("Intensit\u00e9 (mA)")
        self.duree_input = QLineEdit()
        self.duree_input.setPlaceholderText("Dur\u00e9e (ms)")

        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["Image au clic", "Temps imparti", "Barre espace"])
        self.timer_input = QLineEdit()
        self.timer_input.setPlaceholderText("Temps (en secondes)")
        self.timer_input.setVisible(False)
        self.mode_selector.currentTextChanged.connect(lambda x: self.timer_input.setVisible(x == "Temps imparti"))

        start_btn = QPushButton("Valider et Pr\u00e9parer le test")
        start_btn.clicked.connect(self.prepare_test)
        stop_btn = QPushButton("Arr\u00eater et sauvegarder")
        stop_btn.clicked.connect(self.save_results)

        for w in [QLabel("S\u00e9lectionner un patient :"), self.patient_selector,
                  self.contact_input, self.intensite_input, self.duree_input,
                  QLabel("Mode de test :"), self.mode_selector,
                  self.timer_input, start_btn, stop_btn]:
            left_layout.addWidget(w)

        self.status_label = QLabel("En attente du d\u00e9marrage du test…")
        left_layout.addWidget(self.status_label)

        self.right_layout = QVBoxLayout()

        layout.addLayout(left_layout)
        layout.addLayout(self.right_layout)
        central.setLayout(layout)

    def prepare_test(self):
        if self.patient_selector.currentText() == "-- Aucun --" or not all([
            self.contact_input.text().strip(),
            self.intensite_input.text().strip(),
            self.duree_input.text().strip()
        ]):
            QMessageBox.warning(self, "Erreur", "Veuillez remplir tous les champs et choisir un patient.")
            return

        if self.mode_selector.currentText() == "Temps imparti" and not self.timer_input.text().isdigit():
            QMessageBox.warning(self, "Erreur", "Veuillez entrer un temps valide en secondes.")
            return

        self.contact = self.contact_input.text().strip()
        self.intensite = self.intensite_input.text().strip()
        self.duree = self.duree_input.text().strip()
        self.mode = self.mode_selector.currentText()
        self.timer_duration = int(self.timer_input.text()) if self.mode == "Temps imparti" else 0

        self.shuffled_triplets = random.sample(self.test_triplets, len(self.test_triplets))
        self.index = 0
        self.session_results = []
        self.session_active = False

        self.waiting_screen = WaitingScreen()
        self.patient_window = SemanticMatchingPatient()
        self.waiting_screen.show()
        self.patient_window.show()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyRelease and event.key() == Qt.Key.Key_Space:
            if not self.session_active and self.waiting_screen.isVisible():
                self.waiting_screen.hide()
                self.session_active = True
                self.show_next_triplet()
            elif self.session_active and self.mode == "Barre espace":
                self.index += 1
                self.show_next_triplet()
        return super().eventFilter(obj, event)

    def advance_by_timer(self):
        self.index += 1
        self.show_next_triplet()

    def show_next_triplet(self):
        for i in reversed(range(self.right_layout.count())):
            widget = self.right_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        if self.index >= len(self.shuffled_triplets):
            self.save_results()
            return

        test_word, correct, distractor = self.shuffled_triplets[self.index]
        options = [correct, distractor]
        random.shuffle(options)
        is_correct_map = {opt: opt == correct for opt in options}
        self.start_time = time.time()

        word_label = QLabel(f"<b>{test_word}</b>")
        word_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        word_label.setStyleSheet("font-size: 28px; margin: 20px;")

        btn1 = QPushButton(options[0])
        btn2 = QPushButton(options[1])
        for btn in (btn1, btn2):
            btn.setStyleSheet("font-size: 20px; padding: 15px;")

        def make_handler(selected_option, selected_button):
            def handler():
                rt = round(time.time() - self.start_time, 3)
                self.session_results.append({
                    "id_essai": self.index + 1,
                    "temps_reponse": rt,
                    "choix": selected_option,
                    "correct": is_correct_map[selected_option],
                    "mot_test": test_word,
                    "participant": self.patient_selector.currentText(),
                    "contact_stimulation": self.contact,
                    "intensit\u00e9": self.intensite,
                    "dur\u00e9e": self.duree,
                    "mode": self.mode,
                    "horodatage": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "test_name": self.test_name
                })
                for b in (btn1, btn2):
                    b.setEnabled(False)
                selected_button.setStyleSheet(f"font-size: 20px; padding: 15px; border: 4px solid {'green' if is_correct_map[selected_option] else 'red'}")
                self.index += 1
                QTimer.singleShot(500, self.show_next_triplet)
            return handler

        btn1.clicked.connect(make_handler(options[0], btn1))
        btn2.clicked.connect(make_handler(options[1], btn2))

        self.right_layout.addWidget(word_label)
        self.right_layout.addWidget(btn1)
        self.right_layout.addWidget(btn2)

        self.patient_window.show_triplet(test_word, options, [make_handler(options[0], btn1), make_handler(options[1], btn2)])

        if self.mode == "Temps imparti":
            self.timer.start(self.timer_duration * 1000)

    def save_results(self):
        self.timer.stop()
        df = pd.DataFrame(self.session_results)
        if df.empty:
            QMessageBox.information(self, "Fin", "Aucun r\u00e9sultat \u00e0 enregistrer.")
            return

        now = datetime.now().strftime("%Y_%m_%d_%H%M")
        name = self.patient_selector.currentText().replace(" ", "_")
        filename = f"{name}_{now}_{self.contact}-{self.intensite}-{self.duree}_{self.test_name}.xlsx"
        df.to_excel(filename, index=False)
        QMessageBox.information(self, "Fin", f"Test termin\u00e9. R\u00e9sultats enregistr\u00e9s dans :\n{filename}")
        self.status_label.setText("Test termin\u00e9.")
        if self.patient_window:
            self.patient_window.close()
        if self.waiting_screen:
            self.waiting_screen.close()
        self.session_active = False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SemanticMatchingExaminateur(tests)
    window.show()
    sys.exit(app.exec())
