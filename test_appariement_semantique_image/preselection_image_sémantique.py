import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QDialog, QLabel, QVBoxLayout, QScrollArea,
    QWidget, QGridLayout, QPushButton, QMessageBox
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

IMAGE_DIR = "./image_test_appariement"
TRIPLETS = [
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
        ("./image_test_appariement/Image88.jpg", "./image_test_appariement/Image89.jpg", "./image_test_appariement/Image90.jpg"),
    ]

class SelectionImages(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sélection des images")
        self.setGeometry(100, 100, 900, 700)

        self.selections = {}
        self.layout = QVBoxLayout()

        scroll = QScrollArea()
        scroll_widget = QWidget()
        self.grid_layout = QGridLayout()
        scroll_widget.setLayout(self.grid_layout)
        scroll.setWidgetResizable(True)
        scroll.setWidget(scroll_widget)
        self.layout.addWidget(scroll)

        self.btn_valider = QPushButton("Valider la sélection")
        self.btn_valider.clicked.connect(self.valider_selection)
        self.layout.addWidget(self.btn_valider)

        self.setLayout(self.layout)
        self.afficher_images()

    def afficher_images(self):
        images = sorted(set(img for triplet in TRIPLETS for img in triplet))
        row = col = 0
        for img_name in images:
            path = os.path.join(IMAGE_DIR, img_name)
            label = QLabel()
            pixmap = QPixmap(path).scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio)
            label.setPixmap(pixmap)
            label.setFixedSize(130, 130)
            label.setStyleSheet("border: 2px solid green;")
            label.mousePressEvent = self.generer_toggle_handler(label, img_name)
            self.grid_layout.addWidget(label, row, col)
            self.selections[label] = {"selected": True, "path": img_name}
            col += 1
            if col >= 5:
                col = 0
                row += 1

    def generer_toggle_handler(self, label, img_name):
        def handler(event):
            current = self.selections[label]
            current["selected"] = not current["selected"]
            label.setStyleSheet("border: 2px solid green;" if current["selected"] else "border: 2px solid gray;")
        return handler

    def valider_selection(self):
        selected = [info["path"] for info in self.selections.values() if info["selected"]]
        os.makedirs("Patients", exist_ok=True)
        with open("Patients/selection_images.txt", "w", encoding="utf-8") as f:
            f.write(",".join(selected))
        QMessageBox.information(self, "Enregistré", "Sélection sauvegardée.")
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SelectionImages()
    window.show()
    sys.exit(app.exec())