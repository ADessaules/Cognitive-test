from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QHBoxLayout
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt
import sys, os

class ImageSemanticMatching(QMainWindow):
    def __init__(self, tests=None):
        super().__init__()

        if tests is None:
            tests = [
                ("C:/Users/lekil/OneDrive/Bureau/Projet_tutoré-Cognitive_test/Cognitive-test1/image_test_appariement/image10.png", "C:/Users/lekil/OneDrive/Bureau/Projet_tutoré-Cognitive_test/Cognitive-test1/image_test_appariement/IMG_5849.jpg", "C:/Users/lekil/OneDrive/Bureau/Projet_tutoré-Cognitive_test/Cognitive-test1/image_test_appariement/image12.png"),
                ("C:/Users/lekil/OneDrive/Bureau/Projet_tutoré-Cognitive_test/Cognitive-test1/image_test_appariement/image4.jpeg", "C:/Users/lekil/OneDrive/Bureau/Projet_tutoré-Cognitive_test/Cognitive-test1/image_test_appariement/image5.jpeg", "C:/Users/lekil/OneDrive/Bureau/Projet_tutoré-Cognitive_test/Cognitive-test1/image_test_appariement/image6.jpeg"),
                ("C:/Users/lekil/OneDrive/Bureau/Projet_tutoré-Cognitive_test/Cognitive-test1/image_test_appariement/image7.jpeg", "C:/Users/lekil/OneDrive/Bureau/Projet_tutoré-Cognitive_test/Cognitive-test1/image_test_appariement/image8.jpeg", "C:/Users/lekil/OneDrive/Bureau/Projet_tutoré-Cognitive_test/Cognitive-test1/image_test_appariement/image9.jpeg"),
                ("C:/Users/lekil/OneDrive/Bureau/Projet_tutoré-Cognitive_test/Cognitive-test1/image_test_appariement/image10.jpeg", "C:/Users/lekil/OneDrive/Bureau/Projet_tutoré-Cognitive_test/Cognitive-test1/image_test_appariement/image11.jpeg", "C:/Users/lekil/OneDrive/Bureau/Projet_tutoré-Cognitive_test/Cognitive-test1/image_test_appariement/image12.jpeg")
            ]

        self.tests = tests
        self.current_index = 0
        self.responses = []

        self.setWindowTitle("Test d'appariement sémantique - Images")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.image_test_label = QLabel()
        self.image_test_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.choice_layout = QHBoxLayout()
        self.button_choice_1 = QPushButton()
        self.button_choice_2 = QPushButton()

        self.button_choice_1.setFixedSize(300, 300)
        self.button_choice_2.setFixedSize(300, 300)

        self.choice_layout.addWidget(self.button_choice_1)
        self.choice_layout.addWidget(self.button_choice_2)

        self.layout.addWidget(self.image_test_label)
        self.layout.addLayout(self.choice_layout)

        # 🛠️ LIGNE MANQUANTE :
        self.central_widget.setLayout(self.layout)

        self.button_choice_1.clicked.connect(lambda: self.record_response(0))
        self.button_choice_2.clicked.connect(lambda: self.record_response(1))

        self.load_next_test()

    def load_next_test(self):
        if self.current_index >= len(self.tests):
            self.end_test()
            return

        test_image_path, choice1_path, choice2_path = self.tests[self.current_index]

        print("Test image:", test_image_path)
        print("Choix 1:", choice1_path)
        print("Choix 2:", choice2_path)


        if not os.path.exists(test_image_path):
            print(f"[ERREUR] Image test manquante : {test_image_path}")
        if not os.path.exists(choice1_path):
            print(f"[ERREUR] Image 1 manquante : {choice1_path}")
        if not os.path.exists(choice2_path):
            print(f"[ERREUR] Image 2 manquante : {choice2_path}")

        self.image_test_label.setPixmap(QPixmap(test_image_path).scaledToHeight(200))

        pixmap1 = QPixmap(choice1_path).scaled(280, 280, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        pixmap2 = QPixmap(choice2_path).scaled(280, 280, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        print(pixmap1.isNull(), pixmap2.isNull())

        self.button_choice_1.setIcon(QIcon(pixmap1))
        self.button_choice_1.setIconSize(pixmap1.size())

        self.button_choice_2.setIcon(QIcon(pixmap2))
        self.button_choice_2.setIconSize(pixmap2.size())

    def record_response(self, choice_index):
        self.responses.append({
            "test": self.tests[self.current_index],
            "selected": self.tests[self.current_index][choice_index + 1]
        })
        self.current_index += 1
        self.load_next_test()

    def end_test(self):
        print("Test terminé !")
        for i, response in enumerate(self.responses):
            print(f"Item {i + 1} : {response['test'][0]} => {response['selected']}")
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageSemanticMatching()
    window.show()
    sys.exit(app.exec())
