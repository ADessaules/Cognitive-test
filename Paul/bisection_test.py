from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QMessageBox, QLabel
from PyQt6.QtGui import QPainter, QPen, QFont
import sqlite3
from PyQt6.QtCore import Qt
import random
from constant import DB_FILE

class BisectionTest(QWidget):
    def __init__(self, patient_id):
        super().__init__()
        self.setWindowTitle("Test de Bisection")
        self.setGeometry(300, 300, 600, 600)
        self.patient_id = patient_id
        self.attempt = 0
        self.total_attempts = 10
        self.setMouseTracking(True)
        self.generate_new_bar()
        self.waiting_for_space = True
        self.waiting_for_input = False
        #self.fake_click_position = None

        self.btn_stop = QPushButton("Stopper le test")
        self.btn_stop.setStyleSheet("font-size: 18px; background-color: red; color: white; padding: 5px;")
        self.btn_stop.clicked.connect(self.stop_test)
        self.btn_stop.setFocusPolicy(Qt.FocusPolicy.NoFocus)


        layout = QVBoxLayout()
        layout.addWidget(self.btn_stop)
        layout.addStretch()  # Pour placer en haut
        self.setLayout(layout)

        self.label_message = QLabel("Appuyez sur ESPACE pour commencer le test", self)
        self.label_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_message.setFont(QFont("Arial", 16))
        self.label_message.setGeometry(50, 250, 500, 100)
        self.label_message.show()


    def generate_new_bar(self):
        dpi = self.logicalDpiX()
        pixels_per_cm = dpi / 2.54
        length = 20 * pixels_per_cm  # 20 cm

        margin = length / 2 + 10
        cx = random.uniform(margin, self.width() - margin)
        cy = random.uniform(margin, self.height() - margin)

        # Bar horizontale
        self.x1, self.y1 = cx - length / 2, cy
        self.x2, self.y2 = cx + length / 2, cy

        self.bar_cx = cx  # stocke le centre pour le calcul
        self.bar_cy = cy

        self.fake_click_position = None
        self.waiting_for_input = True
        self.update()


    def paintEvent(self, event):
        painter = QPainter(self)
        if self.waiting_for_space:
            return  # Ne rien dessiner avant le début

        pen = QPen(Qt.GlobalColor.black, 5)
        painter.setPen(pen)
        painter.drawLine(int(self.x1), int(self.y1), int(self.x2), int(self.y2))

    def mousePressEvent(self, event):
        if not self.waiting_for_input or self.attempt >= self.total_attempts:
            return
        self.record_click(event.position().x(), event.position().y())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            if self.waiting_for_space:
                self.label_message.hide()
                self.waiting_for_space = False
                self.generate_new_bar()
            elif self.waiting_for_input and self.fake_click_position is None:
                # Simule un clic au centre horizontalement (vous pouvez adapter cette stratégie)
                self.fake_click_position = (self.bar_cx, self.bar_cy)
                self.record_click(*self.fake_click_position)


    def record_click(self, clic_x, clic_y):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO bisection (patient_id, x1, y1, x2, y2, clic_x, clic_y)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (self.patient_id, self.x1, self.y1, self.x2, self.y2, clic_x, clic_y))
        conn.commit()
        conn.close()

        self.attempt += 1
        self.waiting_for_input = False

        if self.attempt < self.total_attempts:
            self.generate_new_bar()
        else:
            QMessageBox.information(self, "Terminé", "Test de bisection terminé.")
            self.close()

    def stop_test(self):
        QMessageBox.information(self, "Test interrompu", "Test de bisection arrêté prématurément.")
        self.close()
