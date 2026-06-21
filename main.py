import pygame
import pygame_gui
import math
import random
import json
import os
import sys
from datetime import datetime

LARGEUR, HAUTEUR = 1100, 600
GRAVITE = 400.0
FICHIER_SCORES = "scores.json"

NOIR = (0, 0, 0)
GRIS = (100, 100, 100)
VIOLET = (120, 0, 180)
ROSE = (255, 0, 190)
JAUNE = (255, 255, 0)
BLANC = (255, 255, 255)
COULEURS_VILLE = [
    (18, 12, 30),
    (24, 16, 40),
    (30, 20, 50),
    (40, 30, 65)
] #palette de couleurs list de tuple 

pygame.init()
ecran = pygame.display.set_mode((LARGEUR, HAUTEUR))
pygame.display.set_caption("GORILLAS 2025 - Version Cyberpunk")
manager = pygame_gui.UIManager((LARGEUR, HAUTEUR))
horloge = pygame.time.Clock()

#images
DOSSIER_COURANT = os.path.dirname(os.path.abspath(__file__)) 

def charger_image_robuste(nom_fichier, taille_cible=None):
    chemin_complet = os.path.join(DOSSIER_COURANT, nom_fichier)
    try:
        img = pygame.image.load(chemin_complet).convert_alpha()
        if taille_cible:
            img = pygame.transform.scale(img, taille_cible)
        print(f"OK: {nom_fichier} chargé.")
        return img
    except:
        print(f"ATTENTION: {nom_fichier} introuvable. Utilisation des formes par défaut.")
        return None # Retourne "rien" si l'image échoue

IMG_GORILLA1 = charger_image_robuste("gorilla2.png", (60, 80)) #taille adaptée a la hitbox
IMG_GORILLA2 = charger_image_robuste("gorilla1.png", (60, 80))
IMG_BANANE = charger_image_robuste("banana.png", (40, 40))

#classes
class Joueur:
    def __init__(self, nom, couleur, image): 
        self.nom = nom
        self.couleur = couleur
        self.image = image 
        self.score = 0
        self.rect = pygame.Rect(0, 0, 60, 80) # La hitbox est un rectangle
        self.en_vie = True

class Banane:
    def __init__(self, x, y, angle, vitesse0):
        self.x = x
        self.y = y
        self.rayon = 5 
        rad = math.radians(angle)
        self.vx = math.cos(rad) * vitesse0
        self.vy = -math.sin(rad) * vitesse0
        self.historique = [] # On crée une liste pour mémoriser le chemin

    def bouger(self, dt, vent):
        # 1. Physique (Gravité + Vent)
        self.vy += GRAVITE * dt
        self.vx += vent * dt
        
        # 2. Sauvegarde de la position AVANT de bouger (pour la traînée)
        self.historique.append((self.x, self.y))
        
        # 3. Limite de la traînée (pour garder seulement les 20 derniers points)
        if len(self.historique) > 20:
            self.historique.pop(0) # On supprime le plus vieux point

        # 4. Déplacement réel
        self.x += self.vx * dt
        self.y += self.vy * dt

    def dessiner(self, surface):
        # --- ÉTAPE 1 : DESSINER LA TRAÎNÉE (Derrière la banane) ---
        nb_points = len(self.historique)
        for i in range(nb_points):
            # On récupère les vieilles positions
            pos_x, pos_y = self.historique[i]
            
            # Calcul mathématique pour la taille :
            # i=0 (queue) -> petit | i=max (tête) -> gros
            taille = 2 + (i / nb_points) * 3 
            
            # On dessine le point de traînée
            pygame.draw.circle(surface, ROSE, (int(pos_x), int(pos_y)), int(taille))

        # --- ÉTAPE 2 : DESSINER LA BANANE (Par-dessus la traînée) ---
        if IMG_BANANE: # Si l'image a bien été chargée
            # On centre l'image sur la position x,y
            rect_img = IMG_BANANE.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(IMG_BANANE, rect_img)
        else:
            # Sinon, on dessine le rond jaune (sécurité)
            pygame.draw.circle(surface, JAUNE, (int(self.x), int(self.y)), self.rayon)

