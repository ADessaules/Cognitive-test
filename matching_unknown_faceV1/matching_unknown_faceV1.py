from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QLineEdit, QMessageBox, QComboBox, QGridLayout
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QTimer, Qt, QEvent
from pathlib import Path
from datetime import datetime
import sys, os, random, time
import pandas as pd
import subprocess


class WaitingScreen(QWidget):
    """
Fenêtre affichée au patient avant le démarrage du test.

Elle présente un simple message : "Appuyez sur Espace pour démarrer le test".
Utilisée pour introduire un délai volontaire avant la session.
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
Fenêtre qui s’affiche sur l'écran du patient pendant le test.

Elle montre :
- une image en haut (le visage cible) ;
- deux images en bas (choix possibles à cliquer pour identifier le bon visage).
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test en cours - Écran patient")
        self.setGeometry(920, 100, 800, 600)

        self.top_label = QLabel()
        self.top_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        #Layout horizontal pour les deux images du bas
        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bottom_layout.setSpacing(50)  # espacement égal

        #Layout global qui centre tout
        outer_layout = QVBoxLayout()
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer_layout.addWidget(self.top_label)
        outer_layout.addLayout(self.bottom_layout)

        self.setLayout(outer_layout)

    def show_triplet(self, top_image_path, bottom_images, handlers):
        screen = QApplication.primaryScreen().geometry()
        img_w = screen.width() // 4
        img_h = screen.height() // 2.5  # un peu plus petit que la moitié

        pixmap_top = QPixmap(top_image_path).scaled(
            int(img_w), int(img_h),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.top_label.setPixmap(pixmap_top)

        for i in reversed(range(self.bottom_layout.count())):
            w = self.bottom_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        for path, handler in zip(bottom_images, handlers):
            label = QLabel()
            pixmap = QPixmap(path).scaled(
                int(img_w), int(img_h),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            label.setPixmap(pixmap)
            label.mousePressEvent = handler
            self.bottom_layout.addWidget(label)
            

class MatchingUnknownTest(QMainWindow):
    """
Fenêtre principale du test Matching Unknown, utilisée par l’expérimentateur.

Ce test consiste à présenter un visage inconnu en haut, et deux visages en bas :
l’un correspond à ce visage vu précédemment, l’autre est un distracteur.

Cette interface permet :
- de préparer le test (sélection patient, paramètres) ;
- de présenter les essais ;
- d'enregistrer les clics et les temps de réponse ;
- de sauvegarder les résultats dans un fichier Excel.
    """
    def __init__(self):
        """
Initialise la fenêtre principale, charge les données, configure les composants,
prépare les événements clavier et timer.
        """
        super().__init__()
        self.setWindowTitle("Matching Unknown Test - Expérimentateur")
        self.setGeometry(100, 100, 1200, 600)
        self.image_folder = os.path.join(os.path.dirname(__file__), "image_matching_unknown_faceV1")
        self.output_folder = os.path.dirname(__file__)
        self.test_name = "matching_unknown"
        self.timer = QTimer()
        self.timer.timeout.connect(self.advance_by_timer)
        self.session_active = False

        self.patient_window = PatientWindow()
        self.waiting_screen = WaitingScreen()

        # Gestion multi-écrans comme dans FamousNameTest
        screens = QApplication.screens()
        if len(screens) >= 2:
            primary_screen = screens[0]
            secondary_screen = screens[1]

            # Expérimentateur en plein écran sur le principal
            self.move(primary_screen.geometry().topLeft())
            self.showFullScreen()

            # Patient en plein écran sur l'écran secondaire
            self.patient_window.move(secondary_screen.geometry().topLeft())
            self.patient_window.showFullScreen()
            self.secondary_screen = secondary_screen
        else:
            print("⚠️ Moins de deux écrans détectés. Utilisation en mode fenêté.")
            self.setGeometry(100, 100, 1200, 600)
            self.patient_window.setGeometry(920, 100, 800, 600)
            self.show()
            self.patient_window.show()
            self.secondary_screen = None

        self.init_data()
        self.init_ui()
        self.installEventFilter(self)

    def init_data(self):
        """
Parcourt le dossier d’images pour construire les triplets valides (0, 1, 2).

