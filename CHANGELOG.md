# Changelog — YogoMFG

## 0.6.2 beta

- **Correctif majeur** : pour un jeu dont le profil NVIDIA est celui d'origine (ex. God of War Ragnarök), YogoMFG créait un
  profil « GoWR » que le pilote ignorait : cap FPS, G-Sync et multiplicateur n'étaient pas appliqués. L'appli interroge
  maintenant le pilote pour trouver le vrai profil du jeu, et relit après écriture avant de dire « appliqué ».
- Plus de grisage deviné d'après la version du plugin (faux : God of War 2.4.15 fait x6). L'appli **mesure** le
  multiplicateur obtenu en session, l'affiche (« dernière mesure : x4 ») et ne grise que ce qui est prouvé impossible.
- README : tableau des jeux testés.

## 0.6.1 beta

- Jeux dont le plugin DLSS-G plafonne à x4 (ex. Resident Evil Requiem) : **x5 et x6 sont grisés**, avec un message clair ;
  le multiplicateur est ramené au maximum possible au lieu de rester sur un choix sans effet.
- La suggestion « conseillé » ne dépasse plus le plafond du jeu.

## 0.6.0 beta

- Première version de test publique : x2 à x6 sans réinstaller, cap et G-Sync dans le profil du jeu, détection
  G-Sync/FreeSync (V-Sync jamais forcé sur un écran variable), sonde matérielle, analyse des saccades.
