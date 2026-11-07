"""YogoMFG - Frame Generation x2…x6 pour RTX 20/30, en un clic (jeux Steam solo/hors ligne).

CRÉDITS : le mod qui rend tout cela possible est « dlssg_for_sm86 / SM75 » de sdli1995
(https://github.com/sdli1995/dlssg_for_sm86, licence MIT). YogoMFG n'est qu'une interface qui l'installe et règle le
profil NVIDIA. Merci aussi à Orbmu2k (NVIDIA Profile Inspector) et à beeradmoore (liste de DLL de DLSS Swapper).
Développé avec l'aide de Claude Code (Anthropic), via l'extension Visual Studio Code.
Projet sans but lucratif, fait pour l'entraide et pour prolonger la vie de nos cartes graphiques.
UI CustomTkinter, thème Yogo (noir/gris, vert flashy).
"""
import os, sys, threading, webbrowser, ctypes
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageDraw, ImageFont
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from core import (i18n, report, probe, nvpreset, hardware, steam, fgdetect, inimaker, installer,
                  nvcp, config, upscalers, optadvice, loganalyze, display)

FROZEN = getattr(sys, "frozen", False)
RES = getattr(sys, "_MEIPASS", HERE)
DATA = (os.path.join(os.environ.get("LOCALAPPDATA") or os.path.dirname(sys.executable), "YogoMFG")
        if FROZEN else HERE)   # gelé (onefile) -> données dans %LOCALAPPDATA%, rien à côté du .exe
if FROZEN:
    os.makedirs(DATA, exist_ok=True)
MOD_ROOT = os.path.join(RES, "mod")
NPI_BUNDLED = os.path.join(RES, "tools", "npi", "nvidiaProfileInspector.exe")

KOFI_URL = "https://ko-fi.com/lahlouyoussef"
VERSION = "0.7.1 beta"

# palette : fond noir/gris, vert flashy pour textes/boutons uniquement
BG, SURF, SURF2, EDGE = "#0b0b0d", "#15151a", "#1f1f27", "#2c2c38"
GREEN, GREEN_D, TXT, DIM = "#b6ff4a", "#8fd82f", "#eef0f4", "#9aa0b0"
FONT = ("Segoe UI", 16)
FONT_B = ("Segoe UI", 16, "bold")
FONT_H = ("Segoe UI", 26, "bold")
FONT_T = ("Segoe UI", 40, "bold")
MONO = ("Consolas", 14)

TR = {
 "fr": {
  "sub": "Multi-Frame Generation x6 · RTX 20/30",
  "start": "Commencer", "back": "‹ Retour", "next": "Suivant ›", "apply": "Appliquer",
  "open_opts": "Options & Appliquer", "close": "Fermer",
  "soft_opts": "Options logiciel", "launch": "Launch", "analyser": "Analyser", "remove": "Retirer",
  "need_game": "Sélectionne un jeu et le .exe d'abord.",
  "remove_ask": "Retirer le mod et restaurer les fichiers d'origine (.yogobak) ?", "removing": "Retrait du mod…",
  "mfg_6x": "✓ Plugin DLSS-G ≥2.11.1 : 6X natif possible — règle le Frame Gen du jeu sur Dynamique/Auto.",
  "mfg_4x": "Plugin DLSS-G 4X : plafonné à 4X (6X fixé par le jeu, pas par le GPU/mod).",
  "mfg_noplugin": "Plugin DLSS-G (sl.dlss_g.dll) non trouvé — multiplicateur décidé par le jeu.",
  "force_mfg": "Forcer le multiplicateur (expérimental)",
  "force_mfg_on": "Forcer 5X/6X même si le jeu plafonne à 4X (ForcePluginFrames + MfgProbe). Peut saccader ou couper la FG selon le jeu — teste puis ouvre Analyser.",
  "force_blocked": "🔒 Indisponible pour ce jeu : son plugin DLSS-G (%s) n'est pas patchable. Forcer ferait x1 (FG coupée) ou saccaderait. Utilise le menu FG du jeu (max 4X).",
  "force_blocked_none": "🔒 Indisponible : plugin DLSS-G du jeu introuvable ou illisible.",
  "conflict": "⚠ Autre mod de FG détecté (%s) : deux mods de FG en même temps = saccades et son haché. Retire-le avant d'appliquer.",
  "unlock_drs": "Imposer le multiplicateur via le pilote NVIDIA",
  "unlock_drs_on": "Appliquer le multiplicateur choisi ci-dessus au profil NVIDIA de CE jeu (le menu du jeu est ignoré). Réversible. Admin requis.",
  "anticheat": "⛔ Anti-cheat détecté (%s) : jeu en ligne probable. N'applique PAS YogoMFG ici — risque de BANNISSEMENT DÉFINITIF.",
  "anticheat_ask": "Un anti-cheat (%s) est présent dans ce jeu.\n\nUtiliser une Frame Generation modifiée sur un jeu en ligne peut entraîner un BANNISSEMENT DÉFINITIF de ton compte, sans recours.\n\nContinuer quand même ?",
  "terms_title": "Avertissement — jeux en ligne et anti-cheat",
  "terms_body": "YogoMFG injecte des DLL dans le rendu des jeux. Les anti-cheats (EasyAntiCheat, BattlEye, Vanguard…) peuvent détecter cette injection et BANNIR définitivement ton compte, sans recours.\n\n• N'utilise JAMAIS YogoMFG sur un jeu en ligne ou multijoueur compétitif.\n• Réserve-le aux jeux solo / hors ligne.\n• Utilisation à tes risques : aucune garantie, les auteurs ne sont pas responsables d'un bannissement ou d'un dommage.\n• Non affilié à NVIDIA, AMD ni Intel.\n\nAs-tu lu et acceptes-tu ces conditions ?",
  "inst_yes": "● YogoMFG installé : %s", "inst_no": "○ Pas d'installation YogoMFG dans ce dossier",
  "inst_bak": "%d sauvegarde(s) d'origine", "apply_upd": "Mettre à jour",
  "nv_btn": "Optimiser NVIDIA", "nv_title": "Optimisation du profil NVIDIA global",
  "nv_goal": "Ton objectif", "nv_perf": "Performances maximales", "nv_bal": "Équilibré", "nv_qual": "Qualité maximale",
  "nv_vsync": "Anti-tearing : forcer la synchronisation verticale ON (recommandé avec G-Sync/FreeSync + Frame Generation)",
  "nv_will": "Sera écrit dans le profil global (réglages vérifiés uniquement) :",
  "nv_note": "Le mode DLSS (Qualité, Équilibré, DLAA…) et Reflex se règlent dans le jeu : YogoMFG ne les écrit pas, leurs valeurs pilote ne sont pas vérifiables. Retour arrière possible à tout moment.",
  "nv_apply": "Appliquer ce preset", "nv_revert": "Revenir à l'état d'origine", "nv_state": "Preset YogoMFG actuel : %s",
  "nv_none": "aucun (profil d'origine)", "nv_run": "⏳ Écriture dans le pilote NVIDIA…",
  "loading": "Chargement…", "none": "Aucune",
  "welcome_h": "Débloque la Frame Generation sur RTX 20/30",
  "welcome_p": "Choisis un jeu, applique le x6, joue — puis laisse l'analyse te guider.",
  "s_machine": "Ta machine", "s_game": "Choisir le jeu", "s_quality": "Qualité d'upscaling",
  "s_tune": "Cible FPS & écran", "s_apply": "Appliquer", "s_analyze": "Analyse de session",
  "manual": "Dossier manuel…", "exe": "Fichier .exe de rendu", "proxy": "Proxy (si version.dll non chargé)",
  "updaters": "Upscalers du jeu — installer la dernière version directement",
  "install_dll": "Installer la dernière", "fg_yes": "✓ Frame Generation NVIDIA détecté dans ce jeu.",
  "fg_no": "? Frame Generation non détecté — vérifie sur le web.",
  "no_ups": "Aucun upscaler (DLSS/FSR/XeSS) trouvé dans ce jeu.",
  "up_all": "Tout mettre à jour", "up_all_run": "Mise à jour de %d upscaler(s)… les boutons restent grisés jusqu'à la fin.",
  "up_all_done": "%d sur %d upscaler(s) mis à jour.",
  "scan_ups": "Analyse des upscalers…",
  "q_hint": "YogoMFG ne force PAS ce réglage (il est interne au jeu). Applique-le toi dans les "
            "options du jeu. Recommandé selon ta cible FPS.",
  "q_reco": "★ recommandé", "q_note": "Plus « Performance » = plus de FPS, image un peu moins nette.",
  "scope": "Portée", "scope_g": "Globale (tous les jeux)", "scope_j": "Ce jeu uniquement",
  "fps": "FPS cible", "mult": "Multiplicateur FG", "preset": "Preset DLSS-G",
  "monitor": "Moniteur", "refresh": "Rafraîchissement", "set_hz": "Changer le refresh",
  "sync": "Synchronisation écran", "gsync": "G-Sync", "freesync": "FreeSync",
  "sync_hint": "Avec G-Sync/FreeSync : YogoMFG active le VRR (plein écran ET fenêtré) + cap FPS, "
               "sans V-Sync. Sans VRR : active la V-Sync à la main.",
  "cap_is": "Cap FPS appliqué",
  "nvcp": "Panneau NVIDIA (automatique, via Profile Inspector inclus)",
  "force_mfg": "Écrit ForcePluginFrames=N + MfgProbe=1 dans l'INI du mod : patche le plugin du jeu pour demander 5X/6X même si son menu plafonne à 4X. Expérimental : selon le plugin, ça marche, ou ça saccade, ou ça coupe la Frame Generation. Après un test en jeu, ouvre Analyser : le log dit si le forçage a pris (plugin_mfg_force) ou non (plugin_mfg_unrecognized).",
  "nvcp_on": "Appliquer : cap Max Frame Rate + VRR/G-Sync (plein écran & fenêtré). Backup auto.",
  "revert": "Annuler NVCP", "admin": "Relancer en admin",
  "admin_warn": "⚠ Profile Inspector exige les droits admin. Relance en admin pour le NVCP.",
  "valider": "Valider › Analyse", "advice": "À faire dans le jeu",
  "an_goal": "Tu préfères", "goal_fps": "Plus de FPS", "goal_q": "Plus belle image",
  "an_run": "Analyser les logs", "an_hint": "Après avoir joué une session (FG activé), lance "
            "l'analyse : YogoMFG lit les mesures et te guide.",
  "apply_reco": "Appliquer la reco", "keep": "Garder mes choix",
  "did_title": "Ce que tu as fait dans le jeu (pour une meilleure proposition)",
  "did_fg": "Frame Generation activé", "did_reflex": "Reflex On", "did_rt": "Ray Tracing",
  "did_pt": "Path Tracing", "did_vsync": "V-Sync in-game OFF", "did_dlss": "Mode DLSS réglé :",
 },
 "en": {
  "sub": "Multi-Frame Generation x6 · RTX 20/30",
  "start": "Start", "back": "‹ Back", "next": "Next ›", "apply": "Apply",
  "open_opts": "Options & Apply", "close": "Close",
  "soft_opts": "Software options", "launch": "Launch", "analyser": "Analyze", "remove": "Remove",
  "need_game": "Pick a game and the .exe first.",
  "remove_ask": "Remove the mod and restore the original files (.yogobak)?", "removing": "Removing mod…",
  "mfg_6x": "✓ DLSS-G plugin ≥2.11.1: native 6X possible — set the game's Frame Gen to Dynamic/Auto.",
  "mfg_4x": "DLSS-G 4X plugin: capped at 4X (6X is set by the game, not the GPU/mod).",
  "mfg_noplugin": "DLSS-G plugin (sl.dlss_g.dll) not found — multiplier decided by the game.",
  "force_mfg": "Force multiplier (experimental)",
  "force_mfg_on": "Force 5X/6X even if the game caps at 4X (ForcePluginFrames + MfgProbe). May judder or disable FG depending on the game — test, then open Analyze.",
  "force_blocked": "🔒 Unavailable for this game: its DLSS-G plugin (%s) cannot be patched. Forcing would give x1 (FG off) or judder. Use the game's FG menu (max 4X).",
  "force_blocked_none": "🔒 Unavailable: the game's DLSS-G plugin is missing or unreadable.",
  "conflict": "⚠ Another FG mod detected (%s): two FG mods at once = judder and choppy audio. Remove it before applying.",
  "unlock_drs": "Enforce the multiplier through the NVIDIA driver",
  "unlock_drs_on": "Apply the multiplier chosen above to THIS game's NVIDIA profile (the in-game menu is ignored). Reversible. Admin required.",
  "anticheat": "⛔ Anti-cheat detected (%s): probably an online game. Do NOT apply YogoMFG here — risk of a PERMANENT BAN.",
  "anticheat_ask": "An anti-cheat (%s) is present in this game.\n\nUsing modified Frame Generation in an online game can get your account PERMANENTLY BANNED, with no appeal.\n\nContinue anyway?",
  "terms_title": "Warning — online games and anti-cheat",
  "terms_body": "YogoMFG injects DLLs into games' rendering. Anti-cheats (EasyAntiCheat, BattlEye, Vanguard…) can detect this injection and PERMANENTLY BAN your account, with no appeal.\n\n• NEVER use YogoMFG in an online or competitive multiplayer game.\n• Keep it for single-player / offline games.\n• Use at your own risk: no warranty, the authors are not liable for any ban or damage.\n• Not affiliated with NVIDIA, AMD or Intel.\n\nHave you read and do you accept these terms?",
  "inst_yes": "● YogoMFG installed: %s", "inst_no": "○ No YogoMFG install in this folder",
  "inst_bak": "%d original backup(s)", "apply_upd": "Update",
  "nv_btn": "Optimize NVIDIA", "nv_title": "Global NVIDIA profile optimization",
  "nv_goal": "Your goal", "nv_perf": "Maximum performance", "nv_bal": "Balanced", "nv_qual": "Maximum quality",
  "nv_vsync": "Anti-tearing: force vertical sync ON (recommended with G-Sync/FreeSync + Frame Generation)",
  "nv_will": "Will be written to the global profile (verified settings only):",
  "nv_note": "The DLSS mode (Quality, Balanced, DLAA…) and Reflex are set in the game: YogoMFG does not write them, their driver values cannot be verified. You can revert at any time.",
  "nv_apply": "Apply this preset", "nv_revert": "Revert to original state", "nv_state": "Current YogoMFG preset: %s",
  "nv_none": "none (original profile)", "nv_run": "⏳ Writing to the NVIDIA driver…",
  "loading": "Loading…", "none": "None",
  "welcome_h": "Unlock Frame Generation on RTX 20/30",
  "welcome_p": "Pick a game, apply x6, play — then let the analysis guide you.",
  "s_machine": "Your machine", "s_game": "Pick a game", "s_quality": "Upscaling quality",
  "s_tune": "Target FPS & display", "s_apply": "Apply", "s_analyze": "Session analysis",
  "manual": "Manual folder…", "exe": "Render .exe file", "proxy": "Proxy (if version.dll not loaded)",
  "updaters": "Game upscalers — install the latest version directly",
  "install_dll": "Install latest", "fg_yes": "✓ NVIDIA Frame Generation detected in this game.",
  "fg_no": "? Frame Generation not detected — check the web.",
  "no_ups": "No upscaler (DLSS/FSR/XeSS) found in this game.",
  "up_all": "Update all", "up_all_run": "Updating %d upscaler(s)… buttons stay greyed until it is done.",
  "up_all_done": "%d of %d upscaler(s) updated.",
  "scan_ups": "Scanning upscalers…",
  "q_hint": "YogoMFG does NOT force this (it is an in-game setting). Set it yourself in the game "
            "options. Recommended per FPS target.",
  "q_reco": "★ recommended", "q_note": "More 'Performance' = more FPS, slightly softer image.",
  "scope": "Scope", "scope_g": "Global (all games)", "scope_j": "This game only",
  "fps": "Target FPS", "mult": "FG multiplier", "preset": "DLSS-G preset",
  "monitor": "Monitor", "refresh": "Refresh rate", "set_hz": "Change refresh",
  "sync": "Display sync", "gsync": "G-Sync", "freesync": "FreeSync",
  "sync_hint": "With G-Sync/FreeSync: YogoMFG enables VRR (fullscreen AND windowed) + FPS cap, "
               "no V-Sync. Without VRR: enable V-Sync manually.",
  "cap_is": "Applied FPS cap",
  "nvcp": "NVIDIA panel (automatic, via bundled Profile Inspector)",
  "force_mfg": "Writes ForcePluginFrames=N + MfgProbe=1 into the mod INI: patches the game's plugin to request 5X/6X even if its menu caps at 4X. Experimental: depending on the plugin it works, judders, or disables Frame Generation. After testing in-game, open Analyze: the log says whether the force took (plugin_mfg_force) or not (plugin_mfg_unrecognized).",
  "nvcp_on": "Apply: Max Frame Rate cap + VRR/G-Sync (fullscreen & windowed). Auto backup.",
  "revert": "Revert NVCP", "admin": "Relaunch as admin",
  "admin_warn": "⚠ Profile Inspector requires admin. Relaunch as admin for NVCP.",
  "valider": "Confirm › Analysis", "advice": "Do this in the game",
  "an_goal": "You prefer", "goal_fps": "More FPS", "goal_q": "Better image",
  "an_run": "Analyze logs", "an_hint": "After playing a session (FG on), run the analysis: "
            "YogoMFG reads the metrics and guides you.",
  "apply_reco": "Apply recommendation", "keep": "Keep my choices",
 },
}

