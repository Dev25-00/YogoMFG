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

FPS_CHOICES = ["30", "60", "90", "120", "144", "165", "180", "240"]
MULT = {"2X": 2, "3X": 3, "4X": 4, "5X": 5, "6X": 6}   # -> MaxGeneratedFrames 1/2/3/4/5 (plafond ; le jeu doit demander le multi)
KOFI_URL = "https://ko-fi.com/lahlouyoussef"
VERSION = "0.6.2 beta"

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
        self._applied = False
        self._busy = False
        self._mfg_cap = 4
        self._mfg_ver = None
        self._force_ok = (False, None)
        self._anticheat = []
        self._clash = []
        self._cover_img = None
        g = self.cfg["global"]
        self.exe = ctk.StringVar()
        self.proxy = ctk.StringVar(value=self.cfg.get("proxy", "version.dll"))
        self.scope = ctk.StringVar(value="global")
        self.fps = ctk.StringVar(value=str(g.get("fps_target", 120)))
        self.mult = ctk.StringVar(value="4X")
        self.preset = ctk.StringVar(value=g.get("preset", "Auto"))
        self.quality = ctk.StringVar(value=g.get("dlss_quality", "balanced"))
        self.sync_type = ctk.StringVar(value=g.get("sync_type", "gsync"))
        self.do_nvcp = ctk.BooleanVar(value=True)
        self.force_mfg = ctk.BooleanVar(value=False)
        self.unlock_drs = ctk.BooleanVar(value=True)
        self._ups_cache = {}        # dossier du jeu -> (upscalers, manifeste) : affichage instantané au changement de jeu
        self._ups_sig = None
        self._up_busy = False       # boutons figés (install/restauration en cours ou confirmation affichée)
        self._up_dl = False         # téléchargement en cours -> barre de progression
        self._up_tok = 0            # jeton d'opération : seul le rescan de la dernière opération libère _up_busy
        self._up_last = None        # dernier message inline (texte, couleur) du jeu courant
        self._up_game = None
        self._nv_busy = False
        self.frame_timing = ctk.BooleanVar(value=bool(g.get("frame_timing", False)))
        self.ref_quality = ctk.BooleanVar(value=int(g.get("optimized", 2)) == 1)
        self._probe = None
        self._fps_touched = False                 # tant que l'utilisateur ne choisit pas : cible FPS = fréquence de l'écran
        self._scanned = False
        self.vrr = None                           # (min, max, nom) de l'écran si G-Sync/FreeSync, sinon None
        self._closing = False
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._thumbs, self._cards, self._grid_gen = {}, {}, 0
        self._cover_pool = ThreadPoolExecutor(max_workers=4)
        self.mon_var = ctk.StringVar()
        self.hz_var = ctk.StringVar()
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
        self._b_nv = ctk.CTkButton(top, text="⚡ " + self.L("nv_btn"), height=36, font=FONT_B, fg_color=GREEN_D,
                                   text_color=BG, hover_color=GREEN, command=self._open_nvidia_tune)
        self._b_nv.pack(side="right", padx=8)

    def _relabel_banner(self):
        """Retraduit la bannière (le changement de langue ne reconstruisait que la page)."""
        self._b_sub.configure(text=self.L("sub"))
        self._b_support.configure(text=self.L("support"))
        self._b_soft.configure(text="⚙ " + self.L("soft_opts"))
        self._b_nv.configure(text="⚡ " + self.L("nv_btn"))

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
            self._async(self._load_hw, lambda r, e: (self._fill_pc_strip(), self._sync_from_screen()))
        # colonne jeux (gauche) + panneau du jeu (droite)
        mid = ctk.CTkFrame(self.body, fg_color="transparent"); mid.grid(row=1, column=0, sticky="nsew", padx=12, pady=4)
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

    def _sync_from_screen(self):
        """Choix G-Sync/FreeSync par défaut d'après l'écran réellement détecté (modifiable dans Avancé)."""
        if self.vrr and self.sync_type.get() == "none":
            self.sync_type.set("gsync")           # on n'impose jamais « none » : une détection ratée ne doit rien casser

    def _load_hw(self):
        self.hw = hardware.summary()
        self.monitors = display.monitors()
        self.refresh = hardware.refresh_hz()
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
        if not messagebox.askyesno("YogoMFG", self.L("remove_ask")):
            return
        exe = self.exe.get()                                   # snapshot (pas de .get() dans le thread)
        proxy = self.cfg.get("applied", {}).get(self.game["appid"]) or self.proxy.get()
        self._busy = True
        self.prog.set(0.2); self._log("⏳ " + self.L("removing"))
        npi = self.npi.get()
        def work():
            r = installer.uninstall(exe, proxy)
            ok, msg = nvcp.restore_mfg(npi, DATA, os.path.basename(exe))   # retire aussi l'override pilote de ce jeu
            return r, ok, msg
        def done(res, e):
            self._busy = False
            self.prog.set(1.0)
            if e:
                self._log("✗ " + str(e))
            else:
                r, ok, msg = res
                self._log("✓ " + ", ".join(r))
                if self.game:
                    self.cfg.get("applied", {}).pop(self.game["appid"], None)
                    config.save(self.cfg)
                if ok:
                    self._log("✓ " + msg)
                elif msg.startswith("NEED_ADMIN"):
                    self._log("✗ Le multiplicateur reste imposé dans le profil NVIDIA de ce jeu : relance YogoMFG en admin puis Retirer à nouveau.")
                    self._ask_admin()
                elif not msg.startswith("Aucun override"):
                    self._log("✗ " + msg)
            self._refresh_status()
        self._async(work, done)

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
        else:
            if self.frame_timing.get():            # « Mesurer la session » : la sonde GPU/CPU tourne pendant que tu joues
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
            self._thumbs[key] = ctk.CTkImage(self._placeholder(g["name"]), size=(120, 180))
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
            return im

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
        ctk.CTkButton(r, text="⚙ " + self.L("open_opts"), font=FONT_B, height=38, fg_color=GREEN,
                      hover_color=GREEN_D, text_color=BG, command=self._open_options).pack(anchor="w", fill="x", pady=(10, 2))
        actions = ctk.CTkFrame(r, fg_color="transparent"); actions.pack(anchor="w", fill="x", pady=(4, 0))
        ctk.CTkButton(actions, text="▶ " + self.L("launch"), font=FONT_B, fg_color=SURF2, hover_color=GREEN_D,
                      command=self._launch).pack(side="left", expand=True, fill="x", padx=(0, 4))
        ctk.CTkButton(actions, text="📊 " + self.L("analyser"), font=FONT_B, fg_color=SURF2, hover_color=GREEN_D,
                      command=self._open_analyze).pack(side="left", expand=True, fill="x", padx=4)
        qk = ctk.CTkFrame(r, fg_color="transparent"); qk.pack(anchor="w", fill="x", pady=(8, 0))
        ctk.CTkLabel(qk, text=self.L("quick_lbl"), font=FONT, text_color=DIM).pack(side="left", padx=(0, 10))
        self.quick_var = ctk.StringVar(value="4X")
        self.seg_quick = ctk.CTkSegmentedButton(qk, values=list(MULT), variable=self.quick_var, font=FONT_B,
                                                selected_color="#3f7a1a", selected_hover_color="#4f8a1e",
                                                unselected_color=EDGE, unselected_hover_color=SURF, text_color=TXT,
                                                command=self._quick_mult, state="disabled")
        self.seg_quick.pack(side="left")
        self.lbl_quick = ctk.CTkLabel(r, text="", font=FONT, text_color=GREEN, anchor="w", wraplength=520, justify="left")
        self.lbl_quick.pack(anchor="w", fill="x", pady=(2, 0))
        self.btn_remove = ctk.CTkButton(actions, text="🗑 " + self.L("remove"), font=FONT_B, fg_color=SURF2,
                                        hover_color="#7a3030", text_color_disabled=DIM, state="disabled",
                                        command=self._remove)
        self.btn_remove.pack(side="left", expand=True, fill="x", padx=(4, 0))
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
        mem = self.cfg.get("mult_by_game", {}).get((self.game or {}).get("appid"))
        if on:
            shown = mem or st["mult"]
            if shown:
                self.quick_var.set(f"{shown}X")
            bits = ([f"x{shown}"] if shown else []) + ([st["proxy"]] if st["proxy"] else []) \
                + ([self.L("inst_bak") % len(st["backups"])] if st["backups"] else [])
            self._fade_text(self.lbl_inst, self.L("inst_yes") % " · ".join(bits), GREEN)
        else:
            self._fade_text(self.lbl_inst, self.L("inst_no"), DIM)
        self.btn_remove.configure(state="normal" if on else "disabled",
                                  fg_color="#5a2020" if on else SURF2)
        self.seg_quick.configure(state="normal" if on else "disabled")

    def _mult_max(self):
        """Plafond réel du jeu : celui de son plugin DLSS-G, sauf plugin patchable (forçage possible)."""
        appid = (self.game or {}).get("appid")       # plafond PROUVÉ par une session mesurée ; la version du plugin ne prouve rien
        return max(2, min(6, self.cfg.get("proven_cap", {}).get(appid, 6)))

    def _lock_mult(self, seg):
        """Grise les multiplicateurs que le jeu ne peut pas afficher. Les boutons internes de CTk : sans l'API publique."""
        top = self._mult_max()
        for val, btn in getattr(seg, "_buttons_dict", {}).items():
            try:
                btn.configure(state="disabled" if MULT[val] > top else "normal")
            except Exception:
                pass

    def _learn_cap(self, g, got):
        """Retient ce que le jeu a réellement donné. Demandé 6, obtenu 4 -> plafond prouvé x4 ; sinon aucun plafond connu."""
        asked = self.cfg.get("mult_by_game", {}).get(g["appid"])
        caps = self.cfg.setdefault("proven_cap", {})
        old = caps.get(g["appid"])
        if got and asked and got < asked:
            caps[g["appid"]] = got
        elif got and old and got > old:          # le jeu a fait mieux que le plafond retenu (mise à jour du jeu) : on l'oublie
            caps.pop(g["appid"], None)
        if caps.get(g["appid"]) != old:
            config.save(self.cfg)

    def _apply_mult_limits(self):
        top = self._mult_max()
        for var in (self.mult, self.quick_var):
            if MULT[var.get()] > top:
                var.set(f"{top}X")
        self._lock_mult(self.seg_quick)

    def _quick_mult(self, val):
        """Change le multiplicateur imposé du jeu sans réinstaller : une seule écriture dans son profil NVIDIA."""
        if self._busy or not (self.game and self.exe.get()):
            return
        m, g, npi, exe = MULT[val], self.game, self.npi.get(), os.path.basename(self.exe.get())
        self._busy = True
        self._fade_text(self.lbl_quick, self.L("quick_run") % m, DIM)

        def done(r, e):
            self._busy = False
            ok, msg = r if r else (False, str(e))
            if not self.lbl_quick.winfo_exists():
                return
            if ok:
                self.cfg.setdefault("mult_by_game", {})[g["appid"]] = m
                self.mult.set(val)
                self.unlock_drs.set(True)
                config.save(self.cfg)
                self._fade_text(self.lbl_quick, self.L("quick_ok") % m, GREEN)
            elif msg.startswith("NEED_ADMIN"):
                self._fade_text(self.lbl_quick, "✗ " + msg, "#f0b63a")
                self._ask_admin()
            else:
                self._fade_text(self.lbl_quick, "✗ " + msg, "#f0b63a")
        self._async(lambda: nvcp.unlock_mfg(npi, DATA, m - 1, exe), done)

    def _apply_scan(self, g, info, silent):
        """Affiche le résultat du scan (support FG, plugin, conflits, anti-cheat) pour le jeu courant."""
        sup, cap, ver, note, clash = info["sup"], info["cap"], info["ver"], info["note"], info["clash"]
        self._anticheat = info["anticheat"]
        self._clash = clash
        self._mfg_cap = cap
        self._mfg_ver = ver
        self._force_ok = info["force_ok"]
        if not self._force_ok[0]:
            self.force_mfg.set(False)   # jamais de force résiduelle d'un jeu précédent sur un plugin non patchable
        self._apply_mult_limits()
        base = self.L("fg_yes") if sup == "yes" else self.L("fg_no")
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
                if self.game is not g or not (r and r[0] and r[0].get("found")):
                    return
                got = r[1]
                self._learn_cap(g, got)
                self.lbl_logs.configure(text=self.L("logs_found") + (self.L("last_measured") % got if got else ""))
                self._apply_mult_limits()
            self._async(lambda: (loganalyze.read(exe0), loganalyze.measured_mult(exe0)), seen)
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
                      font=FONT, fg_color=SURF2, hover_color=GREEN_D, command=self._pick_lib).pack(side="left")
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
            elif avail:
                btxt, state, col = "À jour", "disabled", SURF2
            else:
                btxt, state, col = self.L("install_dll"), "normal", GREEN_D
            tail = f"  →  dispo v{avail}" if avail else "  (dernière : bibliothèque non configurée)"
            ctk.CTkLabel(row, text=f"{u['vendor']} · {u['role']} · v{u['version']}{tail}", font=FONT,
                         anchor="w", text_color=TXT).pack(side="left", fill="x", expand=True)
            if upscalers.has_backup(u["path"]):
                ctk.CTkButton(row, text="Restaurer", font=FONT, width=100, fg_color=SURF2,
                              hover_color=GREEN_D, command=lambda u=u: self._restore_dll(u)).pack(side="left", padx=4)
            ctk.CTkButton(row, text=btxt, font=FONT, width=160, fg_color=col, hover_color=GREEN,
                          text_color=BG, text_color_disabled=DIM,
                          state="disabled" if (self._up_busy or state == "disabled") else "normal",
                          command=lambda u=u: self._install_dll(u)).pack(side="left")

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

    def _target_fps(self):
        """Cible FPS : le choix de l'utilisateur, sinon la fréquence de l'écran (jamais un 120 oublié)."""
        return self._fps_int() if (self._fps_touched or not self.refresh) else self.refresh

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

    def _reco_mult(self):
        """(multiplicateur conseillé, Hz, FPS réels mesurés|None)."""
        hz = self.refresh or 144
        real = loganalyze.real_fps(self.exe.get()) if self.exe.get() else None
        m = max(2, min(6, round((hz - 3) / real))) if real else (6 if self._mfg_cap >= 6 else 4)
        return min(m, self._mult_max()), hz, real

    def _build_simple(self, parent):
        """Écran de base : un seul choix (le multiplicateur). Tout le reste est décidé automatiquement."""
        ctk.CTkLabel(parent, text=self.L("mult_label"), font=FONT_H, text_color=GREEN).pack(anchor="w", padx=18, pady=(16, 6))
        m, hz, real = self._reco_mult()
        helptxt = ctk.CTkLabel(parent, text="", font=FONT, text_color=TXT, wraplength=620, justify="left")
        def upd(*_):
            if helptxt.winfo_exists():
                helptxt.configure(text=self.L(f"mult_help_{MULT[self.mult.get()]}"))
        seg = ctk.CTkSegmentedButton(parent, values=list(MULT), variable=self.mult, font=FONT_B, height=56,
                                     selected_color="#3f7a1a", selected_hover_color="#4f8a1e", unselected_color=EDGE,
                                     unselected_hover_color=SURF, text_color=TXT, command=upd)
        seg.pack(fill="x", padx=18)
        self._lock_mult(seg)
        if self._mult_max() < 6:
            ctk.CTkLabel(parent, text=self.L("mult_capped") % self._mult_max(), font=FONT, text_color="#f0b63a",
                         wraplength=620, justify="left").pack(anchor="w", padx=18, pady=(8, 0))
        helptxt.pack(anchor="w", padx=18, pady=(10, 4))
        reco = (self.L("reco_mult_real") % (m, round(real, 1), hz)) if real else (self.L("reco_mult_none") % hz).replace("x4", f"x{m}", 1)
        ctk.CTkLabel(parent, text=reco, font=FONT, text_color=GREEN, wraplength=620,
                     justify="left").pack(anchor="w", padx=18, pady=(0, 6))
        if self.unlock_drs.get():
            ctk.CTkLabel(parent, text="ℹ " + self.L("imposed_note"), font=FONT, text_color="#f0b63a", wraplength=620,
                         justify="left").pack(anchor="w", padx=18, pady=(0, 10))
        upd()

    def _open_options(self):
        if not self.game or not self.exe.get():
            return messagebox.showwarning("YogoMFG", self.L("need_game"))
        cur = installer.status(self.exe.get())
        if cur["mult"] in (2, 3, 4, 5, 6):
            self.mult.set(f"{min(cur['mult'], self._mult_max())}X")   # reprend ce qui est déjà installé pour ce jeu
        elif not loganalyze.real_fps(self.exe.get()):
            self.mult.set(f"{self._reco_mult()[0]}X")    # première fois : x6 si le plugin du jeu le permet
        body, bar = self._overlay(self.L("simple_title"))
        block = self._apply_block()
        if block:
            ctk.CTkLabel(body, text="⛔ " + block, font=FONT_B, text_color="#ff6b5a", wraplength=620,
                         justify="left").pack(anchor="w", padx=18, pady=(14, 0))
        self._build_simple(body)
        wrap = ctk.CTkFrame(body, fg_color="transparent"); wrap.pack(fill="x")
        adv = ctk.CTkFrame(wrap, fg_color="transparent")
        st = {"built": False, "open": False}
        tgl = ctk.CTkButton(wrap, text="▸ " + self.L("advanced"), font=FONT, anchor="w", fg_color=SURF,
                            hover_color=GREEN_D)
        def toggle():
            st["open"] = not st["open"]
            if st["open"]:
                if not st["built"]:
                    self._build_opts(adv)
                    st["built"] = True
                adv.pack(fill="x", pady=6)
            else:
                adv.pack_forget()
            tgl.configure(text=("▾ " if st["open"] else "▸ ") + self.L("advanced"))
        tgl.configure(command=toggle)
        tgl.pack(fill="x", padx=18, pady=10)
        ctk.CTkButton(bar, text=self.L("close"), font=FONT_B, width=140, height=46, fg_color=SURF2,
                      hover_color=EDGE, command=self._close_overlay).pack(side="left")
        ctk.CTkButton(bar, text=self.L("apply_upd" if installer.status(self.exe.get())["installed"] else "optimize"),
                      font=FONT_B, width=240, height=48, fg_color=GREEN, hover_color=GREEN_D, text_color=BG,
                      text_color_disabled=DIM, state="disabled" if block else "normal",
                      command=self._apply_from_modal).pack(side="right")

    def _apply_from_modal(self):
        """Ferme l'overlay et lance l'installation (console log/prog sur la page)."""
        self._close_overlay()
        self._applied = False
        self.do_apply()

    def _build_opts(self, parent):
        """Toutes les options (qualité DLSS + cible FPS/écran + pilote) dans un seul panneau."""
        ctk.CTkLabel(parent, text=self.L("q_hint"), font=FONT, text_color="#f0b63a",
                     wraplength=820, justify="left").pack(anchor="w", padx=18, pady=(14, 6))
        reco = inimaker.recommend_quality(self._fps_int())
        for q in inimaker.QUALITY:
            txt = inimaker.QUALITY_FR[q] + (f"    {self.L('q_reco')}" if q == reco else "")
            ctk.CTkRadioButton(parent, text=txt, variable=self.quality, value=q, font=FONT,
                               fg_color=GREEN, text_color=GREEN if q == reco else TXT).pack(anchor="w", padx=24, pady=6)
        ctk.CTkLabel(parent, text=self.L("q_note"), font=FONT, text_color=DIM,
                     wraplength=820, justify="left").pack(anchor="w", padx=18, pady=(4, 10))

        top = ctk.CTkFrame(parent, fg_color="transparent"); top.pack(fill="x", padx=18, pady=(6, 6))
        self._label_tip(top, self.L("scope"), "scope").pack(side="left", padx=(0, 8))
        ctk.CTkSegmentedButton(top, variable=self.scope, values=["global", "game"], font=FONT,
                               selected_color=GREEN_D, selected_hover_color=GREEN).pack(side="left")
        ctk.CTkLabel(top, text="  " + self.L("scope_g") + " / " + self.L("scope_j"),
                     font=FONT, text_color=DIM).pack(side="left")

        grid = ctk.CTkFrame(parent, fg_color="transparent"); grid.pack(fill="x", padx=18, pady=10)
        def cell(col, label, tipkey, widget):
            f = ctk.CTkFrame(grid, fg_color="transparent"); f.grid(row=0, column=col, padx=14, sticky="w")
            self._label_tip(f, label, tipkey).pack(anchor="w")
            widget(f)
        cell(0, self.L("fps"), "fps", lambda f: ctk.CTkComboBox(f, variable=self.fps, values=FPS_CHOICES,
             font=FONT, width=120, fg_color=SURF2, button_color=GREEN_D, command=lambda _: (setattr(self, "_fps_touched", True), self._cap_lbl())).pack())
        cell(1, self.L("mult"), "mult", lambda f: ctk.CTkOptionMenu(f, variable=self.mult, values=list(MULT),
             font=FONT, width=110, fg_color=SURF2, button_color=GREEN_D).pack())
        cell(2, self.L("preset"), "preset", lambda f: ctk.CTkOptionMenu(f, variable=self.preset, values=["Auto", "B", "C"],
             font=FONT, width=110, fg_color=SURF2, button_color=GREEN_D).pack())

        mon = ctk.CTkFrame(parent, fg_color="transparent"); mon.pack(fill="x", padx=18, pady=8)
        if not self.monitors:
            self.monitors = display.monitors()
        names = [f"{m['index']}: {m.get('model', m['name'])} · {m.get('res','')}@{m.get('hz','?')}Hz"
                 + (" ★" if m["primary"] else "") for m in self.monitors] or ["—"]
        if not self.mon_var.get():
            self.mon_var.set(names[0])
        self._label_tip(mon, self.L("monitor"), "monitor").grid(row=0, column=0, sticky="w", padx=6)
        ctk.CTkOptionMenu(mon, variable=self.mon_var, values=names, font=FONT, width=300,
                          fg_color=SURF2, button_color=GREEN_D, command=lambda _: self._refresh_list()).grid(row=1, column=0, padx=6)
        self._label_tip(mon, self.L("refresh"), "refresh").grid(row=0, column=1, sticky="w", padx=6)
        self.hz_menu = ctk.CTkOptionMenu(mon, variable=self.hz_var, values=["—"], font=FONT, width=100,
                                         fg_color=SURF2, button_color=GREEN_D)
        self.hz_menu.grid(row=1, column=1, padx=6)
        ctk.CTkButton(mon, text=self.L("set_hz"), font=FONT, fg_color=SURF2, hover_color=GREEN_D,
                      command=self._set_refresh).grid(row=1, column=2, padx=6)
        self._refresh_list()

        self._label_tip(parent, self.L("sync"), "sync", GREEN).pack(anchor="w", padx=18, pady=(10, 0))
        sf = ctk.CTkFrame(parent, fg_color="transparent"); sf.pack(anchor="w", padx=18)
        for txt, val in ((self.L("gsync"), "gsync"), (self.L("freesync"), "freesync"), (self.L("none"), "none")):
            ctk.CTkRadioButton(sf, text=txt, variable=self.sync_type, value=val, font=FONT, fg_color=GREEN).pack(side="left", padx=12)
        det = (self.L("vrr_yes") % (self.vrr[2] or "?", self.vrr[0], self.vrr[1])) if self.vrr else self.L("vrr_no")
        ctk.CTkLabel(parent, text=det, font=FONT, text_color=GREEN if self.vrr else "#f0b63a", wraplength=620,
                     justify="left").pack(anchor="w", padx=18, pady=(6, 0))
        ctk.CTkLabel(parent, text=self.L("sync_hint"), font=FONT, text_color=DIM,
                     wraplength=820, justify="left").pack(anchor="w", padx=18, pady=8)
        self.cap_label = ctk.CTkLabel(parent, text="", font=FONT_B, text_color=GREEN)
        self.cap_label.pack(anchor="w", padx=18, pady=(0, 12))
        self._cap_lbl()

        fm = ctk.CTkFrame(parent, fg_color=BG, corner_radius=12); fm.pack(fill="x", padx=18, pady=(4, 6))
        self._label_tip(fm, self.L("force_mfg"), "force_mfg", "#f0b63a").pack(anchor="w", padx=12, pady=6)
        ok, fver = self._force_ok
        if ok:
            ctk.CTkCheckBox(fm, text=self.L("force_mfg_on"), variable=self.force_mfg, font=FONT,
                            fg_color="#f0b63a").pack(anchor="w", padx=12, pady=(0, 10))
        else:
            msg = self.L("force_blocked") % fver if fver else self.L("force_blocked_none")
            ctk.CTkLabel(fm, text=msg, font=FONT, text_color=DIM, wraplength=780,
                         justify="left").pack(anchor="w", padx=12, pady=(0, 10))

        ud = ctk.CTkFrame(parent, fg_color=BG, corner_radius=12); ud.pack(fill="x", padx=18, pady=(4, 6))
        self._label_tip(ud, self.L("unlock_drs"), "unlock_drs", GREEN).pack(anchor="w", padx=12, pady=6)
        ctk.CTkCheckBox(ud, text=self.L("unlock_drs_on"), variable=self.unlock_drs, font=FONT,
                        fg_color=GREEN).pack(anchor="w", padx=12, pady=(0, 10))

        nv = ctk.CTkFrame(parent, fg_color=BG, corner_radius=12); nv.pack(fill="x", padx=18, pady=(4, 12))
        self._label_tip(nv, self.L("nvcp"), "nvcp", GREEN).pack(anchor="w", padx=12, pady=6)
        ctk.CTkCheckBox(nv, text=self.L("nvcp_on"), variable=self.do_nvcp, font=FONT,
                        fg_color=GREEN).pack(anchor="w", padx=12, pady=(0, 10))

        rq = ctk.CTkFrame(parent, fg_color=BG, corner_radius=12); rq.pack(fill="x", padx=18, pady=(4, 6))
        ctk.CTkLabel(rq, text=self.L("ref_q"), font=FONT_B, text_color=GREEN).pack(anchor="w", padx=12, pady=6)
        ctk.CTkCheckBox(rq, text=self.L("ref_q_on"), variable=self.ref_quality, font=FONT,
                        fg_color=GREEN).pack(anchor="w", padx=12, pady=(0, 10))

        ms = ctk.CTkFrame(parent, fg_color=BG, corner_radius=12); ms.pack(fill="x", padx=18, pady=(4, 12))
        ctk.CTkLabel(ms, text=self.L("measure"), font=FONT_B, text_color=GREEN).pack(anchor="w", padx=12, pady=6)
        ctk.CTkCheckBox(ms, text=self.L("measure_on"), variable=self.frame_timing, font=FONT,
                        fg_color=GREEN).pack(anchor="w", padx=12, pady=(0, 10))

    def _mon(self):
        try:
            i = int(self.mon_var.get().split(":")[0]) - 1
        except (ValueError, IndexError):
            i = 0
        return self.monitors[i] if 0 <= i < len(self.monitors) else None

    def _refresh_list(self):
        m = self._mon()
        if not m:
            return
        rates = display.refresh_rates(m["device"])
        cur = display.current(m["device"])
        self.refresh = cur[2] if cur else self.refresh
        self.hz_menu.configure(values=[str(r) for r in rates] or ["—"])
        self.hz_var.set(str(cur[2]) if cur else (str(rates[-1]) if rates else "—"))
        self._cap_lbl()

    def _set_refresh(self):
        m = self._mon()
        if not m or not self.hz_var.get().isdigit():
            return
        hz = int(self.hz_var.get())
        if not messagebox.askyesno("YogoMFG", f"Changer le refresh en {hz} Hz ? (réversible)", parent=self):
            return
        ok, msg = display.set_refresh(m["device"], hz)
        messagebox.showinfo("YogoMFG", msg, parent=self)
        if ok:
            self.refresh = hz; self._cap_lbl()

    def _cap_lbl(self):
        lbl = getattr(self, "cap_label", None)
        if lbl is not None and lbl.winfo_exists():   # modale détruite -> label périmé, ne pas toucher
            cap = inimaker.fps_cap(self._target_fps(), self.refresh)
            lbl.configure(text=f"{self.L('cap_is')} : {cap} FPS  (refresh {self.refresh or '?'} Hz)")

    def _fps_int(self):
        d = "".join(c for c in self.fps.get() if c.isdigit())
        return max(20, int(d)) if d else 120

    # ---------- 5 apply ----------
    # ---------- optimisation NVIDIA globale (presets vérifiés) ----------
    def _open_nvidia_tune(self):
        body, bar = self._overlay(self.L("nv_title"))
        st = nvpreset.state(DATA)
        self._nv_goal = ctk.StringVar(value=st.get("preset") or "balanced")
        has_vrr = bool(self.vrr) or (not self.hw and self.sync_type.get() in ("gsync", "freesync"))
        self._nv_vsync = ctk.BooleanVar(value=False if has_vrr else bool(st.get("vsync", False)))
        g = self.hw or {}
        card = " · ".join(x for x in (g.get("name", ""), f"{g['vram_mb'] // 1024} {'Go' if self.lang == 'fr' else 'GB'}" if g.get("vram_mb") else "",
                                      f"{'série' if self.lang == 'fr' else 'series'} {g['series']}" if g.get("series") else "") if x)
        ctk.CTkLabel(body, text=card or "NVIDIA", font=FONT_B, text_color=GREEN).pack(anchor="w", padx=18, pady=(14, 2))
        ctk.CTkLabel(body, text=self.L("nv_state") % (st.get("preset") or self.L("nv_none")), font=FONT,
                     text_color=DIM).pack(anchor="w", padx=18)
        self._label_tip(body, self.L("nv_goal"), "nvcp", GREEN).pack(anchor="w", padx=18, pady=(12, 2))
        info = ctk.CTkLabel(body, text="", font=FONT, text_color=TXT, wraplength=620, justify="left")
        prev = ctk.CTkLabel(body, text="", font=("Consolas", 14), text_color=DIM, wraplength=640, justify="left")

        def refresh(*_):
            if not info.winfo_exists():
                return
            k = self._nv_goal.get()
            info.configure(text=nvpreset.info_text(k, self.lang))
            prev.configure(text="\n".join("  • " + x for x in nvpreset.describe(k, self._nv_vsync.get(), self.lang)))
        for key, lbl in (("perf", "nv_perf"), ("balanced", "nv_bal"), ("quality", "nv_qual")):
            ctk.CTkRadioButton(body, text=self.L(lbl) + (f"    {self.L('q_reco')}" if key == "balanced" else ""),
                               variable=self._nv_goal, value=key, font=FONT, fg_color=GREEN,
                               command=refresh).pack(anchor="w", padx=26, pady=5)
        info.pack(anchor="w", padx=18, pady=(8, 6))
        if has_vrr:
            ctk.CTkLabel(body, text="✓ " + self.L("nv_vrr_note"), font=FONT, text_color=GREEN, wraplength=640,
                         justify="left").pack(anchor="w", padx=18, pady=6)
        else:
            ctk.CTkCheckBox(body, text=self.L("nv_vsync_novrr"), variable=self._nv_vsync, font=FONT,
                            fg_color=GREEN, command=refresh).pack(anchor="w", padx=18, pady=6)
        ctk.CTkLabel(body, text=self.L("nv_will"), font=FONT_B, text_color=DIM).pack(anchor="w", padx=18, pady=(10, 0))
        prev.pack(anchor="w", padx=18)
        ctk.CTkLabel(body, text=self.L("nv_note"), font=FONT, text_color="#f0b63a", wraplength=640,
                     justify="left").pack(anchor="w", padx=18, pady=10)
        self._nv_msg = ctk.CTkLabel(body, text="", font=FONT_B, text_color=GREEN, wraplength=640, justify="left")
        self._nv_msg.pack(anchor="w", padx=18, pady=(0, 12))
        refresh()
        ctk.CTkButton(bar, text=self.L("close"), font=FONT_B, width=140, height=46, fg_color=SURF2,
                      hover_color=EDGE, command=self._close_overlay).pack(side="left")
        ctk.CTkButton(bar, text=self.L("nv_apply"), font=FONT_B, width=220, height=48, fg_color=GREEN,
                      hover_color=GREEN_D, text_color=BG, command=self._nv_apply).pack(side="right")
        ctk.CTkButton(bar, text=self.L("nv_revert"), font=FONT_B, width=220, height=48, fg_color=SURF2,
                      hover_color="#7a3030", command=self._nv_revert).pack(side="right", padx=8)

    def _nv_say(self, text, color=GREEN):
        lbl = getattr(self, "_nv_msg", None)
        if lbl is not None and lbl.winfo_exists():
            self._fade_text(lbl, text, color)
        else:
            self._log(text)

    def _nv_run(self, fn):
        if self._nv_busy:
            return
        self._nv_busy = True
        self._nv_say(self.L("nv_run"), DIM)
        def done(r, e):
            self._nv_busy = False
            ok, msg = r if r else (False, str(e))
            if (not ok) and msg.startswith("NEED_ADMIN"):
                self._nv_say("✗ " + msg, "#f0b63a")
                self._ask_admin()
            else:
                self._nv_say(("✓ " if ok else "✗ ") + msg, GREEN if ok else "#f0b63a")
        self._async(fn, done)

    def _nv_apply(self):
        preset, npi = self._nv_goal.get(), self.npi.get()
        vs = self._nv_vsync.get() and not self.vrr       # jamais de V-Sync forcé sur un écran G-Sync / FreeSync
        self._nv_run(lambda: nvpreset.apply(npi, DATA, preset, vs))

    def _nv_revert(self):
        npi = self.npi.get()
        self._nv_run(lambda: nvpreset.revert(npi, DATA))

    def _open_soft_opts(self):
        """Options logiciel (globales) : proxy par défaut, chemin NPI, revert NVCP, admin."""
        pad, bar = self._overlay(self.L("soft_opts"))
        ctk.CTkButton(bar, text=self.L("close"), font=FONT_B, width=140, height=46, fg_color=SURF2,
                      hover_color=EDGE, command=self._close_overlay).pack(side="left")
        ctk.CTkLabel(pad, text=self.L("proxy"), font=FONT_B, text_color=DIM).pack(anchor="w", padx=14, pady=(12, 0))
        ctk.CTkOptionMenu(pad, variable=self.proxy, values=list(installer.PROXIES), font=FONT,
                          width=200, fg_color=SURF, button_color=GREEN_D).pack(anchor="w", padx=14)
        self._label_tip(pad, self.L("nvcp"), "nvcp", GREEN).pack(anchor="w", padx=14, pady=(14, 0))
        row = ctk.CTkFrame(pad, fg_color="transparent"); row.pack(fill="x", padx=14, pady=6)
        ctk.CTkEntry(row, textvariable=self.npi, font=FONT).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(row, text="…", width=46, font=FONT_B, fg_color=GREEN_D, text_color=BG, command=self._pick_npi).pack(side="left", padx=6)
        btns = ctk.CTkFrame(pad, fg_color="transparent"); btns.pack(anchor="w", padx=14, pady=10)
        ctk.CTkButton(btns, text=self.L("revert"), font=FONT, width=160, fg_color=SURF,
                      hover_color=GREEN_D, command=self._revert_nvcp).pack(side="left")
        ctk.CTkButton(pad, text="ℹ " + self.L("about_btn"), font=FONT, anchor="w", height=40, fg_color=SURF,
                      hover_color=GREEN_D, command=self._show_about).pack(fill="x", padx=14, pady=(14, 4))
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
        npi = self.npi.get()
        def work():
            _, a = nvcp.revert(npi, DATA)
            _, b = nvcp.restore_mfg(npi, DATA)
            return a + chr(10) + b
        self._async(work, lambda r, e: messagebox.showinfo(
            "YogoMFG", r if e is None else f"Annulation échouée : {e}", parent=self))

    def _cfg_now(self):
        c = inimaker.default_cfg(self._target_fps())
        c["multiplier"] = MULT[self.mult.get()]
        c["preset"] = self.preset.get()
        c["dlss_quality"] = self.quality.get()
        c["sync_type"] = self.sync_type.get()
        c["frame_timing"] = self.frame_timing.get()
        c["max_ceiling"] = self.unlock_drs.get()
        c["optimized"] = 1 if self.ref_quality.get() else 2
        # le multiplicateur imposé par le pilote rend le patch du plugin inutile (et plus risqué) : exclusifs
        c["force_mfg"] = self.force_mfg.get() and self._force_ok[0] and not self.unlock_drs.get()
        return c

    def _post(self, frac, line=None):
        def u():
            if frac is not None:
                self.prog.set(frac)
            if line:
                self._log(line)
        self.after(0, u)

    def do_apply(self):
        if self._busy or not (self.game and self.exe.get()):
            return
        block = self._apply_block()
        if block:                                        # revérifie au dernier moment (le jeu a pu être lancé entre-temps)
            self._log("⛔ " + block)
            return
        if self._anticheat and not messagebox.askyesno(
                "YogoMFG", self.L("anticheat_ask") % ", ".join(self._anticheat),
                icon="warning", default="no", parent=self):
            return
        self._busy = True
        self.log.delete("1.0", "end"); self.prog.set(0)
        c = self._cfg_now()
        appid = self.game["appid"]
        if self.scope.get() == "game":
            self.cfg["per_game"][appid] = c
        else:
            self.cfg["global"] = c
        self.cfg.setdefault("applied", {})[appid] = self.proxy.get()
        self.cfg.setdefault("mult_by_game", {})[appid] = c["multiplier"]   # proxy appliqué par jeu -> Retirer restaure la bonne DLL
        self.cfg["npi_exe"] = self._npi_to_save(); self.cfg["proxy"] = self.proxy.get()
        config.save(self.cfg)
        # snapshots (pas de StringVar.get() dans le thread) ; NVCP écrit profil global ET jeu.
        exe_full = self.exe.get()
        exe = os.path.basename(exe_full)
        proxy = self.proxy.get()
        npi = self.npi.get()
        cap = inimaker.fps_cap(self._target_fps(), self.refresh)
        vrr = self.sync_type.get() in ("gsync", "freesync")
        want_nvcp = self.do_nvcp.get()
        want_unlock = self.unlock_drs.get()
        qual, fps_i, vram, series = self.quality.get(), self._target_fps(), self.hw.get("vram_mb", 0), self.hw.get("series", "30")
        over_cap = c["multiplier"] > self._mfg_cap and not self._force_ok[0]

        def worker():
            results = []
            need_admin = False
            try:
                self._post(0.1, "⏳ Installation du mod Frame Generation…")
                try:
                    acts = installer.install(MOD_ROOT, exe_full, inimaker.make(c), proxy)
                    self._post(0.45, f"✓ Mod installé ({len(acts)} éléments)")
                    results.append(("Mod x" + str(c["multiplier"]) + " + INI", True))
                except Exception as e:
                    self._post(0.45, "✗ Install mod : " + str(e))
                    results.append(("Mod", False))
                    return
                if want_nvcp:
                    self._post(0.6, "⏳ Réglages pilote NVIDIA (cap FPS + VRR/G-Sync)…")
                    ok, msg = nvcp.apply(npi, DATA, cap, vrr, exe)
                    if (not ok) and msg.startswith("NEED_ADMIN"):
                        need_admin = True
                        self._post(0.85, "✗ NVIDIA : droits admin requis.")
                        results.append(("Réglages NVIDIA", False))
                    else:
                        self._post(0.85, ("✓ " if ok else "✗ ") + "NVIDIA : " + msg)
                        results.append(("Réglages NVIDIA (cap " + str(cap) + ")", ok))
                if want_unlock and not need_admin:
                    if over_cap:
                        self._post(None, f"⚠ Plugin DLSS-G du jeu limité à {self._mfg_cap}X : x{c['multiplier']} peut couper la "
                                         "Frame Generation (x1) ou saccader. Si c'est le cas, repasse en x4.")
                    self._post(0.9, f"⏳ Multiplicateur x{c['multiplier']} imposé via le pilote…")
                    ok, msg = nvcp.unlock_mfg(npi, DATA, c["multiplier"] - 1, exe)
                    need_admin = msg.startswith("NEED_ADMIN")
                    self._post(0.92, ("✓ " if ok else "✗ ") + msg)
                    results.append((f"Multiplicateur pilote x{c['multiplier']}", ok))
                elif not want_unlock and not need_admin:     # décoché : le jeu redécide -> on retire notre override
                    ok, msg = nvcp.restore_mfg(npi, DATA, exe)
                    need_admin = msg.startswith("NEED_ADMIN")
                    if ok or need_admin:
                        self._post(0.92, ("✓ " if ok else "✗ ") + msg)
                self._post(0.95, "⏳ Conseils in-game…")
                self._post(None, chr(10) + self.L("advice") + " :")
                for a in optadvice.advise(fps_i, vram, series, qual):
                    self._post(None, "  • " + a)
            except Exception as e:      # jamais de worker silencieux : sinon _busy reste True et Apply est mort
                self._post(None, "✗ Erreur inattendue : " + str(e))
                results.append(("Erreur", False))
            finally:
                self._post_done(results)
                if need_admin:
                    self.after(0, self._ask_admin)

        threading.Thread(target=worker, daemon=True).start()

    def _ask_admin(self):
        if messagebox.askyesno("YogoMFG", "Le réglage NVIDIA exige l'admin. Relancer en admin ?"):
            self._relaunch_admin()

    def _post_done(self, results):
        def u():
            self._busy = False
            self.prog.set(1.0)
            self._log("\n── Récapitulatif ──")
            for name, ok in results:
                self._log(("  ✓ " if ok else "  ✗ ") + name + ("  validé" if ok else "  NON validé"))
            self._log("\nLance le jeu (bouton Launch), active Frame Generation " + self.mult.get() +
                      ". Puis « " + self.L("analyser") + " » pour lire les logs.")
            self._applied = True
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
            "Plugin DLSS-G du jeu": f"plafond x{self._mfg_cap} ; patchable: {self._force_ok}",
            "Multiplicateur choisi": self.mult.get(), "Multiplicateur imposé": self.unlock_drs.get(),
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
        exe, fps, goal = self.exe.get(), self._fps_int(), self.goal.get()   # snapshot (pas de .get() en thread)
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
        messagebox.showinfo("YogoMFG", "Reco appliquée (DLSS " +
                            inimaker.QUALITY_FR.get(self.quality.get(), "") +
                            "). Retourne à Appliquer pour réécrire l'INI.")
        self._applied = False

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