- **Bouton « Exporter le rapport »** (Analyser) : un .zip avec réglages, logs et résumé machine, sans nom d'utilisateur.
- Numéro de version affiché ; licences tierces dans `legal\`.
- 7 langues avec drapeaux (bouton globe), bouton Ko-fi, fenêtre « À propos » avec crédits (mod original : sdli1995).
- Textes et conseils alignés sur **x6** (plus de « x4 » en vitrine) ; x6 proposé d'office si le plugin du jeu le permet.
- README refait (EN + FR) : mission non lucrative, crédits, feuille de route (Frame Generation pour les jeux sans FG).

## 0.5.10

- Sonde : avertit quand la carte tourne en PCIe x4 (ou moins) au lieu de x16 en charge.

## 0.5.9

- Sécurité : un jeu sans profil NVIDIA n'écrit plus le multiplicateur dans le profil GLOBAL (il serait imposé à tous les jeux).

## 0.5.8

- **Changement rapide du multiplicateur** (x2…x6) sur la fiche du jeu : une seule écriture dans le profil NVIDIA du
  jeu, sans réinstaller. Le plafond du mod reste à x6 quand le pilote impose le multiplicateur.

## 0.5.7

- **Sonde de session** (case « Mesurer la session », puis bouton Launch) : enregistre GPU (puissance, mémoire vidéo,
  températures, limites actives, lien PCIe) et chaque cœur du processeur ; l'Analyser explique les chutes de wattage
  en mots simples (mémoire vidéo pleine, chaleur, limite de puissance, un cœur CPU à fond). Export `probe_last.csv`.
- Preset DLSS-G « B » (HUD plus propre) proposé ; case « Image de référence » (réglage le plus fidèle).

## 0.5.6

- **Jaquettes de secours** : API officielle du magasin Steam (jeux récents), anciens liens CDN, cache local de la
  bibliothèque Steam, puis bannière recadrée en carte. Les échecs sont mémorisés 12 h. Plus de jaquette manquante.

## 0.5.5

- **G-Sync / FreeSync détectés automatiquement** (plage de fréquences de l'écran lue dans son EDID). Avec un écran
  variable, YogoMFG ne force JAMAIS la synchronisation verticale ; l'option V-Sync n'apparaît que sans G-Sync/FreeSync.
  Appliquer un preset sans V-Sync remet le V-Sync d'origine si YogoMFG l'avait forcé.
- Le cap FPS et G-Sync du bouton « Panneau NVIDIA » s'écrivent dans le profil du JEU seulement (plus dans le global).
- Analyse : détecte un jeu limité par le processeur (GPU < 90 %) et des FPS réels figés (limiteur / V-Sync).
- Rappel dans l'écran simple : avec le multiplicateur imposé, ne change pas la Frame Generation dans le jeu.
- Correctif : chemin périmé de Profile Inspector (dossier temporaire du .exe) ; le NPI intégré est retrouvé.

## 0.5.3

- Liste des jeux en **grille de jaquettes** (sans noms ; nom au survol), boutons « Ajouter un dossier de jeux » et
  « Importer un jeu ». Jaquette générée si le jeu n'en a pas.
- Écran **simple** : un seul choix (multiplicateur x2…x6, valeur conseillée affichée) ; tout le reste dans « Avancé ».
  Textes réécrits en phrases courtes.
- **Mesure de session** (option Avancé) : lit les vrais FPS et l'utilisation GPU et explique en clair si la carte
  est saturée ou si un plafond limite (ex. 97 FPS en x6 = 16 images réelles).
- **Garde-fou** : pas de (ré)application si une config modifiée à la main existe, si un autre mod de FG est présent,
  si le jeu est lancé (fichier utilisé) ou si une autre DLL proxy est déjà installée. Une config YogoMFG ou d'usine
  est écrasée sans risque.
- Profils NVIDIA : toute écriture relit puis complète le profil (l'import NPI remplace sinon). Restauration de
  l'état d'origine vérifiée.
- Fenêtre plus grande et centrée.

## 0.5.0

- Interface sur une seule page : jeux Steam + chargement manuel, modal Options & Appliquer dans la fenêtre,
  statut d'installation par jeu, bouton Retirer (restaure les fichiers d'origine).
- Multiplicateur x2 à x6 choisi librement, imposé par jeu via le profil NVIDIA (clé « Override DLSSG multi-frame
  count »), sans toucher aux autres jeux ; réversible. Lecture du multiplicateur réellement créé dans l'Analyser.
- Détection des plugins DLSS-G, des autres mods de FG (OptiScaler, dlssg-to-fsr3, DLSS Enabler) et des anti-cheats.
- Avertissement anti-cheat / jeux en ligne (écran d'installation, premier lancement, confirmation avant d'appliquer) ;
  texte multilingue dans ANTICHEAT.md.
- Cap FPS NVIDIA écrit dans le vrai profil global (« Base Profile »).
- Installeur Windows (Inno Setup) et .exe portable ; données dans %LOCALAPPDATA%\YogoMFG.

## 0.4.0 — première version

Première version jouable : interface graphique qui applique le mod DLSS Frame Generation x4
(RTX 20/30) à un jeu Steam et optimise les réglages pilote selon la cible FPS.

- Stepper en 7 étapes : accueil, détection machine, choix du jeu, qualité d'upscaling, cible
  FPS & écran, application, analyse de session.
- Liste automatique des jeux Steam (toutes bibliothèques) avec jaquettes, détection du .exe de
  rendu et du support Frame Generation.
- Installation du mod à côté du .exe (version.dll + `dlssg_sm86.ini` généré + dossier), avec
  sauvegarde des fichiers remplacés. INI pré-réglé pour RTX 3070 (x4, Optimized 2, CatmullRomWarp,
  SuperResolution INT8).
- Panneau NVIDIA automatique via nvidiaProfileInspector inclus : cap « Max Frame Rate », et
  activation du VRR (G-Sync/FreeSync) en plein écran **et** fenêtré. IDs tirés du Reference.xml
  officiel. Sauvegarde des profils + bouton d'annulation.
- Détection des moniteurs et changement du taux de rafraîchissement depuis l'application.
- Mise à jour directe des DLL d'upscaling (DLSS / FSR / XeSS) dans le jeu.
- Analyse des logs du mod après une session : FPS et temps GPU réels, puis recommandations
  guidées pour atteindre la cible FPS ou améliorer l'image.
- Configuration globale + réglages par jeu. Interface bilingue FR/EN, thème noir/gris + vert Yogo.
- Packaging en .exe autonome (PyInstaller).

Limites connues : le mode DLSS (Qualité/Performance) est recommandé, pas forcé (réglage interne au
jeu). V-Sync et gestion de l'alimentation sont conseillés, pas écrits automatiquement.
