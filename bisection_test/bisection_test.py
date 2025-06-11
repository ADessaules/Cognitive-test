from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QMessageBox, QLabel, QApplication, QHBoxLayout, QComboBox, QLineEdit, QGroupBox, QFormLayout
from PyQt6.QtGui import QPainter, QPen
from PyQt6.QtCore import Qt, QTimer
import sqlite3
import random
import time
import pandas as pd
from datetime import datetime
import os
import subprocess
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from constant import DB_FILE, DOSSIER_PATIENTS

class BisectionTest(QWidget):
    def __init__(self, patient_id, screen_patient, screen_experimenter):
        super().__init__()

        # Sauvegarde des écrans pour le patient et l'expérimentateur
        self.screen_patient = screen_patient
        self.screen_experimenter = screen_experimenter
        self.setWindowTitle("Contrôle du Test de Bisection")
        self.patient_id = patient_id    # ID du patient concerné
        self.attempt = 0                # Compteur d’essais effectués
        self.total_attempts = 10        # Nombre total d’essais à effectuer
        self.trial_data = []            # Liste qui stockera les résultats de chaque essai
        self.stimulation_active = False # État de la stimulation (active ou non)

        self.start_time = None          # Heure de début de la session
        self.trial_start_time = None    # Heure de début d’un essai

        self.setGeometry(screen_experimenter.geometry())
        self.move(screen_experimenter.geometry().topLeft())

        # Boutons principaux
        self.btn_start = QPushButton("Démarrer le test")
        self.btn_stop = QPushButton("Arrêter et sauvegarder")

        # Bouton pour activer la stimulation électrique
        self.btn_toggle_stimulation = QPushButton("Activer la stimulation")
        self.btn_toggle_stimulation.setFixedHeight(60)
        self.btn_toggle_stimulation.setStyleSheet("font-size: 18px;")

        # Connexion des signaux
        self.btn_start.clicked.connect(self.start_test) # Action quand on clique sur "Démarrer"
        self.btn_stop.clicked.connect(self.stop_test)   # Action quand on clique sur "Arrêter"
        self.btn_toggle_stimulation.clicked.connect(self.toggle_stimulation) # Activer/désactiver stimulation

        self.label_stimulation = QLabel("Stimulation: inactive")
        self.label_stimulation.setStyleSheet("font-size: 16px; color: blue;") 

        self.preview = PreviewWidget()

        layout = QVBoxLayout()

        # Sélection du patient
        self.patient_selector = QComboBox() # Menu déroulant pour choisir un patient
        self.populate_patient_list()        # Remplir la liste avec les patients depuis la BDD
        layout.addWidget(QLabel("Sélectionnez un patient :"))
        layout.addWidget(self.patient_selector)

        # Section Stimulation
        stimulation_group = QGroupBox("Paramètres de stimulation :")
        stimulation_layout = QFormLayout()
        self.input_contacts = QLineEdit()
        self.input_intensity = QLineEdit()
        self.input_duration = QLineEdit()
        stimulation_layout.addRow("Contacts de stimulation", self.input_contacts)
        stimulation_layout.addRow("Intensité (mA)", self.input_intensity)
        stimulation_layout.addRow("Durée (ms)", self.input_duration)
        stimulation_group.setLayout(stimulation_layout)
        layout.addWidget(stimulation_group)

        # Section Contrôle Test
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.btn_start)
        controls_layout.addWidget(self.btn_stop)
        layout.addLayout(controls_layout)

        # Section Stimulation active/inactive
        stimulation_state_layout = QHBoxLayout()
        stimulation_state_layout.addWidget(self.btn_toggle_stimulation)
        stimulation_state_layout.addWidget(self.label_stimulation)
        layout.addLayout(stimulation_state_layout)

        # Section Preview
        hbox = QHBoxLayout()
        hbox.addStretch()
        hbox.addWidget(self.preview)
        hbox.addStretch()
        layout.addLayout(hbox)

        # Section Validation
        bottom_buttons_layout = QHBoxLayout()
        bottom_buttons_layout.addWidget(self.btn_start)
        bottom_buttons_layout.addWidget(self.btn_stop)
        layout.addLayout(bottom_buttons_layout)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)

        self.setLayout(layout)

    def toggle_stimulation(self):
        """
        Active la stimulation si elle est actuellement inactive.
        Lit la durée indiquée dans l'interface utilisateur.
        Lance un minuteur pour désactiver automatiquement la stimulation après cette durée.
        """
        if not self.stimulation_active:
            try:  # Tente de lire et convertir la durée de stimulation saisie par l’utilisateur
                duration = int(self.input_duration.text())
            except Exception as e:
                # En cas d'erreur, afficher l'erreur et mettre une durée par défaut
                print(f"Erreur de lecture de durée : {e}")
                duration = 0

            # Active la stimulation
            self.stimulation_active = True
            self.update_stimulus_display(True)

            # Enregistre l'activation de la stimulation
            self.record_stimulation_activation()

            # Lance un timer qui appellera la fonction deactivate_stimulation après "duration" ms
            QTimer.singleShot(duration, self.deactivate_stimulation)

    def deactivate_stimulation(self):
        # Désactive la stimulation et met à jour l'affichage de l'interface.
        self.stimulation_active = False
        self.update_stimulus_display(False)

    def update_stimulus_display(self, active: bool):
        """
        Met à jour le texte du bouton et du label d'information
        selon que la stimulation soit active ou non.
        """
        if active:
            self.btn_toggle_stimulation.setText("Stimulation en cours…")
            self.label_stimulation.setText("Stimulation activée !")
        else:
            self.btn_toggle_stimulation.setText("Activer la stimulation")
            self.label_stimulation.setText("Stimulation désactivée.")

    def start_test(self):
        """
        Démarre le test après avoir vérifié qu’un patient est sélectionné.
        Initialise la fenêtre pour le patient et lance le premier essai.
        """
        selected_id = self.patient_selector.currentData()  # Récupère l’ID du patient sélectionné
        if selected_id is None:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un patient avant de démarrer le test.")
            return

        # Met à jour l'ID du patient dans l'instance actuelle
        self.patient_id = selected_id

        # Désactive la sélection de patient et le bouton de démarrage pour éviter relance multiple
        self.patient_selector.setEnabled(False)
        self.btn_start.setEnabled(False)

        # Créer et afficher la fenêtre patient maintenant que l'ID est choisi
        self.patient_window = PatientWindow(self)
        self.patient_window.setGeometry(self.screen_patient.geometry())
        self.patient_window.move(self.screen_patient.geometry().topLeft())
        self.patient_window.show()
        self.patient_window.setFocus()
        self.patient_window.setMouseTracking(True)

        self.start_trial()

    def start_trial(self):
        """
        Démarre un nouvel essai du test :
        - Stocke le temps de départ
        - Génére une nouvelle barre dans la fenêtre du patient
        - Met à jour l’aperçu de l’expérimentateur
        """
        if self.attempt == 0:
            self.start_time = time.time()       # Si c'est le tout premier essai, on stocke le temps de départ de la session
        self.trial_start_time = time.time()     # Stocke le temps de début de cet essai
        self.patient_window.generate_new_bar()  # Génère une nouvelle barre aléatoire dans la fenêtre du patient

        # Met à jour l'aperçu pour l’expérimentateur avec les coordonnées de la barre du patient
        self.preview.update_bar(
            self.patient_window.x1, # Coordonnée x du début de la barre
            self.patient_window.y1, # Coordonnée y du début de la barre
            self.patient_window.x2, # Coordonnée x de fin
            self.patient_window.y2, # Coordonnée y de fin
            self.patient_window.width(), # Largeur de la fenêtre
            self.patient_window.height() # Hauteur de la fenêtre
        )

    def populate_patient_list(self):
        # Se connecte à la base de données pour récupérer les patients enregistrés
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, nom FROM patients")
        self.patients = cursor.fetchall() # Liste de tuples (id, nom)
        conn.close()

        # Ajoute une option par défaut dans la liste déroulante
        self.patient_selector.addItem("Sélectionnez un patient", None)

        # Pour chaque patient trouvé, ajoute son nom dans le menu déroulant et associe son ID
        for pid, name in self.patients:
            self.patient_selector.addItem(name, pid)

    def record_click(self, clic_x, clic_y):

        # Récupère le temps actuel
        now = time.time()
        response_time = now - self.trial_start_time # Temps de réponse du patient
        elapsed_since_start = now - self.start_time if self.start_time else None # Temps écoulé depuis le début du test

        # Si clic détecté, on calcule l’écart entre le clic et le centre de la barre (en cm)
        if clic_x is not None:
            ecart_cm = (clic_x - self.patient_window.bar_cx) / (self.logicalDpiX() / 2.54)
            reponse = round(ecart_cm, 2)
        else:
            reponse = "non fait" # Cas où aucun clic n’est enregistré

        # Récupère la date et l’heure actuelle
        now_datetime = datetime.now()

        # Si la stimulation était active, on enregistre un essai de type "stimulation"
        if self.stimulation_active:
            trial_entry = {
                "Essai": "",
                "Date": "",
                "Heure": "",
                "Temps total (s)": "",
                "Réponse (écart en cm)": "",
                "Temps de réponse (s)": "",
                "x1": "",
                "y1": "",
                "x2": "",
                "y2": "",
                "Centre X (cx)": "",
                "Centre Y (cy)": "",
                "Clic X": "",
                "Clic Y": "",
                "Stimulation": "active",
                "Contact stimulation": self.input_contacts.text(),
                "Intensité (mA)": self.input_intensity.text(),
                "Durée (ms)": self.input_duration.text()
            }
        else:
            # Sinon, on enregistre un essai classique (avec les données du clic)
            trial_entry = {
            "Essai": self.attempt + 1,
            "Date": now_datetime.strftime("%Y-%m-%d"),
            "Heure": now_datetime.strftime("%H:%M:%S"),
            "Temps total (s)": round(elapsed_since_start, 2),
            "Réponse (écart en cm)": reponse,
            "Temps de réponse (s)": round(response_time, 2),
            "x1": round(self.patient_window.x1, 2),
            "y1": round(self.patient_window.y1, 2),
            "x2": round(self.patient_window.x2, 2),
            "y2": round(self.patient_window.y2, 2),
            "Centre X (cx)": round(self.patient_window.bar_cx, 2),
            "Centre Y (cy)": round(self.patient_window.bar_cy, 2),
            "Clic X": round(clic_x, 2) if clic_x is not None else "NA",
            "Clic Y": round(clic_y, 2) if clic_y is not None else "NA",
            "Stimulation": "",
            "Contact stimulation": "",
            "Intensité (mA)": "",
            "Durée (ms)": ""
        }

        # Ajoute les données de cet essai à la liste des essais du test
        self.trial_data.append(trial_entry)

        # Enregistre certaines infos dans la base de données (coordonnées + clic)
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO bisection (patient_id, x1, y1, x2, y2, clic_x, clic_y)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (self.patient_id, self.patient_window.x1, self.patient_window.y1,
             self.patient_window.x2, self.patient_window.y2, clic_x, clic_y))
        conn.commit()
        conn.close()

        # Passe à l’essai suivant, ou termine si le nombre d’essais est atteint
        self.attempt += 1
        if self.attempt < self.total_attempts:
            QTimer.singleShot(500, self.start_trial) # Attend 500 ms avant d'enchaîner
        else:
            QMessageBox.information(self, "Terminé", "Test de bisection terminé.")
            self.export_results() # Exporte les résultats
            self.patient_window.close() # Ferme la fenêtre du patient
            self.close() # Ferme la fenêtre de contrôle
            subprocess.Popen(["python", "interface.py"]) # Relance l'interface principale

    def stop_test(self):
        # Affiche une boîte de dialogue informant que le test a été interrompu manuellement
        QMessageBox.information(self, "Test interrompu", "Test de bisection arrêté prématurément.")
        self.export_results() # Sauvegarde les données déjà recueillies
        self.patient_window.close() # Ferme la fenêtre côté patient
        self.close() # Ferme la fenêtre de contrôle
        subprocess.Popen(["python", "interface.py"]) # Retour à l’interface principale

    def record_stimulation_activation(self):
        # Ajoute une entrée "vide" indiquant qu'une stimulation a été activée
        # sans essai associé (utile pour suivre les périodes de stimulation)
        self.trial_data.append({
            "Essai": "",
            "Date": "",
            "Heure": "",
            "Temps total (s)": "",
            "Réponse (écart en cm)": "",
            "Temps de réponse (s)": "",
            "x1": "",
            "y1": "",
            "x2": "",
            "y2": "",
            "Centre X (cx)": "",
            "Centre Y (cy)": "",
            "Clic X": "",
            "Clic Y": "",
            "Stimulation": "active",
            "Contact stimulation": self.input_contacts.text(),
            "Intensité (mA)": self.input_intensity.text(),
            "Durée (ms)": self.input_duration.text()
        })

    def export_results(self):
        # Si aucune donnée de test n'est disponible, on quitte la fonction
        if not self.trial_data:
            return

        patient_name = self.get_patient_name() # Récupère le nom du patient depuis la base de données
        date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") # Génère une chaîne de date/heure actuelle pour nommer le fichier
        parametres = "20cm"
        nom_test = "Bisection"
        nom_fichier = f"{patient_name}_{date_str}_{parametres}_{nom_test}.xlsx"

        dossier_patient = os.path.join(DOSSIER_PATIENTS, patient_name)
        os.makedirs(dossier_patient, exist_ok=True)

        df = pd.DataFrame(self.trial_data)
        chemin = os.path.join(dossier_patient, nom_fichier)
        df.to_excel(chemin, index=False)

    def get_patient_name(self):
        # Connexion à la base de données SQLite
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Requête SQL pour obtenir le nom du patient à partir de son ID
        cursor.execute("SELECT nom FROM patients WHERE id = ?", (self.patient_id,))
        result = cursor.fetchone()
        conn.close() # Fermeture de la connexion à la base
        return result[0] if result else f"patient_{self.patient_id}"
    
    def keyPressEvent(self, event):
        # Si l'utilisateur appuie sur la touche "S", bascule l'état de stimulation
        if event.key() == Qt.Key.Key_S:
            self.toggle_stimulation()

    def mousePressEvent(self, event):
        # Si l'utilisateur clique avec le bouton droit de la souris, bascule l'état de stimulation
        if event.button() == Qt.MouseButton.RightButton:
            self.toggle_stimulation()

