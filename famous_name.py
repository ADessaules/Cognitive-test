import sys
import os
import random
import time
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QLineEdit, QMessageBox, QComboBox
)
from PyQt6.QtCore import QTimer, Qt, QEvent
import pandas as pd

class WaitingScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Écran d'attente")
        self.setGeometry(920, 100, 800, 600)
        layout = QVBoxLayout()
        label = QLabel("Appuyez sur Espace pour démarrer le test")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)

class PatientWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test en cours - Écran patient")
        self.setGeometry(920, 100, 800, 600)
        self.name_layout = QHBoxLayout()
        self.setLayout(self.name_layout)

    def show_names(self, triplet, click_handlers):
        for i in reversed(range(self.name_layout.count())):
            widget = self.name_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        for name, handler in zip(triplet, click_handlers):
            button = QPushButton(name)
            button.setFixedSize(250, 100)
            button.setStyleSheet("font-size: 20px;")
            button.clicked.connect(handler)
            self.name_layout.addWidget(button)

class FamousNameTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Famous Name Test - Expérimentateur")
        self.setGeometry(100, 100, 1200, 600)

        self.test_name = "famous_name"
        self.names_file = os.path.join(os.path.dirname(__file__), "nom.txt")

        self.all_triplets = []
        with open(self.names_file, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
            for line in lines:
                triplet = [name.strip() for name in line.split(",") if name.strip()]
                if len(triplet) == 3:
                    self.all_triplets.append(triplet)

        random.shuffle(self.all_triplets)
        self.current_triplets = self.all_triplets[:]

        self.patients_dir = Path(__file__).resolve().parent.parent / "Patients"
        self.patient_selector = QComboBox()
        self.patient_selector.addItem("-- Aucun --")
        for folder in self.patients_dir.iterdir():
            if folder.is_dir():
                self.patient_selector.addItem(folder.name)

        self.init_test_state()
        self.timer = QTimer()
        self.timer.timeout.connect(self.handle_timeout)

        self.patient_window = PatientWindow()
        self.waiting_screen = WaitingScreen()
        self.init_ui()
        self.installEventFilter(self)
        self.patient_window.show()

    def init_test_state(self):
        self.current_index = 0
        self.click_times = []
        self.error_indices = []
        self.trial_results = []
        self.nurse_clicks = []
        self.session_start_time = None
        self.start_time = None
        self.session_active = False
        self.participant_name = ""
        self.mode = "click"
        self.timer_duration = 3
        self.space_mode = False
        self.selected_index = None

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress and self.session_active:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.nurse_clicks.append({"evenement": "clic_infirmiere", "horodatage": now})
        return super().eventFilter(obj, event)

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout()

        self.config_layout = QVBoxLayout()

        self.config_layout.addWidget(QLabel("Sélectionner un patient :"))
        self.config_layout.addWidget(self.patient_selector)

        self.contact_input = QLineEdit()
        self.contact_input.setPlaceholderText("Contacts de stimulation")
        self.intensite_input = QLineEdit()
        self.intensite_input.setPlaceholderText("Intensité (mA)")
        self.duree_input = QLineEdit()
        self.duree_input.setPlaceholderText("Durée (ms)")

        self.mode_label = QLabel("Mode d'affichage :")
        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["Nom au clic", "Temps imparti", "Barre espace"])
        self.mode_selector.currentTextChanged.connect(lambda text: self.timer_input.setVisible(text == "Temps imparti"))

        self.timer_input = QLineEdit()
        self.timer_input.setPlaceholderText("Temps (en secondes)")
        self.timer_input.setVisible(False)

        self.start_btn = QPushButton("Valider et Préparer le test")
        self.start_btn.clicked.connect(self.prepare_test)

        self.stop_btn = QPushButton("Arrêter et sauvegarder")
        self.stop_btn.clicked.connect(self.end_session)

        for widget in [self.contact_input, self.intensite_input, self.duree_input,
                       self.mode_label, self.mode_selector, self.timer_input,
                       self.start_btn, self.stop_btn]:
            self.config_layout.addWidget(widget)

        self.name_layout = QHBoxLayout()
        self.name_panel = QWidget()
        self.name_panel.setLayout(self.name_layout)

        self.main_layout.addLayout(self.config_layout)
        self.main_layout.addWidget(self.name_panel)
        self.central_widget.setLayout(self.main_layout)

    def prepare_test(self):
        contact = self.contact_input.text().strip()
        intensite = self.intensite_input.text().strip()
        duree = self.duree_input.text().strip()
        mode_text = self.mode_selector.currentText()
        timer_text = self.timer_input.text().strip()

        if self.patient_selector.currentText() == "-- Aucun --":
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un patient.")
            return

        if not contact or not intensite or not duree:
            QMessageBox.warning(self, "Erreur", "Veuillez remplir tous les champs de stimulation.")
            return

        if mode_text == "Temps imparti":
            if not timer_text.isdigit() or int(timer_text) <= 0:
                QMessageBox.warning(self, "Erreur", "Veuillez indiquer un temps imparti valide.")
                return
            self.timer_duration = int(timer_text)
        else:
            self.timer_duration = 0

        self.init_test_state()
        self.participant_name = self.patient_selector.currentText()
        self.stim_contact = contact
        self.stim_intensite = intensite
        self.stim_duree = duree
        self.mode = "timer" if mode_text == "Temps imparti" else "click" if mode_text == "Nom au clic" else "space"
        self.space_mode = self.mode == "space"

        self.current_triplets = self.all_triplets[:]
        random.shuffle(self.current_triplets)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()
        self.waiting_screen.show()
        self.patient_window.show()

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            if not self.session_active and self.waiting_screen.isVisible():
                self.waiting_screen.hide()
                self.session_active = True
                self.session_start_time = time.time()
                self.current_index = 0
                self.click_times = []
                self.trial_results = []
                self.nurse_clicks = []
                self.show_triplet()

            elif self.session_active and self.mode == "space":
                self.record_result(None, False)
                self.current_index += 1
                self.show_triplet()

    def show_triplet(self):
        for i in reversed(range(self.name_layout.count())):
            widget = self.name_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        if self.current_index >= len(self.current_triplets):
            self.end_session()
            return

        triplet = self.current_triplets[self.current_index]
        self.current_triplet = triplet
        self.start_time = time.time()
        self.selected_index = None
        self.flags = [i == 0 for i in range(3)]  # famous est toujours en 1er dans nom.txt

        shuffled = list(zip(triplet, self.flags))
        random.shuffle(shuffled)

        def make_handler(is_famous, index):
            return lambda: self.record_result(index, is_famous)

        for i, (name, is_famous) in enumerate(shuffled):
            button = QPushButton(name)
            button.setFixedSize(250, 100)
            button.setStyleSheet("font-size: 18px;")
            button.clicked.connect(make_handler(is_famous, i))
            self.name_layout.addWidget(button)

        self.flags = [is_famous for name, is_famous in shuffled]

        if self.mode == "timer":
            self.timer.start(self.timer_duration * 1000)

    def record_result(self, index, is_famous):
        if not self.session_active:
            return

        if self.timer.isActive():
            self.timer.stop()

        now = time.time()
        reaction_time = round(now - self.start_time, 3)
        elapsed = round(now - self.session_start_time, 3)

        self.trial_results.append({
            "id_essai": self.current_index + 1,
            "temps_total_depuis_debut": elapsed,
            "nom_choisi": self.current_triplet[index] if index is not None else "aucun",
            "correct": is_famous,
            "temps_reponse": reaction_time,
            "horodatage_stimulation": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "participant": self.participant_name,
            "mode": self.mode,
            "contact_stimulation": self.stim_contact
        })

        self.current_index += 1
        QTimer.singleShot(300, self.show_triplet)

    def handle_timeout(self):
        if not self.session_active:
            return
        self.record_result(None, False)

    def end_session(self):
        if not self.session_active:
            return

        self.session_active = False
        self.timer.stop()
        self.patient_window.hide()

        df_trials = pd.DataFrame(self.trial_results)
        df_clicks = pd.DataFrame(self.nurse_clicks)
        full_df = pd.concat([df_trials, df_clicks], ignore_index=True)

        if full_df.empty:
            QMessageBox.information(self, "Info", "Aucune donnée à sauvegarder.")
            return

        now = datetime.now()
        timestamp = now.strftime("%Y_%m_%d_%H%M")
        filename = f"{self.participant_name}_{timestamp}_{self.stim_contact}-{self.stim_intensite}-{self.stim_duree}_{self.test_name}.xlsx"

        patient_dir = self.patients_dir / self.participant_name
        patient_dir.mkdir(parents=True, exist_ok=True)

        output_path = patient_dir / filename

        try:
            full_df.to_excel(output_path, index=False)
            QMessageBox.information(self, "Fin", f"Test terminé. Fichier sauvegardé dans :\n{output_path}")
        except PermissionError:
            QMessageBox.critical(self, "Erreur", "Le fichier est ouvert ailleurs. Fermez-le puis réessayez.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FamousNameTest()
    window.show()
    sys.exit(app.exec())
