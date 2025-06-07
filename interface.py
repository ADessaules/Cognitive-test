import sys
import subprocess
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QWidget, QPushButton, QStackedWidget, QListWidget
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cognitive Test")
        self.setGeometry(100, 100, 400, 600)

        self.stack = QStackedWidget()

        self.page_acceuil = self.create_home_page()
        self.page_choix_test = self.create_tests_page()

        self.stack.addWidget(self.page_acceuil)      # Index 0
        self.stack.addWidget(self.page_choix_test)   # Index 1

        self.setCentralWidget(self.stack)

    def create_home_page(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Cognitive Test")
        title.setStyleSheet("font-size: 24px; padding: 15px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_tests = QPushButton("Faire un test cognitif")
        btn_tests.setStyleSheet("font-size: 20px; padding: 15px;")
        btn_tests.clicked.connect(lambda: self.stack.setCurrentIndex(1))

        layout.addWidget(title)
        layout.addWidget(btn_tests)

        page = QWidget()
        page.setLayout(layout)
        return page

    def create_tests_page(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel("Choisissez un test")
        label.setStyleSheet("font-size: 20px; padding: 10px;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.list_tests = QListWidget()
        self.list_tests.addItem("famous_faceV1")

        self.list_tests.itemClicked.connect(self.launch_test)

        btn_back = QPushButton("Retour")
        btn_back.setStyleSheet("font-size: 18px; padding: 10px;")
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        layout.addWidget(label)
        layout.addWidget(self.list_tests)
        layout.addWidget(btn_back)

        page = QWidget()
        page.setLayout(layout)
        return page

    def launch_test(self, item):
        test_name = item.text()
        if test_name == "famous_faceV1":
            try:
                subprocess.Popen(["python", "./famous_faceV1/famous_faceV1.py"])
            except Exception as e:
                print(f"Erreur lors du lancement du test : {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
