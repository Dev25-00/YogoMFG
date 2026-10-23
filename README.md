# YogoMFG

Applique **DLSS Frame Generation x4** (mod SM86/SM75) aux jeux Steam, sur **RTX séries 20/30**.
Interface CustomTkinter, FR/EN. Windows x64.

> Débloque le Frame Generation NVIDIA sur Ampere/Turing, normalement réservé aux RTX 40+.
> Inutile sur RTX 40/50 (Frame Generation natif).

## Installation

```
pip install -r requirements.txt
```

Puis double-clic sur `YogoMFG.bat` (Python 3 requis), ou `python yogomfg.py`.

Le mod n'est **pas** dans ce dépôt (voir [Fichiers locaux](#fichiers-locaux)) : place le
payload dans `mod/` avant de lancer l'installation.

## Étapes

1. **Machine** : détecte GPU, VRAM, driver, CPU, RAM, moniteurs.
2. **Jeu** : liste les jeux Steam (toutes les bibliothèques), détecte le support FG, choix du `.exe` de rendu.
3. **Qualité** : mode d'upscaling DLSS recommandé selon ta config (non forcé, réglage interne au jeu).
4. **Cible FPS** (60/120/180) + écran (refresh, G-Sync/FreeSync) + portée **globale** ou **par jeu**.
5. **Appliquer** : pose `version.dll` + `dlssg_sm86.ini` (généré) + `dlssg_sm86\` à côté du `.exe`,
   backup des fichiers remplacés (`.yogobak`). Option panneau NVIDIA et mise à jour des upscalers.
6. **Analyse** : lit les logs du mod après une session (FPS et temps GPU réels) et propose des réglages.

Réglages mémorisés dans `config.json` : valeurs globales + override par jeu (appid).

## Panneau NVIDIA (expérimental)

Nécessite [nvidiaProfileInspector](https://github.com/Orbmu2k/nvidiaProfileInspector) (chemin dans
`config.json`, clé `npi_exe`). YogoMFG **exporte un backup `.nip` de tes profils avant toute modif**,
puis applique le cap FPS et le VRR (G-Sync/FreeSync). Les IDs de réglages viennent de
`Reference.xml` (source de vérité, ne pas deviner un ID). V-Sync et gestion de l'alimentation ne
sont pas écrits : conseillés à la main.

## Build

```
scripts\build.bat
```

Sortie : `dist\YogoMFG\YogoMFG.exe`. Lancer en administrateur pour le panneau NVIDIA.

## Structure

```
yogomfg.py        interface (stepper)
core/             logique : matériel, Steam, installation, NVCP, logs, config
assets/           logo et icône
scripts/          build.bat
YogoMFG.bat       lanceur
requirements.txt  dépendances Python
```

## Fichiers locaux

Exclus du dépôt par `.gitignore` :

- `mod/` : payload du mod (DLL NVIDIA et kernels recompilés, non MIT).
- `tools/` : nvidiaProfileInspector et `Reference.xml` (binaire tiers, non réhébergé).
- `config.json`, `*.nip`, `_covers/` : données utilisateur.
- `CLAUDE.md` : guide interne du projet.

## Ce que YogoMFG ne fait PAS

- Il ne **réhéberge pas** le mod ni les DLL NVIDIA (licence / EULA). Récupère le mod sur sa source d'origine.
- Il ne **force pas** le mode DLSS (Qualité / Performance) : il le recommande.
- Pas de lecture de l'offset d'overclock (illisible proprement ; seuls les clocks courants le sont).

## Crédits & licences

- Mod DLSSG SM86 : **Copyright (c) 2026 sdli1995**, licence MIT. *(URL du repo source à ajouter)*
- Famille de kernels SM75 : **Coldwood1026/dlssg_for_sm75** — https://github.com/Coldwood1026/dlssg_for_sm75
- Runtime `nvngx_dlssg.dll` / `nvngx_dlss.dll` : **NVIDIA**, non relicenciés.
- Les kernels recompilés et le runtime NVIDIA **ne sont pas** couverts par la licence MIT du mod.

Code de YogoMFG : *licence à choisir.*
