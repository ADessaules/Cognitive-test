from PyQt6.QtWidgets import QWidget, QPushButton, QLabel, QVBoxLayout, QDialog, QMessageBox, QGridLayout, QScrollArea
from PyQt6.QtGui import QPixmap, QPainter
from PyQt6.QtCore import Qt
import sqlite3
import os
import glob
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from constant import DB_FILE, DOSSIER_PATIENTS, DOSSIER_IMAGES

class SelectionCelebrites(QDialog):
    """
    Fenêtre de sélection des célébrités connues par le patient.

    Elle permet à l’expérimentateur (ou au patient assisté) de parcourir
    toutes les images des célébrités disponibles (ceux marquées avec _0),
    de sélectionner celles reconnues, puis de sauvegarder la sélection
    dans la base de données et dans un fichier `selection.txt` local.
    """
    def __init__(self, patient_id, patient_name):
        """
    Initialise l’interface de sélection pour un patient donné.

    Args:
        patient_id (int): ID unique du patient dans la base de données.
        patient_name (str): Nom du patient (utilisé pour le dossier).
        """
        super().__init__()
        self.setWindowTitle("Sélection des célébrités")
        self.setGeometry(100, 100, 800, 600)
        self.patient_id = patient_id
        self.patient_name = patient_name
        self.selections = {}

        extensions = ["*.jpg", "*.jpeg", "*.png"]
        fichiers = []
        for ext in extensions:
            fichiers.extend(glob.glob(os.path.join(DOSSIER_IMAGES, ext)))

        fichiers_filtres = [f for f in fichiers if os.path.splitext(f)[0].endswith("_0")]
        self.celebrites = [{"nom": os.path.splitext(os.path.basename(f))[0].replace("_", " "), "image": f}
                           for f in fichiers_filtres]

        self.layout = QVBoxLayout()

        scroll = QScrollArea()
        scroll_widget = QWidget()
        self.grid_layout = QGridLayout()
        scroll_widget.setLayout(self.grid_layout)
        scroll.setWidgetResizable(True)
        scroll.setWidget(scroll_widget)
        self.layout.addWidget(scroll)

        self.btn_valider = QPushButton("Valider la sélection")
        self.btn_valider.setStyleSheet("font-size: 18px; padding: 10px;")
        self.btn_valider.clicked.connect(self.valider_selection)
        self.layout.addWidget(self.btn_valider)

        self.btn_stop = QPushButton("Stopper le test")
        self.btn_stop.setStyleSheet("font-size: 18px; padding: 10px; background-color: red; color: white;")
        self.btn_stop.clicked.connect(self.stop_test)
        self.layout.addWidget(self.btn_stop)

        self.setLayout(self.layout)
        self.afficher_celebrite_grid()

    def afficher_celebrite_grid(self):
        """
    Affiche toutes les célébrités disponibles (seules les images finissant par _0)
    dans une grille scrollable.

    Chaque image est cliquable et peut être sélectionnée ou désélectionnée.
        """
        row = col = 0
        for celebrité in self.celebrites:
            nom = celebrité["nom"]
            image_path = celebrité["image"]

            img_label = QLabel()
            img_label.setFixedSize(150, 150)
            img_label.setScaledContents(True)

            if os.path.exists(image_path):
                pixmap = QPixmap(image_path).scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio)
                img_label.setPixmap(pixmap)

            img_label.mousePressEvent = self.generer_toggle_handler(img_label, nom, image_path)
            self.grid_layout.addWidget(img_label, row, col)
            self.selections[img_label] = {"selected": True, "nom": nom, "image": image_path, "pixmap": pixmap}

            col += 1
            if col >= 4:
                col = 0
                row += 1

    def generer_toggle_handler(self, label, nom, image_path):
        """
    Génère un gestionnaire de clic pour une image.

    Permet d'activer/désactiver la sélection de la célébrité et modifie l’apparence
    (transparence) en conséquence.

    Args:
        label (QLabel): Widget contenant l'image.
        nom (str): Nom de la célébrité.
        image_path (str): Chemin de l'image.

    Returns:
        handler (Callable): Fonction à exécuter lors du clic.
        """
        def handler(event):
            current = self.selections[label]
            current["selected"] = not current["selected"]
            opacity = 0.3 if not current["selected"] else 1.0
            pixmap = QPixmap(current["image"]).scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio)
            transparent = QPixmap(pixmap.size())
            transparent.fill(Qt.GlobalColor.transparent)

            painter = QPainter(transparent)
            painter.setOpacity(opacity)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()

            label.setPixmap(transparent)
        return handler

    def enregistrer_selection_txt(self):
        """
    Sauvegarde les images sélectionnées dans un fichier texte `selection.txt`
    dans le dossier du patient (au format : nom_image_0, nom_image_0...).
        """
        selected_images = [os.path.splitext(os.path.basename(info["image"]))[0]
                           for info in self.selections.values() if info["selected"]]
        patient_folder = os.path.join("Patients", self.patient_name)
        os.makedirs(patient_folder, exist_ok=True)
        with open(os.path.join(patient_folder, "selection.txt"), "w") as f:
            f.write(",".join(selected_images))

    def valider_selection(self):
        """
    Enregistre la sélection des célébrités dans la base de données,
    puis appelle `enregistrer_selection_txt` pour la sauvegarde locale.

    Ferme la fenêtre après confirmation.
        """
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM selections WHERE patient_id = ?", (self.patient_id,))
        for info in self.selections.values():
            if info["selected"]:
                cursor.execute(
                    "INSERT INTO selections (patient_id, nom, image) VALUES (?, ?, ?)",
                    (self.patient_id, info["nom"], info["image"])
                )
        conn.commit()
        conn.close()
        self.enregistrer_selection_txt()
        QMessageBox.information(self, "Enregistré", "Sélection mise à jour avec succès.")
        self.close()

    def stop_test(self):
        """
    Permet d’interrompre la présélection sans poursuivre le test.

    Enregistre tout de même les sélections en base et en fichier texte,
    puis ferme la fenêtre.
        """
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM selections WHERE patient_id = ?", (self.patient_id,))
        for info in self.selections.values():
            if info["selected"]:
                cursor.execute(
                    "INSERT INTO selections (patient_id, nom, image) VALUES (?, ?, ?)",
                    (self.patient_id, info["nom"], info["image"])
                )
        conn.commit()
        conn.close()
        self.enregistrer_selection_txt()
        QMessageBox.information(self, "Test interrompu", "Test arrêté. Sélections sauvegardées.")
        self.close()
