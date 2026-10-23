"""YogoMFG - applique DLSS Frame Generation x4 (mod SM86) aux jeux Steam.
Séries RTX 20/30. UI CustomTkinter, thème Yogo (noir/gris, vert flashy). Mod: sdli1995 (MIT).
"""
import os, sys, threading, webbrowser, ctypes
import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from core import (hardware, steam, fgdetect, inimaker, installer,
                  nvcp, config, upscalers, optadvice, loganalyze, display)

FROZEN = getattr(sys, "frozen", False)
RES = getattr(sys, "_MEIPASS", HERE)
DATA = os.path.dirname(sys.executable) if FROZEN else HERE
MOD_ROOT = os.path.join(RES, "mod")
NPI_BUNDLED = os.path.join(RES, "tools", "npi", "nvidiaProfileInspector.exe")

FPS_CHOICES = ["30", "60", "90", "120", "144", "165", "180", "240"]
MULT = {"2X": 2, "3X": 3, "4X": 4}   # x4 = max proposé par le mod

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
  "sub": "Multi-Frame Generation x4 · RTX 20/30",
  "start": "Commencer", "back": "‹ Retour", "next": "Suivant ›", "apply": "Appliquer",
  "loading": "Chargement…", "none": "Aucune",
  "welcome_h": "Débloque la Frame Generation sur RTX 20/30",
  "welcome_p": "Choisis un jeu, applique le x4, joue — puis laisse l'analyse te guider.",
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
  "sub": "Multi-Frame Generation x4 · RTX 20/30",
  "start": "Start", "back": "‹ Back", "next": "Next ›", "apply": "Apply",
  "loading": "Loading…", "none": "None",
  "welcome_h": "Unlock Frame Generation on RTX 20/30",
  "welcome_p": "Pick a game, apply x4, play — then let the analysis guide you.",
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
STEPS = ["welcome", "pc", "pick", "tune", "quality", "apply", "analyze"]

TIPS = {
 "fr": {
  "fps": "Le nombre d'images par seconde que tu veux atteindre. Plus haut = plus fluide mais "
         "demande un upscaling plus agressif et un bon frame-rate de base.",
  "mult": "Nombre d'images générées par le Frame Generation. 4X = 1 vraie + 3 générées. Plus haut "
          "= plus de FPS affichés, mais artefacts si le frame-rate de base est trop bas.",
  "preset": "Auto = meilleure qualité d'image du HUD. C (FG Lite) = plus rapide mais HUD/bords un "
            "peu dégradés.",
  "sync": "G-Sync/FreeSync synchronise l'écran au GPU (zéro tearing sans latence). YogoMFG active "
          "le VRR plein écran ET fenêtré + cap FPS. Sans VRR : active la V-Sync à la main.",
  "monitor": "L'écran sur lequel tu joues. Son taux de rafraîchissement sert à calculer le cap FPS.",
  "refresh": "Change la fréquence de l'écran (Hz). Plus haut = plus fluide si l'écran le supporte.",
  "quality": "Mode d'upscaling DLSS dans le jeu. Qualité = plus net, Performance = plus de FPS. "
             "YogoMFG le recommande, tu l'appliques dans les options du jeu.",
  "nvcp": "Applique via Profile Inspector : cap Max Frame Rate + VRR/G-Sync (plein écran & fenêtré). "
          "Un backup des profils est fait avant.",
  "scope": "Globale = s'applique à tous les jeux. Ce jeu = réglages propres à ce jeu seulement.",
 },
 "en": {
  "fps": "Frames per second you want to reach. Higher = smoother but needs more aggressive "
         "upscaling and a good base frame-rate.",
  "mult": "Frames generated by Frame Generation. 4X = 1 real + 3 generated. Higher = more displayed "
          "FPS but artifacts if base frame-rate is too low.",
  "preset": "Auto = best HUD image quality. C (FG Lite) = faster but slightly degraded HUD/edges.",
  "sync": "G-Sync/FreeSync syncs the display to the GPU (no tearing, no latency). YogoMFG enables "
          "VRR fullscreen AND windowed + FPS cap. Without VRR: enable V-Sync manually.",
  "monitor": "The screen you play on. Its refresh rate is used to compute the FPS cap.",
  "refresh": "Change the display refresh (Hz). Higher = smoother if the screen supports it.",
  "quality": "In-game DLSS upscaling mode. Quality = sharper, Performance = more FPS. YogoMFG "
             "recommends it, you set it in the game options.",
  "nvcp": "Applies via Profile Inspector: Max Frame Rate cap + VRR/G-Sync (fullscreen & windowed). "
          "Profiles are backed up first.",
  "scope": "Global = applies to all games. This game = settings for this game only.",
 },
}