Les fichiers sont regroupés par préfixe commun, puis organisés en triplets
(top + deux images de comparaison). Un mapping est aussi préparé
pour retrouver les noms correspondants aux triplets.
        """
        self.triplets = {}
        for file in os.listdir(self.image_folder):
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                prefix_parts = file.split("_")
                if len(prefix_parts) < 3:
                    continue
                prefix = "_".join(prefix_parts[:2])
                self.triplets.setdefault(prefix, []).append(file)

        self.all_triplets = []
        for prefix, files in self.triplets.items():
            files_dict = {f.split("_")[2].split(".")[0]: f for f in files}
            if all(k in files_dict for k in ["0", "1", "2"]):
                triplet = [files_dict["0"], files_dict["1"], files_dict["2"]]
                self.all_triplets.append(triplet)
            else:
                print(f"\u274c Triplet invalide ignor\u00e9 pour le pr\u00e9fixe {prefix} : {files}")

        self.session_results = []
        self.nurse_clicks = []
        self.triplet_info_map = {
            f"image_{i+1}_": {"nom": name, "num": i+1} for i, name in enumerate([
                "Dale Oen", "Michela Quattrociocche", "Henrik Sass Larsen", "Gavin Rossdale", "Sylvi Listhaug",
                "Laimdota Straujuma", "Evan Spiegel", "Harald Kruger", "Simon Hughes", "Lara Stone",
                "Dieter Bohlen", "Nicolaj Koppel", "Adam Senn", "Lars Ohly", "Bill Shorten",
                "Bob Simon", "Katie Couric", "Brian Urlacher", "Jan Kees De Jager", "Maxi Iglesias",
                "Sean O'pry", "Philippos Of Greece"
            ])
        }

    def init_ui(self):
        """
Construit l’interface graphique de l’expérimentateur :
- panneau de gauche : configuration du test (paramètres, sélection) ;
- panneau de droite : aperçu visuel des images affichées ;
- connecte tous les boutons et champs à leurs fonctions.
        """
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        btn_retour_interface = QPushButton("Retour à l'interface")
        btn_retour_interface.clicked.connect(self.return_to_main_interface)
        left_layout.addWidget(btn_retour_interface)

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
                  QLabel("Mode d'affichage des images :"), self.mode_selector,
                  self.timer_input, start_btn, stop_btn]:
            left_layout.addWidget(w)

        self.image_layout = QGridLayout()
        right_panel = QWidget()
        right_panel.setLayout(self.image_layout)

        layout.addLayout(left_layout)
        layout.addWidget(right_panel)
        central.setLayout(layout)

    def prepare_test(self):
        """
Vérifie que les champs sont bien remplis et prépare une nouvelle session.

Mélange les triplets, réinitialise les données de session, puis affiche
les fenêtres "attente" et "patient". Met le focus clavier sur la fenêtre.
        """
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

        self.shuffled_triplets = random.sample(self.all_triplets, len(self.all_triplets))
        self.index = 0
        self.session_results = []
        self.session_active = False

        # Réaffiche les fenêtres au bon endroit en plein écran si possible
        if self.secondary_screen:
            self.patient_window.move(self.secondary_screen.geometry().topLeft())
            self.patient_window.showFullScreen()
            self.waiting_screen.move(self.secondary_screen.geometry().topLeft())
            self.waiting_screen.setGeometry(150, 150, 800, 600)
            self.waiting_screen.show()
        else:
            self.patient_window.setGeometry(920, 100, 800, 600)
            self.waiting_screen.setGeometry(920, 100, 800, 600)
            self.patient_window.show()
            self.waiting_screen.show()

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()

    def eventFilter(self, obj, event):
        """
Gère deux cas :
1. Enregistrement d’un clic pour la stimulation (hors essai de réponse) ;
2. Détection de la barre espace pour commencer ou passer au suivant.

