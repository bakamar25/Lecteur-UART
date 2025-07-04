#!/usr/bin/env python3
import tkinter as tk
from tkinter import scrolledtext
from tkinter.filedialog import *
from tkinter.messagebox import *
from tkinter import * 
import threading
import time
import os
import serial
import serial.tools.list_ports
import datetime


PORT = "COM5"
FICHIER_LOG = ""
TAB_FILTRE = []
STATE_FILTRE = 0
STATE_LECTURE_LOG = 0  # Sert à bloquer certaines actions pendant l'écriture


# Fonction pour filtrer la ligne ET
def and_verificateur(txt):
    string = txt.decode('utf-8') 
    print("TAB :", TAB_FILTRE)
    for element in TAB_FILTRE: 
        print(element," in ",string)
        if element not in string : 
            return False
    return True

# Fonction pour filtrer la ligne OU
def or_verificateur(txt):
    string = txt.decode('utf-8') 
    print("TAB :", TAB_FILTRE)
    for element in TAB_FILTRE: 
        print(element," in ",string)
        if element in string:
            return True
    return False
    

def demarrer_interface():
   # Définit ma fenetre principale
    fenetre = tk.Tk()
    fenetre.title("Filtre Trace")
    fenetre.geometry("500x400")
   
    # Var 
    FILTRE_TYPE = StringVar()
    FILTRE_TYPE.set("or")
    
    # Fonction lecture UART
    def lecture_UART(zone_texte, arret_event):
        print("start lecture")
        ser = serial.Serial(PORT, baudrate=115200) # Ouverture d'une connexion
        while not arret_event.is_set():
            txt = ser.readline()
            if STATE_FILTRE:
                if FILTRE_TYPE.get() == "or":
                    if or_verificateur(txt):
                        zone_texte.insert(tk.END,datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
                        zone_texte.insert(tk.END,":: ")
                        zone_texte.insert(tk.END,txt)
                elif FILTRE_TYPE.get() == "and":
                    if and_verificateur(txt):
                        zone_texte.insert(tk.END,datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
                        zone_texte.insert(tk.END,":: ")
                        zone_texte.insert(tk.END,txt)
            else:
                zone_texte.insert(tk.END,datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
                zone_texte.insert(tk.END,":: ")
                zone_texte.insert(tk.END,txt)
            zone_texte.see(tk.END)
            
        ser.close() # Fermeture de la connexion 
        print("end lecture")
                    
   
    # Barre de menu personnalisée (Frame horizontale)
    menu_frame = tk.Frame(fenetre, bg="lightgrey", height=30)
    menu_frame.pack(fill="x")
    
    # Ajout d’un voyant dans la "barre de menu"
    canvas = tk.Canvas(menu_frame, width=20, height=20, highlightthickness=0)
    canvas.pack(side="left", padx=10)
    voyant_id = canvas.create_oval(2, 2, 18, 18, fill="red")
    
    # Ajout d'un texte pour l'état du filtre 
    Texte_filtre = Text(menu_frame,height = 1, bg="lightgrey")
    Texte_filtre.pack(side="left")
    Texte_filtre.insert(tk.END,"Filtre désactivé")
    Texte_filtre.config(state="disabled")

    
    # Zone de texte 
    texte = scrolledtext.ScrolledText(fenetre, wrap=tk.WORD)
    texte.pack(expand=True, fill='both')

    # Définit mes conditions de thread pour faire fonctionner mes fonctions 
    arret_event = threading.Event()

    def Filtre_Texte_mise_a_jours(etat):
        if etat:
            Texte_filtre.config(state="normal")
            Texte_filtre.delete("1.0", tk.END)
            Texte_filtre.insert(tk.END,"Filtre activé")
        else:
            Texte_filtre.config(state="normal")
            Texte_filtre.delete("1.0", tk.END)
            Texte_filtre.insert(tk.END,"Filtre désactivé")
        Texte_filtre.config(state="disabled")
             
    
    def start():
        # Démarre mon thread 
        print("Start::Chemin de log ",FICHIER_LOG)
        print("Start::Le type de filtre est ",FILTRE_TYPE.get())

        texte.delete("1.0", tk.END)
        if 1:
            thread_lecture = threading.Thread(target=lecture_UART, args=(texte, arret_event))
            thread_lecture.daemon = True # Sert à faire tourner en arrière plan
            arret_event.clear()# Clear la var qui fini la fonction
            thread_lecture.start()
            canvas.itemconfig(voyant_id, fill="green")
        else :
            showerror("Fichier introuvable","Le fichier selectionné est introuvable")
            
    def stop():
        canvas.itemconfig(voyant_id, fill="red")
        arret_event.set()
        
    
        
    def POWER_FILTRE(): 
        global STATE_FILTRE
        if STATE_FILTRE : 
            STATE_FILTRE = 0
        else : 
            STATE_FILTRE = 1
        Filtre_Texte_mise_a_jours(STATE_FILTRE)
    
    def fenetre_param_filtre():
        # Création de la fenetre
        fenetre_filtre = Toplevel(fenetre)  
        fenetre_filtre.title("Paramètres de Filtrage")
        fenetre_filtre.geometry("250x150")
        
        # Met à jours l'affichage des filtres pour l'utilisateur
        def mise_a_jours_affichage():
            Output.config(state="normal")
            Output.delete("1.0", tk.END)
            for FILTRE in TAB_FILTRE : 
                Output.insert(tk.END, f"{FILTRE}\n")
            print("Mise à jour affichage filtres")
            Output.config(state="disabled")

        def add_filtre():
            
            # Fonction qui récupère le texte
            def valider():
                global TAB_FILTRE
                FILTRE = entree.get()
                TAB_FILTRE.append(FILTRE)
                print("Nouveau tableau de filtre:", TAB_FILTRE)
                fenetre_saisie.destroy()  # Ferme la petite fenêtre
                mise_a_jours_affichage()
            
            # Créer une nouvelle fenêtre
            fenetre_saisie = Toplevel(fenetre)
            fenetre_saisie.title("Saisir un texte")
            fenetre_saisie.geometry("300x120")

            # Label
            label = tk.Label(fenetre_saisie, text="Entrez votre filtre :")
            label.pack(pady=5)

            # Champ de saisie
            entree = tk.Entry(fenetre_saisie, width=40)
            entree.pack(pady=5)

            # Bouton de validation
            bouton_valider = tk.Button(fenetre_saisie, text="Valider", command=valider)
            bouton_valider.pack(pady=5)
        
        def RAZ_TAB_FILTRE():
            global TAB_FILTRE 
            TAB_FILTRE = []
            mise_a_jours_affichage()
            print("RAZ des filtres, TAB_FILTRE = ",TAB_FILTRE)
            
        # Faux menu (une frame en haut qui imite une barre de menu)
        menu_bar = tk.Frame(fenetre_filtre, bg="lightgray", height=30)
        menu_bar.pack(side="top", fill="x")
        
        # BP ajouter un filtre 
        BP_add_filtre = tk.Button(menu_bar, text="Ajouter", command=add_filtre, relief="flat", bg="lightgray")
        BP_add_filtre.pack(side="left", padx=5, pady=2)
        
        # BP retirer tous les filtres
        BP_remove_filtre = tk.Button(menu_bar, text="Effacer", command=RAZ_TAB_FILTRE, relief="flat", bg="lightgray")
        BP_remove_filtre.pack(side="left", padx=5, pady=2)
        
        # BP radio type filtre ET
        BP_radio_and = Radiobutton(menu_bar, text="ET", variable=FILTRE_TYPE, value="and")
        BP_radio_and.pack(anchor = W,side="left")
        
        # BP radio type filtre OU
        BP_radio_or = Radiobutton(menu_bar, text="OU", variable=FILTRE_TYPE, value="or")
        BP_radio_or.pack(anchor = W,side="left")
        
        # Texte pour afficher les filtres
        Output = Text(fenetre_filtre, height = 5, bg = "light cyan")
        mise_a_jours_affichage()
        Output.config(state="disabled")
        Output.pack(expand=True, fill="both")
    
    def effacer_logs():
        texte.delete("1.0", tk.END)
        
    menubar = Menu(fenetre)
    menu1 = Menu(menubar, tearoff=0)
    menu1.add_command(label="Start", command=start )
    menu1.add_command(label="Stop", command=stop)
    menu1.add_separator()
    menu1.add_command(label="Effacer", command=effacer_logs)
    menu1.add_separator()
    menu1.add_command(label="Quitter", command=fenetre.quit)
    menubar.add_cascade(label="Action", menu=menu1)
    
    
    menu3 = Menu(menubar, tearoff=0)
    menu3.add_command(label="ON/OFF", command=POWER_FILTRE)
    menu3.add_command(label="Selection filtre", command=fenetre_param_filtre)
    menubar.add_cascade(label="Filtre", menu=menu3)



    fenetre.config(menu=menubar)
    fenetre.mainloop()

demarrer_interface()

