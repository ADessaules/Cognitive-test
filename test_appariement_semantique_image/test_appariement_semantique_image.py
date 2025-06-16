# VERSION ADAPTÉE DU TEST SÉMANTIQUE PAR IMAGES
# Ce script suit la même structure que matching_unknown_faceV1.py


import sys
import os
import random
import time
from datetime import datetime 
import subprocess
import pandas as pd
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QLineEdit, QMessageBox, QComboBox, QGridLayout
)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt, QTimer, QEvent

class WaitingScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("\u00c9cran d'attente")
        self.setGeometry(920, 100, 800, 600)
        layout = QVBoxLayout()
        label = QLabel("Appuyez sur Espace pour d\u00e9marrer le test")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)

class PatientWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Appariement S\u00e9mantique - Patient")
        self.setGeometry(920, 100, 800, 600)
        self.top_label = QLabel()
        self.top_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bottom_layout = QHBoxLayout()
        layout = QVBoxLayout()
        layout.addWidget(self.top_label)
        layout.addLayout(self.bottom_layout)
        self.setLayout(layout)

    def show_triplet(self, top_image_path, options, handlers):
        pixmap_top = QPixmap(top_image_path).scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio)
        self.top_label.setPixmap(pixmap_top)

        for i in reversed(range(self.bottom_layout.count())):
            w = self.bottom_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        for path, handler in zip(options, handlers):
            btn = QPushButton()
            btn.setIcon(QIcon(path))
            btn.setIconSize(pixmap_top.size())
            btn.setFixedSize(220, 220)
            btn.clicked.connect(handler)
            self.bottom_layout.addWidget(btn)

