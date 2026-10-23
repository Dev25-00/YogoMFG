# Changelog — YogoMFG

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