TIPS = {
 "fr": {
  "fps": "Le nombre d'images par seconde que tu veux atteindre. Plus haut = plus fluide mais "
         "demande un upscaling plus agressif et un bon frame-rate de base.",
  "mult": "Combien d'images sont affichées pour 1 image réellement calculée : x2 = 1 générée, x4 = 3, x6 = 5. "
          "Choisis selon ton écran et ta cible : FPS cible ÷ multiplicateur = FPS réels dont ton GPU a besoin "
          "(ex. 180 Hz en x6 = 30 FPS réels seulement ; en x3 = 60). Plus haut = plus de FPS affichés, mais plus "
          "d'artefacts et de latence si la base est basse. ★ Repères : jeux rapides/compétitifs x2-x3 ; "
          "solo fluide x4 ; écran 144-180 Hz avec base ≥ 30-40 FPS x5-x6. Le x6 exige un plugin DLSS-G récent "
          "dans le jeu OU l'option « Imposer le multiplicateur via le pilote » cochée.",
  "preset": "Auto = meilleure image du HUD. C (FG Lite) = coût GPU par image générée divisé par ~2 "
            "à 4X (mesuré sur RTX 3070 : −46…−54 %), HUD un peu moins propre. ★ Recommandé si ton FPS "
            "plafonne (35-60 FPS affichés en 5X/6X) : le goulot est le coût de la FG, pas le multiplicateur.",
  "sync": "G-Sync/FreeSync synchronise l'écran au GPU (zéro tearing sans latence). YogoMFG active "
          "le VRR plein écran ET fenêtré + cap FPS. Sans VRR : active la V-Sync à la main.",
  "monitor": "L'écran sur lequel tu joues. Son taux de rafraîchissement sert à calculer le cap FPS.",
  "refresh": "Change la fréquence de l'écran (Hz). Plus haut = plus fluide si l'écran le supporte.",
  "quality": "Mode d'upscaling DLSS dans le jeu. Qualité = plus net, Performance = plus de FPS. "
             "YogoMFG le recommande, tu l'appliques dans les options du jeu.",
  "nvcp": "Applique via Profile Inspector : cap Max Frame Rate + VRR/G-Sync (plein écran & fenêtré). "
          "Un backup des profils est fait avant.",
  "unlock_drs": "Le pilote NVIDIA peut imposer le multiplicateur au plugin du jeu (clé « Override DLSSG multi-frame count »). "
                "Coché : YogoMFG écrit le multiplicateur choisi (x2…x6) dans le profil de CE jeu : c'est lui qui s'applique, "
                "le menu du jeu est ignoré. Décoché : le jeu décide (limité par son plugin). Les autres jeux ne sont pas touchés. "
                "★ Recommandé : coché.",
  "scope": "Globale = s'applique à tous les jeux. Ce jeu = réglages propres à ce jeu seulement.",
 },
 "en": {
  "fps": "Frames per second you want to reach. Higher = smoother but needs more aggressive "
         "upscaling and a good base frame-rate.",
  "mult": "How many frames are shown for each really rendered frame: x2 = 1 generated, x4 = 3, x6 = 5. "
          "Pick it for your screen and target: target FPS ÷ multiplier = real FPS your GPU must deliver "
          "(e.g. 180 Hz at x6 = only 30 real FPS; at x3 = 60). Higher = more displayed FPS but more "
          "artifacts and latency when the base is low. ★ Guide: fast/competitive-feel games x2-x3; "
          "smooth single-player x4; 144-180 Hz screen with base ≥ 30-40 FPS x5-x6. x6 needs a recent DLSS-G "
          "plugin in the game OR the \"Enforce the multiplier through the NVIDIA driver\" option ticked.",
  "preset": "Auto = best HUD image. C (FG Lite) = GPU cost per generated frame roughly halved at 4X "
            "(measured on RTX 3070: −46…−54 %), slightly less clean HUD. ★ Recommended when your FPS "
            "stalls (35-60 shown at 5X/6X): the bottleneck is FG cost, not the multiplier.",
  "sync": "G-Sync/FreeSync syncs the display to the GPU (no tearing, no latency). YogoMFG enables "
          "VRR fullscreen AND windowed + FPS cap. Without VRR: enable V-Sync manually.",
  "monitor": "The screen you play on. Its refresh rate is used to compute the FPS cap.",
  "refresh": "Change the display refresh (Hz). Higher = smoother if the screen supports it.",
  "quality": "In-game DLSS upscaling mode. Quality = sharper, Performance = more FPS. YogoMFG "
             "recommends it, you set it in the game options.",
  "nvcp": "Applies via Profile Inspector: Max Frame Rate cap + VRR/G-Sync (fullscreen & windowed). "
          "Profiles are backed up first.",
  "unlock_drs": "The NVIDIA driver can force the multiplier onto the game's plugin (key \"Override DLSSG multi-frame count\"). "
                "Ticked: YogoMFG writes the chosen multiplier (x2…x6) into THIS game's profile: it wins and the in-game "
                "menu is ignored. Unticked: the game decides (limited by its plugin). Other games are untouched. "
                "★ Recommended: ticked.",
  "scope": "Global = applies to all games. This game = settings for this game only.",
 },
}


# --- textes courts et simples (surchargent les anciens) -------------------------------------------------
TR["fr"].update({
    "vrr_yes": "Écran détecté : %s, variable %d-%d Hz → compatible G-Sync / FreeSync.",
    "vrr_no": "Aucun écran G-Sync / FreeSync détecté : la synchronisation verticale peut aider.",
    "nv_vsync_novrr": "Écran sans G-Sync / FreeSync : forcer la synchronisation verticale (supprime les déchirures).",
    "nv_vrr_note": "Ton écran gère G-Sync / FreeSync : YogoMFG ne touche PAS à la synchronisation verticale.",
    "imposed_note": "Multiplicateur imposé : dans le jeu, ne change pas la Frame Generation et n'utilise pas « Dynamique ». Change-le ici.",
    "scanning": "Analyse du dossier du jeu…",
    "blk_foreign_ini": "Une config perso existe déjà (dlssg_sm86.ini modifiée à la main). YogoMFG ne l'écrase pas. Clique Retirer d'abord, ou garde-la.",
    "blk_other_proxy": "Déjà installé avec %s. Clique Retirer d'abord, puis réapplique.",
    "blk_locked": "%s est utilisé : ferme le jeu, puis réessaie.",
    "blk_clash": "Un autre mod de Frame Generation est là (%s). Retire-le d'abord.",
    "sub": "Frame Generation jusqu'à x6 · RTX 20/30",
    "simple_title": "Optimiser ce jeu", "mult_label": "Combien d'images en plus ?",
    "mult_help_2": "x2 : 1 image ajoutée pour 1 vraie. L'image la plus propre.",
    "mult_help_3": "x3 : 2 images ajoutées. Bon équilibre.",
    "mult_help_4": "x4 : 3 images ajoutées. Le choix de la plupart des joueurs.",
    "mult_help_5": "x5 : 4 images ajoutées. Pour un écran 144 Hz ou plus.",
    "mult_help_6": "x6 : 5 images ajoutées. FPS maximum. Il faut 30 vraies images par seconde.",
    "reco_mult_real": "★ Conseillé : x%d (tu fais %s vraies images/s, écran %d Hz).",
    "reco_mult_none": "★ Conseillé pour commencer : x4 (écran %d Hz). Joue, puis lance l'analyse pour affiner.",
    "advanced": "Avancé", "optimize": "Optimiser", "measure": "Mesurer la session",
    "measure_on": "Enregistre les vrais FPS pour expliquer ce qui te limite.",
    "add_lib": "Ajouter un dossier de jeux", "import_game": "Importer un jeu",
    "unlock_drs": "Multiplicateur imposé", "unlock_drs_on": "Impose ton choix dans le profil NVIDIA du jeu (réversible).",
    "force_mfg": "Patch du plugin (test)", "force_mfg_on": "Patcher le plugin du jeu. Risqué, déconseillé.",
    "q_hint": "À régler dans le jeu. Mode conseillé :", "nvcp_on": "Écrire le cap FPS et G-Sync pour ce jeu (sauvegarde auto).",
    "sync_hint": "G-Sync/FreeSync évite les déchirures. Sans écran VRR, active le V-Sync.",
})
TR["en"].update({
    "vrr_yes": "Screen detected: %s, variable %d-%d Hz → G-Sync / FreeSync compatible.",
    "vrr_no": "No G-Sync / FreeSync screen detected: vertical sync can help.",
    "nv_vsync_novrr": "Screen without G-Sync / FreeSync: force vertical sync (removes tearing).",
    "nv_vrr_note": "Your screen supports G-Sync / FreeSync: YogoMFG does NOT touch vertical sync.",
    "imposed_note": "Multiplier enforced: in the game, do not change Frame Generation and do not use \"Dynamic\". Change it here.",
    "did_title": "What you did in the game (for a better suggestion)", "did_dlss": "DLSS mode set:",
    "scanning": "Scanning the game folder…",
    "blk_foreign_ini": "A custom config already exists (dlssg_sm86.ini edited by hand). YogoMFG will not overwrite it. Click Remove first, or keep it.",
    "blk_other_proxy": "Already installed with %s. Click Remove first, then apply again.",
    "blk_locked": "%s is in use: close the game, then try again.",
    "blk_clash": "Another Frame Generation mod is here (%s). Remove it first.",
    "sub": "Frame Generation up to x6 · RTX 20/30",
    "simple_title": "Optimize this game", "mult_label": "How many extra frames?",
    "mult_help_2": "x2: 1 frame added per real one. The cleanest image.",
    "mult_help_3": "x3: 2 frames added. Good balance.",
    "mult_help_4": "x4: 3 frames added. Most players' choice.",
    "mult_help_5": "x5: 4 frames added. For a 144 Hz screen or more.",
    "mult_help_6": "x6: 5 frames added. Maximum FPS. You need 30 real frames per second.",
    "reco_mult_real": "★ Suggested: x%d (you get %s real frames/s, %d Hz screen).",
    "reco_mult_none": "★ Suggested to start: x4 (%d Hz screen). Play, then run the analysis to refine.",
    "advanced": "Advanced", "optimize": "Optimize", "measure": "Measure the session",
    "measure_on": "Records the real FPS to explain what limits you.",
    "add_lib": "Add a games folder", "import_game": "Import a game",
    "unlock_drs": "Enforced multiplier", "unlock_drs_on": "Enforce your choice in the game's NVIDIA profile (reversible).",
    "force_mfg": "Plugin patch (test)", "force_mfg_on": "Patch the game's plugin. Risky, not recommended.",
    "q_hint": "Set it in the game. Suggested mode:", "nvcp_on": "Write the FPS cap and G-Sync for this game (auto backup).",
    "sync_hint": "G-Sync/FreeSync prevents tearing. Without a VRR screen, enable V-Sync.",
})
TIPS["fr"].update({
    "fps": "Les FPS que tu vises. Mets la fréquence de ton écran.",
    "mult": "Images affichées pour 1 image vraiment calculée. Plus haut = plus de FPS, mais plus d'artefacts si la base est basse.",
    "preset": "Auto = HUD le plus propre. C = plus rapide, HUD un peu moins net.",
    "sync": "G-Sync/FreeSync = pas de déchirure. Sans écran VRR, active le V-Sync.",
    "monitor": "L'écran où tu joues.", "refresh": "Hz de ton écran. Plus haut = plus fluide.",
    "quality": "Mode DLSS du jeu. Qualité = net. Performance = plus de FPS.",
    "nvcp": "Écrit le cap FPS et G-Sync dans le profil NVIDIA. Sauvegarde auto.",
    "scope": "Global = tous les jeux. Ce jeu = seulement celui-ci.",
    "force_mfg": "Test risqué : patche le plugin du jeu. Peut couper la Frame Generation.",
    "unlock_drs": "Le pilote NVIDIA peut imposer le multiplicateur. Coché : ton choix gagne sur le menu du jeu. Décoché : le jeu décide. ★ Coché.",
})
TIPS["en"].update({
    "fps": "The FPS you aim for. Use your screen's refresh rate.",
    "mult": "Frames shown per really rendered frame. Higher = more FPS, but more artifacts if the base is low.",
    "preset": "Auto = cleanest HUD. C = faster, slightly softer HUD.",
    "sync": "G-Sync/FreeSync = no tearing. Without a VRR screen, enable V-Sync.",
    "monitor": "The screen you play on.", "refresh": "Your screen's Hz. Higher = smoother.",
    "quality": "The game's DLSS mode. Quality = sharp. Performance = more FPS.",
    "nvcp": "Writes the FPS cap and G-Sync in the NVIDIA profile. Auto backup.",
    "scope": "Global = all games. This game = only this one.",
    "force_mfg": "Risky test: patches the game's plugin. May turn Frame Generation off.",
    "unlock_drs": "The NVIDIA driver can enforce the multiplier. Ticked: your choice beats the game's menu. Unticked: the game decides. ★ Ticked.",
})


TR["fr"].update({
    "mfg_6x": "✓ Plugin DLSS-G récent : le x6 est possible.", "mfg_4x": "Plugin DLSS-G ancien : le jeu peut plafonner à x4. Joue une fois : YogoMFG mesure le vrai maximum.",
    "support": "Me soutenir", "support_tip": "Offre-moi un café : ça aide à faire vivre et améliorer YogoMFG. Merci !",
    "report_btn": "Exporter le rapport", "report_ok": "✓ Rapport enregistré : %s",
    "report_hint": "Envoie ce fichier .zip si tu as un problème : il contient tes réglages et tes logs (sans ton nom d'utilisateur).",
    "quick_lbl": "Changer vite le multiplicateur :", "quick_run": "⏳ Passage à x%d dans le profil NVIDIA…",
    "quick_ok": "✓ x%d enregistré. Relance le jeu (ou coupe puis remets la Frame Generation dans son menu).",
    "probe_on": "Sonde GPU/CPU démarrée : joue quelques minutes, puis clique Analyser.",
    "ref_q": "Image de référence", "ref_q_on": "Image la plus fidèle (un peu plus lent, environ 3 %).",
})
TR["en"].update({
    "mfg_6x": "✓ Recent DLSS-G plugin: x6 is possible.", "mfg_4x": "Old DLSS-G plugin: the game may cap at x4. Play once: YogoMFG measures the real maximum.",
    "support": "Support me", "support_tip": "Buy me a coffee: it helps keep YogoMFG alive and improving. Thank you!",
    "report_btn": "Export report", "report_ok": "✓ Report saved: %s",
    "report_hint": "Send this .zip if you have a problem: it holds your settings and logs (without your user name).",
    "quick_lbl": "Quick multiplier change:", "quick_run": "⏳ Switching to x%d in the NVIDIA profile…",
    "quick_ok": "✓ x%d saved. Restart the game (or turn Frame Generation off then on in its menu).",
    "probe_on": "GPU/CPU probe started: play a few minutes, then click Analyze.",
    "ref_q": "Reference image", "ref_q_on": "Most faithful image (slightly slower, about 3 %).",
})
TIPS["fr"]["preset"] = ("Auto = le jeu décide. B = HUD plus propre si le jeu le permet. "
                        "C = plus rapide, HUD un peu moins net. Ghosting : baisse le multiplicateur (x4 ou x3).")
TIPS["en"]["preset"] = ("Auto = the game decides. B = cleaner HUD if the game allows it. "
                        "C = faster, slightly softer HUD. Ghosting: lower the multiplier (x4 or x3).")

TIPS["fr"].update({
    "fps": "Les images par seconde que tu veux atteindre. Mets la vitesse de ton écran (par exemple 180 si ton écran est à 180 Hz).",
    "mult": "L'ordinateur invente des images entre les vraies pour que tout paraisse plus fluide. x4 = 3 images inventées pour 1 vraie. Plus c'est haut, plus tu as de FPS, mais plus l'image peut baver si ta carte est lente. Pour toi : x3 ou x4.",
    "preset": "Réglage avancé de la façon dont le jeu dessine l'interface (barres de vie, menus). « Auto » convient presque toujours. Change-le seulement si l'interface tremble.",
    "sync": "G-Sync ou FreeSync : ton écran adapte sa vitesse à ta carte, sans image déchirée. Si ton écran n'a pas ça, choisis « Aucune ».",
    "monitor": "L'écran sur lequel tu joues.",
    "refresh": "La vitesse de ton écran, en Hz. Plus c'est haut, plus c'est fluide. Mets le maximum de ton écran.",
    "quality": "Le mode d'image DLSS, à régler dans le jeu. Qualité = image plus nette. Performance = plus de FPS.",
    "nvcp": "Écrit un plafond de FPS et active G-Sync pour ce jeu dans le panneau NVIDIA. Une sauvegarde est faite avant.",
    "scope": "Global = pour tous tes jeux. Ce jeu = seulement celui-ci.",
    "force_mfg": "Test risqué : modifie le jeu pour qu'il demande plus d'images inventées. Peut couper la fonction. À laisser décoché.",
    "unlock_drs": "Ton choix de multiplicateur est imposé au jeu par le pilote NVIDIA, même si le jeu propose autre chose dans ses menus. Coché = recommandé.",
})
TIPS["en"].update({
    "fps": "The frames per second you want. Use your screen's speed (for example 180 if your screen is 180 Hz).",
    "mult": "The computer invents frames between the real ones so everything looks smoother. x4 = 3 invented frames for 1 real one. Higher = more FPS, but the picture can smear if your card is slow. For you: x3 or x4.",
    "preset": "Advanced setting for how the game draws its interface (health bars, menus). \"Auto\" is right almost always. Change it only if the interface shakes.",
    "sync": "G-Sync or FreeSync: your screen adapts its speed to your card, with no torn image. If your screen does not have it, choose \"None\".",
    "monitor": "The screen you play on.",
    "refresh": "Your screen's speed, in Hz. Higher is smoother. Use your screen's maximum.",
    "quality": "The DLSS picture mode, set in the game. Quality = sharper image. Performance = more FPS.",
    "nvcp": "Writes an FPS cap and turns on G-Sync for this game in the NVIDIA panel. A backup is made first.",
    "scope": "Global = for all your games. This game = only this one.",
    "force_mfg": "Risky test: changes the game so it asks for more invented frames. May turn the feature off. Leave unticked.",
    "unlock_drs": "Your multiplier choice is forced on the game by the NVIDIA driver, even if the game offers something else in its menus. Ticked = recommended.",
})


