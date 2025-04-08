import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QMessageBox
from PyQt6.QtCore import Qt

tests = [
    ("Chien", "Loup", "Chat"),
    ("Voiture", "Vélo", "Eléphant"),
    ("Pomme", "Banane", "Voiture")
]

class SemanticMatching(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Appariement Sémantique")
        self.setGeometry(100, 100, 400, 300)

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
        if self.current_index < len(tests):
            test_word, choice1, choice2 = tests[self.current_index]
            self.label_test_word.setText(f"Mot test : {test_word}")
            self.button_choice_1.setText(choice1)
            self.button_choice_2.setText(choice2)
        else:
            self.end_test()

    def reccord_response(self,choice_index):
        test = tests[self.current_index]
        selected_word = test[1 + choice_index]
        self.responses.append({
            "test_word": test[0],
            "choice1": test[1],
            "choice2": test[2],
            "selected": selected_word
        })

    def end_test(self):
        QMessageBox.information(self, "Fin du test")
        print("Réponses :")
        for r in self.responses:
            print(r)
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SemanticMatching()
    window.show()
    sys.exit(app.exec())



