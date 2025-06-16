import sys
import os
import random
import subprocess
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
    """
Fenêtre d'attente affichée au patient avant le début du test.

Affiche un message invitant à appuyer sur la barre espace
pour démarrer l’épreuve.
    """
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
    """
Fenêtre affichée sur l'écran secondaire (côté patient).

Elle affiche des boutons avec des noms de célébrités pendant les essais.
Les noms sont disposés horizontalement et sont interactifs.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test en cours - Écran patient")
        self.setGeometry(920, 100, 800, 600)

        self.name_layout = QHBoxLayout()
        self.name_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_layout.setSpacing(50)

        self.outer_layout = QVBoxLayout()
        self.outer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.outer_layout.addLayout(self.name_layout)

        self.setLayout(self.outer_layout)

    def show_names(self, triplet, click_handlers):
        for i in reversed(range(self.name_layout.count())):
            widget = self.name_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        screen = QApplication.primaryScreen().geometry()
        btn_width = screen.width() // 4
        btn_height = screen.height() // 4.5

        for name, handler in zip(triplet, click_handlers):
            button = QPushButton(name)
            button.setFixedSize(int(btn_width), int(btn_height))
            button.setStyleSheet("font-size: 28px;")
            button.clicked.connect(handler)
            self.name_layout.addWidget(button)

class FamousNameTest(QMainWindow):
    """
Fenêtre principale du test de reconnaissance de noms célèbres (pour l’expérimentateur).

Fonctionnalités principales :
- charger les triplets de noms ;
- gérer la configuration du test ;
- afficher les noms à l'écran patient ;
- gérer les clics, les temps de réponse et les sauvegardes.
    """
    def __init__(self):
        """
Initialise la fenêtre, charge les noms depuis un fichier `nom.txt`,
configure les écrans, les patients et les widgets.
Gère le mode double écran si disponible.
        """
        super().__init__()
        self.setWindowTitle("Famous Name Test - Exp\u00e9rimentateur")
        self.setGeometry(100, 100, 1200, 600)

        self.test_name = "famous_name"
        self.names_file = os.path.join(os.path.dirname(__file__), "nom.txt")

        self.all_triplets = []
        with open(self.names_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    names = line.strip("()\n ").split(",")
                    triplet = [n.strip() for n in names]
                    if len(triplet) == 3:
                        self.all_triplets.append(triplet)

        self.current_triplets = []
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
    
        screens = QApplication.screens()
        if len(screens) >= 2:
            primary_screen = screens[0]
            secondary_screen = screens[1]
        
            # Expérimentateur : plein écran sur l'écran principal
            self.move(primary_screen.geometry().topLeft())
            self.showFullScreen()
        
            # Patient : plein écran sur le deuxième écran
            self.patient_window.move(secondary_screen.geometry().topLeft())
            self.patient_window.showFullScreen()
        else:
            print("⚠️ Moins de deux écrans détectés. Utilisation en mode fenêtré.")
            self.setGeometry(100, 100, 1200, 600)
            self.patient_window.setGeometry(920, 100, 800, 600)
            self.show()
            self.patient_window.show()
        
        self.init_ui()
        self.installEventFilter(self)

    def init_test_state(self):
        """
Réinitialise toutes les variables liées à une session de test.

Appelée à chaque démarrage ou redémarrage d’un test.
        """
        self.current_index = 0
        self.click_times = []
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
        self.experimenter_labels = []

    def eventFilter(self, obj, event):
        """
Capture les clics souris pendant une session active,
et enregistre les événements de stimulation (aucun choix).

Permet aussi un suivi du temps même si le patient ne clique pas.
        """
        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.RightButton and obj == self:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                elapsed = round(time.time() - self.session_start_time, 3) if self.session_start_time else ""

                self.nurse_clicks.append({
                    "id_essai": self.current_index + 1,
                    "temps_total_depuis_debut": elapsed,
                    "nom_choisi": "",
                    "correct": "",
                    "temps_reponse": "",
                    "horodatage_stimulation": now,
                    "participant": self.participant_name,
                    "mode": "clic droit",
                    "contact_stimulation": self.stim_contact,
                    "intensité": self.stim_intensite,
                    "durée": self.stim_duree
                })

        return super().eventFilter(obj, event)

    def init_ui(self):
        """
Construit l’interface utilisateur (interface expérimentateur) :
- champs de saisie pour les paramètres de stimulation,
- choix du mode (clic, timer, espace),
- boutons de démarrage et d’arrêt,
- zone miroir des noms affichés pour l’expérimentateur.
        """
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout()

        self.config_layout = QVBoxLayout()

        btn_retour_interface = QPushButton("Retour à l'interface")
        btn_retour_interface.clicked.connect(self.return_to_main_interface)
        self.config_layout.addWidget(btn_retour_interface)

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

    def return_to_main_interface(self):
        """
Ferme la fenêtre actuelle et relance l’interface principale (`interface.py`).
        """
        try:
            self.patient_window.close()
            self.close()
            subprocess.Popen(["python", "interface.py"])
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de retourner à l'interface principale : {e}")

    def prepare_test(self):
        """
Vérifie les champs obligatoires (stimulation, mode, patient), initialise la session.

Charge les triplets de noms, prépare les timers, configure l’écran d’attente.
        """
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
        """