class ImageSemanticMatchingTest(QMainWindow):
    def __init__(self, test_triplets):
        super().__init__()
        self.setWindowTitle("Test Appariement S\u00e9mantique - Images")
        self.setGeometry(100, 100, 1200, 600)
        self.test_triplets = test_triplets
        self.test_name = "matching_images"
        self.timer = QTimer()
        self.timer.timeout.connect(self.advance_by_timer)
        self.session_active = False
        self.init_ui()
        self.installEventFilter(self)

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout()
        left_layout = QVBoxLayout()

        btn_preselection = QPushButton("Aller à la préselection")
        btn_preselection.clicked.connect(self.launch_preselection)
        btn_retour = QPushButton("Retour à l'interface principale")
        btn_retour.clicked.connect(self.retour_interface)
        left_layout.addWidget(btn_preselection)
        left_layout.addWidget(btn_retour)

        self.patient_selector = QComboBox()
        self.patient_selector.addItem("-- Aucun --")
        patients_path = Path(__file__).resolve().parent.parent / "Patients"
        if patients_path.exists():
            for folder in patients_path.iterdir():
                if folder.is_dir():
                    self.patient_selector.addItem(folder.name)

        self.contact_input = QLineEdit()
        self.contact_input.setPlaceholderText("Contacts de stimulation")
        self.intensite_input = QLineEdit()
        self.intensite_input.setPlaceholderText("Intensit\u00e9 (mA)")
        self.duree_input = QLineEdit()
        self.duree_input.setPlaceholderText("Dur\u00e9e (ms)")

        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["Image au clic", "Temps imparti", "Barre espace"])
        self.timer_input = QLineEdit()
        self.timer_input.setPlaceholderText("Temps (en secondes)")
        self.timer_input.setVisible(False)
        self.mode_selector.currentTextChanged.connect(lambda x: self.timer_input.setVisible(x == "Temps imparti"))

        start_btn = QPushButton("Valider et Pr\u00e9parer le test")
        start_btn.clicked.connect(self.prepare_test)
        stop_btn = QPushButton("Arr\u00eater et sauvegarder")
        stop_btn.clicked.connect(self.save_results)

        for w in [QLabel("S\u00e9lectionner un patient :"), self.patient_selector,
                  self.contact_input, self.intensite_input, self.duree_input,
                  QLabel("Mode de test :"), self.mode_selector,
                  self.timer_input, start_btn, stop_btn]:
            left_layout.addWidget(w)

        self.status_label = QLabel("En attente du d\u00e9marrage du test…")
        left_layout.addWidget(self.status_label)

        self.image_layout = QVBoxLayout()
        layout.addLayout(left_layout)
        layout.addLayout(self.image_layout)
        central.setLayout(layout)

    def launch_preselection(self):
        try:
            script_path = Path(__file__).resolve().parent / "preselection_image_sémantique.py"
            subprocess.Popen(["python", str(script_path)])
            print("Exécution du fichier")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible d'ouvrir l'interface de présélection : {e}")


    def init_test_state(self):
        self.current_index = 0
        self.click_times = []
        self.error_indices = []
        self.trial_results = []
        self.nurse_clicks = []
        self.session_start_time = None
        self.start_time = None
        self.session_active = False
        self.name = ""
        self.mode = "click"
        self.timer_duration = 3
        self.space_mode = False
        self.selected_index = None
        self.experimenter_labels = []
        self.stimulus_active = False
        self.stimulus_start_time = None
        self.stimulus_end_time = None  

    def clear_layout(self, layout): # faite pour eviter que les images testé ne s'accumulent sur la page de l'éxaminateur
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget:
                widget.setParent(None)
            elif child_layout:
                self.clear_layout(child_layout)
    def retour_interface(self):
        try:
            import subprocess
            import os
            interface_path = os.path.join(os.path.dirname(__file__), "interface.py")
            subprocess.Popen(["python", interface_path], shell=True)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de lancer l'interface principale :\n{e}")
        finally:
            self.close()

    def prepare_test(self):
        if self.patient_selector.currentText() == "-- Aucun --" or not all([
            self.contact_input.text().strip(),
            self.intensite_input.text().strip(),
            self.duree_input.text().strip()
        ]):
            QMessageBox.warning(self, "Erreur", "Veuillez remplir tous les champs et choisir un patient.")
            return

        if self.mode_selector.currentText() == "Temps imparti" and not self.timer_input.text().isdigit():
            QMessageBox.warning(self, "Erreur", "Veuillez entrer un temps valide en secondes.")
            return

        self.contact = self.contact_input.text().strip()
        self.intensite = self.intensite_input.text().strip()
        self.duree = self.duree_input.text().strip()
        self.mode = self.mode_selector.currentText()
        self.timer_duration = int(self.timer_input.text()) if self.mode == "Temps imparti" else 0

        self.shuffled_triplets = random.sample(self.test_triplets, len(self.test_triplets))
        self.index = 0
        self.session_results = []
        self.session_active = False

        self.patient_window = PatientWindow()
        self.waiting_screen = WaitingScreen()

        # 🆕 Gestion multi-écrans
        screens = QApplication.screens()
        if len(screens) >= 2:
            primary_screen = screens[0]
            secondary_screen = screens[1]
        
            # Interface expérimentateur sur écran principal
            self.move(primary_screen.geometry().topLeft())
            self.showFullScreen()
        
            # Interface patient sur écran secondaire
            self.patient_window.move(secondary_screen.geometry().topLeft())
            self.patient_window.showFullScreen()
        else:
            print("⚠️ Moins de deux écrans détectés. Affichage en mode fenêtré.")
            self.setGeometry(100, 100, 1200, 600)
            self.patient_window.setGeometry(920, 100, 800, 600)
            self.show()
            self.patient_window.show()

        self.init_test_state()
        self.participant_name = self.patient_selector.currentText()
        self.stim_contact = self.contact
        self.stim_intensite = self.intensite
        self.stim_duree = self.duree
        mode_text = self.mode_selector.currentText()
        self.mode = "timer" if mode_text == "Temps imparti" else "click" if mode_text == "Image au clic" else "space"
        self.space_mode = self.mode == "space"

        self.waiting_screen.show()
        self.patient_window.show()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyRelease and event.key() == Qt.Key.Key_Space:
            if not self.session_active and self.waiting_screen.isVisible():
                self.waiting_screen.hide()
                self.session_active = True
                self.show_next_triplet()
            elif self.session_active and self.mode == "Barre espace":
                self.index += 1
                self.show_next_triplet()

        if event.type() == QEvent.Type.KeyRelease:
            print("Touche relâchée :", event.key())

            if event.key() == Qt.Key.Key_S:
                print("✅ Touche S détectée")
                self.lancer_stimulus()
                return True
            elif event.key() == Qt.Key.Key_Space:
                print("Espace détecté")

        return super().eventFilter(obj, event)
    
    def lancer_stimulus(self):
        try:
            duree_ms = int(float(self.duree))
        except ValueError :
            QMessageBox.warning(self, "Erreur", "Durée de stimulation invalide.")
            return
        
        self.stimulus_active = True
        self.stimulus_start_time = time.time()
        self.stimulus_end_time = self.stimulus_start_time + (duree_ms/1000)

        QTimer.singleShot(duree_ms, self.fin_stimulus)
    
    def fin_stimulus(self):
        self.stimulus_active = False
        self.stimulus_start_time = None
        self.stimulus_end_time = None

    def advance_by_timer(self):
        self.index += 1
        self.show_next_triplet()

    def show_next_triplet(self):
        self.clear_layout(self.image_layout)

        if self.index >= len(self.shuffled_triplets):
            self.save_results()
            return

        test_path, correct_path, distractor_path = self.shuffled_triplets[self.index]
        options = [correct_path, distractor_path]
        random.shuffle(options)
        is_correct_map = {opt: os.path.basename(opt) == os.path.basename(correct_path) for opt in options}
        self.start_time = time.time()

        def make_handler(selected_img, btn):
            def handler():
                rt = round(time.time() - self.start_time, 3)
                now = time.time()
                now_datetime = datetime.now()
                elapsed_since_start = now - self.start_time if self.start_time else None # Temps écoulé depuis le début du test
                entry = {
                    "Essai": self.index + 1,
                    "Date": now_datetime.strftime("%Y-%m-%d"),
                    "Heure": now_datetime.strftime("%H:%M:%S"),
                    "Temps total (s)": round(elapsed_since_start, 2),
                    "Temps de réponse (s)": rt,
                    "Stimulation": "active" if self.stimulus_active else "",
                    "Contact stimulation": self.contact,
                    "Intensité (mA)": self.intensite,
                    "Durée (ms)": self.duree,
                    "Mot testé": test_path,
                    "Choix": selected_img,
                    "Correct": is_correct_map[selected_img]
                }
                self.session_results.append(entry)

                for b in buttons:
                    b.setEnabled(False)
                color = "green" if is_correct_map[selected_img] else "red"
                btn.setStyleSheet(f"border: 4px solid {color}; margin: 5px;")
                self.index += 1
                QTimer.singleShot(500, self.show_next_triplet)
            return handler

        buttons = []
        top_label = QLabel()
        top_label.setPixmap(QPixmap(test_path).scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio))
        self.image_layout.addWidget(top_label, alignment=Qt.AlignmentFlag.AlignCenter)

        option_layout = QHBoxLayout()
        handlers = []
        for path in options:
            btn = QPushButton()
            btn.setIcon(QIcon(path))
            btn.setIconSize(top_label.pixmap().size())
            btn.setFixedSize(220, 220)
            handler = make_handler(path, btn)
            btn.clicked.connect(handler)
            option_layout.addWidget(btn)
            buttons.append(btn)
            handlers.append(handler)

        self.image_layout.addLayout(option_layout)
        self.patient_window.show_triplet(test_path, options, handlers)

        if self.mode == "Temps imparti":
            self.timer.start(self.timer_duration * 1000)

    def save_results(self):
        self.timer.stop()
        df = pd.DataFrame(self.session_results)
        if df.empty:
            QMessageBox.information(self, "Fin", "Aucun résultat à enregistrer.")
            return

        now = datetime.now().strftime("%Y_%m_%d_%H%M")
        name = self.patient_selector.currentText()
        print(self.patient_selector.currentText())
        filename = f"{name}_{now}_{self.contact}-{self.intensite}-{self.duree}_{self.test_name}.xlsx"

        patients_root = Path(__file__).resolve().parent.parent / "Patients"
        patient_dir = patients_root / self.participant_name
        patient_dir.mkdir(parents=True, exist_ok=True)  # Crée si manquant
    
        output_path = patient_dir / filename

        df.to_excel(output_path, index=False)

        QMessageBox.information(self, "Fin", f"Test terminé. Résultats enregistrés dans :\n{filename}")
        if self.patient_window:
            self.patient_window.close()
        if self.waiting_screen:
            self.waiting_screen.close()
        self.session_active = False

