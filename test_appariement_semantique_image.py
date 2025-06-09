import sys
import os
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QDialog, QListWidget, QScrollArea, QDialogButtonBox, QListWidgetItem
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt

class ImageSemanticMatching(QWidget):
    def __init__(self, tests):
        super().__init__()
        self.setWindowTitle("Test Appariement Sémantique - Images")
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
        ("./image_test_appariement/Image1.jpg", "./image_test_appariement/Image2.jpg", "./image_test_appariement/Image3.jpg"),
        ("./image_test_appariement/Image4.jpg", "./image_test_appariement/Image5.jpg", "./image_test_appariement/Image6.jpg"),
        ("./image_test_appariement/Image7.jpg", "./image_test_appariement/Image8.jpg", "./image_test_appariement/Image9.jpg"),
        ("./image_test_appariement/Image10.jpg", "./image_test_appariement/Image11.jpg", "./image_test_appariement/Image12.jpg"),
        ("./image_test_appariement/Image13.jpg", "./image_test_appariement/Image14.jpg", "./image_test_appariement/Image15.jpg"),
        ("./image_test_appariement/Image16.jpg", "./image_test_appariement/Image17.jpg", "./image_test_appariement/Image18.jpg"),
        ("./image_test_appariement/Image19.jpg", "./image_test_appariement/Image20.jpg", "./image_test_appariement/Image21.jpg"),
        ("./image_test_appariement/Image22.jpg", "./image_test_appariement/Image23.jpg", "./image_test_appariement/Image24.jpg"),
        ("./image_test_appariement/Image25.jpg", "./image_test_appariement/Image26.jpg", "./image_test_appariement/Image27.jpg"),
        ("./image_test_appariement/Image28.jpg", "./image_test_appariement/Image29.jpg", "./image_test_appariement/Image30.jpg"),
        ("./image_test_appariement/Image31.jpg", "./image_test_appariement/Image32.jpg", "./image_test_appariement/Image33.jpg"),
        ("./image_test_appariement/Image34.jpg", "./image_test_appariement/Image35.jpg", "./image_test_appariement/Image36.jpg"),
        ("./image_test_appariement/Image37.jpg", "./image_test_appariement/Image38.jpg", "./image_test_appariement/Image39.jpg"),
        ("./image_test_appariement/Image40.jpg", "./image_test_appariement/Image41.jpg", "./image_test_appariement/Image42.jpg"),
        ("./image_test_appariement/Image43.jpg", "./image_test_appariement/Image44.jpg", "./image_test_appariement/Image45.jpg"),
        ("./image_test_appariement/Image46.jpg", "./image_test_appariement/Image47.jpg", "./image_test_appariement/Image48.jpg"),
        ("./image_test_appariement/Image49.jpg", "./image_test_appariement/Image50.jpg", "./image_test_appariement/Image51.jpg"),
        ("./image_test_appariement/Image52.jpg", "./image_test_appariement/Image53.jpg", "./image_test_appariement/Image54.jpg"),
        ("./image_test_appariement/Image55.jpg", "./image_test_appariement/Image56.jpg", "./image_test_appariement/Image57.jpg"),
        ("./image_test_appariement/Image58.jpg", "./image_test_appariement/Image59.jpg", "./image_test_appariement/Image60.jpg"),
        ("./image_test_appariement/Image61.jpg", "./image_test_appariement/Image62.jpg", "./image_test_appariement/Image63.jpg"),
        ("./image_test_appariement/Image64.jpg", "./image_test_appariement/Image65.jpg", "./image_test_appariement/Image66.jpg"),
        ("./image_test_appariement/Image67.jpg", "./image_test_appariement/Image68.jpg", "./image_test_appariement/Image69.jpg"),
        ("./image_test_appariement/Image70.jpg", "./image_test_appariement/Image71.jpg", "./image_test_appariement/Image72.jpg"),
        ("./image_test_appariement/Image73.jpg", "./image_test_appariement/Image74.jpg", "./image_test_appariement/Image75.jpg"),
        ("./image_test_appariement/Image76.jpg", "./image_test_appariement/Image77.jpg", "./image_test_appariement/Image78.jpg"),
        ("./image_test_appariement/Image79.jpg", "./image_test_appariement/Image80.jpg", "./image_test_appariement/Image81.jpg"),
        ("./image_test_appariement/Image82.jpg", "./image_test_appariement/Image83.jpg", "./image_test_appariement/Image84.jpg"),
        ("./image_test_appariement/Image85.jpg", "./image_test_appariement/Image86.jpg", "./image_test_appariement/Image87.jpg"),
        (";/image_test_appariement/Image88.jpg", "./image_test_appariement/Image89.jpg", "./image_test_appariement/Image90.jpg"),
    ]

    app = QApplication(sys.argv)
    window = ImageSemanticMatching(tests_image)
    window.show()
    sys.exit(app.exec())