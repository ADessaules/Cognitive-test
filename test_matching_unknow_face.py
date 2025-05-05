import sys
import os
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QDialog, QListWidget, QScrollArea, QDialogButtonBox, QListWidgetItem
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt

class MatchingUnknowFace(QWidget):
    def __init__(self, tests):
        super().__init__()
        self.setWindowTitle("Test Matching Unknow face - Images")
        self.setGeometry(100, 100, 800, 600)

        self.tests = tests
        self.current_index = 0
        self.responses = []

        # Widgets
        self.label_test_image = QLabel()
        self.label_test_image.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.button_choice_1 = QPushButton()
        self.button_choice_2 = QPushButton()
        self.button_choice_1.setFixedSize(200, 200)
        self.button_choice_2.setFixedSize(200, 200)

        self.button_choice_1.clicked.connect(lambda: self.record_response(0))
        self.button_choice_2.clicked.connect(lambda: self.record_response(1))

        # Layouts
        layout = QVBoxLayout()
        layout.addWidget(self.label_test_image)

        choices_layout = QHBoxLayout()
        choices_layout.addWidget(self.button_choice_1)
        choices_layout.addWidget(self.button_choice_2)

        layout.addLayout(choices_layout)
        self.setLayout(layout)

        self.load_next_test()

    def load_next_test(self):
        if self.current_index < len(self.tests):
            test_path, choice1_path, choice2_path = self.tests[self.current_index]

            print(f"[INFO] Loading test #{self.current_index + 1}:")
            print("Test Image:", test_path)
            print("Choices:", choice1_path, choice2_path)

            # Test image
            pixmap_test = QPixmap(test_path)
            if pixmap_test.isNull():
                print(f"[ERREUR] Impossible de charger l'image test : {test_path}")
            self.label_test_image.setPixmap(pixmap_test.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio))

            # Choix
            pixmap1 = QPixmap(choice1_path)
            pixmap2 = QPixmap(choice2_path)

            self.button_choice_1.setIcon(QIcon(pixmap1))
            self.button_choice_1.setIconSize(self.button_choice_1.size())

            self.button_choice_2.setIcon(QIcon(pixmap2))
            self.button_choice_2.setIconSize(self.button_choice_2.size())
        else:
            self.end_test()

    def record_response(self, choice_index):
        test = self.tests[self.current_index]
        selected_path = test[1 + choice_index]
        self.responses.append({
            "test": test[0],
            "choice1": test[1],
            "choice2": test[2],
            "selected": selected_path
        })

        self.current_index += 1
        self.load_next_test()
       
    def end_test(self):
        recap = "Test terminé ! \n\n Les Réponses :\n\n"
        for r in self.responses:
            recap += f"- Test : {r['test']}\n -> Réponse : {r['selected']}"

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

        self.item_map = {}
        for i,r in enumerate(self.responses):
            item_image= f"{r['test']} -> {r['selected']}"
            item = QListWidgetItem(item_image)
            item.setCheckState(Qt.CheckState.Unchecked)
            list_widget.addItem(item)
            self.item_map[i] = r

        layout.addWidget(QLabel("Sélectionner les items que vous voulez faire repasser"))
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
                    response = self.item_map[i]
                    test = (response['test'], response['choice1'], response['choice2'])
                    items_to_retry.append(test)
            if items_to_retry:
                self.retry_item(items_to_retry)

    def retry_item(self, items):
        self.new_window = ImageSemanticMatching(items)
        self.new_window.show()
        self.close()

if __name__ == "__main__":
    tests_image = [
        ("C:/Users/lekil/OneDrive/Bureau/Projet_tutoré-Cognitive_test/Cognitive-test/image_test_matching_unknow_face/Image1.jpg", "C:/Users/lekil/OneDrive/Bureau/Projet_tutoré-Cognitive_test/Cognitive-test/image_test_matching_unknow_face/Image2.jpg", "C:/Users/lekil/OneDrive/Bureau/Projet_tutoré-Cognitive_test/Cognitive-test/image_test_matching_unknow_face/Image3.jpg"),
        ("C:/Users/lekil/OneDrive/Bureau/Projet_tutoré-Cognitive_test/Cognitive-test/image_test_matching_unknow_face/Image4.jpg", "C:/Users/lekil/OneDrive/Bureau/Projet_tutoré-Cognitive_test/Cognitive-test/image_test_matching_unknow_face/Image5.jpg", "C:/Users/lekil/OneDrive/Bureau/Projet_tutoré-Cognitive_test/Cognitive-test/image_test_matching_unknow_face/Image6.jpg"),
        ("C:/Users/lekil/OneDrive/Bureau/Projet_tutoré-Cognitive_test/Cognitive-test/image_test_matching_unknow_face/Image7.jpg", "C:/Users/lekil/OneDrive/Bureau/Projet_tutoré-Cognitive_test/Cognitive-test/image_test_matchung_unknow_face/Image8.jpg", "C:/Users/lekil/OneDrive/Bureau/Projet_tutoré-Cognitive_test/Cognitive-test/image_test_matching_unknow_face/Image9.jpg"),
    ]

    app = QApplication(sys.argv)
    window = MatchingUnknowFace(tests_image)
    window.show()
    sys.exit(app.exec())