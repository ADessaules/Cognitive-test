from PyQt6.QtWidgets import QApplication
from main_window import MainApp
from database import creer_base

if __name__ == "__main__":
    creer_base()
    app = QApplication([])
    window = MainApp()
    window.show()
    app.exec()