class Tooltip:
    """Infobulle au survol. Show retardé, hide garanti (Leave + clic + sécurité)."""
    def __init__(self, widget, text):
        self.w, self.text, self.tip, self._after = widget, text, None, None
        widget.bind("<Enter>", self._enter, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<Button-1>", self._hide, add="+")

    def _enter(self, _):
        self._cancel()
        self._after = self.w.after(350, self._show)

    def _cancel(self):
        if self._after:
            try: self.w.after_cancel(self._after)
            except Exception: pass
            self._after = None

    def _show(self):
        if self.tip or not self.text:
            return
        x = self.w.winfo_rootx() + 18
        y = self.w.winfo_rooty() + self.w.winfo_height() + 4
        self.tip = tw = ctk.CTkToplevel(self.w)
        tw.overrideredirect(True)
        tw.geometry(f"+{x}+{y}")
        try:
            tw.attributes("-topmost", True)
        except Exception:
            pass
        # le toplevel ne doit pas capturer le survol : le relais vers hide reste sur le widget
        ctk.CTkLabel(tw, text=self.text, font=("Segoe UI", 13), text_color=TXT, fg_color=EDGE,
                     corner_radius=8, wraplength=340, justify="left").pack(ipadx=8, ipady=6)
        self.w.after(6000, self._hide)   # sécurité : auto-disparition

    def _hide(self, _=None):
        self._cancel()
        if self.tip:
            try: self.tip.destroy()
            except Exception: pass
            self.tip = None


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.title("YogoMFG")
        self.geometry("1040x780")
        self.minsize(900, 680)
        self.configure(fg_color=BG)
        try:
            self.attributes("-alpha", 0.97)          # léger effet verre
        except Exception:
            pass
        try:
            self.iconbitmap(os.path.join(RES, "assets", "yogo.ico"))
        except Exception:
            pass

        self.cfg = config.load()
        self.lang = "fr"
        self.hw, self.games, self.game = {}, [], None
        self.monitors, self.refresh = [], 0
        self.step, self._applied = 0, False
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
        self.mon_var = ctk.StringVar()
        self.hz_var = ctk.StringVar()
        self.goal = ctk.StringVar(value="fps")
        npi = self.cfg.get("npi_exe", "") or (NPI_BUNDLED if os.path.isfile(NPI_BUNDLED) else "")
        self.npi = ctk.StringVar(value=npi)

        self._banner()
        ctk.CTkFrame(self, fg_color=GREEN, height=2, corner_radius=0).pack(fill="x", padx=20)  # liseré sharp
        self.body = ctk.CTkFrame(self, fg_color=SURF, border_color="#3c5a26", border_width=2, corner_radius=16)
        self.body.pack(fill="both", expand=True, padx=20, pady=10)
        nav = ctk.CTkFrame(self, fg_color="transparent"); nav.pack(fill="x", padx=20, pady=(0, 16))
        self.b_back = ctk.CTkButton(nav, text="", width=140, height=46, font=FONT_B,
                                    fg_color=SURF2, hover_color=EDGE, command=self.back)
        self.b_back.pack(side="left")
        self.dots = ctk.CTkLabel(nav, text="", font=FONT, text_color=DIM); self.dots.pack(side="left", expand=True)
        self.b_next = ctk.CTkButton(nav, text="", width=210, height=48, font=FONT_B,
                                    fg_color=GREEN, hover_color=GREEN_D, text_color=BG, command=self.next)
        self.b_next.pack(side="right")
        self.render()

    def L(self, k): return TR[self.lang].get(k, k)

    def _info(self, parent, key):
        lbl = ctk.CTkLabel(parent, text=" ⓘ", font=FONT_B, text_color=GREEN, cursor="hand2")
        Tooltip(lbl, TIPS[self.lang].get(key, ""))
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
        ctk.CTkLabel(top, text=self.L("sub"), font=FONT, text_color=DIM).pack(side="left", padx=16)
        self.lang_btn = ctk.CTkButton(top, text="EN", width=54, height=36, font=FONT_B,
                                      fg_color=SURF2, hover_color=GREEN_D, command=self._lang)
        self.lang_btn.pack(side="right")

    def _lang(self):
        self.lang = "en" if self.lang == "fr" else "fr"
        self.lang_btn.configure(text="FR" if self.lang == "en" else "EN")
        self.render()

    # ---------- threading ----------
    def _async(self, fn, cb):
        def run():
            try:
                r, e = fn(), None
            except Exception as ex:
                r, e = None, ex
            self.after(0, lambda: cb(r, e))
        threading.Thread(target=run, daemon=True).start()

    # ---------- nav ----------
    def render(self):
        for w in self.body.winfo_children():
            w.destroy()
        s = STEPS[self.step]
        getattr(self, "_" + s)()
        self.b_back.configure(state="disabled" if self.step == 0 else "normal", text=self.L("back"))
        self.dots.configure(text="● " * self.step + "○ " * (len(STEPS) - self.step))
        if s == "apply":
            self.b_next.configure(text=self.L("valider") if self._applied else self.L("apply"))
        elif s == "analyze":
            self.b_next.configure(text=self.L("an_run"))
        elif s == "welcome":
            self.b_next.configure(text=self.L("start"))
        else:
            self.b_next.configure(text=self.L("next"))

    def back(self):
        if self.step:
            self.step -= 1; self.render()

    def next(self):
        s = STEPS[self.step]
        if s == "pick" and not self.game:
            return messagebox.showwarning("YogoMFG", "Choisis un jeu / pick a game.")
        if s == "pick" and not self.exe.get():
            return messagebox.showwarning("YogoMFG", "Choisis le .exe / pick the .exe.")
        if s == "apply" and not self._applied:
            return self.do_apply()
        if s == "analyze":
            return self.do_analyze()
        self.step += 1; self.render()

    def _head(self, key):
        ctk.CTkLabel(self.body, text=f"{self.step}. {self.L(key)}", font=FONT_H,
                     text_color=GREEN, anchor="w").pack(anchor="w", padx=28, pady=(22, 14), fill="x")

    def _card(self, scroll=False):
        c = (ctk.CTkScrollableFrame(self.body, fg_color=SURF2, corner_radius=14) if scroll
             else ctk.CTkFrame(self.body, fg_color=SURF2, corner_radius=14))
        c.pack(fill="both", expand=True, padx=28, pady=(0, 20))
        return c

    # ---------- 0 welcome ----------
    def _welcome(self):
        f = ctk.CTkFrame(self.body, fg_color="transparent"); f.pack(expand=True, fill="both")
        inner = ctk.CTkFrame(f, fg_color="transparent"); inner.place(relx=0.5, rely=0.5, anchor="center")
        try:
            img = ctk.CTkImage(Image.open(os.path.join(RES, "assets", "yogo_logo.png")), size=(190, 190))
            ctk.CTkLabel(inner, image=img, text="").pack(pady=10)
        except Exception:
            pass
        ctk.CTkLabel(inner, text="YogoMFG", font=FONT_T, text_color=GREEN).pack()
        ctk.CTkLabel(inner, text=self.L("welcome_h"), font=FONT_H, text_color=TXT).pack(pady=(6, 2))
        ctk.CTkLabel(inner, text=self.L("welcome_p"), font=FONT, text_color=DIM).pack(pady=4)
        ctk.CTkButton(inner, text=self.L("start"), font=FONT_B, fg_color=GREEN, hover_color=GREEN_D,
                      text_color=BG, width=260, height=52, command=self.next).pack(pady=18)

    # ---------- 1 pc ----------
    def _pc(self):
        self._head("s_machine")
        card = self._card()
        if self.hw:
            return self._pc_show(card)
        ctk.CTkLabel(card, text=self.L("loading"), font=FONT, text_color=DIM).pack(pady=30)
        def work():
            self.hw = hardware.summary()
            self.monitors = display.monitors()
            self.refresh = hardware.refresh_hz()
            return True
        self._async(work, lambda r, e: self.step == 1 and self.render())

    def _pc_show(self, card):
        h = self.hw
        rows = [("GPU", f"{h.get('name','?')}  ·  série {h.get('series','?')} ({h.get('sm','?')})"),
                ("VRAM", f"{h.get('vram_mb',0)} Mo"), ("Driver", h.get("driver", "?")),
                ("CPU", h.get("cpu", "?")), ("RAM", f"{h.get('ram_gb',0)} Go"),
                ("Moniteur", f"{self.refresh or '?'} Hz  ·  {len(self.monitors)} écran(s)"),
                ("Util GPU", f"{h.get('util_pct','?')} %"), ("Clock", f"{h.get('clock_mhz','?')} MHz")]
        grid = ctk.CTkFrame(card, fg_color="transparent"); grid.pack(expand=True, padx=30, pady=20)
        for i, (k, v) in enumerate(rows):
            ctk.CTkLabel(grid, text=k, font=FONT_B, text_color=GREEN, anchor="e", width=130).grid(row=i, column=0, sticky="e", padx=10, pady=5)
            ctk.CTkLabel(grid, text=v, font=FONT, text_color=TXT, anchor="w").grid(row=i, column=1, sticky="w", padx=10, pady=5)
        if h.get("warn"):
            ctk.CTkLabel(card, text="⚠ " + h["warn"], font=FONT, text_color="#f0b63a",
                         wraplength=820).pack(pady=(0, 16))

    # ---------- 2 pick ----------
    def _pick(self):
        self._head("s_game")
        card = self._card()
        left = ctk.CTkScrollableFrame(card, fg_color=BG, width=300, corner_radius=12,
                                      label_text="Steam", label_font=FONT_B, label_fg_color=SURF2)
        left.pack(side="left", fill="y", padx=14, pady=14)
        self.right = ctk.CTkFrame(card, fg_color="transparent"); self.right.pack(side="left", fill="both", expand=True, padx=(0, 16), pady=14)
        self._pick_right()
        if self.games:
            self._fill_games(left)
        else:
            ctk.CTkLabel(left, text=self.L("loading"), font=FONT, text_color=DIM).pack(pady=12)
            self._async(steam.games, lambda r, e: (setattr(self, "games", r or []),
                        self.step == 2 and self.render()))

    def _fill_games(self, parent):
        for g in self.games:
            ctk.CTkButton(parent, text=g["name"], font=FONT, anchor="w", height=38,
                          fg_color="transparent", hover_color=GREEN_D, text_color=TXT,
                          command=lambda x=g: self._set_game(x)).pack(fill="x", pady=1)

    def _pick_right(self):
        r = self.right
        head = ctk.CTkFrame(r, fg_color="transparent"); head.pack(fill="x")
        self.cover = ctk.CTkLabel(head, text="", width=150, height=210, fg_color=BG, corner_radius=10)
        self.cover.pack(side="right", padx=(10, 0))
        meta = ctk.CTkFrame(head, fg_color="transparent"); meta.pack(side="left", fill="x", expand=True)
        self.game_name = ctk.CTkLabel(meta, text="—", font=FONT_H, text_color=GREEN, anchor="w",
                                      wraplength=380, justify="left"); self.game_name.pack(anchor="w")
        self.lbl_fg = ctk.CTkLabel(meta, text="", font=FONT, wraplength=380, justify="left", anchor="w"); self.lbl_fg.pack(anchor="w", pady=6)
        self.lbl_logs = ctk.CTkLabel(meta, text="", font=FONT, wraplength=380, justify="left", anchor="w", text_color=DIM); self.lbl_logs.pack(anchor="w")
        ctk.CTkButton(meta, text=self.L("manual"), font=FONT, fg_color=SURF2, hover_color=GREEN_D,
                      command=self._manual).pack(anchor="w")
        ctk.CTkLabel(r, text=self.L("exe"), font=FONT_B, text_color=DIM).pack(anchor="w", pady=(12, 0))
        self.cmb = ctk.CTkOptionMenu(r, variable=self.exe, values=[""], font=FONT,
                                     fg_color=SURF2, button_color=GREEN_D, dropdown_font=FONT)
        self.cmb.pack(anchor="w", fill="x")
        ctk.CTkLabel(r, text=self.L("proxy"), font=FONT_B, text_color=DIM).pack(anchor="w", pady=(8, 0))
        ctk.CTkOptionMenu(r, variable=self.proxy, values=list(installer.PROXIES), font=FONT,
                          width=200, fg_color=SURF2, button_color=GREEN_D).pack(anchor="w")
        self.up_box = ctk.CTkScrollableFrame(r, fg_color=BG, corner_radius=12,
                                             label_text=self.L("updaters"), label_font=FONT_B, label_fg_color=SURF2)
        self.up_box.pack(fill="both", expand=True, pady=12)

    def _set_game(self, g):
        self.game = g
        self.game_name.configure(text=g["name"])
        self._load_cover(g["appid"])
        sup = fgdetect.supports(g["dir"])
        self.lbl_fg.configure(text=self.L("fg_yes") if sup == "yes" else self.L("fg_no"),
                              text_color=GREEN if sup == "yes" else "#f0b63a")
        if sup != "yes" and messagebox.askyesno("YogoMFG", "FG inconnu. Recherche web ? / Unknown. Web search?"):
            webbrowser.open(fgdetect.web_query(g["name"]))
        self.cmb.configure(values=g["exes"] or [""])
        self.exe.set(g["exes"][0] if g["exes"] else "")
        # logs déjà présents dans le dossier du jeu -> aperçu direct de l'analyse
        self.lbl_logs.configure(text="")
        exe0 = self.exe.get()
        if exe0:
            self._async(lambda: loganalyze.read(exe0),
                        lambda r, e: self.game is g and r and r.get("found") and
                        self.lbl_logs.configure(text="📊 Logs trouvés — va à l'étape Analyse pour la proposition."))
        for w in self.up_box.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.up_box, text=self.L("scan_ups"), font=FONT, text_color=DIM).pack(anchor="w")
        def work():
            ups = upscalers.scan(g["dir"])
            if not getattr(self, "_manifest", None):
                self._manifest = upscalers.latest()   # CDN DLSS Swapper, mis en cache
            return ups, self._manifest
        self._async(work, lambda r, e: self.game is g and self._fill_upscalers(*(r or ([], {}))))

    def _fill_upscalers(self, ups, manifest=None):
        manifest = manifest or {}
        for w in self.up_box.winfo_children():
            w.destroy()
        hdr = ctk.CTkFrame(self.up_box, fg_color="transparent"); hdr.pack(fill="x")
        lib = self.cfg.get("dll_lib", "")
        ctk.CTkButton(hdr, text="Bibliothèque DLL : " + (os.path.basename(lib) if lib else "choisir…"),
                      font=FONT, fg_color=SURF2, hover_color=GREEN_D, command=self._pick_lib).pack(side="left")
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
                          text_color=BG, state=state, command=lambda u=u: self._install_dll(u)).pack(side="left")

    def _pick_lib(self):
        d = filedialog.askdirectory(title="Dossier bibliothèque de DLL (DLSS/FSR/XeSS récents)")
        if d:
            self.cfg["dll_lib"] = d; config.save(self.cfg)
            if self.game:
                self._set_game(self.game)

    def _restore_dll(self, u):
        try:
            messagebox.showinfo("YogoMFG", upscalers.restore(u["path"]))
            self._set_game(self.game)
        except Exception as e:
            messagebox.showerror("YogoMFG", str(e))

    def _install_dll(self, u):
        # Priorité : bibliothèque locale (fiable, hors ligne) -> manifeste -> fichier manuel.
        lib = self.cfg.get("dll_lib", "") or os.path.join(RES, "tools", "dlls")
        m = upscalers.library_match(u["name"], lib)
        if m:
            try:
                messagebox.showinfo("YogoMFG", upscalers.swap(u["path"], m[0]) + f" (v{m[1]})")
                return self._set_game(self.game)
            except Exception as e:
                return messagebox.showerror("YogoMFG", str(e))

        def work():
            return upscalers.install_latest(u["path"])
        def done(res, e):
            ok, msg = (res if res else (False, str(e)))
            if ok:
                messagebox.showinfo("YogoMFG", msg)
                return self._set_game(self.game)
            if messagebox.askyesno("YogoMFG", msg + "\n\nChoisir un .dll téléchargé manuellement ?"):
                p = filedialog.askopenfilename(title=u["name"], filetypes=[(u["name"], u["name"]), ("dll", "*.dll")])
                if p:
                    try:
                        messagebox.showinfo("YogoMFG", upscalers.swap(u["path"], p))
                        self._set_game(self.game)
                    except Exception as ex:
                        messagebox.showerror("YogoMFG", str(ex))
        self._async(work, done)

    def _load_cover(self, appid):
        self.cover.configure(image=None, text=self.L("loading"))
        if not str(appid).isdigit():
            return self.cover.configure(text="")
        dest = os.path.join(DATA, "_covers", f"{appid}.jpg")
        def done(p, e):
            if not p:
                return self.cover.configure(text="")
            try:
                self.cover.configure(image=ctk.CTkImage(Image.open(p), size=(150, 210)), text="")
            except Exception:
                self.cover.configure(text="")
        self._async(lambda: steam.fetch_cover(appid, dest), done)

    def _manual(self):
        d = filedialog.askdirectory(title="Dossier du jeu / game folder")
        if d:
            self._set_game({"appid": "manual:" + d, "name": os.path.basename(d),
                            "dir": d, "exes": steam._render_exes(d)})

    # ---------- 3 quality ----------
    def _quality(self):
        self._head("s_quality")
        card = self._card()
        ctk.CTkLabel(card, text=self.L("q_hint"), font=FONT, text_color="#f0b63a",
                     wraplength=840, justify="left").pack(anchor="w", padx=24, pady=(18, 6))
        reco = inimaker.recommend_quality(self._fps_int())
        for q in inimaker.QUALITY:
            txt = inimaker.QUALITY_FR[q] + (f"    {self.L('q_reco')}" if q == reco else "")
            ctk.CTkRadioButton(card, text=txt, variable=self.quality, value=q, font=FONT,
                               fg_color=GREEN, text_color=GREEN if q == reco else TXT).pack(anchor="w", padx=30, pady=8)
        ctk.CTkLabel(card, text=self.L("q_note"), font=FONT, text_color=DIM,
                     wraplength=840, justify="left").pack(anchor="w", padx=24, pady=10)

    # ---------- 4 tune ----------
    def _tune(self):
        self._head("s_tune")
        card = self._card(scroll=True)
        top = ctk.CTkFrame(card, fg_color="transparent"); top.pack(fill="x", padx=24, pady=(18, 6))
        self._label_tip(top, self.L("scope"), "scope").pack(side="left", padx=(0, 8))
        ctk.CTkSegmentedButton(top, variable=self.scope, values=["global", "game"], font=FONT,
                               selected_color=GREEN_D, selected_hover_color=GREEN).pack(side="left")
        ctk.CTkLabel(top, text="  " + self.L("scope_g") + " / " + self.L("scope_j"),
                     font=FONT, text_color=DIM).pack(side="left")

        grid = ctk.CTkFrame(card, fg_color="transparent"); grid.pack(fill="x", padx=24, pady=10)
        def cell(col, label, tipkey, widget):
            f = ctk.CTkFrame(grid, fg_color="transparent"); f.grid(row=0, column=col, padx=14, sticky="w")
            self._label_tip(f, label, tipkey).pack(anchor="w")
            widget(f)
        cell(0, self.L("fps"), "fps", lambda f: ctk.CTkComboBox(f, variable=self.fps, values=FPS_CHOICES,
             font=FONT, width=120, fg_color=SURF2, button_color=GREEN_D, command=lambda _: self._cap_lbl()).pack())
        cell(1, self.L("mult"), "mult", lambda f: ctk.CTkOptionMenu(f, variable=self.mult, values=list(MULT),
             font=FONT, width=110, fg_color=SURF2, button_color=GREEN_D).pack())
        cell(2, self.L("preset"), "preset", lambda f: ctk.CTkOptionMenu(f, variable=self.preset, values=["Auto", "C"],
             font=FONT, width=110, fg_color=SURF2, button_color=GREEN_D).pack())

        # moniteur + refresh
        mon = ctk.CTkFrame(card, fg_color="transparent"); mon.pack(fill="x", padx=24, pady=8)
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

        self._label_tip(card, self.L("sync"), "sync", GREEN).pack(anchor="w", padx=24, pady=(10, 0))
        sf = ctk.CTkFrame(card, fg_color="transparent"); sf.pack(anchor="w", padx=24)
        for txt, val in ((self.L("gsync"), "gsync"), (self.L("freesync"), "freesync"), (self.L("none"), "none")):
            ctk.CTkRadioButton(sf, text=txt, variable=self.sync_type, value=val, font=FONT, fg_color=GREEN).pack(side="left", padx=12)
        ctk.CTkLabel(card, text=self.L("sync_hint"), font=FONT, text_color=DIM,
                     wraplength=840, justify="left").pack(anchor="w", padx=24, pady=8)
        self.cap_label = ctk.CTkLabel(card, text="", font=FONT_B, text_color=GREEN)
        self.cap_label.pack(anchor="w", padx=24, pady=(0, 12))
        self._cap_lbl()

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
        if not messagebox.askyesno("YogoMFG", f"Changer le refresh en {hz} Hz ? (réversible)"):
            return
        ok, msg = display.set_refresh(m["device"], hz)
        messagebox.showinfo("YogoMFG", msg)
        if ok:
            self.refresh = hz; self._cap_lbl()

    def _cap_lbl(self):
        if hasattr(self, "cap_label"):
            cap = inimaker.fps_cap(self._fps_int(), self.refresh)
            self.cap_label.configure(text=f"{self.L('cap_is')} : {cap} FPS  (refresh {self.refresh or '?'} Hz)")

    def _fps_int(self):
        d = "".join(c for c in self.fps.get() if c.isdigit())
        return max(20, int(d)) if d else 120

    # ---------- 5 apply ----------
    def _apply(self):
        self._head("s_apply")
        card = self._card()
        g = self.game
        ctk.CTkLabel(card, font=FONT, text_color=TXT, justify="left", anchor="w",
                     text=(f"{g['name']}\n{self.exe.get()}\n{self.mult.get()} FG · preset "
                           f"{self.preset.get()} · {self._fps_int()} FPS · DLSS "
                           f"{inimaker.QUALITY_FR[self.quality.get()]} · {self.L('scope').lower()} "
                           f"{self.scope.get()}")).pack(anchor="w", padx=24, pady=(16, 6))
        nv = ctk.CTkFrame(card, fg_color=BG, corner_radius=12); nv.pack(fill="x", padx=24, pady=8)
        self._label_tip(nv, self.L("nvcp"), "nvcp", GREEN).pack(anchor="w", padx=12, pady=6)
        ctk.CTkCheckBox(nv, text=self.L("nvcp_on"), variable=self.do_nvcp, font=FONT, fg_color=GREEN).pack(anchor="w", padx=12)
        row = ctk.CTkFrame(nv, fg_color="transparent"); row.pack(fill="x", padx=12, pady=6)
        ctk.CTkEntry(row, textvariable=self.npi, font=FONT).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(row, text="…", width=46, font=FONT_B, fg_color=GREEN_D, text_color=BG, command=self._pick_npi).pack(side="left", padx=6)
        btns = ctk.CTkFrame(nv, fg_color="transparent"); btns.pack(anchor="w", padx=12, pady=6)
        ctk.CTkButton(btns, text=self.L("revert"), font=FONT, width=150, fg_color=SURF2,
                      hover_color=GREEN_D, command=self._revert_nvcp).pack(side="left")
        if not nvcp.is_admin():
            ctk.CTkButton(btns, text=self.L("admin"), font=FONT, width=170, fg_color="#7a5a20",
                          hover_color="#9a7430", command=self._relaunch_admin).pack(side="left", padx=8)
            ctk.CTkLabel(nv, text=self.L("admin_warn"), font=FONT, text_color="#f0b63a").pack(anchor="w", padx=12)
        self.prog = ctk.CTkProgressBar(card, progress_color=GREEN, fg_color=SURF2, height=14)
        self.prog.set(0); self.prog.pack(fill="x", padx=24, pady=(8, 2))
        self.log = ctk.CTkTextbox(card, font=MONO, fg_color=BG, text_color=TXT)
        self.log.pack(fill="both", expand=True, padx=24, pady=10)

    def _pick_npi(self):
        p = filedialog.askopenfilename(title="nvidiaProfileInspector.exe", filetypes=[("exe", "*.exe")])
        if p: self.npi.set(p)

    def _relaunch_admin(self):
        self.cfg["npi_exe"] = self.npi.get(); config.save(self.cfg)
        try:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable,
                                                f'"{os.path.abspath(__file__)}"', None, 1)
            self.destroy()
        except Exception as e:
            messagebox.showerror("YogoMFG", f"Relance admin échouée: {e}")

    def _revert_nvcp(self):
        _, msg = nvcp.revert(self.npi.get(), DATA)
        messagebox.showinfo("YogoMFG", msg)

    def _cfg_now(self):
        c = inimaker.default_cfg(self._fps_int())
        c["multiplier"] = MULT[self.mult.get()]
        c["preset"] = self.preset.get()
        c["dlss_quality"] = self.quality.get()
        c["sync_type"] = self.sync_type.get()
        return c

    def _post(self, frac, line=None):
        def u():
            if frac is not None:
                self.prog.set(frac)
            if line:
                self._log(line)
        self.after(0, u)

    def do_apply(self):
        self.log.delete("1.0", "end"); self.prog.set(0)
        self.b_next.configure(state="disabled")
        c = self._cfg_now()
        if self.scope.get() == "game":
            self.cfg["per_game"][self.game["appid"]] = c
        else:
            self.cfg["global"] = c
        self.cfg["npi_exe"] = self.npi.get(); self.cfg["proxy"] = self.proxy.get()
        config.save(self.cfg)
        # NVCP écrit dans le profil global ET le profil du jeu (vrais noms résolus par nvcp).
        exe = os.path.basename(self.exe.get())
        cap = inimaker.fps_cap(self._fps_int(), self.refresh)
        vrr = self.sync_type.get() in ("gsync", "freesync")
        want_nvcp = self.do_nvcp.get()

        def worker():
            results = []
            self._post(0.1, "⏳ Installation du mod Frame Generation…")
            try:
                acts = installer.install(MOD_ROOT, self.exe.get(), inimaker.make(c), self.proxy.get())
                self._post(0.45, f"✓ Mod installé ({len(acts)} éléments)")
                results.append(("Mod x" + str(c["multiplier"]) + " + INI", True))
            except Exception as e:
                self._post(0.45, "✗ Install mod : " + str(e))
                results.append(("Mod", False))
                return self._post_done(results)
            if want_nvcp:
                self._post(0.6, "⏳ Réglages pilote NVIDIA (cap FPS + VRR/G-Sync)…")
                ok, msg = nvcp.apply(self.npi.get(), DATA, cap, vrr, exe)
                if (not ok) and msg.startswith("NEED_ADMIN"):
                    self._post(0.85, "✗ NVIDIA : droits admin requis.")
                    results.append(("Réglages NVIDIA", False))
                    self.after(0, self._ask_admin)
                else:
                    self._post(0.85, ("✓ " if ok else "✗ ") + "NVIDIA : " + msg)
                    results.append(("Réglages NVIDIA (cap " + str(cap) + ")", ok))
            self._post(0.95, "⏳ Conseils in-game…")
            self._post(None, "\n" + self.L("advice") + " :")
            for a in optadvice.advise(self._fps_int(), self.hw.get("vram_mb", 0),
                                      self.hw.get("series", "30"), self.quality.get()):
                self._post(None, "  • " + a)
            self._post_done(results)

        threading.Thread(target=worker, daemon=True).start()

    def _ask_admin(self):
        if messagebox.askyesno("YogoMFG", "Le réglage NVIDIA exige l'admin. Relancer en admin ?"):
            self._relaunch_admin()

    def _post_done(self, results):
        def u():
            self.prog.set(1.0)
            self._log("\n── Récapitulatif ──")
            for name, ok in results:
                self._log(("  ✓ " if ok else "  ✗ ") + name + ("  validé" if ok else "  NON validé"))
            self._log("\nLance le jeu, active Frame Generation " + self.mult.get() +
                      ". Puis « " + self.L("valider") + " » pour l'analyse.")
            self._applied = True
            self.b_next.configure(state="normal", text=self.L("valider"))
        self.after(0, u)

    # ---------- 6 analyze ----------
    def _analyze(self):
        self._head("s_analyze")
        card = self._card()
        gf = ctk.CTkFrame(card, fg_color="transparent"); gf.pack(anchor="w", padx=24, pady=(16, 4))
        ctk.CTkLabel(gf, text=self.L("an_goal") + " :", font=FONT_B, text_color=DIM).pack(side="left", padx=(0, 10))
        ctk.CTkRadioButton(gf, text=self.L("goal_fps"), variable=self.goal, value="fps", font=FONT, fg_color=GREEN).pack(side="left", padx=8)
        ctk.CTkRadioButton(gf, text=self.L("goal_q"), variable=self.goal, value="quality", font=FONT, fg_color=GREEN).pack(side="left", padx=8)
        ctk.CTkLabel(card, text=self.L("an_hint"), font=FONT, text_color=DIM,
                     wraplength=840, justify="left").pack(anchor="w", padx=24, pady=6)
        # checklist : ce que l'utilisateur a réellement fait en jeu -> meilleure guidance
        ctk.CTkLabel(card, text=self.L("did_title"), font=FONT_B, text_color=GREEN).pack(anchor="w", padx=24, pady=(6, 0))
        cl = ctk.CTkFrame(card, fg_color="transparent"); cl.pack(anchor="w", padx=24)
        if not hasattr(self, "did"):
            self.did = {k: ctk.BooleanVar(value=d) for k, d in
                        (("fg", True), ("reflex", True), ("rt", False), ("pt", False), ("vsync_off", True))}
            self.did_dlss = ctk.StringVar(value=self.quality.get())
        for i, (k, lab) in enumerate((("fg", "did_fg"), ("reflex", "did_reflex"), ("rt", "did_rt"),
                                      ("pt", "did_pt"), ("vsync_off", "did_vsync"))):
            ctk.CTkCheckBox(cl, text=self.L(lab), variable=self.did[k], font=FONT, fg_color=GREEN
                            ).grid(row=i // 3, column=i % 3, sticky="w", padx=8, pady=4)
        dl = ctk.CTkFrame(card, fg_color="transparent"); dl.pack(anchor="w", padx=24, pady=4)
        ctk.CTkLabel(dl, text=self.L("did_dlss"), font=FONT, text_color=DIM).pack(side="left", padx=(0, 8))
        ctk.CTkOptionMenu(dl, variable=self.did_dlss, values=inimaker.QUALITY, font=FONT, width=180,
                          fg_color=SURF2, button_color=GREEN_D).pack(side="left")
        self.an_box = ctk.CTkTextbox(card, font=MONO, fg_color=BG, text_color=TXT)
        self.an_box.pack(fill="both", expand=True, padx=24, pady=8)
        self._delta = {}
        act = ctk.CTkFrame(card, fg_color="transparent"); act.pack(anchor="w", padx=24, pady=10)
        self.b_reco = ctk.CTkButton(act, text=self.L("apply_reco"), font=FONT, fg_color=GREEN,
                                    hover_color=GREEN_D, text_color=BG, state="disabled", command=self._apply_reco)
        self.b_reco.pack(side="left")
        ctk.CTkButton(act, text=self.L("keep"), font=FONT, fg_color=SURF2, hover_color=GREEN_D,
                      command=lambda: messagebox.showinfo("YogoMFG", "OK")).pack(side="left", padx=8)

    def do_analyze(self):
        if not (self.game and self.exe.get()):
            return messagebox.showwarning("YogoMFG", "Sélectionne le jeu (étape 2).")
        self.an_box.delete("1.0", "end"); self.an_box.insert("end", self.L("loading") + "\n")
        def done(res, e):
            self.an_box.delete("1.0", "end")
            if e:
                return self.an_box.insert("end", "Erreur: " + str(e))
            lines, delta = res
            self.an_box.insert("end", "\n".join(lines) + "\n")
            self._delta = delta or {}
            self.b_reco.configure(state="normal" if delta else "disabled")
        did = {k: v.get() for k, v in self.did.items()}
        did["dlss"] = self.did_dlss.get()
        self._async(lambda: loganalyze.analyze(self.exe.get(), self._fps_int(), self.goal.get(), did), done)

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
