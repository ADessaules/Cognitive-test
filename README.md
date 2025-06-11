# Cognitive Test

## Présentation

**Cognitive Test** est une application interactive développée en Python avec PyQt6. Elle permet de réaliser plusieurs tests cognitifs, notamment :
- Un test d'appariement sémantique basé sur les **mots**
- Un test d'appariement sémantique basé sur les **images**
- Un test matching Unknow face
- Un test famous_face
- Un test famous_name
- Une interface de gestion de patients
- Un système de lancement centralisé pour tous les modules de test

L'application est pensée pour être utilisée dans un cadre de recherche ou de bilan cognitif (éducation, neuropsychologie, etc.).

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

```
Cognitive-test/
├── interface.py                          # Interface principale (menu centralisé)
├── test_appareiment_semantique_mots.py  # Test sémantique basé sur des mots
├── test_appariement_semantique_image.py # Test sémantique basé sur des images
├── constant.py                           # Constantes générales
├── famous_name.py                        # Utilisé dans certains tests ou affichages
├── patients.db                           # Base de données SQLite
├── nom.txt                               # Fichier de noms
├── README.md                             # Ce fichier
```

---

