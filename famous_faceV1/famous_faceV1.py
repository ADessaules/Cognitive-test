import sys
import os
import random
import subprocess
import time
import sqlite3
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QLineEdit, QMessageBox, QComboBox
)
from PyQt6.QtGui import QPixmap
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
        self.image_layout = QHBoxLayout()
        self.setLayout(self.image_layout)

    def show_images(self, triplet, click_handlers):
        for i in reversed(range(self.image_layout.count())):
            widget = self.image_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        for img_path, handler in zip(triplet, click_handlers):
            pixmap = QPixmap(img_path).scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio)
            label = QLabel()
            label.setPixmap(pixmap)
            label.mousePressEvent = handler
            self.image_layout.addWidget(label)

class FamousFaceTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Famous Face Test - Expérimentateur")
        self.setGeometry(100, 100, 1200, 600)

        self.image_folder = os.path.join(os.path.dirname(__file__), "image_famous_faceV1")
        self.test_name = "famous_face"

        all_images = [img for img in os.listdir(self.image_folder) if img.lower().endswith((".png", ".jpg", ".jpeg"))]
        triplet_dict = {}
        for img in all_images:
            try:
                prefix = img.split("_")[1]
                if prefix not in triplet_dict:
                    triplet_dict[prefix] = []
                triplet_dict[prefix].append(img)
            except IndexError:
                continue

        self.selection_images = set()
        if hasattr(self, "selected_patient_name"):
            selection_path = os.path.join("Paul", "Patients", self.selected_patient_name, "selection.txt")
            if os.path.exists(selection_path):
                with open(selection_path, "r", encoding="utf-8") as f:
                    self.selection_images = set([img.strip() for img in f.read().split(",") if img.strip()])
        
        # Construire les triplets filtrés à partir du fichier selection.txt
        self.all_triplets = []
        prefixes = set("_".join(img.strip().split("_")[:2]) for img in self.selection_images)
        
        for prefix in prefixes:
            triplet = [f"{prefix}_{i}.jpg" for i in range(3)]  # .jpg ou .png selon ton cas
            if all(os.path.exists(os.path.join(self.image_folder, img)) for img in triplet):
                self.all_triplets.append(triplet)

        random.shuffle(self.all_triplets)
        self.current_triplets = self.all_triplets[:]

        self.triplet_name_map = {
            f"image_{i+1}_": name for i, name in enumerate([
                "Sophie Marceau", "Tom cruise", "François Hollande", "Brad Pitt", "Patrick Sébastien",
                "Angela Merkel", "Zinédine Zidane", "Georges Bush", "Léonardo Dicaprio", "Nicolas Sarkozy",
                "Marine Le Pen", "Patrick Bruel", "Nagui", "Ségolène Royal", "Jacques Chirac", "Michel Drucker",
                "Jean Reno", "Michel Sardou", "Vladimir Poutine", "Patrick Poivre d’Arvor", "Le Prince Charles",
                "Jean-Jacques Goldman", "Georges Clooney", "Arnold Schwarzenegger", "Gérard Depardieu", "Manuel Valls",
                "Florent Pagny", "Arthur", "François Mitterand", "Johnny Hallyday", "Gad Elmaleh", "Mimie Mathy",
                "Alain Delon", "Renaud", "Jean Dujardin", "Dany Boon", "Vanessa Paradis", "Bill Clinton", "Garou",
                "Muriel Robin", "Laurent Ruquier", "Claire Chazal", "Serge Gainsbourg", "Céline Dion", "Guy Bedos",
                "Bernard Tapie", "Dominique  Strauss Kahn", "Fabrice Luchini", "Charles Aznavour", "Jack Nicholson"
            ])
        }
        self.triplet_map_by_index = {
            f"image_{int(prefix)}_0": sorted(images, key=lambda name: int(name.split("_")[2].split(".")[0]))
            for prefix, images in triplet_dict.items()
            if len(images) == 3
        }

        from pathlib import Path
        self.patients_dir = Path(__file__).resolve().parent.parent / "Patients"
        self.patient_selector = QComboBox()
        self.patient_selector.addItem("-- Aucun --")
        for folder in self.patients_dir.iterdir():
            if folder.is_dir():
                self.patient_selector.addItem(folder.name)
        self.patient_selector.currentTextChanged.connect(self.load_patient_selection)
        self.selected_triplets = []
        self.selection_loaded = False

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
        self.experimenter_labels = []

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress and self.session_active:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.nurse_clicks.append({"evenement": "clic_infirmiere", "horodatage": now})
        return super().eventFilter(obj, event)

    def toggle_timer_input(self):
        self.timer_input.setVisible(self.mode_selector.currentText() == "Temps imparti")

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout()
    
        self.config_layout = QVBoxLayout()  # ✅ Do this first!
    
        # 🆕 Add buttons *after* defining self.config_layout
        btn_preselection = QPushButton("Aller à la présélection")
        btn_preselection.clicked.connect(self.launch_preselection_interface)
        btn_retour_interface = QPushButton("Retour à l'interface")
        btn_retour_interface.clicked.connect(self.return_to_main_interface)
    
        self.config_layout.addWidget(btn_preselection)
        self.config_layout.addWidget(btn_retour_interface)
    
        self.config_layout.addWidget(QLabel("Sélectionner un patient :"))
        self.config_layout.addWidget(self.patient_selector)
    
        # Retire prénom/nom ici si ce n’est plus utile
        self.contact_input = QLineEdit()
        self.contact_input.setPlaceholderText("Contacts de stimulation")
        self.intensite_input = QLineEdit()
        self.intensite_input.setPlaceholderText("Intensité (mA)")
        self.duree_input = QLineEdit()
        self.duree_input.setPlaceholderText("Durée (ms)")
    
        self.mode_label = QLabel("Mode d'affichage des images :")
        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["Image au clic", "Temps imparti", "Barre espace"])
        self.mode_selector.currentTextChanged.connect(self.toggle_timer_input)
    
        self.timer_input = QLineEdit()
        self.timer_input.setPlaceholderText("Temps (en secondes)")
        self.timer_input.setVisible(False)
    
        self.start_btn = QPushButton("Valider et Préparer le test")
        self.start_btn.clicked.connect(self.prepare_test)
    
        self.stop_btn = QPushButton("Arrêter et sauvegarder")
        self.stop_btn.clicked.connect(self.end_session)
    
        for widget in [
            self.contact_input, self.intensite_input, self.duree_input,
            self.mode_label, self.mode_selector, self.timer_input,
            self.start_btn, self.stop_btn
        ]:
            self.config_layout.addWidget(widget)
    
        self.image_layout = QHBoxLayout()
        self.image_panel = QWidget()
        self.image_panel.setLayout(self.image_layout)
    
        self.main_layout.addLayout(self.config_layout)
        self.main_layout.addWidget(self.image_panel)
        self.central_widget.setLayout(self.main_layout)

    def launch_preselection_interface(self):
        try:
            self.patient_window.close()
            self.close()  # ✅ Ferme la fenêtre du test
            subprocess.Popen(["python", "famous_faceV1/main.py"])
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible d'ouvrir l'interface de présélection : {e}")
            
    def return_to_main_interface(self):
        try:
            self.patient_window.close()
            self.close()
            subprocess.Popen(["python", "interface.py"])
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de retourner à l'interface principale : {e}")
        
    def load_patient_selection(self, patient_name):
        if patient_name == "-- Aucun --":
            self.selected_triplets = []
            self.selection_loaded = False
            return
    
        try:
            # Chemin vers le fichier selection.txt
            selection_path = self.patients_dir / patient_name / "selection.txt"
            if not selection_path.exists():
                self.selected_triplets = []
                self.selection_loaded = False
                return
    
            with open(selection_path, "r", encoding="utf-8") as f:
                selections = [s.strip() for s in f.read().strip().split(",") if s.strip()]
    
            # Extraire les préfixes "image_X" depuis "image_X_0"
            prefixes = set("_".join(s.split("_")[:2]) for s in selections)
    
            # Construire les triplets correspondants
            triplets = []
            for prefix in prefixes:
                candidate = []
                for i in range(3):
                    for ext in [".jpg", ".jpeg", ".png"]:
                        path = os.path.join(self.image_folder, f"{prefix}_{i}{ext}")
                        if os.path.exists(path):
                            candidate.append(f"{prefix}_{i}{ext}")
                            break
                if len(candidate) == 3:
                    triplets.append(candidate)
    
            self.selected_triplets = triplets
            self.selection_loaded = True if self.selected_triplets else False
            print(f"✅ {len(self.selected_triplets)} triplets chargés pour le patient '{patient_name}'")
    
        except Exception as e:
            print(f"❌ Erreur chargement sélection patient : {e}")
            self.selected_triplets = []
            self.selection_loaded = False
            
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
            if not timer_text or not timer_text.isdigit() or int(timer_text) <= 0:
                QMessageBox.warning(self, "Erreur", "Veuillez indiquer un temps imparti valide (en secondes).")
                return
            self.timer_duration = int(timer_text)
        else:
            self.timer_duration = 0
    
        self.init_test_state()
        self.participant_name = self.patient_selector.currentText()
        self.stim_contact = contact
        self.stim_intensite = intensite
        self.stim_duree = duree
        self.mode = "timer" if mode_text == "Temps imparti" else "click" if mode_text == "Image au clic" else "space"
        self.space_mode = self.mode == "space"
    
        if self.selection_loaded and self.selected_triplets:
            random.shuffle(self.selected_triplets)
            self.current_triplets = self.selected_triplets[:]
        else:
            QMessageBox.warning(self, "Pas de sélection", "Ce patient n'a pas encore effectué de sélection. Veuillez retourner à la présélection.")
            return
    
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()
        self.waiting_screen.show()
        self.patient_window.show()

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            if not self.session_active and self.waiting_screen.isVisible():
                self.waiting_screen.hide()
                self.session_active = True
                self.current_index = 0
                self.click_times = []
                self.error_indices = []
                self.trial_results = []
                self.nurse_clicks = []
    
                if self.selection_loaded and self.selected_triplets:
                    self.current_triplets = self.selected_triplets[:]
                    random.shuffle(self.current_triplets)
                    print(f"🔁 {len(self.current_triplets)} triplets sélectionnés pour le test.")
                else:
                    print("⚠️ Aucun triplet sélectionné.")
                    QMessageBox.warning(self, "Erreur", "Aucun triplet sélectionné à afficher.")
                    self.end_session()
                    return
    
                self.session_start_time = time.time()
                self.show_triplet()
    
            elif self.session_active and self.mode == "space":
                self.current_index += 1
                self.show_triplet()
                
    def show_triplet(self):
        for layout in (self.image_layout, self.patient_window.image_layout):
            for i in reversed(range(layout.count())):
                widget = layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)

        self.experimenter_labels.clear()

        if self.current_index >= len(self.current_triplets):
            self.end_session()
            return

        images = self.current_triplets[self.current_index]
        prefix = images[0].rsplit("_", 1)[0] + "_"
        self.current_triplet_name = self.triplet_name_map.get(prefix, "Inconnu")

        famous_img = next((img for img in images if "_0." in img), None)
        if not famous_img:
            QMessageBox.critical(self, "Erreur", "Impossible de trouver l'image _0 pour ce triplet.")
            return

        shuffled = images[:]
        random.shuffle(shuffled)
        self.flags = [img == famous_img for img in shuffled]
        self.selected_index = None
        self.start_time = time.time()

        for idx, (img_name, is_famous) in enumerate(zip(shuffled, self.flags)):
            img_path = os.path.join(self.image_folder, img_name)
            pixmap = QPixmap(img_path).scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio)

            label_patient = QLabel()
            label_patient.setPixmap(pixmap)
            label_patient.mousePressEvent = self.make_click_handler(is_famous, idx)
            self.patient_window.image_layout.addWidget(label_patient)

            label_mirror = QLabel()
            label_mirror.setPixmap(pixmap)
            label_mirror.setStyleSheet("border: 2px solid transparent; margin: 5px;")
            self.image_layout.addWidget(label_mirror)
            self.experimenter_labels.append(label_mirror)

        if self.mode == "timer":
            self.timer.start(self.timer_duration * 1000)

    def make_click_handler(self, is_famous, index):
        def handler(event):
            self.selected_index = index
            self.handle_click(is_famous)
        return handler

    def handle_click(self, is_famous):
        if not self.session_active:
            return

        if self.timer.isActive():
            self.timer.stop()

        now = time.time()
        reaction_time = round(now - self.start_time, 3)
        elapsed_since_start = round(now - self.session_start_time, 3)

        self.click_times.append(reaction_time)
        if not is_famous:
            self.error_indices.append(self.current_index)

        self.trial_results.append({
            "id_essai": self.current_index + 1,
            "temps_total_depuis_debut": elapsed_since_start,
            "image_choisie": "famous" if is_famous else "distracteur",
            "correct": is_famous,
            "temps_reponse": reaction_time,
            "horodatage_stimulation": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "triplet_nom": self.current_triplet_name,
            "participant": self.participant_name,
            "mode": self.mode,
            "contact_stimulation": self.stim_contact
        })

        for i, label in enumerate(self.experimenter_labels):
            if i == self.selected_index:
                color = "green" if self.flags[i] else "red"
                label.setStyleSheet(f"border: 4px solid {color}; margin: 5px;")

        self.current_index += 1
        QTimer.singleShot(500, self.show_triplet)

    def handle_timeout(self):
        self.timer.stop()
    
        if not self.session_active:
            return
    
        now = time.time()
        elapsed_since_start = round(now - self.session_start_time, 3)
    
        self.click_times.append(self.timer_duration)
        self.error_indices.append(self.current_index)
    
        self.trial_results.append({
            "id_essai": self.current_index + 1,
            "temps_total_depuis_debut": elapsed_since_start,
            "image_choisie": "aucune",
            "correct": False,
            "temps_reponse": self.timer_duration,
            "horodatage_stimulation": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "triplet_nom": self.current_triplet_name,
            "participant": self.participant_name,
            "mode": self.mode,
            "contact_stimulation": self.stim_contact
        })
    
        self.current_index += 1
    
        # ✅ Ajoute un délai minimal avant de passer au triplet suivant
        QTimer.singleShot(100, self.show_triplet)

    def end_session(self):
        if not self.session_active:
            return
    
        self.session_active = False
        self.timer.stop()  # ⬅️ Ajout important ici
        self.patient_window.hide()

        df_trials = pd.DataFrame(self.trial_results)
        df_clicks = pd.DataFrame(self.nurse_clicks)
        full_df = pd.concat([df_trials, df_clicks], ignore_index=True)

        now = datetime.now()
        timestamp = now.strftime("%Y_%m_%d_%H%M")
        prenom_nom = self.participant_name.replace(" ", "").lower()
        filename = f"{prenom_nom}_{timestamp}_{self.stim_contact}-{self.stim_intensite}-{self.stim_duree}_{self.test_name}.xlsx"
        output_path = os.path.join(os.path.dirname(__file__), filename)
        
        try:
            full_df.to_excel(output_path, index=False, engine='openpyxl')
            QMessageBox.information(self, "Fin", f"Test terminé. Résultats sauvegardés dans {filename}.")
        except PermissionError:
            QMessageBox.critical(self, "Erreur", "Le fichier Excel est ouvert. Fermez-le puis relancez.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FamousFaceTest()
    window.show()
    sys.exit(app.exec())