class Ville: 
    def __init__(self):
        self.surface = pygame.Surface((LARGEUR, HAUTEUR))
        self.surface.set_colorkey(NOIR) #pour l'ordi noir c invisible
        self.generer()

    def generer(self):
        self.surface.fill(NOIR)
        self.emplacements = []
        x = 10
        while x < LARGEUR: #tant que je sors pas de l'écran
            largeur = random.randint(60, 100)
            hauteur = random.randint(100, 400)
            espace = random.randint(5, 25) 
            rect = pygame.Rect(x, HAUTEUR - hauteur, largeur, hauteur) #y=H-h
            couleur = random.choice(COULEURS_VILLE)
            pygame.draw.rect(self.surface, couleur, rect)
            larg_fen, haut_fen = 10, 14
            for yy in range(rect.top + 16, rect.bottom - 10, 24): #range(debut,fin,pas)
                for xx in range(rect.left + 10, rect.right - 10, 22):
                    if random.random() < 0.7: #on créer une prob 
                        couleur_fenetre = random.choice([(255, 255, 255, 180), VIOLET + (180,)]) #180 pour transparence
                        pygame.draw.rect(self.surface, couleur_fenetre, (xx, yy, larg_fen, haut_fen))
            self.emplacements.append(rect) #immeuble fini on l'ajoute a la liste
            x += largeur + espace

    def faire_trou(self, x, y):
        pygame.draw.circle(self.surface, NOIR, (int(x), int(y)), 40) #x y dans boucle principale banane

    def touche_immeuble(self, x, y):
        if 0 <= x < LARGEUR and 0 <= y < HAUTEUR: #banane dans l'ecran avnt quelle verifie le pixel
            return self.surface.get_at((int(x), int(y))) != NOIR
        return False

#sauvegarde 
def sauvegarder_score(j1, j2):
    nouvelle_partie = {
        "date": str(datetime.now()),
        "joueurs": [j1.nom, j2.nom],
        "score_final": f"{j1.score} - {j2.score}",
        "vainqueur": j1.nom if j1.score > j2.score else j2.nom
    }
    historique = []
    if os.path.exists(FICHIER_SCORES):
        try:
            with open(FICHIER_SCORES, "r") as f:
                historique = json.load(f)
        except:
            historique = []
    historique.append(nouvelle_partie)
    with open(FICHIER_SCORES, "w") as f:
        json.dump(historique, f, indent=4)

def placer_joueurs(ville, j1, j2):
    if len(ville.emplacements) > 2:
        j1.rect.midbottom = ville.emplacements[1].midtop
        j2.rect.midbottom = ville.emplacements[-2].midtop

#interfaces
panel_pseudos = pygame_gui.elements.UIPanel(pygame.Rect(350, 150, 400, 300), manager=manager)
pygame_gui.elements.UILabel(pygame.Rect(20, 20, 360, 30), "Pseudo Joueur 1:", manager=manager, container=panel_pseudos)
input_j1 = pygame_gui.elements.UITextEntryLine(pygame.Rect(20, 60, 360, 30), manager=manager, container=panel_pseudos)
input_j1.set_text("Gorille 1")
pygame_gui.elements.UILabel(pygame.Rect(20, 110, 360, 30), "Pseudo Joueur 2:", manager=manager, container=panel_pseudos)
input_j2 = pygame_gui.elements.UITextEntryLine(pygame.Rect(20, 150, 360, 30), manager=manager, container=panel_pseudos)
input_j2.set_text("Gorille 2")
btn_valider = pygame_gui.elements.UIButton(pygame.Rect(100, 220, 200, 50), "COMMENCER", manager=manager, container=panel_pseudos)