if __name__ == "__main__":
    base_path = Path(__file__).resolve().parent / "image_test_appariement"
    test_triplets =     [
        (base_path/"Image1.jpg", base_path/"Image2.jpg", base_path/"Image3.jpg"),
        (base_path/"Image4.jpg", base_path/"Image5.jpg", base_path/"Image6.jpg"),
        (base_path/"Image7.jpg", base_path/"Image8.jpg", base_path/"Image9.jpg"),
        (base_path/"Image10.jpg", base_path/"Image11.jpg", base_path/"Image12.jpg"),
        (base_path/"Image13.jpg", base_path/"Image14.jpg", base_path/"Image15.jpg"),
        (base_path/"Image16.jpg", base_path/"Image17.jpg", base_path/"Image18.jpg"),
        (base_path/"Image19.jpg", base_path/"Image20.jpg", base_path/"Image21.jpg"),
        (base_path/"Image22.jpg", base_path/"Image23.jpg", base_path/"Image24.jpg"),
        (base_path/"Image25.jpg", base_path/"Image26.jpg", base_path/"Image27.jpg"),
        (base_path/"Image28.jpg", base_path/"Image29.jpg", base_path/"Image30.jpg"),
        (base_path/"Image31.jpg", base_path/"Image32.jpg", base_path/"Image33.jpg"),
        (base_path/"Image34.jpg", base_path/"Image35.jpg", base_path/"Image36.jpg"),
        (base_path/"Image37.jpg", base_path/"Image38.jpg", base_path/"Image39.jpg"),
        (base_path/"Image40.jpg", base_path/"Image41.jpg", base_path/"Image42.jpg"),
        (base_path/"Image43.jpg", base_path/"Image44.jpg", base_path/"Image45.jpg"),
        (base_path/"Image46.jpg", base_path/"Image47.jpg", base_path/"Image48.jpg"),
        (base_path/"Image49.jpg", base_path/"Image50.jpg", base_path/"Image51.jpg"),
        (base_path/"Image52.jpg", base_path/"Image53.jpg", base_path/"Image54.jpg"),
        (base_path/"Image55.jpg", base_path/"Image56.jpg", base_path/"Image57.jpg"),
        (base_path/"Image58.jpg", base_path/"Image59.jpg", base_path/"Image60.jpg"),
        (base_path/"Image61.jpg", base_path/"Image62.jpg", base_path/"Image63.jpg"),
        (base_path/"Image64.jpg", base_path/"Image65.jpg", base_path/"Image66.jpg"),
        (base_path/"Image67.jpg", base_path/"Image68.jpg", base_path/"Image69.jpg"),
        (base_path/"Image70.jpg", base_path/"Image71.jpg", base_path/"Image72.jpg"),
        (base_path/"Image73.jpg", base_path/"Image74.jpg", base_path/"Image75.jpg"),
        (base_path/"Image76.jpg", base_path/"Image77.jpg", base_path/"Image78.jpg"),
        (base_path/"Image79.jpg", base_path/"Image80.jpg", base_path/"Image81.jpg"),
        (base_path/"Image82.jpg", base_path/"Image83.jpg", base_path/"Image84.jpg"),
        (base_path/"Image85.jpg", base_path/"Image86.jpg", base_path/"Image87.jpg"),
        (base_path/"Image88.jpg", base_path/"Image89.jpg", base_path/"Image90.jpg"),
    ]
    test_triplets = [(str(a), str(b), str(c)) for (a, b, c) in test_triplets]

    app = QApplication(sys.argv)
    window = ImageSemanticMatchingTest(test_triplets)
    window.show()
    sys.exit(app.exec())
