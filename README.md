# Cognitive Test

## Présentation

**Cognitive Test** est une application interactive développée en Python avec PyQt6. Elle permet de réaliser plusieurs tests cognitifs, notamment :
- Un test d'appariement sémantique basé sur les **mots**
- Un test d'appariement sémantique basé sur les **images**
- Un test matching Unknow face
- Un test famous_face
- Un test famous_name
- Une interface de gestion de patients
- Le test de bissection
- Un système de lancement centralisé pour tous les modules de test

L'application est pensée pour être utilisée dans un cadre de recherche ou de bilan cognitif (éducation, neuropsychologie, etc.).

Il est indispensable de posséder deux écrans pour bien faire fonctionner l'application.

---

## Technologies utilisées

- Python 3.10+ (testé avec Python 3.13)
- PyQt6
- SQLite3 (via `patients.db`)
- CSV / fichiers texte pour certaines données

---

## Installation

1. **Cloner le dépôt** ou extraire l’archive `.zip` :
    ```bash
    git clone <url-du-dépôt>  # si disponible
    ```
    ou simplement extraire l’archive sur votre machine.

2. **Créer un environnement virtuel** (optionnel mais recommandé) :
    ```bash
    python -m venv venv
    venv\Scripts\activate  # Windows
    ```

3. **Installer les dépendances** :
    ```bash
    pip install pyqt6
    ```

---

## Utilisation

Lancer l’interface principale depuis le dossier `Cognitive-test` :

Aller dans dist puis interface.exe.

Depuis cette interface, vous pouvez :
- Lancer les tests cognitifs
- Gérer les patients
- Créer un patient
- Accéder à l’ensemble des modules via une interface centralisée

---

## Structure du projet

📁 bisection_test
│   └── 📁 __pycache__
│   └── 📄 bisection_test.py
│
📁 build\interface
│
📁 database
│   └── 📁 __pycache__
│   └── 📄 database.py
│   └── 📄 patients.db
│
📁 famous_faceV1
│   └── 📁 __pycache__
│   └── 📁 image_famous_faceV1
│   └── 📁 image_preselection
│   └── 📄 dialogs.py
│   └── 📄 famous_faceV1.py
│   └── 📄 main_window.py
│   └── 📄 main.py
│   └── 📄 preselection_celeb.py
│
📁 famous_name
│   └── 📄 famous_name.py
│   └── 📄 nom.txt
│
📁 gestion_patient
│   └── 📁 __pycache__
│   └── 📄 creation_patient.py
│   └── 📄 detail_patient.py
│   └── 📄 liste_patients.py
│
📁 matching_unknown_faceV1
│   └── 📁 image_matching_unknown_faceV1
│   └── 📄 matching_unknown_faceV1.py
│
📁 Patients
│
📁 test_appariement_semantique_image
│   └── 📁 image_test_appariemment
│   └── 📄 preselection_image_sémantique.py
│   └── 📄 test_appariement_semantique_image.py
│
📁 test_appariement_semantique_mots
│   └── 📁 __pycache__
│   └── 📄 constant.py
│   └── 📄 preselection_mots_semantique.py
│   └── 📄 test_appariement_semantique_mots.py
│
📄 brain_icon.ico  
📄 icon.png  
📄 interface.exe  
📄 interface.py  
📄 interface.spec  
📄 README.md