C’est ici que sont capturées les interactions "globales" de l’utilisateur.
        """
        if event.type() == QEvent.Type.MouseButtonPress:
            # Seulement si clic droit ET dans la fenêtre de l'expérimentateur
            if event.button() == Qt.MouseButton.RightButton and obj == self:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                elapsed = round(time.time() - self.start_time, 3) if hasattr(self, "start_time") else ""
                self.nurse_clicks.append({
                    "id_essai": self.index + 1,
                    "temps_reponse": elapsed,
                    "image_choisie": "",
                    "correct": "",
                    "triplet_nom": self.triplet_info_map.get(self.shuffled_triplets[self.index][0].rsplit("_", 1)[0] + "_", {}).get("nom", "Inconnu"),
                    "triplet_num": self.triplet_info_map.get(self.shuffled_triplets[self.index][0].rsplit("_", 1)[0] + "_", {}).get("num", -1),
                    "participant": self.patient_selector.currentText(),
                    "contact_stimulation": self.contact,
                    "intensité": self.intensite,
                    "durée": self.duree,
                    "mode": "clic droit",
                    "horodatage": now
                })

        if event.type() == QEvent.Type.KeyRelease and event.key() == Qt.Key.Key_Space:
            if not self.session_active and self.waiting_screen and self.waiting_screen.isVisible():
                self.waiting_screen.hide()
                self.session_active = True
                self.show_next_triplet()
            elif self.session_active and self.mode == "Barre espace":
                now = time.time()
                reaction_time = round(now - self.start_time, 3)

                self.session_results.append({
                    "id_essai": self.index + 1,
                    "temps_reponse": reaction_time,
                    "image_choisie": "aucune",
                    "correct": False,
                    "triplet_nom": self.triplet_info_map.get(self.shuffled_triplets[self.index][0].rsplit("_", 1)[0] + "_", {}).get("nom", "Inconnu"),
                    "triplet_num": self.triplet_info_map.get(self.shuffled_triplets[self.index][0].rsplit("_", 1)[0] + "_", {}).get("num", -1),
                    "participant": self.patient_selector.currentText(),
                    "contact_stimulation": self.contact,
                    "intensité": self.intensite,
                    "durée": self.duree,
                    "mode": self.mode,
                    "horodatage": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

                self.index += 1
                self.show_next_triplet()

        return super().eventFilter(obj, event)

    def advance_by_timer(self):
        """
Appelée lorsque le temps imparti est écoulé sans clic utilisateur.

Enregistre une réponse vide (non cliquée) et passe au triplet suivant.
        """
        # Enregistre une non-réponse
        self.session_results.append({
            "id_essai": self.index + 1,
            "temps_reponse": self.timer_duration,
            "image_choisie": "aucune",
            "correct": False,
            "triplet_nom": self.triplet_info_map.get(self.shuffled_triplets[self.index][0].rsplit("_", 1)[0] + "_", {}).get("nom", "Inconnu"),
            "triplet_num": self.triplet_info_map.get(self.shuffled_triplets[self.index][0].rsplit("_", 1)[0] + "_", {}).get("num", -1),
            "participant": self.patient_selector.currentText(),
            "contact_stimulation": self.contact,
            "intensité": self.intensite,
            "durée": self.duree,
            "mode": self.mode,
            "horodatage": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        self.index += 1
        self.show_next_triplet()

    def show_next_triplet(self):
        """
Affiche le prochain triplet :
- 1 image cible (top)
- 2 images réponses (dont une correcte), dans un ordre aléatoire

Crée les gestionnaires de clics pour chaque image réponse.
Affiche en parallèle les images sur l’interface expérimentateur.
        """
        for i in reversed(range(self.image_layout.count())):
            w = self.image_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        if self.index >= len(self.shuffled_triplets):
            self.save_results()
            return

        triplet = self.shuffled_triplets[self.index]
        sorted_triplet = sorted(triplet, key=lambda f: int(f.split("_")[2].split(".")[0]))
        top, correct, distractor = sorted_triplet

        options = [correct, distractor]
        random.shuffle(options)
        is_correct_map = {img: (img == correct) for img in options}
        self.start_time = time.time()

        def make_handler(selected_img):
            """