TR["en"].update({
    "mult_capped": "🔒 Measured in your last session: this game stops at x%d, so higher multipliers are greyed out.",
    "last_measured": " · last measured: x%d",
    "change_exe": "Change .exe", "logs_found": "📊 Logs found — open Analyze for the suggestion.",
    "did_fg": "Frame Generation ON", "did_reflex": "Reflex ON", "did_rt": "Ray Tracing", "did_pt": "Path Tracing",
    "did_vsync": "V-Sync in-game OFF",
    "about_btn": "About / Credits", "about_title": "About YogoMFG",
    "about_text": "YogoMFG is a non-profit project, made to help each other and to improve the daily life of the older "
                 "graphics cards we still rely on, and will for a few more years. Thank you to everyone who downloads and tests it! "
                 "Please send us your feedback, bugs and issues (Analyze → Export report): we are here to help.\n\n"
                 "It is possible thanks to the work of sdli1995 (the dlssg_for_sm86 / SM75 mod), Orbmu2k (NVIDIA Profile Inspector) "
                 "and beeradmoore (DLSS Swapper's DLL list). Built with Claude Code (Anthropic), through the Visual Studio Code extension.",
})
TR["fr"].update({
    "mult_capped": "🔒 Mesuré à ta dernière session : ce jeu s'arrête à x%d, les multiplicateurs au-dessus sont grisés.",
    "last_measured": " · dernière mesure : x%d",
    "change_exe": "Changer le .exe", "logs_found": "📊 Logs trouvés — ouvre Analyser pour la proposition.",
    "about_btn": "À propos / Crédits", "about_title": "À propos de YogoMFG",
    "about_text": "YogoMFG est un projet sans but lucratif, fait pour s'entraider et améliorer le quotidien des anciennes cartes "
                  "graphiques auxquelles on tient encore, et sur lesquelles on compte encore quelques années. Merci à toutes celles "
                  "et ceux qui le téléchargent et le testent ! Envoyez-nous vos retours, bugs et problèmes (Analyser → Exporter le "
                  "rapport) : nous sommes là pour vous aider.\n\n"
                  "Il existe grâce au travail de sdli1995 (le mod dlssg_for_sm86 / SM75), d'Orbmu2k (NVIDIA Profile Inspector) et de "
                  "beeradmoore (liste de DLL de DLSS Swapper). Développé avec Claude Code (Anthropic), via l'extension Visual Studio Code.",
})
TR["fr"].update({                           # 0.7.0 : un clic pour optimiser, un clic pour tout remettre
    "optimize_game": "Optimiser ce jeu", "remove_restore": "Retirer et restaurer",
    "mode_auto": "Recommandé", "mode_manual": "Manuel", "opt_update": "↻ Mettre à jour l'optimisation (x%d)",
    "opt_all": "Optimiser tous les jeux", "rm_all": "Retirer de tous les jeux", "opt_all_go": "Optimiser tout",
    "opt_all_hint": "%d jeux compatibles. Recommandé : YogoMFG calcule le meilleur multiplicateur pour chaque jeu. Manuel : le même plafond pour tous, puis tu choisis dans le menu de chaque jeu.",
    "opt_all_cap": "En Manuel, le plafond prouvé d'un jeu (ex. Resident Evil Requiem à x4) est indicatif seulement : tu peux quand même choisir x5 ou x6, le jeu donnera ce qu'il peut. Les jeux lancés ou protégés par un anti-cheat sont sautés.",
    "busy_opt_all": "Optimisation de %d jeux en cours…", "busy_rm_all": "Restauration de %d jeux en cours…",
    "skip_ac": "sauté : anti-cheat (%s)", "skip_busy": "sauté : jeu lancé ou autre mod présent",
    "rm_all_ask": "Retirer YogoMFG de %d jeu(x) et remettre leurs fichiers et réglages NVIDIA d'origine ?", "cap_reset": "Jeu mis à jour (plugin DLSS-G %s → %s) : l'ancien plafond est oublié, x5 et x6 sont de nouveau proposés.", "mult_free": "Multiplicateur libre : choisis de x2 à x%d dans le menu du jeu (le pilote n'impose plus rien).", "opt_apply": "Appliquer x%d",
    "vram_note": "VRAM : la génération d'images prend environ +0,5 Go en 1440p (+0,35 Go en 1080p), autant en x3 qu'en x6. Ce qui change avec le multiplicateur : moins d'images réelles, donc un peu plus de latence et d'artefacts possibles. Le plafond, G-Sync et le profil NVIDIA restent réglés automatiquement.",
    "cap_kept": "Plafond FPS de ton profil NVIDIA respecté : %d images affichées au maximum.",
    "opt_done": "↺ Ré-optimiser (x%d)", "opt_better": "✨ Optimisation disponible (x%d)",
    "better_log": "optimisation disponible : x%d → x%d d'après ta dernière partie.",
    "after_opt_hint": "Joue 5 minutes avec la génération d'images activée : au prochain lancement, YogoMFG lira tes mesures et te proposera une meilleure optimisation si elle existe.",
    "busy_opt": "Optimisation en cours…", "busy_rm": "Restauration du jeu d'origine…", "busy_cal": "Calibrage en cours…",
    "busy_hint": "Ne ferme pas YogoMFG : ça prend quelques secondes.",
    "tip_optimize": "Pose le mod Frame Generation, règle le profil NVIDIA de CE jeu et le plafond x6 du profil global. Tout est choisi pour une image "
                    "propre : le plus petit multiplicateur (x3 à x6) qui remplit la fréquence de "
                    "ton écran. Les fichiers d'origine sont sauvegardés avant.",
    "tip_remove": "Retire tout ce que YogoMFG a posé dans ce jeu, remet les fichiers d'origine (vérifiés octet par "
                  "octet) et annule les réglages NVIDIA de ce jeu. Sans Steam.",
    "result": "x%d · %d images calculées → %d affichées", "result_plan": "Optimiser fera : %s",
    "result_cal": "Calibré : x%d, %d images réelles → %d affichées",
    "warn_soft": "image moins nette : baisser un réglage graphique dans le jeu (DLSS Équilibré, ombres)",
    "hz_unknown": "fréquence de l'écran inconnue : x2, pas de cap FPS",
    "opt_files": "Pose du mod (fichiers d'origine sauvegardés dans YogoMFG_backup)…",
    "opt_nv": "Profil NVIDIA du jeu : cap %d FPS%s…", "opt_mult": "Profil NVIDIA du jeu : multiplicateur x%d…",
    "need_admin_nv": "droits administrateur requis.",
    "rc_global": "Profil global : plafond x6 (+ VRR)",
    "gsync_hint": "Écran FreeSync ? Active une fois « G-SYNC Compatible » dans le Panneau de configuration NVIDIA → "
                  "Affichage → Configurer G-SYNC. C'est un réglage de l'écran : YogoMFG ne peut ni le lire ni le changer.",
    "rc_mod": "Mod x%d + INI", "rc_cap": "Cap FPS %d dans le profil du jeu", "rc_mult": "Multiplicateur x%d dans le profil du jeu",
    "recap": "── Récapitulatif ──", "ok_v": "OK", "ko_v": "NON appliqué",
    "done_hint": "Lance le jeu (bouton Launch), active la Frame Generation dans ses options graphiques, joue deux "
                 "minutes, puis « Analyser ».",
    "remove_ask2": "Retirer le mod de ce jeu, remettre ses fichiers d'origine (vérifiés) et annuler les réglages NVIDIA "
                   "de ce jeu ?",
    "rm_files_err": "Fichiers : %s", "rm_done": "✓ Jeu remis dans son état d'origine.",
    "rm_need_admin": "Les réglages NVIDIA de ce jeu restent en place : relance YogoMFG en administrateur puis "
                     "« Retirer et restaurer » à nouveau.",
})
TR["en"].update({
    "optimize_game": "Optimize this game", "remove_restore": "Remove and restore",
    "mode_auto": "Recommended", "mode_manual": "Manual", "opt_update": "↻ Update the optimization (x%d)",
    "opt_all": "Optimize all games", "rm_all": "Remove from all games", "opt_all_go": "Optimize all",
    "opt_all_hint": "%d compatible games. Recommended: YogoMFG works out the best multiplier for each game. Manual: the same ceiling for all, then you pick in each game's menu.",
    "opt_all_cap": "In Manual, a game's proven ceiling (e.g. Resident Evil Requiem at x4) is informational only: you can still pick x5 or x6 — the game will deliver what it can. Running games and games with anti-cheat are skipped.",
    "busy_opt_all": "Optimizing %d games…", "busy_rm_all": "Restoring %d games…",
    "skip_ac": "skipped: anti-cheat (%s)", "skip_busy": "skipped: game running or another mod present",
    "rm_all_ask": "Remove YogoMFG from %d game(s) and restore their original files and NVIDIA settings?", "cap_reset": "Game updated (DLSS-G plugin %s → %s): the old ceiling is forgotten, x5 and x6 are offered again.", "mult_free": "Free multiplier: pick x2 to x%d in the game menu (the driver no longer forces anything).", "opt_apply": "Apply x%d",
    "vram_note": "VRAM: frame generation takes about +0.5 GB at 1440p (+0.35 GB at 1080p), the same at x3 and x6. What changes with the multiplier: fewer real frames, so a little more latency and possible artefacts. The fps cap, G-Sync and the NVIDIA profile stay automatic.",
    "cap_kept": "Your NVIDIA profile fps limit is kept: %d displayed frames at most.",
    "opt_done": "↺ Re-optimize (x%d)", "opt_better": "✨ Optimization available (x%d)",
    "better_log": "optimization available: x%d → x%d from your last session.",
    "after_opt_hint": "Play 5 minutes with frame generation on: at the next start, YogoMFG reads your measurements and offers a better optimization if there is one.",
    "busy_opt": "Optimizing…", "busy_rm": "Restoring the original game…", "busy_cal": "Calibrating…",
    "busy_hint": "Do not close YogoMFG: it takes a few seconds.",
    "tip_optimize": "Installs the Frame Generation mod, sets THIS game's NVIDIA profile and the global x6 ceiling. Everything is chosen for a "
                    "clean image: the smallest multiplier (x3 to x6) that fills your screen's refresh rate. The "
                    "original files are backed up first.",
    "tip_remove": "Removes everything YogoMFG put in this game, puts the original files back (checked byte for byte) "
                  "and undoes this game's NVIDIA settings. No Steam needed.",
    "result": "x%d · %d rendered frames → %d displayed", "result_plan": "Optimize will set: %s",
    "result_cal": "Calibrated: x%d, %d real frames → %d displayed",
    "warn_soft": "less sharp image: lower a graphics setting in the game (DLSS Balanced, shadows)",
    "hz_unknown": "screen refresh rate unknown: x2, no FPS cap",
    "opt_files": "Installing the mod (original files backed up in YogoMFG_backup)…",
    "opt_nv": "Game NVIDIA profile: %d FPS cap%s…", "opt_mult": "Game NVIDIA profile: x%d multiplier…",
    "need_admin_nv": "administrator rights required.",
    "rc_global": "Global profile: x6 ceiling (+ VRR)",
    "gsync_hint": "FreeSync screen? Turn on \"G-SYNC Compatible\" once in NVIDIA Control Panel → Display → Set up "
                  "G-SYNC. It is a screen setting: YogoMFG can neither read nor change it.",
    "rc_mod": "Mod x%d + INI", "rc_cap": "%d FPS cap in the game profile", "rc_mult": "x%d multiplier in the game profile",
    "recap": "── Summary ──", "ok_v": "OK", "ko_v": "NOT applied",
    "done_hint": "Start the game (Launch button), turn Frame Generation on in its graphics options, play two minutes, "
                 "then \"Analyze\".",
    "remove_ask2": "Remove the mod from this game, put its original files back (checked) and undo this game's NVIDIA "
                   "settings?",
    "rm_files_err": "Files: %s", "rm_done": "✓ Game back to its original state.",
    "rm_need_admin": "This game's NVIDIA settings are still in place: restart YogoMFG as administrator, then \"Remove "
                     "and restore\" again.",
})
for _c in i18n.CODES:                       # langues supplémentaires : ce qui manque retombe sur l'anglais
    if _c not in ("fr", "en"):
        TR[_c] = {**TR["en"], **i18n.section("TR", _c)}
        TIPS[_c] = {**TIPS["en"], **i18n.section("TIPS", _c)}


