# Changelog — YogoMFG

## 0.7.0 beta

- Le plafond prouvé d'un jeu (ex. x4 pour Resident Evil Requiem, plugin DLSS-G 2.8.0) est lié à la version du plugin :
  si le jeu est mis à jour avec un autre plugin, le plafond est oublié et x5/x6 sont de nouveau proposés.
- Mode Manuel = liberté dans le jeu : xN devient un PLAFOND (INI du mod) et le pilote n'impose plus de multiplicateur ;
  le joueur choisit de x2 à xN dans le menu du jeu. Un multiplicateur imposé par une optimisation précédente est retiré.
  En Recommandé, le pilote impose toujours le multiplicateur calculé (nécessaire pour les jeux dont le menu plafonne).
- Deux modes au-dessus d'Optimiser : « Recommandé » (calcul automatique, par défaut) et « Manuel » (le joueur choisit
  x3, x4, x5 ou x6, borné au plafond prouvé du jeu). Le plafond FPS, G-Sync/FreeSync et le profil NVIDIA restent réglés
  automatiquement dans les deux modes. En Manuel, une ligne rappelle le coût VRAM de la génération d'images
  (environ +0,5 Go en 1440p, le même de x3 à x6) et ce qui change vraiment : moins d'images réelles.
- Le plafond FPS réglé par le joueur (« Nombre maximal d'images par seconde » de l'application NVIDIA, profil du jeu ou
  global) est respecté : la cible devient le plus petit des deux entre ce plafond et « fréquence − 3 ». La fiche l'annonce
  dès la sélection du jeu. YogoMFG distingue sa propre valeur écrite de celle du joueur.
- Retirer liste chaque fichier supprimé ou restauré, et la jaquette perd son bandeau YOGOMFG tout de suite (avant, il
  restait affiché jusqu'au redémarrage).
- Écran de chargement pendant Optimiser et Retirer : la liste des jeux et la fiche sont couvertes (spinner + message),
  rien d'autre n'est cliquable ; la langue et les Options logiciel attendent la fin.
- Le bouton devient « ✓ Déjà optimisé » (grisé) quand le jeu a déjà YogoMFG au bon multiplicateur, et la jaquette porte un
  bandeau vert « ✓ YOGOMFG ».
- Plus d'écriture silencieuse au démarrage : quand la dernière partie mesurée permet un meilleur multiplicateur, YogoMFG le
  propose (« ✨ Optimisation disponible (xN) » sur le bouton, bandeau ambre « ✨ OPTI DISPO » sur la jaquette) ; un clic l'applique.
  Après Optimiser, un message invite à jouer 5 minutes pour obtenir cette proposition.
- La liste n'affiche plus que les jeux qui contiennent la Frame Generation DLSS (`sl.dlss_g.dll` ou `nvngx_dlssg.dll`).
  Un jeu déjà optimisé reste visible pour pouvoir le retirer.
- Plus de bouton « Analyser » : la session est analysée en interne au clic suivant sur Optimiser (ou au démarrage)
  et le multiplicateur est recalibré tout seul. « Exporter le rapport » passe dans les Options logiciel.
- Le choix du proxy disparaît des Options logiciel : le mod est toujours posé en `version.dll`.
- Upscalers : nouveau bouton « Tout mettre à jour ». Pendant une mise à jour, tous les boutons (installer, restaurer,
  bibliothèque) sont grisés à l'écran jusqu'à la fin, au lieu de rester cliquables en apparence.

YogoMFG devient une application en un clic. La fiche du jeu n'a plus que deux grands boutons, « Optimiser ce jeu » et
« Retirer et restaurer », et une ligne de résultat (par exemple « x3 · 59 images calculées → 177 affichées »). Le
choix du multiplicateur, de la cible FPS, de la fréquence de l'écran, du préréglage DLSS-G, des options du mod et le
préréglage NVIDIA global ont disparu de l'interface : tout est décidé automatiquement. Cliquer « Optimiser » vaut
accord : il n'y a plus de fenêtre de confirmation, mais chaque écriture reste relue, affichée dans la console et
annulée par « Retirer et restaurer ».

- **Mod 0.4.1** (release de sdli1995 publiée par Coldwood1026). Pilote NVIDIA R580 ou plus récent exigé par le mod.
  Le fichier `dlssg_sm86.ini` ne contient plus que des clés valides avec des valeurs fixes et sûres : image identique au
  runtime officiel NVIDIA (`Optimized=1`, `Preset=A`), mesure de la session toujours active (`FrameTiming=1`),
  super-résolution du mod coupée. Les clés inventées des versions précédentes (HudFix, VBlankSync, INT8Boost) et le
  réglage avec pertes `Optimized=2` sont supprimés.
- **Multiplicateur automatique, de x3 à x6** (le x2 est laissé à la Frame Generation FSR d'AMD). La cible est la
  fréquence de l'écran le plus rapide, 3 FPS en dessous sur un écran G-Sync / FreeSync ; c'est aussi le cap FPS du
  profil du jeu. La première fois, le multiplicateur vise environ 55 images réelles par seconde (180 Hz → x3,
  240 Hz → x4, 360 Hz → x6). Ensuite YogoMFG se calibre sur la session mesurée : il prend le plus petit multiplicateur
  qui atteint la cible avec le nombre d'images réelles que la carte tient sans faiblir, respecte un plafond de FPS posé
  par le jeu ou l'utilisateur, ne dépasse jamais le maximum prouvé du jeu, et prévient en une ligne quand le jeu
  tomberait sous 45 images réelles (30 sur les cartes d'entrée de gamme). Le recalibrage se fait au clic suivant sur
  « Optimiser » ou au démarrage suivant de YogoMFG.
- **Profil NVIDIA** : dans le profil du jeu, cap FPS, G-Sync / FreeSync et nombre d'images générées ; dans le profil
  global, seulement le plafond de la Frame Generation (jusqu'à x6) et G-Sync / FreeSync en plein écran et fenêtré,
  jamais un multiplicateur imposé. Les valeurs globales d'origine sont sauvegardées avant la première écriture et
  remises quand plus aucun jeu n'utilise YogoMFG. Ré-optimiser un jeu ne remplace plus les valeurs d'origine mémorisées
  par les nôtres, et le retour arrière d'un jeu ne touche plus aux autres jeux.
- **Sauvegarde et restauration vérifiées** : avant d'écrire, chaque fichier du jeu qui serait écrasé est déplacé dans
  `YogoMFG_backup\` à côté du `.exe`, avec un `manifest.json` (chemin, SHA-256, remplacé ou ajouté). « Retirer et
  restaurer » supprime ce qui a été ajouté, remet chaque fichier remplacé, vérifie son SHA-256, supprime la sauvegarde
  et annule les réglages NVIDIA du jeu, sans passer par Steam. Les installations 0.6.x (fichiers `.yogobak`) sont
  reconnues et restaurées. Rien n'est touché si le jeu est lancé.
- **Analyse** : lecture des nouveaux journaux du mod 0.4.1 (`dlssg_sm86.log` et `frame_timing.txt`) ; les menus, pauses
  et cinématiques sont écartés des mesures.
- **README** : correction d'une erreur. Le mod n'est pas open source : ce sont des binaires tiers fermés. Les contrôles
  faits avant de l'embarquer (empreinte SHA-256, Microsoft Defender, signatures) et leur limite sont expliqués.

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
