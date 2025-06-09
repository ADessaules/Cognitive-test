import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QMessageBox, QListWidget, QListWidgetItem, QDialog, QDialogButtonBox, QScrollArea
from PyQt6.QtCore import Qt

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
    ("écureuil", "maïs", "gland")]


class SemanticMatching(QWidget):
    def __init__(self, tests):
        super().__init__()
        self.setWindowTitle("Test Appariement Sémantique")
        self.setGeometry(100, 100, 400, 300)

        self.tests = tests
        self.current_index = 0
        self.responses = []

        self.label_test_word = QLabel("", alignment = Qt.AlignmentFlag.AlignCenter)
        self.label_test_word.setStyleSheet("font-size: 24px; margin: 20px;")

        self.button_choice_1 = QPushButton("")
        self.button_choice_2 = QPushButton("")
        self.button_choice_1.setStyleSheet("font-size: 18px; padding: 15px;")
        self.button_choice_2.setStyleSheet("font-size: 18px; padding: 15px;")

        self.button_choice_1.clicked.connect(lambda: self.reccord_response(0))
        self.button_choice_2.clicked.connect(lambda: self.reccord_response(1))

        layout = QVBoxLayout()
        layout.addWidget(self.label_test_word)
        layout.addWidget(self.button_choice_1)
        layout.addWidget(self.button_choice_2)
        self.setLayout(layout)

        self.load_next_test()

    def load_next_test(self):
        if self.current_index < len(self.tests):  # ⚠️ ici on utilise bien self.tests
            test_word, choice1, choice2 = self.tests[self.current_index]
            self.label_test_word.setText(f"Mot test : {test_word}")
            self.button_choice_1.setText(choice1)
            self.button_choice_2.setText(choice2)
        else:
            self.end_test()


    def reccord_response(self,choice_index):
        if self.current_index < len(self.tests):
            test = self.tests[self.current_index]
            selected_word = test[1 + choice_index]
            self.responses.append({
                "test_word": test[0],
                "choice1": test[1],
                "choice2": test[2],
                "selected": selected_word
            })
            self.current_index += 1
            self.load_next_test()

    def end_test(self):
        recap = "Test terminé !\n\n Les Réponses :\n\n"
        for r in self.responses:
            recap += f"- Mot : {r['test_word']}\n -> {r['choice1']} | {r['choice2']} -> Réponse : {r['selected']}\n\n"
        # Crée un QDialog personnalisé avec scroll
        recap_dialog = QDialog(self)
        recap_dialog.setWindowTitle("Résultats du test")
        layout = QVBoxLayout()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = QWidget()
        content_layout = QVBoxLayout()
        label = QLabel(recap)
        label.setWordWrap(True)
        content_layout.addWidget(label)
        content.setLayout(content_layout)

        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Boutons Oui / Non
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Yes | QDialogButtonBox.StandardButton.No)
        buttons.button(QDialogButtonBox.StandardButton.Yes).setText("Repasser certains items")
        buttons.button(QDialogButtonBox.StandardButton.No).setText("Quitter")

        buttons.accepted.connect(recap_dialog.accept)
        buttons.rejected.connect(recap_dialog.reject)

        layout.addWidget(buttons)
        recap_dialog.setLayout(layout)
        recap_dialog.resize(500, 400)

        if recap_dialog.exec():
            self.select_item_to_retry()
        else:
            self.close()

    def select_item_to_retry(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Repasser certains items")
        layout = QVBoxLayout()

        list_widget = QListWidget()
        list_widget.setMinimumHeight(200)
        list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.items_map = {}
        for i, r in enumerate(self.responses):
            item_text = f"{r['test_word']} -> {r['selected']}"
            item = QListWidgetItem(item_text)
            item.setCheckState(Qt.CheckState.Unchecked)
            list_widget.addItem(item)
            self.items_map[i] = r  # mappe l'index de l'affichage à la réponse

        layout.addWidget(QLabel("Sélectionnez les items que vous souhaitez faire repasser :"))
        layout.addWidget(list_widget)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)

        if dialog.exec():
            items_to_retry = []
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                if item.checkState() == Qt.CheckState.Checked:
                    response = self.items_map[i]
                    # 🔥 CONSTRUIT le test à refaire depuis la réponse
                    test = (response['test_word'], response['choice1'], response['choice2'])
                    items_to_retry.append(test)
            if items_to_retry:
                self.retry_item(items_to_retry)

    def retry_item(self, items):
        self.new_window = SemanticMatching(items)
        self.new_window.show()
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SemanticMatching(tests)
    window.show()
    sys.exit(app.exec())



