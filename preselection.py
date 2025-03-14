import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk
import sqlite3
import os

# --- Configuration des fichiers ---
DB_FILE = "patients.db"  # Base de données SQLite pour stocker les patients et célébrités
DOSSIER_IMAGES = "C:\\Users\\Paul\\Documents\\GitHub\\Cognitive-test\\image"


# --- Création de la base de données ---
def creer_base():
    """Crée la base de données des patients et célébrités si elle n'existe pas."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Table des patients
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT
        )
    """)
    
    # Table des célébrités reconnues par chaque patient
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS selections (
            patient_id INTEGER,
            nom TEXT,
            image TEXT,
            FOREIGN KEY(patient_id) REFERENCES patients(id)
        )
    """)
    
    conn.commit()
    conn.close()

# --- Gestion des patients ---
def creer_patient():
    """Demande le nom du patient et l'ajoute à la base de données."""
    global current_patient_id
    nom = simpledialog.askstring("Nouveau Patient", "Entrez l'ID du patient :")
    if nom:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO patients (nom) VALUES (?)", (nom,))
        conn.commit()
        current_patient_id = cursor.lastrowid  # Récupère l'ID du patient ajouté
        conn.close()
        afficher_selection()
        charger_celebrites()

def charger_celebrites():
    """Charge une liste de célébrités en utilisant un dossier d'images commun."""
    global celebrites
    noms = ["Brad Pitt", "Angelina Jolie", "Leonardo DiCaprio"]
    fichiers = ["bradpitt.webp", "jolie.webp", "dicaprio.webp"]
    
    celebrites = [{"nom": nom, "image": os.path.join(DOSSIER_IMAGES, fichier)} for nom, fichier in zip(noms, fichiers)]
    
    afficher_celebrite()

# --- Présélection des célébrités ---
current_patient_id = None
celebrites = []
current_celebrity = None
img_tk = None

def afficher_selection():
    """Affiche l'écran de sélection des célébrités."""
    frame_top.pack_forget()
    frame_selection.pack(pady=20)

def afficher_celebrite():
    """Affiche la prochaine célébrité de la liste."""
    global current_celebrity, img_tk
    if not celebrites:
        messagebox.showinfo("Terminé", "Sélection terminée.")
        retour_menu()
        return
    
    current_celebrity = celebrites.pop(0)
    try:
        img = Image.open(current_celebrity["image"])
        img = img.resize((400, 400))
        img_tk = ImageTk.PhotoImage(img)
        photo_label.config(image=img_tk)
        nom_label.config(text=current_celebrity["nom"])
    except FileNotFoundError:
        connu()

def connu():
    """Ajoute la célébrité reconnue en base de données et passe à la suivante."""
    if current_patient_id:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO selections (patient_id, nom, image) VALUES (?, ?, ?)",
                       (current_patient_id, current_celebrity["nom"], current_celebrity["image"]))
        conn.commit()
        conn.close()
    afficher_celebrite()

def inconnu():
    """Passe à la prochaine célébrité sans l'ajouter."""
    afficher_celebrite()

def retour_menu():
    """Retourne au menu principal."""
    frame_selection.pack_forget()
    frame_top.pack(pady=20)

# --- Affichage des patients et de leur sélection ---
def afficher_liste_patients():
    """Affiche les patients sous forme de boutons cliquables."""
    liste_fenetre = tk.Toplevel(root)
    liste_fenetre.title("Liste des patients")
    liste_fenetre.geometry("600x600")
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nom FROM patients")
    patients = cursor.fetchall()
    conn.close()
    
    for patient in patients:
        patient_id, nom = patient
        btn = tk.Button(liste_fenetre, text=nom, font=("Arial", 14), bg="#007BFF", fg="white", width=20, height=2,
                         command=lambda p=patient_id: afficher_details_patient(p))
        btn.pack(pady=5)