class Tooltip:
    """Infobulle lisible : grande police, fort contraste, cadre vert. Survol (rapide) OU clic sur le « ⓘ » (reste affichée)."""
    def __init__(self, widget, text, click=False):
        self.w, self.text, self.tip, self._after, self._pin = widget, text, None, None, False
        self._click = click
        widget.bind("<Enter>", self._enter, add="+")
        widget.bind("<Leave>", self._leave, add="+")
        widget.bind("<Button-1>", self._clicked, add="+")

    def _enter(self, _):
        self._cancel()
        self._after = self.w.after(150, self._show)

    def _cancel(self):
        if self._after:
            try: self.w.after_cancel(self._after)
            except Exception: pass
            self._after = None

    def _show(self):
        if self.tip or not self.text:
            return
        self.tip = tw = ctk.CTkToplevel(self.w)
        tw.overrideredirect(True)
        try:
            tw.attributes("-topmost", True)
        except Exception:
            pass
        box = ctk.CTkFrame(tw, fg_color="#101014", border_color=GREEN, border_width=2, corner_radius=10)
        box.pack()
        ctk.CTkLabel(box, text=self.text, font=("Segoe UI", 17), text_color="#ffffff", fg_color="transparent",
                     wraplength=520, justify="left").pack(padx=16, pady=12)
        tw.update_idletasks()
        sw, sh = tw.winfo_screenwidth(), tw.winfo_screenheight()
        x = min(self.w.winfo_rootx() + 18, sw - tw.winfo_width() - 10)
        y = self.w.winfo_rooty() + self.w.winfo_height() + 6
        if y + tw.winfo_height() > sh - 10:                         # pas assez de place en bas : au-dessus du widget
            y = max(10, self.w.winfo_rooty() - tw.winfo_height() - 6)
        tw.geometry(f"+{max(0, x)}+{y}")
        self.w.after(20000 if self._pin else 12000, self._hide)   # sécurité : auto-disparition

    def _leave(self, _=None):
        if not self._pin:
            self._hide()

    def _clicked(self, _=None):
        """Sur le « ⓘ » : un clic épingle l'infobulle (elle reste), un second clic la ferme."""
        if not self._click:
            self._hide()
            return
        if self.tip and self._pin:
            self._hide()
        else:
            self._hide()
            self._pin = True
            self._show()

    def _hide(self, _=None):
        self._cancel()
        self._pin = False
        if self.tip:
            try: self.tip.destroy()
            except Exception: pass
            self.tip = None


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.title("YogoMFG " + VERSION)
        w, h = min(1360, self.winfo_screenwidth() - 100), min(900, self.winfo_screenheight() - 120)   # grande fenêtre : jaquettes + fiche du jeu
        self.geometry(f"{w}x{h}+{(self.winfo_screenwidth() - w) // 2}+{max(10, (self.winfo_screenheight() - h) // 2 - 20)}")
        self.minsize(min(1180, w), min(740, h))
        self.bind("<Configure>", self._on_win_configure, add="+")
        self.configure(fg_color=BG)
        try:
            self.iconbitmap(os.path.join(RES, "assets", "yogo.ico"))
        except Exception:
            pass

        self.cfg = config.load()
        self.lang = self.cfg.get("lang") if self.cfg.get("lang") in i18n.CODES else i18n.detect()
        self.hw, self.games, self.game = {}, [], None
        self.monitors, self.refresh = [], 0
        self._busy = False
        self._caps = {}             # exe -> plafond FPS réglé par le joueur (profil NVIDIA), respecté par le plan
        self._better = set()        # jeux optimisés pour lesquels une session mesurée propose un meilleur multiplicateur
        self._mfg_cap = 4
        self._mfg_ver = None
        self._anticheat = []
        self._clash = []
        self._cover_img = None
        self.exe = ctk.StringVar()
        self.proxy = ctk.StringVar(value=self.cfg.get("proxy", "version.dll"))
        self.quality = ctk.StringVar(value=self.cfg.get("global", {}).get("dlss_quality", "balanced"))   # analyse seulement
        self._stats = {}            # .exe -> résumé de la dernière session mesurée (calibrage du multiplicateur)
        self._ups_cache = {}        # dossier du jeu -> (upscalers, manifeste) : affichage instantané au changement de jeu
        self._ups_sig = None
        self._up_busy = False       # boutons figés (install/restauration en cours ou confirmation affichée)
        self._up_dl = False         # téléchargement en cours -> barre de progression
        self._up_tok = 0            # jeton d'opération : seul le rescan de la dernière opération libère _up_busy
        self._up_last = None        # dernier message inline (texte, couleur) du jeu courant
        self._up_game = None
        self._probe = None
        self._scanned = False
        self.vrr = None                           # (min, max, nom) de l'écran si G-Sync/FreeSync, sinon None
        self._closing = False
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._thumbs, self._cards, self._grid_gen = {}, {}, 0
        self._cover_pool = ThreadPoolExecutor(max_workers=4)
        self.goal = ctk.StringVar(value="fps")
        npi = self.cfg.get("npi_exe", "")
        if not (npi and os.path.isfile(npi)):          # chemin périmé (le dossier temporaire du .exe change à chaque lancement)
            npi = NPI_BUNDLED if os.path.isfile(NPI_BUNDLED) else ""
        self.npi = ctk.StringVar(value=npi)

        self._banner()
        ctk.CTkFrame(self, fg_color=GREEN, height=2, corner_radius=0).pack(fill="x", padx=20)  # liseré sharp
        # fond : image (placeholder dégradé, à remplacer par une photo falaise/avalanche) derrière un body transparent
        wrap = ctk.CTkFrame(self, fg_color=BG, border_color="#3c5a26", border_width=2, corner_radius=16)
        wrap.pack(fill="both", expand=True, padx=20, pady=10)
        self.body = wrap
        self._bg_lbl = None
        try:
            self._bg_img = ctk.CTkImage(Image.open(os.path.join(RES, "assets", "bg.png")), size=(1180, 820))
            self._bg_lbl = ctk.CTkLabel(wrap, image=self._bg_img, text="")   # fond, derrière les cartes (visible dans les marges)
            self._bg_lbl.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception:
            pass
        self._build_page()
        self.after(700, self._check_terms)   # avertissement anti-cheat, une seule fois

    def L(self, k): return TR[self.lang].get(k) or TR["en"].get(k, k)

    def _info(self, parent, key):
        lbl = ctk.CTkLabel(parent, text=" ⓘ ", font=("Segoe UI", 22, "bold"), text_color=GREEN, cursor="hand2")
        Tooltip(lbl, TIPS[self.lang].get(key, ""), click=True)
        return lbl

    def _label_tip(self, parent, text, key, color=None):
        """Ligne : libellé + ⓘ avec tooltip. Retourne le frame."""
        f = ctk.CTkFrame(parent, fg_color="transparent")
        ctk.CTkLabel(f, text=text, font=FONT_B, text_color=color or DIM).pack(side="left")
        self._info(f, key).pack(side="left")
        return f

    def _banner(self):
        top = ctk.CTkFrame(self, fg_color="transparent"); top.pack(fill="x", padx=20, pady=(16, 2))
        try:
            img = ctk.CTkImage(Image.open(os.path.join(RES, "assets", "yogo_small.png")), size=(56, 56))
            ctk.CTkLabel(top, image=img, text="").pack(side="left")
        except Exception:
            pass
        ctk.CTkLabel(top, text="  YogoMFG", font=FONT_T, text_color=GREEN).pack(side="left")
        self._b_sub = ctk.CTkLabel(top, text=self.L("sub"), font=FONT, text_color=DIM)
        self._b_sub.pack(side="left", padx=16)
        self._b_ver = ctk.CTkLabel(top, text="v" + VERSION, font=("Segoe UI", 13, "bold"), text_color=BG,
                                   fg_color=GREEN_D, corner_radius=8, width=96, height=24)
        self._b_ver.pack(side="left", padx=4)
        self._flags = {}
        try:
            self._globe_img = ctk.CTkImage(Image.open(os.path.join(RES, "assets", "globe.png")), size=(26, 26))
        except Exception:
            self._globe_img = None
        self.lang_btn = ctk.CTkButton(top, text=self.lang.upper(), image=self._globe_img, compound="left", width=84,
                                      height=36, font=FONT_B, fg_color=SURF2, text_color=GREEN, hover_color=GREEN_D,
                                      command=self._toggle_lang_menu)
        self.lang_btn.pack(side="right")
        try:                                           # logo officiel Ko-fi (l'emoji s'affiche mal dans Tk)
            self._coffee_img = ctk.CTkImage(Image.open(os.path.join(RES, "assets", "kofi.png")), size=(37, 24))   # logo officiel Ko-fi
        except Exception:
            self._coffee_img = None
        self._b_support = ctk.CTkButton(top, text=self.L("support"), image=self._coffee_img, compound="left",
                                        height=36, font=FONT_B, fg_color=SURF2,
                                        text_color=GREEN, hover_color=GREEN_D, border_width=2, border_color=GREEN_D,
                                        command=lambda: webbrowser.open(KOFI_URL))
        self._b_support.pack(side="right", padx=8)
        Tooltip(self._b_support, self.L("support_tip"))
        self._b_soft = ctk.CTkButton(top, text="⚙ " + self.L("soft_opts"), height=36, font=FONT_B, fg_color=SURF2,
                                     hover_color=GREEN_D, command=self._open_soft_opts)
        self._b_soft.pack(side="right", padx=8)

    def _relabel_banner(self):
        """Retraduit la bannière (le changement de langue ne reconstruisait que la page)."""
        self._b_sub.configure(text=self.L("sub"))
        self._b_support.configure(text=self.L("support"))
        self._b_soft.configure(text="⚙ " + self.L("soft_opts"))

    def _flag(self, code):
        if code not in self._flags:
            try:
                self._flags[code] = ctk.CTkImage(Image.open(os.path.join(RES, "assets", "flags", code + ".png")),
                                                 size=(30, 20))
            except Exception:
                self._flags[code] = None
        return self._flags[code]

    def _toggle_lang_menu(self):
        """Menu des langues (un drapeau par langue), posé sur la fenêtre sous le bouton globe."""
        pop = getattr(self, "_lang_pop", None)
        if pop is not None and pop.winfo_exists():
            pop.destroy()
            self._lang_pop = None
            return
        pop = ctk.CTkFrame(self, fg_color=SURF, border_color=GREEN, border_width=2, corner_radius=12)
        for code, name in i18n.LANGS:
            cur = code == self.lang
            ctk.CTkButton(pop, text=name, image=self._flag(code), compound="left", anchor="w", width=240, height=42,
                          font=FONT, fg_color=GREEN_D if cur else "transparent", text_color=BG if cur else TXT,
                          hover_color=GREEN_D, command=lambda c=code: self._set_lang(c)).pack(padx=8, pady=3)
        pop.place(relx=1.0, x=-22, y=66, anchor="ne")
        pop.lift()
        self._lang_pop = pop

    def _set_lang(self, code):
        if self._busy:                                   # rebuilding the page mid-optimisation would drop the loading screen
            return
        pop = getattr(self, "_lang_pop", None)
        if pop is not None and pop.winfo_exists():
            pop.destroy()
        self._lang_pop = None
        if code == self.lang or code not in i18n.CODES:
            return
        self._close_overlay()
        self.lang = code
        self.cfg["lang"] = code
        config.save(self.cfg)
        self.lang_btn.configure(text=code.upper())
        self._relabel_banner()
        try:
            t, p = self.log.get("1.0", "end-1c"), self.prog.get()
        except Exception:
            t, p = "", 0
        self._build_page()
        if t:
            self.log.insert("end", t); self.prog.set(p)

    # ---------- threading ----------
    def _async(self, fn, cb):
        def run():
            try:
                r, e = fn(), None
            except Exception as ex:
                r, e = None, ex
            try:
                self.after(0, lambda: cb(r, e))
            except (RuntimeError, tk.TclError):
                pass                              # fenêtre fermée pendant le travail : rien à mettre à jour
        threading.Thread(target=run, daemon=True).start()

    # ---------- page unique ----------
    def _check_terms(self):
        """Avertissement anti-cheat / jeux en ligne : accepté une fois, sinon l'appli se ferme."""
        if self.cfg.get("terms_ok"):
            return
        sep = chr(10) * 2 + "─" * 24 + chr(10) * 2      # les deux langues dans la même fenêtre (la langue de l'UI n'est pas choisie)
        lg = self.lang
        title = TR[lg]["terms_title"] + ("" if lg == "en" else " / " + TR["en"]["terms_title"])
        body = TR[lg]["terms_body"] + ("" if lg == "en" else sep + TR["en"]["terms_body"])
        if messagebox.askyesno(title, body, icon="warning", parent=self):
            self.cfg["terms_ok"] = True
            try:
                config.save(self.cfg)
            except OSError:
                pass                              # le dialogue réapparaîtra au prochain lancement
        else:
            self.destroy()

    def _build_page(self):
        for w in self.body.winfo_children():
            if w is self._bg_lbl:
                continue          # garder l'image de fond
            w.destroy()
        if self._bg_lbl is not None:
            self._bg_lbl.lower()  # rester derrière les cartes
        # bandeau machine (compact)
        self.pc_strip = ctk.CTkFrame(self.body, fg_color=SURF2, corner_radius=10)
        self.body.grid_columnconfigure(0, weight=1)
        self.body.grid_rowconfigure(1, weight=5)
        self.body.grid_rowconfigure(2, weight=2, minsize=190)     # la console du bas garde toujours de la place
        self.pc_strip.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))
        self._fill_pc_strip()
        if not self.hw:
            self._async(self._load_hw, lambda r, e: (self._fill_pc_strip(), self._refresh_status(), self._auto_calibrate()))
        # colonne jeux (gauche) + panneau du jeu (droite)
        mid = ctk.CTkFrame(self.body, fg_color="transparent"); mid.grid(row=1, column=0, sticky="nsew", padx=12, pady=4)
        self._mid = mid                                            # couvert par l'écran de chargement (_set_busy)
        mid.grid_rowconfigure(0, weight=1)
        mid.grid_columnconfigure(0, weight=1, uniform="moitie")   # moitié-moitié, quelle que soit la taille d'écran
        mid.grid_columnconfigure(1, weight=1, uniform="moitie")
        leftcol = ctk.CTkFrame(mid, fg_color="transparent"); leftcol.grid(row=0, column=0, sticky="nsew", padx=(2, 8))
        leftcol.bind("<Configure>", self._on_grid_resize)
        gbar = ctk.CTkFrame(leftcol, fg_color="transparent"); gbar.pack(fill="x", pady=(0, 6))
        ctk.CTkButton(gbar, text="📁 " + self.L("add_lib"), font=FONT, fg_color=SURF2, hover_color=GREEN_D,
                      command=self._add_library).pack(side="left", expand=True, fill="x", padx=(0, 4))
        ctk.CTkButton(gbar, text="➕ " + self.L("import_game"), font=FONT, fg_color=SURF2, hover_color=GREEN_D,
                      command=self._manual).pack(side="left", expand=True, fill="x", padx=(4, 0))
        gall = ctk.CTkFrame(leftcol, fg_color="transparent"); gall.pack(fill="x", pady=(0, 6))
        ctk.CTkButton(gall, text="⚡ " + self.L("opt_all"), font=FONT_B, fg_color=GREEN_D, hover_color=GREEN, text_color=BG,
                      command=self._open_opt_all).pack(side="left", expand=True, fill="x", padx=(0, 4))
        ctk.CTkButton(gall, text="↩ " + self.L("rm_all"), font=FONT_B, fg_color="#5a2020", hover_color="#7a3030",
                      command=self._remove_all).pack(side="left", expand=True, fill="x", padx=(4, 0))
        self._games_left = ctk.CTkScrollableFrame(leftcol, fg_color=SURF, corner_radius=12)
        self._games_left.pack(fill="both", expand=True)
        self.right = ctk.CTkScrollableFrame(mid, fg_color=SURF, corner_radius=12)
        self.right.grid(row=0, column=1, sticky="nsew", padx=(8, 2))
        self._pick_right()
        if self.games:
            self._fill_games(self._games_left)
        else:
            ctk.CTkLabel(self._games_left, text=self.L("loading"), font=FONT, text_color=DIM).pack(pady=12)
            self._async(self._load_games, lambda r, e: (setattr(self, "games", r or []), self._refresh_games()))
        # console persistante (progression + log d'application/retrait)
        cons = ctk.CTkFrame(self.body, fg_color=SURF2, corner_radius=12)
        cons.grid(row=2, column=0, sticky="nsew", padx=12, pady=(4, 10))
        self.prog = ctk.CTkProgressBar(cons, progress_color=GREEN, fg_color=BG, height=12)
        self.prog.set(0); self.prog.pack(fill="x", padx=12, pady=(10, 4))
        self.log = ctk.CTkTextbox(cons, font=MONO, fg_color=BG, text_color=TXT, height=120)
        self.log.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        # panneau de droite reconstruit -> réafficher le jeu sélectionné (sinon Apply/Remove agissent à l'aveugle)
        if self.game:
            self._set_game(self.game, silent=True, keep_exe=True)

    def _load_hw(self):
        self.hw = hardware.summary()
        self.monitors = display.monitors()
        # écran du jeu inconnu : l'écran le plus rapide branché (repli : premier contrôleur vidéo vu par WMI)
        self.refresh = max((m["hz"] for m in self.monitors if m["hz"] > 1), default=0) or hardware.refresh_hz()
        try:
            self.vrr = display.vrr_for(self.refresh)
        except Exception:
            self.vrr = None                       # détection impossible : on ne devine pas
        return True

    def _fill_pc_strip(self):
        if not getattr(self, "pc_strip", None) or not self.pc_strip.winfo_exists():
            return
        for w in self.pc_strip.winfo_children():
            w.destroy()
        if not self.hw:
            ctk.CTkLabel(self.pc_strip, text=self.L("loading"), font=FONT, text_color=DIM).pack(side="left", padx=12, pady=8)
            return
        h = self.hw
        txt = (f"GPU {h.get('name','?')} ({h.get('series','?')}/{h.get('sm','?')}) · {h.get('vram_mb',0)} {'Mo' if self.lang == 'fr' else 'MB'} · "
               f"driver {h.get('driver','?')} · {h.get('cpu','?')} · {h.get('ram_gb',0)} {'Go' if self.lang == 'fr' else 'GB'} · {self.refresh or '?'} Hz")
        ctk.CTkLabel(self.pc_strip, text=txt, font=FONT, text_color=TXT, anchor="w").pack(side="left", padx=12, pady=8, fill="x", expand=True)
        if h.get("warn"):
            ctk.CTkLabel(self.pc_strip, text="⚠ " + h["warn"], font=FONT, text_color="#f0b63a").pack(side="right", padx=12)

    def _set_busy(self, on, text=None):
        """Optimiser / Retirer / calibrage en cours : un écran couvre la liste des jeux et la fiche (spinner + message),
        rien d'autre n'est cliquable ; la console du bas reste visible pour suivre la progression."""
        self._busy = on
        old = getattr(self, "_cover", None)
        self._cover = None
        if old is not None and old.winfo_exists():
            old.destroy()
        mid = getattr(self, "_mid", None)
        if not on or not mid or not mid.winfo_exists():
            if not on:
                self._thumbs.pop((self.game or {}).get("dir"), None)   # la jaquette reprend ou perd son bandeau
                self._refresh_games()
                self._refresh_status()
            return
        cover = ctk.CTkFrame(mid, fg_color=BG, corner_radius=12)
        cover.place(relx=0, rely=0, relwidth=1, relheight=1)
        box = ctk.CTkFrame(cover, fg_color="transparent"); box.place(relx=0.5, rely=0.5, anchor="center")
        spin = ctk.CTkLabel(box, text="◐", font=("Segoe UI", 72, "bold"), text_color=GREEN); spin.pack()
        ctk.CTkLabel(box, text=text or "", font=FONT_H, text_color=TXT).pack(pady=(10, 2))
        ctk.CTkLabel(box, text=self.L("busy_hint"), font=FONT, text_color=DIM).pack()
        self._cover = cover

        def tick(i=0):
            if self._cover is cover and spin.winfo_exists():
                spin.configure(text="◐◓◑◒"[i % 4])
                self.after(140, tick, i + 1)
        tick()

    def _badge(self, im, g):
        """Bandeau en bas d'une jaquette : vert « ✓ YOGOMFG » (optimisé) ou ambre « ✨ OPTI DISPO » (meilleur réglage mesuré)."""
        if not self._optimized(g):
            return im
        better = g.get("appid") in self._better
        im = im.copy()
        dr = ImageDraw.Draw(im)
        w, h = im.size
        bh = max(28, h // 8)
        dr.rectangle((0, h - bh, w, h), fill=(240, 182, 58) if better else (182, 255, 74))
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", int(bh * (0.48 if better else 0.55)))
        except OSError:
            font = ImageFont.load_default()
        dr.text((w // 2, h - bh // 2), "✨ OPTI DISPO" if better else "✓ YOGOMFG", font=font, fill=(11, 11, 13), anchor="mm")
        return im

    def _optimized(self, g):
        return bool(g) and g.get("appid") in self.cfg.get("installed_exe", {})

    def _refresh_games(self):
        gl = getattr(self, "_games_left", None)
        if not gl or not gl.winfo_exists():
            return
        for w in gl.winfo_children():
            w.destroy()
        self._fill_games(gl)

    def _remove(self):
        if self._busy:
            return
        if not (self.game and self.exe.get()):
            return messagebox.showwarning("YogoMFG", self.L("need_game"))
        if not messagebox.askyesno("YogoMFG", self.L("remove_ask2"), parent=self):
            return
        exe = self.exe.get()                                   # snapshot (pas de .get() dans le thread)
        proxy = self.cfg.get("applied", {}).get(self.game["appid"]) or self.proxy.get()
        appid = self.game["appid"]
        last = not [a for a in self.cfg.get("installed_exe", {}) if a != appid]
        self._set_busy(True, self.L("busy_rm"))
        self.log.delete("1.0", "end")
        self.prog.set(0.2); self._log("⏳ " + self.L("removing"))
        npi = self.npi.get()

        def work():
            try:
                files, ferr = installer.uninstall(exe, proxy), None
            except Exception as ex:                            # fichier verrouillé ou restauration non vérifiée
                files, ferr = [], str(ex)
            base = os.path.basename(exe)
            # profil NVIDIA du jeu : cap/VRR puis multiplicateur, chacun relu (rien à faire = message « Aucun … »)
            nv = [nvcp.revert(npi, DATA, base), nvcp.restore_mfg(npi, DATA, base)]
            if last and not ferr:          # plus aucun jeu optimisé : le profil global reprend ses valeurs d'origine
                nv.append(nvpreset.revert_fg_global(npi, DATA))
            return files, ferr, nv

        def done(res, e):
            self.prog.set(1.0)
            if e:
                self._log("✗ " + str(e))
                return self._set_busy(False)
            files, ferr, nv = res
            if ferr:
                self._log("✗ " + self.L("rm_files_err") % ferr)
            else:
                for f in files:
                    self._log("  ✓ " + f)
                self.cfg.get("applied", {}).pop(appid, None)
                self.cfg.get("installed_exe", {}).pop(appid, None)
                self.cfg.get("cap_written", {}).pop(appid, None)
                self._better.discard(appid)
                config.save(self.cfg)
            need_admin = False
            for ok, msg in nv:
                if ok:
                    self._log("✓ " + msg)
                elif msg.startswith("NEED_ADMIN"):
                    need_admin = True
                elif not msg.startswith("Aucun"):
                    self._log("✗ " + msg)
            if need_admin:
                self._log("✗ " + self.L("rm_need_admin"))
                self._ask_admin()
            elif not ferr:
                self._log(self.L("rm_done"))
            self._set_busy(False)                       # after the config update: the cover loses its YOGOMFG ribbon
        self._async(work, done)

    def _open_opt_all(self):
        """« Optimiser tous les jeux » : choix Recommandé (calcul par jeu) ou Manuel (x3..x6 pour tous), puis tout est fait."""
        if self._busy or not self.games:
            return
        body, bar = self._overlay(self.L("opt_all"))
        ctk.CTkLabel(body, text=self.L("opt_all_hint") % len(self.games), font=FONT, text_color=TXT, wraplength=620,
                     justify="left").pack(anchor="w", padx=14, pady=(12, 8))
        mode = ctk.CTkSegmentedButton(body, values=[self.L("mode_auto"), self.L("mode_manual")], font=FONT_B,
                                      selected_color=GREEN_D, selected_hover_color=GREEN)
        mode.set(self.L("mode_auto"))
        mode.pack(anchor="w", fill="x", padx=14, pady=4)
        mult = ctk.CTkSegmentedButton(body, values=["x3", "x4", "x5", "x6"], font=FONT_B, selected_color=GREEN_D,
                                      selected_hover_color=GREEN)
        mult.set("x4")
        mult.pack(anchor="w", fill="x", padx=14, pady=4)
        ctk.CTkLabel(body, text=self.L("opt_all_cap"), font=FONT, text_color=DIM, wraplength=620,
                     justify="left").pack(anchor="w", padx=14, pady=(4, 8))
        ctk.CTkButton(bar, text=self.L("close"), font=FONT_B, width=140, fg_color=SURF2, hover_color=EDGE,
                      command=self._close_overlay).pack(side="right")
        ctk.CTkButton(bar, text="⚡ " + self.L("opt_all_go"), font=FONT_B, fg_color=GREEN, hover_color=GREEN_D, text_color=BG,
                      command=lambda: self._opt_all(None if mode.get() == self.L("mode_auto") else int(mult.get().lstrip("x")))
                      ).pack(side="left")

    def _opt_all(self, manual):
        """Optimise chaque jeu listé, l'un après l'autre (même chemin que le bouton d'un jeu) ; saute un jeu lancé ou à anti-cheat."""
        self._close_overlay()
        games = [g for g in self.games if g.get("exes")]
        mm = self.cfg.setdefault("manual_mult", {})
        for g in games:
            if manual:
                mm[g["appid"]] = manual
            else:
                mm.pop(g["appid"], None)
        config.save(self.cfg)
        self._set_busy(True, self.L("busy_opt_all") % len(games))
        self.log.delete("1.0", "end")
        self.prog.set(0.02)
        npi, vrr = self.npi.get(), bool(self.vrr)
        written = dict(self.cfg.get("cap_written", {}))
        applied = dict(self.cfg.get("applied", {}))

        def worker():
            out = []
            for i, g in enumerate(games):
                exe, appid, name = g["exes"][0], g["appid"], g["name"]
                try:
                    info = fgdetect.scan(g["dir"])
                    if info.get("anticheat"):
                        out.append((name, None, self.L("skip_ac") % ", ".join(info["anticheat"])))
                        continue
                    ok, code, _ = installer.check_apply(MOD_ROOT, exe, "version.dll", applied.get(appid))
                    if not ok:
                        out.append((name, None, self.L("skip_busy") + f" ({code})"))
                        continue
                    stats = loganalyze.session_stats(exe)
                    self._stats[exe] = stats
                    self._caps[exe] = nvcp.user_cap(npi, DATA, os.path.basename(exe), written.get(appid))
                    p = self._plan(appid, stats, exe)
                    self.after(0, lambda i=i, n=name: (self.prog.set((i + 0.5) / len(games)), self._log(f"⏳ {n} …")))
                    res, need_admin = self._write_game(exe, "version.dll", p[0], p[1], vrr, npi, lambda f, line: None,
                                                       bool(manual))
                    good = bool(res) and all(r for _, r in res)
                    out.append((name, good, self._result_text(p).partition(chr(10))[0]))
                    if good:
                        out_cfg.append((appid, exe, p[0], p[1]))
                    if need_admin:
                        out.append((self.L("need_admin_nv"), False, ""))
                        break
                except Exception as e:                   # un jeu en échec ne bloque pas les autres
                    out.append((name, False, str(e)))
            return out

        out_cfg = []

        def done(out, e):
            for appid, exe, mult, cap in out_cfg:        # config modifiée dans le thread UI seulement
                self.cfg.setdefault("applied", {})[appid] = "version.dll"
                self.cfg.setdefault("installed_exe", {})[appid] = exe
                self.cfg.setdefault("mult_by_game", {})[appid] = mult
                self.cfg.setdefault("cap_written", {})[appid] = cap
                self._better.discard(appid)
            config.save(self.cfg)
            for name, ok, msg in out or []:
                self._log(("  ✓ " if ok else "  ⏭ " if ok is None else "  ✗ ") + name + (" — " + msg if msg else ""))
            if e:
                self._log("✗ " + str(e))
            self.prog.set(1.0)
            self._log(chr(10) + "💡 " + self.L("after_opt_hint"))
            self._thumbs.clear()
            self._set_busy(False)
        self._async(worker, done)

    def _remove_all(self):
        """« Retirer de tous les jeux » : chaque jeu YogoMFG retrouve ses fichiers et son profil NVIDIA, puis le global."""
        games = {a: e for a, e in self.cfg.get("installed_exe", {}).items() if e}
        if self._busy:
            return
        if not games:
            # S'il ne reste plus rien dans installed_exe mais que l'utilisateur clique, on nettoie quand même le global
            if messagebox.askyesno("YogoMFG", self.L("rm_all_ask") % 0, parent=self):
                self._set_busy(True, self.L("busy_rm_all") % 0)
                npi = self.npi.get()
                def clean_global():
                    ok, msg = nvpreset.revert_fg_global(npi, DATA)[:2]
                    return [("NVIDIA (profil global)", ok, [msg])], []
                def clean_done(res, e):
                    out, _ = res or ([], [])
                    for name, ok, files in out:
                        self._log(("✓ " if ok else "✗ ") + name)
                        for f in files: self._log("    " + f)
                    self._set_busy(False)
                self._async(clean_global, clean_done)
            return
        if not messagebox.askyesno("YogoMFG", self.L("rm_all_ask") % len(games), parent=self):
            return
        self._set_busy(True, self.L("busy_rm_all") % len(games))
        self.log.delete("1.0", "end")
        self.prog.set(0.05)
        npi, applied = self.npi.get(), dict(self.cfg.get("applied", {}))

        def worker():
            out, ok_ids = [], []
            for appid, exe in games.items():
                name = os.path.basename(os.path.dirname(exe))
                try:
                    files = installer.uninstall(exe, applied.get(appid) or "version.dll") if os.path.isfile(exe) else []
                    base = os.path.basename(exe)
                    nvcp.revert(npi, DATA, base)
                    nvcp.restore_mfg(npi, DATA, base)
                    out.append((name, True, files))
                    ok_ids.append(appid)
                except Exception as e:                   # fichier verrouillé (jeu lancé) : ce jeu reste installé
                    out.append((name, False, [str(e)]))
            
            # On tente de remettre le global si on a réussi à enlever tous les jeux demandÉS
            # ou si plus aucun jeu n'est marqué comme installé dans la config globale
            remaining = [a for a in self.cfg.get("installed_exe", {}) if a not in ok_ids]
            if not remaining:
                try:
                    ok, msg = nvpreset.revert_fg_global(npi, DATA)[:2]
                    out.append(("NVIDIA (profil global)", ok, [msg]))
                except Exception as e:
                    out.append(("NVIDIA (profil global)", False, [str(e)]))
            return out, ok_ids

        def done(res, e):
            out, ok_ids = res or ([], [])
            for name, ok, files in out:
                self._log(("✓ " if ok else "✗ ") + name)
                for f in files:
                    self._log("    " + f)
            
            for a in ok_ids:
                for k in ("applied", "installed_exe", "cap_written", "manual_mult"):
                    self.cfg.get(k, {}).pop(a, None)
                self._better.discard(a)
            
            config.save(self.cfg)
            if e:
                self._log("✗ " + str(e))
            
            self.prog.set(1.0)
            self._thumbs.clear() # Force le rechargement de toutes les jaquettes
            self._set_busy(False)
        self._async(worker, done)

    def _launch(self):
        exe = self.exe.get()
        if not exe or not os.path.isfile(exe):
            return messagebox.showwarning("YogoMFG", self.L("need_game"))
        aid = str((self.game or {}).get("appid", ""))
        try:
            if aid.isdigit():
                os.startfile(f"steam://rungameid/{aid}")   # via Steam : pas d'élévation forcée, DRM/cwd corrects
            else:
                try:
                    os.startfile(exe, cwd=os.path.dirname(exe))   # cwd : jeux à assets relatifs (Python 3.10+)
                except TypeError:
                    os.startfile(exe)
        except Exception as e:
            messagebox.showerror("YogoMFG", str(e))
        else:                                      # la sonde GPU/CPU tourne pendant que tu joues (lue par Analyser)
            if self._probe:
                self._probe.stop()
            self._probe = probe.Probe()
            self._probe.start()
            self._log("● " + self.L("probe_on"))

    COLS = 3

    def _on_win_configure(self, event):
        """Fenêtre étroite : on masque le sous-titre de la bannière pour garder tous les boutons visibles."""
        if event.widget is not self or not hasattr(self, "_b_sub"):
            return
        narrow = event.width < 1420
        if narrow and self._b_sub.winfo_ismapped():
            self._b_sub.pack_forget()
        elif not narrow and not self._b_sub.winfo_ismapped():
            self._b_sub.pack(side="left", padx=16, before=self._b_ver)

    def _on_grid_resize(self, event):
        """Recalcule le nombre de colonnes de jaquettes quand la fenêtre change de taille (anti-rebond)."""
        job = getattr(self, "_grid_job", None)
        if job:
            try:
                self.after_cancel(job)
            except Exception:
                pass
        w = event.width
        self._grid_job = self.after(250, lambda: self._relayout_grid(w))

    def _relayout_grid(self, width):
        cols = max(2, min(8, (width - 40) // 146))
        if cols != self.COLS and self.games and not self._closing:
            self.COLS = cols
            self._refresh_games()

    def _load_games(self):
        """Jeux Steam + dossiers ajoutés + jeux importés (hors thread UI)."""
        out, seen = [], set()
        for g in steam.games():
            out.append(g); seen.add(os.path.normcase(g["dir"]))
        extra = [g for lib in self.cfg.get("extra_libs", []) if os.path.isdir(lib) for g in steam.games_in(lib)]
        extra += [steam.game_from_dir(d) for d in self.cfg.get("extra_games", []) if os.path.isdir(d)]
        for g in extra:
            if os.path.normcase(g["dir"]) not in seen:
                out.append(g); seen.add(os.path.normcase(g["dir"]))
        # only games that ship DLSS Frame Generation; a game YogoMFG already touched stays listed so it can be removed
        keep = set(self.cfg.get("installed_exe", {})) | set(self.cfg.get("applied", {}))
        out = [g for g in out if g.get("appid") in keep or fgdetect.fg_capable(g["dir"])]
        # filtrage manuel des benchmarks/outils connus (non-jeux)
        noise = ("3dmark", "v-ray", "cinebench", "superposition", "pcmark")
        out = [g for g in out if not any(n in g["name"].lower() for n in noise)]
        out.sort(key=lambda g: g["name"].lower())
        return out

    def _add_library(self):
        d = filedialog.askdirectory(title=self.L("add_lib"))
        if not d:
            return
        libs = self.cfg.setdefault("extra_libs", [])
        if d not in libs:
            libs.append(d)
            config.save(self.cfg)
        self._async(self._load_games, lambda r, e: (setattr(self, "games", r or self.games), self._refresh_games()))

    @staticmethod
    def _placeholder(name):
        """Jaquette de secours (jeu sans image) : carte sombre avec le nom du jeu."""
        im = Image.new("RGB", (240, 360), (31, 31, 39))
        dr = ImageDraw.Draw(im)
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 26)
        except OSError:
            font = ImageFont.load_default()
        words, lines, cur = name.split(), [], ""
        for w in words:
            if len(cur) + len(w) + 1 > 14 and cur:
                lines.append(cur); cur = w
            else:
                cur = (cur + " " + w).strip()
        lines.append(cur)
        y = 180 - 17 * len(lines)
        for ln in lines[:6]:
            dr.text((120, y), ln, font=font, fill=(182, 255, 74), anchor="mm"); y += 34
        return im

    def _thumb(self, g):
        key = g["dir"]
        if key not in self._thumbs:
            self._thumbs[key] = ctk.CTkImage(self._badge(self._placeholder(g["name"]), g), size=(120, 180))
        return self._thumbs[key]

    def _fill_games(self, parent):
        self._cards = {}
        self._grid_gen += 1
        gen = self._grid_gen
        games = list(self.games)
        for c in range(self.COLS):
            parent.grid_columnconfigure(c, weight=1)

        def build(i):
            if gen != self._grid_gen or not parent.winfo_exists():
                return                              # grille reconstruite entre-temps
            for k in range(i, min(i + 9, len(games))):
                self._make_card(parent, games[k], k, gen)
            if i + 9 < len(games):
                parent.after(15, lambda: build(i + 9))      # par lots : l'UI ne fige jamais
        build(0)

    def _make_card(self, parent, g, k, gen):
        sel = bool(self.game) and self.game["dir"] == g["dir"]
        btn = ctk.CTkButton(parent, text="", image=self._thumb(g), width=132, height=198, corner_radius=10,
                            fg_color=SURF2, hover_color=GREEN_D, border_width=3,
                            border_color=GREEN if sel else SURF, command=lambda x=g: self._set_game(x))
        btn.grid(row=k // self.COLS, column=k % self.COLS, padx=5, pady=5)
        Tooltip(btn, g["name"])
        self._cards[g["dir"]] = btn
        if not str(g["appid"]).isdigit():
            return
        dest = os.path.join(DATA, "_covers", f"{g['appid']}.jpg")

        def work():
            if self._closing or gen != self._grid_gen:
                return None                      # fenêtre fermée ou grille reconstruite : inutile de télécharger
            p = steam.fetch_cover(g["appid"], dest)
            if not p:
                return None
            im = Image.open(p).convert("RGB")
            im.thumbnail((240, 360))
            return self._badge(im, g)

        def apply(fut):
            try:
                im = fut.result()
            except Exception:
                return
            if im is None:
                return
            def ui():
                if self._closing or gen != self._grid_gen or not btn.winfo_exists():
                    return
                img = ctk.CTkImage(im, size=(120, 180))
                self._thumbs[g["dir"]] = img           # référence gardée (sinon Tk libère l'image)
                btn.configure(image=img)
            try:
                self.after(0, ui)
            except (RuntimeError, tk.TclError):
                pass
        self._cover_pool.submit(work).add_done_callback(apply)

    def _mark_selected(self, g):
        for d, b in list(self._cards.items()):
            if b.winfo_exists():
                b.configure(border_color=GREEN if d == g["dir"] else SURF)

    def _pick_right(self):
        r = self.right
        head = ctk.CTkFrame(r, fg_color="transparent"); head.pack(fill="x")
        self.cover = ctk.CTkLabel(head, text="", width=112, height=158, fg_color=BG, corner_radius=10)
        self.cover.pack(side="right", padx=(10, 0))
        meta = ctk.CTkFrame(head, fg_color="transparent"); meta.pack(side="left", fill="x", expand=True)
        self.game_name = ctk.CTkLabel(meta, text="—", font=FONT_H, text_color=GREEN, anchor="w",
                                      wraplength=380, justify="left"); self.game_name.pack(anchor="w")
        self.lbl_fg = ctk.CTkLabel(meta, text="", font=FONT, wraplength=380, justify="left", anchor="w"); self.lbl_fg.pack(anchor="w", pady=6)
        self.lbl_inst = ctk.CTkLabel(meta, text="", font=FONT, wraplength=380, justify="left", anchor="w", text_color=DIM)
        self.lbl_inst.pack(anchor="w", pady=(0, 6))
        self.lbl_logs = ctk.CTkLabel(meta, text="", font=FONT, wraplength=380, justify="left", anchor="w", text_color=DIM); self.lbl_logs.pack(anchor="w")
        ctk.CTkLabel(r, text=self.L("exe"), font=FONT_B, text_color=DIM).pack(anchor="w", pady=(12, 0))
        self.cmb = ctk.CTkOptionMenu(r, variable=self.exe, values=[""], font=FONT,
                                     fg_color=SURF2, button_color=GREEN_D, dropdown_font=FONT)
        self.cmb.pack(anchor="w", fill="x")
        ctk.CTkButton(r, text=self.L("change_exe"), font=FONT, fg_color=SURF2,
                      hover_color=GREEN_D, command=self._pick_exe).pack(anchor="w", pady=(6, 0))
        # mode : Recommandé (calcul automatique) ou Manuel (le joueur choisit x3..x6) ; le reste est toujours automatique
        self.seg_mode = ctk.CTkSegmentedButton(r, values=[self.L("mode_auto"), self.L("mode_manual")], font=FONT_B,
                                               selected_color=GREEN_D, selected_hover_color=GREEN, command=self._on_mode)
        self.seg_mode.pack(anchor="w", fill="x", pady=(14, 4))
        self.seg_mult = ctk.CTkSegmentedButton(r, values=["x3", "x4", "x5", "x6"], font=FONT_B, selected_color=GREEN_D,
                                               selected_hover_color=GREEN, command=self._on_manual_mult)
        self.lbl_vram = ctk.CTkLabel(r, text="", font=FONT, text_color=DIM, anchor="w", justify="left", wraplength=520)
        # un clic : tout est décidé automatiquement (multiplicateur, cap FPS, VRR) ; un clic pour tout remettre
        self.btn_opt = ctk.CTkButton(r, text=self.L("optimize_game"), font=FONT_H, height=64, fg_color=GREEN,
                                     hover_color=GREEN_D, text_color=BG, command=self.do_apply)
        self.btn_opt.pack(anchor="w", fill="x", pady=(14, 6))
        Tooltip(self.btn_opt, self.L("tip_optimize"))
        self.btn_remove = ctk.CTkButton(r, text=self.L("remove_restore"), font=FONT_H, height=56, fg_color=SURF2,
                                        hover_color="#7a3030", text_color_disabled=DIM, state="disabled",
                                        command=self._remove)
        self.btn_remove.pack(anchor="w", fill="x", pady=(0, 6))
        Tooltip(self.btn_remove, self.L("tip_remove"))
        self.lbl_result = ctk.CTkLabel(r, text="", font=FONT_B, text_color=GREEN, anchor="w", wraplength=520,
                                       justify="left")
        self.lbl_result.pack(anchor="w", fill="x", pady=(0, 6))
        actions = ctk.CTkFrame(r, fg_color="transparent"); actions.pack(anchor="w", fill="x", pady=(4, 0))
        ctk.CTkButton(actions, text="▶ " + self.L("launch"), font=FONT_B, fg_color=SURF2, hover_color=GREEN_D,
                      command=self._launch).pack(side="left", expand=True, fill="x")
        # no Analyser screen any more: the session is analysed automatically at the next Optimiser click / start (calibration)
        if getattr(self, "_exe_trace", None):
            self.exe.trace_remove("write", self._exe_trace)    # _pick_right est rappelé à chaque rebuild (langue)
        self._exe_trace = self.exe.trace_add("write", lambda *_: self._refresh_status())
        ctk.CTkLabel(r, text=self.L("updaters"), font=FONT_B, fg_color=SURF2, corner_radius=8,
                     height=34).pack(fill="x", pady=(12, 4))
        self.up_box = ctk.CTkFrame(r, fg_color=BG, corner_radius=12)
        self.up_box.pack(fill="x", pady=(0, 8))

    @staticmethod
    def _blend(c1, c2, t):
        a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
        b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
        return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(a, b))

    def _fade_text(self, lbl, text, color, steps=6):
        """Texte posé tout de suite, couleur qui s'installe en douceur (pas de clignotement sec)."""
        if not lbl.winfo_exists():
            return
        job = getattr(lbl, "_fade_job", None)
        if job:
            try: lbl.after_cancel(job)
            except Exception: pass
        lbl.configure(text=text)
        def step(i):
            if not lbl.winfo_exists():
                return
            lbl.configure(text_color=self._blend(SURF2, color, i / steps))
            lbl._fade_job = lbl.after(28, lambda: step(i + 1)) if i < steps else None
        step(1)

    def _refresh_status(self):
        """Détecte une installation YogoMFG existante pour l'exe choisi ; dégrise/grise Retirer."""
        if not hasattr(self, "btn_remove") or not self.btn_remove.winfo_exists():
            return
        exe = self.exe.get()
        st = installer.status(exe, self.cfg.get("applied", {}).get((self.game or {}).get("appid"))) if exe else None
        on = bool(st and st["installed"])
        if on:
            bits = ([f"x{st['mult']}"] if st["mult"] else []) + ([st["proxy"]] if st["proxy"] else []) \
                + ([self.L("inst_bak") % len(st["backups"])] if st["backups"] else [])
            self._fade_text(self.lbl_inst, self.L("inst_yes") % " · ".join(bits), GREEN)
        else:
            self._fade_text(self.lbl_inst, self.L("inst_no"), DIM)
        # Retirer reste possible tant qu'un réglage NVIDIA de ce jeu est à annuler (ex. fichiers retirés sans admin)
        rm = on or bool(exe and nvcp.pending(DATA, os.path.basename(exe)))
        self.btn_remove.configure(state="normal" if rm else "disabled", fg_color="#5a2020" if rm else SURF2)
        self._sync_mode()
        p = self._plan()
        txt = self._result_text(p)
        cur = bool(on and installer.up_to_date(MOD_ROOT, exe, inimaker.make(st["mult"] or p[0]), st["proxy"] or "version.dll"))
        done = bool(exe and on and cur and st["mult"] == p[0])   # installé, à jour, au bon multiplicateur : rien à refaire
        stale = bool(exe and on and not cur)                  # YogoMFG a été mis à jour depuis : réappliquer
        better = bool(exe and on and not done and not stale)  # une session mesurée propose un autre multiplicateur
        self.btn_opt.configure(text=(self.L("opt_done") % p[0]) if done else (self.L("opt_update") % p[0]) if stale else ((self.L("opt_apply") if self.cfg.get("manual_mult", {}).get((self.game or {}).get("appid"))
                                                       else self.L("opt_better")) % p[0] if better else self.L("optimize_game")),
                               state="disabled" if self._busy else "normal",
                               fg_color=SURF2 if done else ("#f0b63a" if better else GREEN), text_color_disabled=DIM)
        if not exe:
            self.lbl_result.configure(text="")
        elif on and st["mult"] == p[0]:
            self._fade_text(self.lbl_result, "✓ " + txt, "#f0b63a" if p[2] else GREEN)
        else:
            self._fade_text(self.lbl_result, self.L("result_plan") % txt, DIM)

    def _mult_max(self, appid=None):
        """Plafond PROUVÉ du jeu (session mesurée), sinon celui du mod (x6) ; la version du plugin ne prouve rien."""
        appid = appid or (self.game or {}).get("appid")
        return max(2, min(6, self.cfg.get("proven_cap", {}).get(appid, 6)))

    def _plan(self, appid=None, stats=False, exe=None):
        """(multiplicateur, cible T, avertissement, calibré) : écran + dernière session mesurée (voir inimaker.plan)."""
        exe = exe or self.exe.get()
        if stats is False:
            stats = self._stats.get(exe)
        weak = inimaker.weak_gpu((self.hw or {}).get("name"))
        p = inimaker.plan(self.refresh, bool(self.vrr), stats, self._mult_max(appid), weak, self._caps.get(exe))
        man = self.cfg.get("manual_mult", {}).get(appid or (self.game or {}).get("appid"))
        if man and p[1]:                                  # Manuel : le choix du joueur, sans bride proven_cap
            m = max(inimaker.MIN_MULT, min(6, int(man)))
            p = (m, p[1], p[1] / m < (inimaker.WEAK_BASE if weak else inimaker.MIN_BASE), p[3])
        return p

    def _sync_mode(self):
        """Affiche le mode du jeu sélectionné (Recommandé / Manuel + xN) et les multiplicateurs que ce jeu accepte."""
        if not hasattr(self, "seg_mode") or not self.seg_mode.winfo_exists() or not self.game:
            return
        appid, top = self.game["appid"], self._mult_max()
        man = self.cfg.get("manual_mult", {}).get(appid)
        self.seg_mode.set(self.L("mode_manual") if man else self.L("mode_auto"))
        vals = [f"x{k}" for k in range(inimaker.MIN_MULT, 7)]   # x3..x6 toujours disponibles en Manuel
        self.seg_mult.configure(values=vals)
        if man:
            self.seg_mult.set(f"x{max(inimaker.MIN_MULT, min(6, int(man)))}")
            self.seg_mult.pack(anchor="w", fill="x", pady=(0, 4), after=self.seg_mode)
            self.lbl_vram.configure(text=self.L("vram_note"))
            self.lbl_vram.pack(anchor="w", fill="x", pady=(0, 4), after=self.seg_mult)
        else:
            self.seg_mult.pack_forget()
            self.lbl_vram.pack_forget()

    def _on_mode(self, val):
        if self._busy or not self.game:
            return self._sync_mode()
        mm = self.cfg.setdefault("manual_mult", {})
        if val == self.L("mode_manual"):
            mm[self.game["appid"]] = self._plan()[0]      # part du multiplicateur recommandé
        else:
            mm.pop(self.game["appid"], None)
        config.save(self.cfg)
        self._sync_mode()
        self._refresh_status()

    def _on_manual_mult(self, val):
        if self._busy or not self.game:
            return self._sync_mode()
        self.cfg.setdefault("manual_mult", {})[self.game["appid"]] = int(val.lstrip("x"))
        config.save(self.cfg)
        self._refresh_status()

    def _result_text(self, p):
        """« x3 · 59 images calculées → 177 affichées » (ou « Calibré : … » après une session mesurée) + avertissement."""
        mult, t, warn, cal = p
        if not t:
            return f"x{mult} · " + self.L("hz_unknown")
        txt = self.L("result_cal" if cal else "result") % (mult, round(t / mult), t)
        return txt + ("\n⚠ " + self.L("warn_soft") if warn else "")

    def _learn_cap(self, g, got):
        """Retient ce que le jeu a réellement donné. Demandé 6, obtenu 4 -> plafond prouvé x4 ; sinon aucun plafond connu."""
        asked = self.cfg.get("mult_by_game", {}).get(g["appid"])
        caps = self.cfg.setdefault("proven_cap", {})
        old = caps.get(g["appid"])
        if got and asked and got < asked:
            caps[g["appid"]] = got
            if self.game and self.game.get("appid") == g["appid"] and self._mfg_ver:   # plugin du jeu au moment de la preuve
                self.cfg.setdefault("proven_cap_ver", {})[g["appid"]] = self._mfg_ver
        elif got and old and got > old:          # le jeu a fait mieux que le plafond retenu (mise à jour du jeu) : on l'oublie
            caps.pop(g["appid"], None)
        if caps.get(g["appid"]) != old:
            config.save(self.cfg)

    def _apply_scan(self, g, info, silent):
        """Affiche le résultat du scan (support FG, plugin, conflits, anti-cheat) pour le jeu courant."""
        sup, cap, ver, note, clash = info["sup"], info["cap"], info["ver"], info["note"], info["clash"]
        old_ver = self.cfg.get("proven_cap_ver", {}).get(g["appid"])
        if ver and old_ver and ver != old_ver and g["appid"] in self.cfg.get("proven_cap", {}):
            # le jeu a changé de plugin DLSS-G (mise à jour) : le plafond prouvé avec l'ancien ne vaut plus, x6 redevient possible
            self.cfg["proven_cap"].pop(g["appid"], None)
            self.cfg["proven_cap_ver"].pop(g["appid"], None)
            config.save(self.cfg)
            self._log("ℹ " + self.L("cap_reset") % (old_ver, ver))
        self._anticheat = info["anticheat"]
        self._clash = clash
        self._mfg_cap = cap
        self._mfg_ver = ver
        base =self.L("fg_yes") if sup == "yes" else self.L("fg_no")
        if sup == "yes":
            base += "\n" + self.L(note) + (f"  (plugin {ver})" if ver else "")
        if clash:
            base += "\n" + self.L("conflict") % ", ".join(clash)
        if self._anticheat:
            base += "\n" + self.L("anticheat") % ", ".join(self._anticheat)
        self.lbl_fg.configure(text=base, text_color="#ff6b5a" if self._anticheat
                              else ("#f0b63a" if (clash or sup != "yes") else GREEN))
        if (not silent) and sup != "yes" and messagebox.askyesno("YogoMFG", "FG inconnu. Recherche web ? / Unknown. Web search?"):
            webbrowser.open(fgdetect.web_query(g["name"]))
        self._scanned = True

    def _set_game(self, g, silent=False, keep_exe=False):
        self.game = g
        self._mark_selected(g)
        self.game_name.configure(text=g["name"])
        self._load_cover(g["appid"])
        self._scanned = False
        self._anticheat, self._clash = [], []
        self.lbl_fg.configure(text=self.L("scanning"), text_color=DIM)
        def scan_done(info, e):
            if self.game is g and info and not e:       # le jeu a pu changer pendant le scan
                self._apply_scan(g, info, silent)
        self._async(lambda: fgdetect.scan(g["dir"]), scan_done)
        cur = self.exe.get()
        vals = g["exes"] or ([cur] if cur else [""])
        if keep_exe and cur and cur not in vals:
            vals = [cur] + vals
        self.cmb.configure(values=vals)
        if not (keep_exe and cur):
            self.exe.set(g["exes"][0] if g["exes"] else "")
        # logs déjà présents dans le dossier du jeu -> aperçu direct de l'analyse
        self.lbl_logs.configure(text="")
        exe0 = self.exe.get()
        if exe0:
            def seen(r, e):
                if r:
                    self._stats[exe0] = r[1]
                if self.game is not g or not (r and r[0] and r[0].get("found")):
                    return self._refresh_status()
                got = int(round(r[1]["mult"])) if r[1] and r[1]["mult"] > 1 else None
                self._learn_cap(g, got)
                self.lbl_logs.configure(text=self.L("logs_found") + (self.L("last_measured") % got if got else ""))
                self._refresh_status()                  # un plafond prouvé change le multiplicateur prévu
            self._async(lambda: (loganalyze.read(exe0), loganalyze.session_stats(exe0)), seen)
            npi0, w0 = self.npi.get(), self.cfg.get("cap_written", {}).get(g["appid"])

            def capped(v, e):                            # plafond FPS du joueur : la fiche l'annonce avant le clic
                self._caps[exe0] = None if e else v
                if self.game is g:
                    self._refresh_status()
            self._async(lambda: nvcp.user_cap(npi0, DATA, os.path.basename(exe0), w0), capped)
        if self._up_game != g["dir"]:
            self._up_game, self._up_last = g["dir"], None
            self._up_tok += 1                        # les opérations de l'ancien jeu ne touchent plus à l'état
            self._up_busy = self._up_dl = False
        cached = self._ups_cache.get(g["dir"])
        if cached:                                   # changement de jeu instantané : on montre le dernier état connu
            self._fill_upscalers(*cached)
        else:
            self._up_bar(False)
            self._ups_sig = None                     # sinon un jeu à signature identique resterait sur « scan… »
            for w in self.up_box.winfo_children():
                w.destroy()
            ctk.CTkLabel(self.up_box, text=self.L("scan_ups"), font=FONT, text_color=DIM).pack(anchor="w")
        self._reload_upscalers(g)
        self._refresh_status()

    @staticmethod
    def _ups_signature(ups):
        return [(u["name"], u["version"], upscalers.has_backup(u["path"])) for u in ups]

    def _reload_upscalers(self, g, delay=0, tok=None):
        """Rescan léger en arrière-plan ; ne reconstruit la liste que si quelque chose a changé.

        `tok` = jeton de l'opération (install/restauration) qui demande ce rescan : seul le rescan
        portant le jeton courant libère les boutons.
        """
        def work():
            ups = upscalers.scan(g["dir"])
            man = getattr(self, "_manifest", None)
            if not man:
                try:
                    man = self._manifest = upscalers.latest()   # CDN DLSS Swapper, cache disque 6 h
                except Exception:
                    man = {}                                    # un manifeste cassé ne doit pas effacer le scan
            return ups, man
        def done(r, e):
            if tok is not None and tok == self._up_tok:
                self._up_busy = self._up_dl = False
                self._up_bar(False)
            if self.game is not g or e or not r:
                if self.game is g and tok is not None and tok == self._up_tok and g["dir"] in self._ups_cache:
                    self._fill_upscalers(*self._ups_cache[g["dir"]])   # au moins ré-armer les boutons
                return
            ups, man = r
            self._ups_cache[g["dir"]] = (ups, man)
            if (self._ups_signature(ups) != self._ups_sig or not self.up_box.winfo_children()
                    or (tok is not None and tok == self._up_tok)):
                self._fill_upscalers(ups, man)
        self.after(delay, lambda: self._async(work, done))

    def _pick_exe(self):
        """Choix manuel du .exe quand l'auto-détection ne résout rien (jeu sans exe trouvé)."""
        p = filedialog.askopenfilename(title=self.L("change_exe"),
                                       filetypes=[("Exécutable", "*.exe"), ("Tous", "*.*")],
                                       initialdir=(self.game or {}).get("dir", ""))
        if p:
            p = os.path.normpath(p)
            keep = [v for v in self.cmb.cget("values") if v and v != p]
            self.cmb.configure(values=[p] + keep)   # garde les exe auto-détectés
            self.exe.set(p)
            self.lbl_logs.configure(text="")        # aperçu logs lié à l'ancien exe -> vide

    def _fill_upscalers(self, ups, manifest=None):
        manifest = manifest or {}
        self._ups_sig = self._ups_signature(ups)
        self._up_bar(False)                          # arrête l'animation AVANT de détruire la barre
        for w in self.up_box.winfo_children():
            w.destroy()
        hdr = ctk.CTkFrame(self.up_box, fg_color="transparent"); hdr.pack(fill="x")
        lib = self.cfg.get("dll_lib", "")
        ctk.CTkButton(hdr, text="Bibliothèque DLL : " + (os.path.basename(lib) if lib else "choisir…"),
                      font=FONT, fg_color=SURF2, hover_color=GREEN_D, command=self._pick_lib,
                      state="disabled" if self._up_busy else "normal").pack(side="left")
        self._ups_todo = []                          # upscalers with a newer version, filled below
        self._up_all_btn = ctk.CTkButton(hdr, text=self.L("up_all"), font=FONT_B, width=190, fg_color=GREEN_D, hover_color=GREEN,
                                         text_color=BG, text_color_disabled=DIM, state="disabled", command=self._install_all)
        self._up_all_btn.pack(side="right")
        self._up_status = ctk.CTkLabel(self.up_box, text="", font=FONT, text_color=GREEN, anchor="w", wraplength=440, justify="left")
        self._up_status.pack(fill="x", pady=(2, 4))
        self._up_prog = ctk.CTkProgressBar(self.up_box, mode="indeterminate", height=6, progress_color=GREEN, fg_color=SURF2)
        if self._up_last:
            self._up_status.configure(text=self._up_last[0], text_color=self._up_last[1])
        if self._up_dl:
            self._up_bar(True)
        if not ups:
            ctk.CTkLabel(self.up_box, text=self.L("no_ups"), font=FONT, text_color=DIM).pack(anchor="w")
            return
        lib = lib or os.path.join(RES, "tools", "dlls")
        for u in ups:
            row = ctk.CTkFrame(self.up_box, fg_color="transparent"); row.pack(fill="x", pady=4)
            m = upscalers.library_match(u["name"], lib)
            avail = (m[1] if m else manifest.get(u["name"].lower(), {}).get("version"))
            if avail and avail != u["version"]:
                btxt, state, col = f"Installer v{avail}", "normal", GREEN_D
                self._ups_todo.append(u)
            elif avail:
                btxt, state, col = "À jour", "disabled", SURF2
            else:
                btxt, state, col = self.L("install_dll"), "normal", GREEN_D
            tail = f"  →  dispo v{avail}" if avail else "  (dernière : bibliothèque non configurée)"
            ctk.CTkLabel(row, text=f"{u['vendor']} · {u['role']} · v{u['version']}{tail}", font=FONT,
                         anchor="w", text_color=TXT).pack(side="left", fill="x", expand=True)
            if upscalers.has_backup(u["path"]):
                ctk.CTkButton(row, text="Restaurer", font=FONT, width=100, fg_color=SURF2, text_color_disabled=DIM,
                              hover_color=GREEN_D, state="disabled" if self._up_busy else "normal",
                              command=lambda u=u: self._restore_dll(u)).pack(side="left", padx=4)
            ctk.CTkButton(row, text=btxt, font=FONT, width=160, fg_color=col, hover_color=GREEN,
                          text_color=BG, text_color_disabled=DIM,
                          state="disabled" if (self._up_busy or state == "disabled") else "normal",
                          command=lambda u=u: self._install_dll(u)).pack(side="left")
        if self._ups_todo and not self._up_busy:
            self._up_all_btn.configure(state="normal")

    def _install_all(self):
        """Update every upscaler that has a newer version, one after the other in the background; all buttons stay greyed until the end."""
        if self._up_busy or not self._ups_todo:
            return
        g, todo = self.game, list(self._ups_todo)
        lib = self.cfg.get("dll_lib", "") or os.path.join(RES, "tools", "dlls")
        self._up_busy = self._up_dl = True
        self._up_tok += 1
        tok = self._up_tok
        cached = self._ups_cache.get(g["dir"])
        if cached:
            self._fill_upscalers(*cached)            # every button greyed at once
        self._up_bar(True)
        self._up_msg("⏳ " + self.L("up_all_run") % len(todo), DIM)

        def work():
            lines = []
            for u in todo:
                try:
                    m = upscalers.library_match(u["name"], lib)
                    if m:
                        lines.append((True, upscalers.swap(u["path"], m[0]) + f" (v{m[1]})"))
                    else:
                        ok, msg = upscalers.install_latest(u["path"])
                        lines.append((ok, u["name"] + " : " + msg))
                except Exception as e:                # one failure must not stop the others
                    lines.append((False, u["name"] + " : " + str(e)))
            return lines
        def done(lines, e):
            lines = lines or [(False, str(e))]
            for ok, msg in lines:
                self._log(("✓ " if ok else "✗ ") + msg)
            if tok != self._up_tok or self.game is not g:
                return
            self._up_dl = False
            self._up_bar(False)
            good = sum(ok for ok, _ in lines)
            self._up_msg(("✓ " if good == len(lines) else "⚠ ") + self.L("up_all_done") % (good, len(lines)),
                         GREEN if good == len(lines) else "#f0b63a")
            self._reload_upscalers(g, 3500, tok)     # the rescan with this token frees the buttons
        self._async(work, done)

    def _pick_lib(self):
        d = filedialog.askdirectory(title="Dossier bibliothèque de DLL (DLSS/FSR/XeSS récents)")
        if d:
            self.cfg["dll_lib"] = d; config.save(self.cfg)
            if self.game:
                self._set_game(self.game)

    def _up_msg(self, text, color=GREEN):
        """Confirmation INLINE dans la zone updater (pas de fenêtre popup)."""
        self._up_last = (text, color)
        lbl = getattr(self, "_up_status", None)
        if lbl is not None and lbl.winfo_exists():
            self._fade_text(lbl, text, color)

    def _up_bar(self, on):
        bar = getattr(self, "_up_prog", None)
        if bar is None or not bar.winfo_exists():
            return
        if on:
            bar.pack(fill="x", pady=(0, 6), after=self._up_status)
            bar.start()
        else:
            bar.stop()
            bar.pack_forget()

    def _restore_dll(self, u):
        if self._up_busy:
            return
        g = self.game
        try:
            self._up_msg("✓ " + upscalers.restore(u["path"]), GREEN)
        except Exception as e:
            self._up_msg("✗ " + str(e), "#f0b63a")
            return
        self._begin_up_op(g, 3500)

    def _begin_up_op(self, g, delay):
        """Fige les boutons, puis rescan léger après `delay` (confirmation inline visible entre-temps)."""
        self._up_busy = True
        self._up_tok += 1
        cached = self._ups_cache.get(g["dir"])
        if cached:
            self._fill_upscalers(*cached)            # boutons grisés immédiatement
        self._reload_upscalers(g, delay, self._up_tok)

    def _install_dll(self, u):
        # Priorité : bibliothèque locale (fiable, hors ligne) -> manifeste CDN. Confirmation inline.
        if self._up_busy:
            return
        g = self.game
        lib = self.cfg.get("dll_lib", "") or os.path.join(RES, "tools", "dlls")
        self._up_msg("⏳ " + u["name"] + " …", DIM)
        m = upscalers.library_match(u["name"], lib)
        if m:
            try:
                self._up_msg("✓ " + upscalers.swap(u["path"], m[0]) + f" (v{m[1]})", GREEN)
            except Exception as e:
                self._up_msg("✗ " + str(e), "#f0b63a")
                return
            self._begin_up_op(g, 4500)
            return
        self._up_busy = self._up_dl = True
        self._up_tok += 1
        tok = self._up_tok
        cached = self._ups_cache.get(g["dir"])
        if cached:
            self._fill_upscalers(*cached)            # grey the other buttons on screen too, not only internally
        self._up_bar(True)

        def work():
            return upscalers.install_latest(u["path"])
        def done(res, e):
            ok, msg = (res if res else (False, str(e)))
            if tok != self._up_tok or self.game is not g:   # jeu changé / autre opération : ne touche plus à l'UI
                self._log(("✓ " if ok else "✗ ") + u["name"] + " : " + msg)
                return
            self._up_dl = False
            self._up_bar(False)
            if ok:
                self._up_msg("✓ " + msg, GREEN)
                self._reload_upscalers(g, 4500, tok)  # confirmation ~4,5 s puis la ligne passe à « À jour »
            else:
                self._up_busy = False
                self._up_msg("✗ " + msg + "  — configure une bibliothèque DLL (bouton ci-dessus).", "#f0b63a")
                self._reload_upscalers(g, 0)
        self._async(work, done)

    def _load_cover(self, appid):
        if not self.cover.winfo_exists():
            return
        self._cover_img = None                 # garder une réf -> éviter que Tk libère l'image (bug pyimage)
        dest = os.path.join(DATA, "_covers", f"{appid}.jpg")
        try:                                   # déjà en cache disque (la grille l'a chargée) : affichage immédiat, sans « Chargement… »
            if str(appid).isdigit() and os.path.getsize(dest) > 0:
                self._cover_img = ctk.CTkImage(Image.open(dest).convert("RGB"), size=(112, 158))
                return self.cover.configure(image=self._cover_img, text="")
        except Exception:
            pass
        try:
            self.cover.configure(image=None, text=self.L("loading"))
        except Exception:
            pass
        if not str(appid).isdigit():
            return self.cover.configure(text="")
        g = self.game
        def done(p, e):
            if not self.cover.winfo_exists() or self.game is not g:
                return                          # jeu changé / panneau détruit -> ne pas toucher une image périmée
            try:
                if p:
                    self._cover_img = ctk.CTkImage(Image.open(p), size=(112, 158))
                    self.cover.configure(image=self._cover_img, text="")
                else:
                    self.cover.configure(image=None, text="")
            except Exception:
                try: self.cover.configure(image=None, text="")
                except Exception: pass
        self._async(lambda: steam.fetch_cover(appid, dest), done)

    def _manual(self):
        d = filedialog.askdirectory(title="Dossier du jeu / game folder")
        if not d:
            return
        def done(g, e):
            if e or not g:
                return
            extra = self.cfg.setdefault("extra_games", [])
            if g["dir"] not in extra:
                extra.append(g["dir"])
                config.save(self.cfg)
            if all(os.path.normcase(x["dir"]) != os.path.normcase(g["dir"]) for x in self.games):
                self.games.append(g)
                self.games.sort(key=lambda x: x["name"].lower())
                self._refresh_games()
            self._set_game(g)
        self._async(lambda: steam.game_from_dir(d), done)

    # ---------- modale DANS la fenêtre (overlay, pas de 2e fenêtre) ----------
    def _overlay(self, title):
        """Carte modale posée SUR la fenêtre (plus petite que la fenêtre -> on voit le cadre autour)."""
        self._close_overlay()
        card = ctk.CTkFrame(self, fg_color=SURF, corner_radius=16, border_color=GREEN, border_width=2)
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.64, relheight=0.74)
        self._ov = card
        head = ctk.CTkFrame(card, fg_color="transparent"); head.pack(fill="x", padx=16, pady=(14, 4))
        ctk.CTkLabel(head, text=title, font=FONT_H, text_color=GREEN).pack(side="left")
        ctk.CTkButton(head, text="✕", width=42, height=36, font=FONT_B, fg_color=SURF2,
                      hover_color=EDGE, command=self._close_overlay).pack(side="right")
        bar = ctk.CTkFrame(card, fg_color="transparent"); bar.pack(side="bottom", fill="x", padx=16, pady=(6, 14))
        body = ctk.CTkScrollableFrame(card, fg_color=SURF2, corner_radius=12)
        body.pack(fill="both", expand=True, padx=16, pady=(0, 6))
        return body, bar

    def _close_overlay(self):
        ov = getattr(self, "_ov", None)
        if ov is not None and ov.winfo_exists():
            ov.destroy()
        self._ov = None

    def _npi_to_save(self):
        """On ne mémorise que un NPI choisi à la main ; jamais le NPI intégré (son dossier temporaire change)."""
        p = self.npi.get()
        return "" if os.path.normcase(p) == os.path.normcase(NPI_BUNDLED) else p

    def _on_close(self):
        """Fermeture propre : annule les jaquettes en attente (sinon le process reste vivant des minutes)."""
        self._closing = True
        if self._probe:
            self._probe.stop()
        self._cover_pool.shutdown(wait=False, cancel_futures=True)
        self.destroy()

    def _apply_block(self):
        """Texte qui explique pourquoi on ne peut pas appliquer ici, ou None si on peut (installer/écraser)."""
        exe = self.exe.get()
        if not (self.game and exe):
            return None
        if not self._scanned:
            return self.L("scanning")
        if self._clash:
            return self.L("blk_clash") % ", ".join(self._clash)
        hint = self.cfg.get("applied", {}).get(self.game["appid"])
        ok, code, detail = installer.check_apply(MOD_ROOT, exe, self.proxy.get(), hint)
        if ok:
            return None
        return {"foreign_ini": self.L("blk_foreign_ini"),
                "other_proxy": self.L("blk_other_proxy") % detail,
                "locked": self.L("blk_locked") % detail}[code]

    # ---------- 5 apply ----------
    def _open_soft_opts(self):
        """Options logiciel (globales) : chemin NPI, revert NVCP, rapport, admin."""
        if self._busy:
            return
        pad, bar = self._overlay(self.L("soft_opts"))
        ctk.CTkButton(bar, text=self.L("close"), font=FONT_B, width=140, height=46, fg_color=SURF2,
                      hover_color=EDGE, command=self._close_overlay).pack(side="left")
        self._label_tip(pad, self.L("nvcp"), "nvcp", GREEN).pack(anchor="w", padx=14, pady=(14, 0))
        row = ctk.CTkFrame(pad, fg_color="transparent"); row.pack(fill="x", padx=14, pady=6)
        ctk.CTkEntry(row, textvariable=self.npi, font=FONT).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(row, text="…", width=46, font=FONT_B, fg_color=GREEN_D, text_color=BG, command=self._pick_npi).pack(side="left", padx=6)
        btns = ctk.CTkFrame(pad, fg_color="transparent"); btns.pack(anchor="w", padx=14, pady=10)
        ctk.CTkButton(btns, text=self.L("revert"), font=FONT, width=160, fg_color=SURF,
                      hover_color=GREEN_D, command=self._revert_nvcp).pack(side="left")
        ctk.CTkButton(pad, text="📦 " + self.L("report_btn"), font=FONT, anchor="w", height=40, fg_color=SURF,
                      hover_color=GREEN_D, command=self._export_report).pack(fill="x", padx=14, pady=(14, 4))
        ctk.CTkButton(pad, text="ℹ " + self.L("about_btn"), font=FONT, anchor="w", height=40, fg_color=SURF,
                      hover_color=GREEN_D, command=self._show_about).pack(fill="x", padx=14, pady=(4, 4))
        if not nvcp.is_admin():
            ctk.CTkButton(btns, text=self.L("admin"), font=FONT, width=180, fg_color="#7a5a20",
                          hover_color="#9a7430", command=self._relaunch_admin).pack(side="left", padx=8)
            ctk.CTkLabel(pad, text=self.L("admin_warn"), font=FONT, text_color="#f0b63a",
                         wraplength=560, justify="left").pack(anchor="w", padx=14)

    def _show_about(self):
        body, bar = self._overlay(self.L("about_title"))
        ctk.CTkButton(bar, text=self.L("close"), font=FONT_B, width=140, height=46, fg_color=SURF2,
                      hover_color=EDGE, command=self._close_overlay).pack(side="left")
        ctk.CTkLabel(body, text=self.L("about_text"), font=FONT, text_color=TXT, wraplength=640,
                     justify="left").pack(anchor="w", padx=18, pady=16)
        for label, url in (("dlssg_for_sm86 / SM75 — sdli1995 (GitHub)", "https://github.com/sdli1995/dlssg_for_sm86"),
                           ("NVIDIA Profile Inspector — Orbmu2k (GitHub)", "https://github.com/Orbmu2k/nvidiaProfileInspector"),
                           ("DLSS Swapper — beeradmoore (GitHub)", "https://github.com/beeradmoore/dlss-swapper"),
                           ("☕ Ko-fi", KOFI_URL)):
            ctk.CTkButton(body, text=label, font=FONT, anchor="w", height=40, fg_color=SURF, hover_color=GREEN_D,
                          command=lambda u=url: webbrowser.open(u)).pack(fill="x", padx=18, pady=4)

    def _pick_npi(self):
        p = filedialog.askopenfilename(title="nvidiaProfileInspector.exe", filetypes=[("exe", "*.exe")])
        if p: self.npi.set(p)

    def _relaunch_admin(self):
        self.cfg["npi_exe"] = self._npi_to_save(); config.save(self.cfg)
        try:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable,
                                                f'"{os.path.abspath(__file__)}"', None, 1)
            self.destroy()
        except Exception as e:
            messagebox.showerror("YogoMFG", f"Relance admin échouée: {e}")

    def _revert_nvcp(self):
        """Annule TOUT ce que YogoMFG a écrit dans les profils NVIDIA (tous les jeux + ancien préréglage global 0.6.x)."""
        npi = self.npi.get()
        def work():
            out = [nvcp.revert(npi, DATA)[1], nvcp.restore_mfg(npi, DATA)[1], nvpreset.revert_fg_global(npi, DATA)[1]]
            if "originals" in nvpreset.state(DATA):      # préréglage global posé par une 0.6.x (bouton retiré en 0.7.0)
                out.append(nvpreset.revert(npi, DATA)[1])
            return chr(10).join(out)
        self._async(work, lambda r, e: messagebox.showinfo(
            "YogoMFG", r if e is None else f"Annulation échouée : {e}", parent=self))

    def _post(self, frac, line=None):
        def u():
            if frac is not None:
                self.prog.set(frac)
            if line:
                self._log(line)
        self.after(0, u)

    def do_apply(self):
        """« Optimiser ce jeu » : mod + INI + profil NVIDIA du jeu, tout décidé automatiquement (voir inimaker.plan)."""
        if self._busy:
            return
        if not (self.game and self.exe.get()):
            return messagebox.showwarning("YogoMFG", self.L("need_game"))
        block = self._apply_block()
        if block:                                        # revérifie au dernier moment (le jeu a pu être lancé entre-temps)
            self.log.delete("1.0", "end")
            self._log("⛔ " + block)
            return
        if self._anticheat and not messagebox.askyesno(
                "YogoMFG", self.L("anticheat_ask") % ", ".join(self._anticheat),
                icon="warning", default="no", parent=self):
            return
        # Règle 2 (0.7.0) : cliquer « Optimiser » EST l'accord ; chaque écriture est relue, journalisée, annulée par Retirer.
        self._set_busy(True, self.L("busy_opt"))
        self.log.delete("1.0", "end"); self.prog.set(0.05)
        exe_full, g, npi = self.exe.get(), self.game, self.npi.get()
        written = self.cfg.get("cap_written", {}).get(g["appid"])
        # dernière session + plafond FPS du joueur (profil NVIDIA), relus au moment du clic (hors thread UI)
        self._async(lambda: (loganalyze.session_stats(exe_full), nvcp.user_cap(npi, DATA, os.path.basename(exe_full), written)),
                    lambda r, e: self._apply_planned(g, exe_full, None if e else r[0], None if e else r[1]))

    def _apply_planned(self, g, exe_full, stats, ucap=None):
        """Suite d'« Optimiser » : plan calculé avec la session fraîche et le plafond du joueur, puis écritures dans un thread."""
        self._stats[exe_full] = stats
        self._caps[exe_full] = ucap
        appid = g["appid"]
        if stats and stats["mult"] > 1:
            self._learn_cap(g, int(round(stats["mult"])))      # demandé x4, obtenu x3 -> plafond prouvé x3
        p = self._plan(appid, stats)
        mult, cap, warn, cal = p
        self._better.discard(appid)                                  # la proposition est appliquée
        prev = installer.status(exe_full)["mult"]
        self.cfg.setdefault("applied", {})[appid] = self.proxy.get()   # proxy posé pour ce jeu
        self.cfg.setdefault("mult_by_game", {})[appid] = mult          # demandé -> plafond prouvé si le jeu donne moins
        self.cfg.setdefault("installed_exe", {})[appid] = exe_full     # recalibrage au prochain démarrage
        self.cfg.setdefault("cap_written", {})[appid] = cap            # notre cap : distingué du plafond réglé par le joueur
        if ucap and cap == ucap:
            self._log("ℹ " + self.L("cap_kept") % ucap)
        self.cfg["npi_exe"] = self._npi_to_save(); self.cfg["proxy"] = self.proxy.get()
        config.save(self.cfg)
        head, _, tail = self._result_text(p).partition(chr(10))
        self._log(("✓ " if cal else "ℹ ") + head + (f"  (x{prev} → x{mult})" if cal and prev and prev != mult else "")
                  + (chr(10) + tail if tail else ""))
        if self.vrr:
            self._log("ℹ " + self.L("gsync_hint"))
        args = (exe_full, self.proxy.get(), mult, cap, bool(self.vrr), self.npi.get())
        free = bool(self.cfg.get("manual_mult", {}).get(appid))   # Manuel : plafond seulement, le menu du jeu décide
        qual, hz, vram, series = self.quality.get(), self.refresh, self.hw.get("vram_mb", 0), self.hw.get("series", "30")
        L = self.L

        def worker():
            results, need_admin = [], False
            try:
                results, need_admin = self._write_game(*args, self._post, free)
                if results and results[0][1]:
                    self._post(None, chr(10) + L("advice") + " :")
                    for a in optadvice.advise(hz or 60, vram, series, qual):
                        self._post(None, "  • " + a)
            except Exception as e:      # jamais de worker silencieux : sinon _busy reste True et le bouton est mort
                self._post(None, "✗ " + str(e))
                results.append(("Erreur", False))
            finally:
                self._post_done(results)
                if need_admin:
                    self.after(0, self._ask_admin)

        threading.Thread(target=worker, daemon=True).start()

    def _write_game(self, exe_full, proxy, mult, cap, vrr, npi, post, free=False):
        """Écritures d'« Optimiser » (thread de travail) : fichiers du mod puis profil NVIDIA du jeu, chacun vérifié.

        Retourne (résultats [(libellé, ok)], admin_requis). `post(fraction, ligne)` publie vers la console.
        """
        L, exe, results = self.L, os.path.basename(exe_full), []
        post(0.1, "⏳ " + L("opt_files"))
        try:
            acts = installer.install(MOD_ROOT, exe_full, inimaker.make(mult), proxy)
            post(0.45, "✓ " + ", ".join(acts))
            results.append((L("rc_mod") % mult, True))
        except Exception as e:
            post(0.45, "✗ " + str(e))
            return results + [(L("rc_mod") % mult, False)], False
        need_admin = False
        if cap:
            post(0.6, "⏳ " + L("opt_nv") % (cap, " + G-Sync/FreeSync" if vrr else ""))
            ok, msg = nvcp.apply(npi, DATA, cap, vrr, exe)
            need_admin = msg.startswith("NEED_ADMIN")
            post(0.75, ("✓ " if ok else "✗ ") + ("NVIDIA : " + L("need_admin_nv") if need_admin else msg))
            results.append((L("rc_cap") % cap, ok))
        else:
            post(0.75, "ℹ " + L("hz_unknown"))
        if not need_admin and free:     # Manuel : xN = PLAFOND ; le menu du jeu choisit librement de x2 à xN
            ok, msg = nvcp.restore_mfg(npi, DATA, exe)   # enlève un multiplicateur imposé par une optimisation précédente
            need_admin = msg.startswith("NEED_ADMIN")
            ok = ok or msg.startswith("Aucun")
            post(0.92, ("✓ " if ok else "✗ ") + L("mult_free") % mult)
            results.append((L("rc_mult") % mult, ok))
        elif not need_admin:
            post(0.85, "⏳ " + L("opt_mult") % mult)
            ok, msg = nvcp.unlock_mfg(npi, DATA, mult - 1, exe)
            need_admin = msg.startswith("NEED_ADMIN")
            post(0.92, ("✓ " if ok else "✗ ") + msg)
            results.append((L("rc_mult") % mult, ok))
        if not need_admin:            # plafond x6 + VRR plein écran/fenêtré dans le global ; jamais de nombre imposé
            ok, msg = nvpreset.apply_fg_global(npi, DATA, vrr)
            need_admin = msg.startswith("NEED_ADMIN")
            post(0.96, ("✓ " if ok else "✗ ") + msg)
            results.append((L("rc_global"), ok))
        return results, need_admin

    def _auto_calibrate(self):
        """Au démarrage : recalcule le multiplicateur des jeux optimisés d'après leur dernière session mesurée et
        réécrit INI + profil du jeu s'il a changé. Jamais d'INI et de profil désaccordés : sans admin alors que le
        pilote est autorisé, on laisse le clic « Optimiser » le faire (il demandera l'admin)."""
        games = {a: e for a, e in self.cfg.get("installed_exe", {}).items() if e and os.path.isfile(e)}
        if self._busy or not games or not self.refresh:
            return
        self._busy = True                                # lecture des journaux seulement : pas d'écran de chargement

        npi, written = self.npi.get(), dict(self.cfg.get("cap_written", {}))

        def read():
            return {a: (e, installer.status(e), loganalyze.session_stats(e),
                        nvcp.user_cap(npi, DATA, os.path.basename(e), written.get(a))) for a, e in games.items()}

        def decided(found, err):
            # nothing is written here: a better multiplier is only PROPOSED (button + cover), one click applies it
            for appid, (exe, st, stats, ucap) in (found or {}).items():
                if stats and stats["mult"] > 1:
                    self._learn_cap({"appid": appid}, int(round(stats["mult"])))
                self._stats[exe], self._caps[exe] = stats, ucap
                p = self._plan(appid, stats, exe)
                if st["installed"] and p[3] and p[0] != st["mult"]:
                    self._better.add(appid)
                    self._log("✨ " + os.path.basename(exe) + " — " + self.L("better_log") % (st["mult"], p[0]))
            self._set_busy(False)
        self._async(read, decided)

    def _ask_admin(self):
        if messagebox.askyesno("YogoMFG", "Le réglage NVIDIA exige l'admin. Relancer en admin ?"):
            self._relaunch_admin()

    def _post_done(self, results):
        def u():
            self._set_busy(False)
            self.prog.set(1.0)
            self._log(chr(10) + self.L("recap"))
            for name, ok in results:
                self._log(("  ✓ " if ok else "  ✗ ") + name + "  " + self.L("ok_v" if ok else "ko_v"))
            self._log(chr(10) + self.L("done_hint"))
            self._log("💡 " + self.L("after_opt_hint"))
            self._refresh_status()
        self.after(0, u)

    # ---------- 6 analyze ----------
    def _open_analyze(self):
        if not (self.game and self.exe.get()):
            return messagebox.showwarning("YogoMFG", self.L("need_game"))
        card, bar = self._overlay(self.L("an_run"))
        self.b_reco = ctk.CTkButton(bar, text=self.L("apply_reco"), font=FONT_B, fg_color=GREEN,
                                    hover_color=GREEN_D, text_color=BG, state="disabled", command=self._apply_reco)
        self.b_reco.pack(side="left")
        ctk.CTkButton(bar, text=self.L("an_run"), font=FONT_B, width=180, fg_color=GREEN, hover_color=GREEN_D,
                      text_color=BG, command=self.do_analyze).pack(side="right")
        ctk.CTkButton(bar, text=self.L("close"), font=FONT_B, width=120, fg_color=SURF2,
                      hover_color=EDGE, command=self._close_overlay).pack(side="right", padx=8)
        ctk.CTkButton(bar, text="📦 " + self.L("report_btn"), font=FONT_B, width=190, fg_color=SURF2,
                      hover_color=GREEN_D, command=self._export_report).pack(side="right", padx=4)
        gf = ctk.CTkFrame(card, fg_color="transparent"); gf.pack(anchor="w", padx=18, pady=(12, 4))
        ctk.CTkLabel(gf, text=self.L("an_goal") + " :", font=FONT_B, text_color=DIM).pack(side="left", padx=(0, 10))
        ctk.CTkRadioButton(gf, text=self.L("goal_fps"), variable=self.goal, value="fps", font=FONT, fg_color=GREEN).pack(side="left", padx=8)
        ctk.CTkRadioButton(gf, text=self.L("goal_q"), variable=self.goal, value="quality", font=FONT, fg_color=GREEN).pack(side="left", padx=8)
        ctk.CTkLabel(card, text=self.L("an_hint"), font=FONT, text_color=DIM,
                     wraplength=680, justify="left").pack(anchor="w", padx=18, pady=6)
        ctk.CTkLabel(card, text=self.L("did_title"), font=FONT_B, text_color=GREEN).pack(anchor="w", padx=18, pady=(6, 0))
        cl = ctk.CTkFrame(card, fg_color="transparent"); cl.pack(anchor="w", padx=18)
        if not hasattr(self, "did"):
            self.did = {k: ctk.BooleanVar(value=d) for k, d in
                        (("fg", True), ("reflex", True), ("rt", False), ("pt", False), ("vsync_off", True))}
            self.did_dlss = ctk.StringVar(value=self.quality.get())
        for i, (k, lab) in enumerate((("fg", "did_fg"), ("reflex", "did_reflex"), ("rt", "did_rt"),
                                      ("pt", "did_pt"), ("vsync_off", "did_vsync"))):
            ctk.CTkCheckBox(cl, text=self.L(lab), variable=self.did[k], font=FONT, fg_color=GREEN
                            ).grid(row=i // 3, column=i % 3, sticky="w", padx=8, pady=4)
        dl = ctk.CTkFrame(card, fg_color="transparent"); dl.pack(anchor="w", padx=18, pady=4)
        ctk.CTkLabel(dl, text=self.L("did_dlss"), font=FONT, text_color=DIM).pack(side="left", padx=(0, 8))
        ctk.CTkOptionMenu(dl, variable=self.did_dlss, values=inimaker.QUALITY, font=FONT, width=180,
                          fg_color=SURF, button_color=GREEN_D).pack(side="left")
        self.an_box = ctk.CTkTextbox(card, font=MONO, fg_color=BG, text_color=TXT, height=240)
        self.an_box.pack(fill="both", expand=True, padx=18, pady=8)
        self._delta = {}

    def _report_info(self):
        h = self.hw or {}
        g = self.game or {}
        return {
            "YogoMFG": VERSION, "Jeu": g.get("name", "?"), "Exe": os.path.basename(self.exe.get() or "?"),
            "GPU": h.get("name", "?"), "VRAM Mo": h.get("vram_mb", "?"), "Pilote": h.get("driver", "?"),
            "CPU": h.get("cpu", "?"), "RAM Go": h.get("ram_gb", "?"), "Écran Hz": self.refresh or "?",
            "VRR (G-Sync/FreeSync)": self.vrr or "non détecté",
            "Plugin DLSS-G du jeu": f"{self._mfg_ver or '?'} (plafond indicatif x{self._mfg_cap})",
            "Multiplicateur automatique": "x%d, cap FPS %s, avertissement %s, calibré %s" % self._plan(),
            "Mémorisé pour ce jeu": self.cfg.get("mult_by_game", {}).get(g.get("appid", ""), "-"),
            "Anti-cheat détecté": self._anticheat or "aucun", "Autres mods FG": self._clash or "aucun",
        }

    def _export_report(self):
        if not (self.game and self.exe.get()):
            return messagebox.showwarning("YogoMFG", self.L("need_game"))
        import datetime
        path = filedialog.asksaveasfilename(
            title=self.L("report_btn"), defaultextension=".zip", filetypes=[("ZIP", "*.zip")],
            initialfile=f"YogoMFG-rapport-{datetime.datetime.now():%Y%m%d-%H%M}.zip")
        if not path:
            return
        info, exe = self._report_info(), self.exe.get()
        extra = [x for x in self.an_box.get("1.0", "end").splitlines() if x.strip()] if hasattr(self, "an_box") \
            and self.an_box.winfo_exists() else []

        def done(res, e):
            msg = (self.L("report_ok") % path) if not e else ("✗ " + str(e))
            if hasattr(self, "an_box") and self.an_box.winfo_exists():
                self.an_box.insert("end", chr(10) + msg + chr(10) + self.L("report_hint") + chr(10))
                self.an_box.see("end")
            else:
                self._log(msg)
        self._async(lambda: report.build(path, info, exe, DATA, extra), done)

    def do_analyze(self):
        if not (self.game and self.exe.get()):
            return messagebox.showwarning("YogoMFG", self.L("need_game"))
        exe, fps, goal = self.exe.get(), self.refresh or 60, self.goal.get()   # snapshot (pas de .get() en thread)
        self.an_box.delete("1.0", "end"); self.an_box.insert("end", self.L("loading") + "\n")
        def done(res, e):
            if not self.an_box.winfo_exists():   # modale fermée avant la fin -> ne rien toucher
                return
            self.an_box.delete("1.0", "end")
            if e:
                return self.an_box.insert("end", "Erreur: " + str(e))
            lines, delta = res
            self.an_box.insert("end", "\n".join(lines) + "\n")
            self._delta = delta or {}
            self.b_reco.configure(state="normal" if delta else "disabled")
        did = {k: v.get() for k, v in self.did.items()}
        did["dlss"] = self.did_dlss.get()
        lang = self.lang
        pr, self._probe = self._probe, None

        def work():
            head = []
            if pr:
                pr.stop()
                pr.save_csv(os.path.join(DATA, "probe_last.csv"))
                head = probe.report(pr.rows, lang) + [""]
            lines, delta = loganalyze.analyze(exe, fps, goal, did, lang)
            return head + lines, delta
        self._async(work, done)

    def _apply_reco(self):
        if self._delta.get("dlss_quality"):
            self.quality.set(self._delta["dlss_quality"])
        messagebox.showinfo("YogoMFG", "Reco : DLSS " + inimaker.QUALITY_FR.get(self.quality.get(), "") +
                            " (à régler dans le menu graphique du jeu).")

    def _log(self, s):
        self.log.insert("end", s + "\n"); self.log.see("end")


if __name__ == "__main__":
    try:
        App().mainloop()
    except Exception:
        import traceback
        with open(os.path.join(DATA, "yogomfg_error.log"), "w", encoding="utf-8") as f:
            traceback.print_exc(file=f)
        raise