Capture l'appui sur la barre espace :
- démarre la session si elle ne l’est pas encore,
- passe à l’essai suivant en mode "barre espace".
        """
        if event.key() == Qt.Key.Key_Space:
            if not self.session_active and self.waiting_screen.isVisible():
                self.waiting_screen.hide()
                self.session_active = True
                self.current_index = 0
                self.click_times = []
                self.trial_results = []
                self.nurse_clicks = []
    
                # ✅ re-lire timer_input ici (comme dans famous_faceV1)
                if self.mode == "timer":
                    timer_text = self.timer_input.text().strip()
                    if timer_text.isdigit():
                        self.timer_duration = int(timer_text)
                    else:
                        self.timer_duration = 1  # valeur par défaut
    
                self.session_start_time = time.time()
                self.show_triplet()
    
            elif self.session_active and self.mode == "space":
                self.record_result(None, False)
                self.current_index += 1
                self.show_triplet()

    def show_triplet(self):
        """
Affiche un triplet de noms sur l’interface patient et celle de l’expérimentateur.

Les noms sont mélangés. Le nom célèbre (premier du triplet) est comparé
aux clics pour déterminer si la réponse est correcte.
        """
        for layout in (self.name_layout, self.patient_window.name_layout):
            for i in reversed(range(layout.count())):
                widget = layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
    
        self.experimenter_labels.clear()  # 🟢 CORRECTION ICI
    
        if self.current_index >= len(self.current_triplets):
            self.end_session()
            return
    
        triplet = self.current_triplets[self.current_index]
        self.start_time = time.time()
        famous = triplet[0]
        shuffled = triplet[:]
        random.shuffle(shuffled)
        self.flags = [name == famous for name in shuffled]
    
        def make_handler(is_famous, idx):
            return lambda: self.handle_click(is_famous, idx, shuffled)
    
        handlers = [make_handler(flag, i) for i, flag in enumerate(self.flags)]
    
        self.patient_window.show_names(shuffled, handlers)
    
        for name in shuffled:
            label = QLabel(name)
            label.setFixedSize(200, 80)
            label.setStyleSheet("font-size: 14px; border: 2px solid gray; margin: 5px;")
            self.name_layout.addWidget(label)
            self.experimenter_labels.append(label)
    
        if self.mode == "timer":
            self.timer.start(self.timer_duration * 1000)

    def handle_click(self, is_famous, index, names):
        """
Enregistre le clic du patient, calcule le temps de réponse,
évalue la correction et affiche un retour visuel (bordure verte ou rouge).
        """
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
            "nom_choisi": names[index],
            "correct": is_famous,
            "temps_reponse": reaction_time,
            "horodatage_stimulation": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "participant": self.participant_name,
            "mode": self.mode,
            "contact_stimulation": self.stim_contact,
            "intensité": self.stim_intensite,
            "durée": self.stim_duree
        })

        for i, label in enumerate(self.experimenter_labels):
            if i == index:
                color = "green" if self.flags[i] else "red"
                label.setStyleSheet(f"font-size: 18px; border: 4px solid {color}; margin: 5px;")

        self.current_index += 1
        QTimer.singleShot(500, self.show_triplet)

    def handle_timeout(self):
        """
Gère les essais où aucun choix n’est fait dans le temps imparti.

Enregistre une réponse incorrecte et passe à l’essai suivant.
        """
        if not self.session_active:
            return
    
        self.timer.stop()
    
        # Affichage neutre sur l'interface expérimentateur
        for label in self.experimenter_labels:
            label.setStyleSheet("font-size: 18px; border: 4px solid gray; margin: 5px;")
    
        self.record_result(None, False)
        self.current_index += 1
        QTimer.singleShot(100, self.show_triplet)

    def record_result(self, index, is_famous):
        """
Ajoute un essai dans les résultats, qu’il y ait eu réponse ou non.

Utilisé dans `handle_timeout` et dans les essais espace non cliqués.
        """
        now = time.time()
        reaction_time = round(now - self.start_time, 3)
        elapsed = round(now - self.session_start_time, 3)

        name = "aucun" if index is None else self.current_triplets[self.current_index][index]

        self.trial_results.append({
            "id_essai": self.current_index + 1,
            "temps_total_depuis_debut": elapsed,
            "nom_choisi": name,
            "correct": is_famous,
            "temps_reponse": reaction_time,
            "horodatage_stimulation": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "participant": self.participant_name,
            "mode": self.mode,
            "contact_stimulation": self.stim_contact,
            "intensité": self.stim_intensite,
            "durée": self.stim_duree
        })

    def end_session(self):
        """
Termine la session de test :
- arrête le timer,
- cache la fenêtre patient,
- regroupe toutes les données en un fichier Excel,
- sauvegarde les résultats dans le dossier du patient.
        """
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
        prenom_nom = self.participant_name.replace(" ", "").lower()
        filename = f"{prenom_nom}_{timestamp}_{self.stim_contact}-{self.stim_intensite}-{self.stim_duree}_{self.test_name}.xlsx"

        patient_dir = self.patients_dir / self.participant_name
        patient_dir.mkdir(parents=True, exist_ok=True)

        output_path = patient_dir / filename

        try:
            full_df.to_excel(output_path, index=False, engine='openpyxl')
            QMessageBox.information(self, "Fin", f"Test terminé. Fichier sauvegardé dans :\n{output_path}")
        except PermissionError:
            QMessageBox.critical(self, "Erreur", "Le fichier est ouvert ailleurs. Fermez-le puis réessayez.")

if __name__ == "__main__":
    """
Point d’entrée du programme.

Instancie et affiche la fenêtre principale `FamousNameTest`.
Démarre l’application Qt.
    """
    app = QApplication(sys.argv)
    window = FamousNameTest()
    window.show()
    sys.exit(app.exec())