Fonction imbriquée (factory) utilisée dans `show_next_triplet` pour
générer des handlers qui enregistrent le choix utilisateur et
affichent un retour visuel (bordure verte ou rouge).
            """
            def handler(event):
                rt = round(time.time() - self.start_time, 3)
                self.session_results.append({
                    "id_essai": self.index + 1,
                    "temps_reponse": rt,
                    "image_choisie": "correct" if is_correct_map[selected_img] else "distracteur",
                    "correct": is_correct_map[selected_img],
                    "triplet_nom": self.triplet_info_map.get(self.shuffled_triplets[self.index][0].rsplit("_", 1)[0] + "_", {}).get("nom", "Inconnu"),
                    "triplet_num": self.triplet_info_map.get(self.shuffled_triplets[self.index][0].rsplit("_", 1)[0] + "_", {}).get("num", -1),
                    "participant": self.patient_selector.currentText(),
                    "contact_stimulation": self.contact,
                    "intensit\u00e9": self.intensite,
                    "dur\u00e9e": self.duree,
                    "mode": self.mode,
                    "horodatage": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                for i, opt in enumerate(options):
                    label = self.image_layout.itemAtPosition(1, i).widget()
                    color = "green" if is_correct_map[opt] else "red"
                    if selected_img == opt:
                        label.setStyleSheet(f"border: 4px solid {color}; margin: 5px;")
                self.index += 1
                QTimer.singleShot(500, self.show_next_triplet)
            return handler

        top_path = os.path.join(self.image_folder, top)
        options_path = [os.path.join(self.image_folder, opt) for opt in options]
        handlers = [make_handler(opt) for opt in options]

        self.patient_window.show_triplet(top_path, options_path, handlers)

        # Affichage triangle sur interface exp\u00e9rimentateur
        top_lbl = QLabel()
        top_lbl.setPixmap(QPixmap(top_path).scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio))
        self.image_layout.addWidget(top_lbl, 0, 0, 1, 2, alignment=Qt.AlignmentFlag.AlignCenter)
        for i, path in enumerate(options_path):
            lbl = QLabel()
            lbl.setPixmap(QPixmap(path).scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio))
            self.image_layout.addWidget(lbl, 1, i)

        if self.mode == "Temps imparti":
            self.timer.start(self.timer_duration * 1000)

    def save_results(self):
        """
À la fin du test ou sur demande :
- regroupe les résultats en un DataFrame ;
- les sauvegarde dans un fichier Excel nommé avec le patient et la date ;
- ferme les fenêtres et stoppe le timer.
        """
        df_trials = pd.DataFrame(self.session_results)
        df_clicks = pd.DataFrame(self.nurse_clicks)
        df = pd.concat([df_trials, df_clicks], ignore_index=True)
        if df.empty:
            return
    
        now = datetime.now().strftime("%Y_%m_%d_%H%M")
        name = self.patient_selector.currentText().replace(" ", "_")
        filename = f"{name}_{now}_{self.contact}-{self.intensite}-{self.duree}_{self.test_name}.xlsx"
    
        patients_root = Path(__file__).resolve().parent.parent / "Patients"
        patient_dir = patients_root / name
        patient_dir.mkdir(parents=True, exist_ok=True)  # Crée le dossier s'il n'existe pas
    
        output_path = patient_dir / filename
    
        try:
            df.to_excel(output_path, index=False)
            QMessageBox.information(self, "Fin", f"Test terminé. Fichier sauvegardé dans : {output_path}")
        except PermissionError:
            QMessageBox.critical(self, "Erreur", "Le fichier est ouvert ailleurs. Fermez-le puis réessayez.")
    
        if self.patient_window:
            self.patient_window.close()
        if self.waiting_screen:
            self.waiting_screen.close()
        self.timer.stop()
        self.session_active = False

    def return_to_main_interface(self):
        """
Ferme toutes les fenêtres liées au test et relance l’interface principale.

Utilisé pour revenir au menu principal après ou pendant un test.
        """
        try:
            if self.patient_window:
                self.patient_window.close()
            if self.waiting_screen:
                self.waiting_screen.close()
            self.close()
            subprocess.Popen(["python", "interface.py"])
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de retourner à l'interface principale : {e}")


if __name__ == "__main__":
    """
Point d’entrée principal du script.

Crée l’application Qt et affiche la fenêtre principale du test Matching Unknown.
    """
    app = QApplication(sys.argv)
    window = MatchingUnknownTest()
    window.show()
    sys.exit(app.exec())