def afficher_liste_patients_supprimer():
    """Affiche les patients sous forme de boutons cliquables et permet de les supprimer."""
    liste_fenetre = tk.Toplevel(root)
    liste_fenetre.title("Supprimer un Patient")
    liste_fenetre.geometry("600x600")
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nom FROM patients")
    patients = cursor.fetchall()
    conn.close()
    
    for patient in patients:
        patient_id, nom = patient
        btn = tk.Button(liste_fenetre, text=nom, font=("Arial", 14), bg="#dc3545", fg="white", width=20, height=2,
                         command=lambda p=patient_id: supprimer_patient(p, liste_fenetre))
        btn.pack(pady=5)

def supprimer_patient(patient_id, fenetre):
    """Supprime le patient et ses sélections associées de la base de données."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Supprime les sélections associées à ce patient
    cursor.execute("DELETE FROM selections WHERE patient_id = ?", (patient_id,))
    
    # Supprime le patient
    cursor.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
    
    conn.commit()
    conn.close()
    
    # Fermer la fenêtre de suppression
    fenetre.destroy()
    
    messagebox.showinfo("Supprimé", "Le patient a été supprimé avec succès.")

def afficher_details_patient(patient_id):
    """Affiche les célébrités gardées par un patient."""
    details_fenetre = tk.Toplevel(root)
    details_fenetre.title("Détails du Patient")
    details_fenetre.geometry("500x500")
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT nom, image FROM selections WHERE patient_id = ?", (patient_id,))
    celebrites = cursor.fetchall()
    conn.close()
    
    # Création d'un cadre pour organiser les célébrités en ligne
    frame_images = tk.Frame(details_fenetre)
    frame_images.pack(pady=20)

    for celeb in celebrites:
        nom, image_path = celeb
        try:
            img = Image.open(image_path)
            img = img.resize((150, 150))
            img_tk = ImageTk.PhotoImage(img)
            
            # Frame pour chaque célébrité
            celeb_frame = tk.Frame(frame_images)
            celeb_frame.pack(side=tk.LEFT, padx=10)

            # Image
            img_label = tk.Label(celeb_frame, image=img_tk)
            img_label.image = img_tk
            img_label.pack()

            # Nom
            nom_label = tk.Label(celeb_frame, text=nom, font=("Arial", 12))
            nom_label.pack()
        except FileNotFoundError:
            continue  # Passe l'affichage si l'image n'existe pas

# --- Interface graphique ---
root = tk.Tk()
root.title("Reconnaissance de célébrités")
root.geometry("600x700")
root.configure(bg="#f4f4f4")

# Page d'accueil
frame_top = tk.Frame(root, bg="#f4f4f4")
frame_top.pack(pady=20)
btn_patient = tk.Button(frame_top, text="Créer Patient", command=creer_patient, bg="#007BFF", fg="white", font=("Arial", 16), width=15, height=2)
btn_patient.pack()
btn_liste = tk.Button(frame_top, text="Voir Patients", command=afficher_liste_patients, bg="#17a2b8", fg="white", font=("Arial", 16), width=15, height=2)
btn_liste.pack(pady=10)
btn_supprimer = tk.Button(frame_top, text="Supprimer Patient", command=afficher_liste_patients_supprimer, bg="#dc3545", fg="white", font=("Arial", 16), width=15, height=2)
btn_supprimer.pack(pady=10)

# Interface de présélection
frame_selection = tk.Frame(root, bg="#f4f4f4")
photo_label = tk.Label(frame_selection, bg="#f4f4f4")
photo_label.pack(pady=20)
nom_label = tk.Label(frame_selection, font=("Arial", 24, "bold"), bg="#f4f4f4")
nom_label.pack()
btn_connu = tk.Button(frame_selection, text="Connu", command=connu, bg="green", fg="white", font=("Arial", 16), width=10)
btn_connu.pack(side=tk.LEFT, padx=20)
btn_inconnu = tk.Button(frame_selection, text="Inconnu", command=inconnu, bg="red", fg="white", font=("Arial", 16), width=10)
btn_inconnu.pack(side=tk.RIGHT, padx=20)

creer_base()
root.mainloop()