panel_jeu = pygame_gui.elements.UIPanel(pygame.Rect(0, 0, LARGEUR, 60), manager=manager)
pygame_gui.elements.UILabel(pygame.Rect(10, 15, 50, 30), "Angle:", manager=manager, container=panel_jeu)
input_angle = pygame_gui.elements.UITextEntryLine(pygame.Rect(65, 15, 60, 30), manager=manager, container=panel_jeu)
pygame_gui.elements.UILabel(pygame.Rect(140, 15, 60, 30), "Vitesse:", manager=manager, container=panel_jeu)
input_vitesse0 = pygame_gui.elements.UITextEntryLine(pygame.Rect(205, 15, 60, 30), manager=manager, container=panel_jeu)
btn_tirer = pygame_gui.elements.UIButton(pygame.Rect(290, 15, 100, 30), "TIRER", manager=manager, container=panel_jeu)
label_info = pygame_gui.elements.UILabel(pygame.Rect(410, 15, 650, 30), "En attente...", manager=manager, container=panel_jeu)

input_angle.set_text("45")
input_vitesse0.set_text("600")
panel_jeu.hide() 

#variables globales
ville = Ville()
j1 = Joueur("J1", VIOLET, IMG_GORILLA1) 
j2 = Joueur("J2", ROSE, IMG_GORILLA2)
placer_joueurs(ville, j1, j2)

joueur_actif = j1
banane = None
vent = random.randint(-50, 50)
phase = "PSEUDOS"

#boucle principale
while True:
    #Entrée
    dt = horloge.tick(60) / 1000.0 
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == btn_valider:
                j1.nom = input_j1.get_text()
                j2.nom = input_j2.get_text()
                panel_pseudos.hide()
                panel_jeu.show()
                phase = "JEU"
                
            if event.ui_element == btn_tirer and phase == "JEU" and banane is None:
                try:
                    ang = float(input_angle.get_text())
                    frc = float(input_vitesse0.get_text())
                    if joueur_actif == j2: ang = 180 - ang #inversion angle joueur 2 pour la gauche
                    banane = Banane(joueur_actif.rect.centerx, joueur_actif.rect.top-10, ang, frc)
                except:
                    print("Chiffres uniquement !")

        manager.process_events(event)

    manager.update(dt)
    #jeu (maj)
    if phase == "JEU":
        label_info.set_text(f"Tour: {joueur_actif.nom} | Vent: {vent} | Score: {j1.score}-{j2.score}")
        
        if banane:
            banane.bouger(dt, vent)
            
            # Sortie
            if banane.x < 0 or banane.x > LARGEUR or banane.y > HAUTEUR:
                banane = None
                joueur_actif = j2 if joueur_actif == j1 else j1
                vent = random.randint(-50, 50)
                
            # Touché Joueur
            elif j1.rect.collidepoint(banane.x, banane.y) or j2.rect.collidepoint(banane.x, banane.y):
                touche = j1 if j1.rect.collidepoint(banane.x, banane.y) else j2
                touche.en_vie = False
                banane = None
                
                gagnant = j2 if touche == j1 else j1
                gagnant.score += 1
                
                if gagnant.score >= 2:
                    sauvegarder_score(j1, j2)
                    phase = "FIN"
                    label_info.set_text(f"VICTOIRE FINALE DE {gagnant.nom} !")
                else:
                    ville = Ville()
                    placer_joueurs(ville, j1, j2)
                    j1.en_vie = j2.en_vie = True
                    vent = random.randint(-50, 50)
                    
            # Touché Immeuble
            elif ville.touche_immeuble(banane.x, banane.y):
                ville.faire_trou(banane.x, banane.y)
                banane = None 
                joueur_actif = j2 if joueur_actif == j1 else j1
                vent = random.randint(-50, 50)

    # Affichage dessin 
    ecran.fill(NOIR)
    
    if phase == "JEU" or phase == "FIN":
        ecran.blit(ville.surface, (0,0))
        
        if j1.en_vie:
            if j1.image: # Si l'image existe, on l'affiche
                ecran.blit(j1.image, j1.rect.topleft)
            else: # Sinon, le rectangle rouge
                pygame.draw.rect(ecran, j1.couleur, j1.rect)

        if j2.en_vie:
            if j2.image: # Si l'image existe, on l'affiche
                ecran.blit(j2.image, j2.rect.topleft)
            else: # Sinon, le rectangle bleu
                pygame.draw.rect(ecran, j2.couleur, j2.rect)
                
        if banane:
            banane.dessiner(ecran)
        
    manager.draw_ui(ecran)
    pygame.display.flip()