class PatientWindow(QWidget): #interface du patient
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app # Référence à l'application principale
        self.waiting_for_input = True # Attend une interaction utilisateur
        self.bar_cx = 0
        self.bar_cy = 0

    def generate_new_bar(self):
        # Calcule la taille en pixels de 1 cm (selon le DPI de l'écran)
        dpi = self.logicalDpiX()
        pixels_per_cm = dpi / 2.54

        # Longueur de la barre en pixels (20 cm)
        length = 20 * pixels_per_cm

        # Marge pour éviter que la barre dépasse les bords
        margin = length / 2 + 10

        # Position centrale aléatoire dans les limites de la fenêtre
        cx = random.uniform(margin, self.width() - margin)
        cy = random.uniform(margin, self.height() - margin)

        # Position centrale aléatoire dans les limites de la fenêtre
        self.x1 = cx - length / 2
        self.y1 = cy
        self.x2 = cx + length / 2
        self.y2 = cy

        # Stocke le centre
        self.bar_cx = cx
        self.bar_cy = cy

        # Active l'attente d'une interaction utilisateur
        self.waiting_for_input = True

        # Redessine la fenêtre
        self.update()

    def paintEvent(self, event):
        # Si la barre n'existe pas ou si on n'attend pas d'interaction, ne rien dessiner
        if not hasattr(self, 'x1') or not self.waiting_for_input:
            return
        
        # Crée un pinceau pour dessiner
        painter = QPainter(self)

        # Crée un trait noir de largeur 5
        pen = QPen(Qt.GlobalColor.black, 5)
        painter.setPen(pen)

        # Dessine la ligne horizontale représentant la barre
        painter.drawLine(int(self.x1), int(self.y1), int(self.x2), int(self.y2))

    def mousePressEvent(self, event):
        # Si on n'attend pas de clic, on ignore
        if not self.waiting_for_input:
            return
        
        # Désactive l'attente d'entrée
        self.waiting_for_input = False

        # Envoie les coordonnées du clic à l'application principale
        self.main_app.record_click(event.position().x(), event.position().y())

class PreviewWidget(QWidget): # Affiche une version miniature de la barre dans un cadre
    def __init__(self, parent=None):
        super().__init__(parent)

        # Taille du widget
        self.setFixedSize(300, 300)

        # Coordonnées initiales de la barre (non définies)
        self.x1 = self.y1 = self.x2 = self.y2 = None

        # Dimensions du cadre de prévisualisation (zone de dessin)
        self.frame_width = 280
        self.frame_height = 160

        # Position du cadre centré dans le widget
        self.frame_x = (self.width() - self.frame_width) // 2
        self.frame_y = 20

    def update_bar(self, x1, y1, x2, y2, width_real, height_real):
        # Calcule les facteurs d'échelle pour réduire les coordonnées à la taille du cadre
        scale_x = self.frame_width / width_real
        scale_y = self.frame_height / height_real

        # Met à l’échelle les coordonnées de la barre
        self.x1 = x1 * scale_x
        self.y1 = y1 * scale_y
        self.x2 = x2 * scale_x
        self.y2 = y2 * scale_y

        # Redessine le widget
        self.update()

    def paintEvent(self, event):
        # Crée un pinceau de dessin
        painter = QPainter(self)

        # Dessine le cadre de prévisualisation
        pen_frame = QPen(Qt.GlobalColor.black, 3)
        painter.setPen(pen_frame)
        painter.drawRect(self.frame_x, self.frame_y, self.frame_width, self.frame_height)

        # Si la barre est définie, on la dessine aussi
        if None not in (self.x1, self.y1, self.x2, self.y2):
            pen_line = QPen(Qt.GlobalColor.red, 3)
            painter.setPen(pen_line)

            # Adapte les coordonnées de la barre à l’intérieur du cadre
            bar_x1 = self.x1 + self.frame_x
            bar_y1 = self.y1 + self.frame_y
            bar_x2 = self.x2 + self.frame_x
            bar_y2 = self.y2 + self.frame_y

            # Dessine la barre
            painter.drawLine(int(bar_x1), int(bar_y1), int(bar_x2), int(bar_y2))

if __name__ == "__main__":
    app = QApplication(sys.argv) # Crée l'application Qt
    screens = QApplication.screens() # Récupère la liste des écrans disponibles
    # définition des écrans
    screen_experimenter = screens[0]
    screen_patient = screens[1]
    app_window = {} # Dictionnaire pour stocker les fenêtres de l'application
    app_window["main"] = BisectionTest(patient_id=None, screen_patient=screen_patient, screen_experimenter=screen_experimenter) # Crée une instance du test de bisection, en passant les écrans pour affichage
    app_window["main"].show() # Affiche la fenêtre principale du test
    sys.exit(app.exec())