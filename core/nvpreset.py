"""Presets d'optimisation du profil NVIDIA GLOBAL (Base Profile) via nvidiaProfileInspector.

RÈGLE (CLAUDE.md) : on n'écrit QUE des réglages dont l'ID ET les valeurs sont vérifiés.
Source : en-tête officiel NVAPI (docs.nvidia.com/nvapi/NvApiDriverSettings_8h.html), et l'ID du V-Sync
(0x00A879CF) recoupé avec l'export réel du profil de l'utilisateur. Rien d'autre n'est écrit : le mode
DLSS (Qualité/DLAA), les overrides DLSS-SR/RR et le Reflex dépendent de valeurs non vérifiées -> à régler
dans le jeu.

Sauvegarde : l'état d'origine du Base Profile est mémorisé UNE fois (nvpreset_prev.json) ; on peut changer
de preset librement et revenir à l'origine. Une clé absente à l'origine ne peut pas être supprimée par un
.nip : on remet alors la valeur par défaut documentée par NVAPI.
"""
import os, json, subprocess

from core import nvcp, i18n

# clé -> (SettingID, libellé FR, libellé EN, valeur par défaut NVAPI pour le retour arrière)
SETTINGS = {
    "pstate":     (0x1057EB71, "Mode de gestion de l'alimentation", "Power management mode", 5),          # OPTIMAL_POWER
    "tf_quality": (0x00CE2691, "Filtrage de texture : qualité", "Texture filtering: quality", 0),         # QUALITY
    "aniso_opt":  (0x00E73211, "Filtrage de texture : optimisation des échantillons anisotropes",
                   "Texture filtering: anisotropic sample optimization", 0),
    "trilinear":  (0x002ECAF2, "Filtrage de texture : optimisation trilinéaire",
                   "Texture filtering: trilinear optimization", 0),
    "neg_lod":    (0x0019BB68, "Filtrage de texture : biais LOD négatif (verrouillé)",
                   "Texture filtering: negative LOD bias (clamp)", 0),
    "prerender":  (0x007BA09E, "Images pré-rendues maximum", "Max pre-rendered frames", 0),               # app
    "vsync":      (0x00A879CF, "Synchronisation verticale", "Vertical sync", 0x60925292),                # PASSIVE
}

PSTATE_MAX = 1                       # PREFER_MAX
TF_HQ, TF_Q, TF_HP = 0xFFFFFFF6, 0, 20
VSYNC_ON, VSYNC_OFF = 0x47814940, 0x08416747

# Chaque preset : {clé: valeur}. Les clés absentes ne sont PAS touchées.
PRESETS = {
    "perf": {"pstate": PSTATE_MAX, "tf_quality": TF_HP, "aniso_opt": 1, "trilinear": 1, "neg_lod": 1,
             "prerender": 1},
    "balanced": {"pstate": PSTATE_MAX, "tf_quality": TF_Q, "aniso_opt": 0, "trilinear": 1, "neg_lod": 1},
    "quality": {"pstate": PSTATE_MAX, "tf_quality": TF_HQ, "aniso_opt": 0, "trilinear": 0, "neg_lod": 1},
}

INFO = {   # clé -> (FR, EN) : ce que fait le preset, affiché avant d'appliquer
    "perf": ("Gagne quelques % de FPS et de stabilité : GPU toujours en performance max, filtrage de texture "
             "« haute performance » (légère perte de netteté au loin), 1 image pré-rendue (latence plus basse).",
             "Gains a few % FPS and stability: GPU always at max performance, 'high performance' texture "
             "filtering (slightly softer distance), 1 pre-rendered frame (lower latency)."),
    "balanced": ("Réglage recommandé pour la plupart des joueurs : GPU en performance max, filtrage "
                 "qualité standard, optimisations par défaut, pas de scintillement de textures.",
                 "Recommended for most players: GPU at max performance, standard texture filtering quality, "
                 "default optimizations, no texture shimmer."),
    "quality": ("Image la plus propre : filtrage de texture « haute qualité », optimisations désactivées. "
                "Coût en FPS faible. Pour le DLAA / résolution native, règle le mode DLSS dans le jeu.",
                "Cleanest image: 'high quality' texture filtering, optimizations off. Low FPS cost. For "
                "DLAA / native resolution, set the DLSS mode in the game."),
}


def info_text(preset, lang):
    """Description du preset dans la langue (FR/EN d'origine, sinon traduction, sinon anglais)."""
    if lang in ("fr", "en"):
        return INFO[preset][0 if lang == "fr" else 1]
    return i18n.section("INFO", lang).get(preset) or INFO[preset][1]


def _path(out_dir):
    return os.path.join(out_dir, "nvpreset_prev.json")


def state(out_dir):
    """{"preset": nom|None, "vsync": bool} du dernier preset appliqué par YogoMFG, ou {} si rien."""
    try:
        with open(_path(out_dir), encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def values_for(preset, vsync):
    """{clé: valeur} réellement écrites pour (preset, anti-tearing)."""
    vals = dict(PRESETS[preset])
    if vsync:
        vals["vsync"] = VSYNC_ON
    return vals


def describe(preset, vsync, lang="fr"):
    """Lignes lisibles « réglage = valeur » pour l'écran de confirmation."""
    idx = 1 if lang == "fr" else 2
    names = {PSTATE_MAX: "Prefer max performance" if lang != "fr" else "Performance maximale"}
    out = []
    for k, v in values_for(preset, vsync).items():
        label = SETTINGS[k][idx]
        if k == "pstate":
            txt = names[v]
        elif k == "tf_quality":
            txt = {TF_HQ: "High quality" if lang != "fr" else "Haute qualité",
                   TF_Q: "Quality" if lang != "fr" else "Qualité",
                   TF_HP: "High performance" if lang != "fr" else "Haute performance"}[v]
        elif k == "vsync":
            txt = "ON"
        elif k == "prerender":
            txt = str(v)
        else:
            txt = "ON" if v else "OFF"
        out.append(f"{label} = {txt}")
    return out


def _block(text, profile, values):
    """Profil en lecture-modification-écriture : tout l'existant est conservé (l'import NPI remplace sinon)."""
    ch = {SETTINGS[k][0]: (SETTINGS[k][2], v) for k, v in values.items()}
    return nvcp._wrap(nvcp._merge_xml(text, profile, None, ch))


def _verify(npi_exe, profile, expect):
    text = nvcp._export_text(npi_exe)
    if not text:
        return False, "relecture des profils impossible"
    for k, v in expect.items():
        got = nvcp._profile_dword(text, profile, SETTINGS[k][0])
        if got != v:
            return False, f"« {SETTINGS[k][2]} » vaut {got} au lieu de {v}"
    return True, ""


def apply(npi_exe, out_dir, preset, vsync=False):
    """Applique `preset` (+ V-Sync ON si vsync) au Base Profile. Retourne (ok, message) ; 'NEED_ADMIN' si pas élevé."""
    if preset not in PRESETS:
        return False, "Preset inconnu."
    if not npi_exe or not os.path.isfile(npi_exe):
        return False, "nvidiaProfileInspector.exe introuvable."
    if not nvcp.is_admin():
        return False, "NEED_ADMIN : nvidiaProfileInspector exige les droits admin."
    try:
        os.makedirs(out_dir, exist_ok=True)
        text = nvcp._export_text(npi_exe)
        if not text:
            return False, "Export NVIDIA vide, rien modifié."
        profile = nvcp._global_name(nvcp._parse_profiles_text(text))
        prev = state(out_dir)
        if "originals" not in prev:        # l'origine n'est mémorisée qu'une fois (changer de preset ne l'écrase pas)
            prev = {"profile": profile,
                    "originals": {k: nvcp._profile_dword(text, profile, SETTINGS[k][0]) for k in SETTINGS}}
        vals = values_for(preset, vsync)
        if not vsync and prev.get("vsync"):          # le V-Sync avait été forcé par YogoMFG : on remet l'état d'origine
            o = prev["originals"].get("vsync")
            vals["vsync"] = o if o is not None else SETTINGS["vsync"][3]
        nip = os.path.join(out_dir, "yogomfg_nvpreset_apply.nip")
        with open(nip, "w", encoding="utf-16") as f:
            f.write(_block(text, prev["profile"], vals))
        # on mémorise AVANT d'importer : si l'import échoue à mi-chemin, l'origine reste récupérable
        prev.update({"preset": preset, "vsync": bool(vsync)})
        with open(_path(out_dir), "w", encoding="utf-8") as f:
            json.dump(prev, f)
        subprocess.run([npi_exe, "-silentImport", nip], timeout=30,
                       cwd=os.path.dirname(npi_exe), creationflags=nvcp._NO_WINDOW)
        ok, why = _verify(npi_exe, prev["profile"], vals)
    except (OSError, subprocess.SubprocessError) as ex:
        return False, f"Optimisation NVIDIA : {ex}"
    if not ok:
        return False, "Optimisation NVIDIA NON vérifiée : " + why
    return True, f"Preset « {preset} » appliqué au profil global ({len(vals)} réglages vérifiés)."


def revert(npi_exe, out_dir):
    """Remet le Base Profile dans son état d'origine (valeur par défaut NVAPI pour une clé absente à l'origine)."""
    prev = state(out_dir)
    if "originals" not in prev:
        return False, "Aucune optimisation YogoMFG à annuler."
    if not npi_exe or not os.path.isfile(npi_exe):
        return False, "nvidiaProfileInspector.exe introuvable."
    if not nvcp.is_admin():
        return False, "NEED_ADMIN : nvidiaProfileInspector exige les droits admin."
    try:
        text = nvcp._export_text(npi_exe)
        if not text:
            return False, "Export des profils NVIDIA vide : rien modifié."
        vals = {k: (o if o is not None else SETTINGS[k][3]) for k, o in prev["originals"].items()}
        nip = os.path.join(out_dir, "yogomfg_nvpreset_revert.nip")
        with open(nip, "w", encoding="utf-16") as f:
            f.write(_block(text, prev["profile"], vals))
        subprocess.run([npi_exe, "-silentImport", nip], timeout=30,
                       cwd=os.path.dirname(npi_exe), creationflags=nvcp._NO_WINDOW)
        ok, why = _verify(npi_exe, prev["profile"], vals)
        if not ok:
            return False, "Retour arrière NON vérifié (sauvegarde conservée) : " + why
        os.remove(_path(out_dir))
    except (OSError, subprocess.SubprocessError) as ex:
        return False, f"Retour arrière échoué : {ex}"
    return True, "Profil NVIDIA global remis dans son état d'origine."


# ---------- Profil global pour la Frame Generation (0.7.0) ----------
# Règle 6 : le GLOBAL ne reçoit que le PLAFOND dynamique DLSS-G (5 = jusqu'à x6) et le VRR/G-SYNC plein écran ET
# fenêtré ; jamais le nombre d'images IMPOSÉ (0x104D6667), qui forcerait ce multiplicateur sur tous les jeux.
FG_LABELS = {nvcp.ID_MFG_DYN_MAX: "Override maximum DLSSG dynamic multi frame count",
             nvcp.ID_VRR: "VRR requested state", nvcp.ID_GSYNC_GLOBAL: "Enable G-SYNC globally"}
FG_CEILING = 5


def _fg_path(out_dir):
    return os.path.join(out_dir, "nvglobal_prev.json")


def fg_global_changes(text, vrr):
    """{SettingID: (libellé, valeur)} écrit dans le Base Profile. Les deux clés VRR ne sont écrites que si l'export du
    pilote les nomme déjà ainsi (ID confirmé par le pilote lui-même, jamais deviné) ; sinon elles sont sautées."""
    ch = {nvcp.ID_MFG_DYN_MAX: (FG_LABELS[nvcp.ID_MFG_DYN_MAX], FG_CEILING)}
    if vrr:
        for sid in (nvcp.ID_VRR, nvcp.ID_GSYNC_GLOBAL):
            if nvcp._named(text, sid, FG_LABELS[sid]):
                ch[sid] = (FG_LABELS[sid], 2)
    return ch


def apply_fg_global(npi_exe, out_dir, vrr):
    """Plafond DLSS-G x6 (+ VRR plein écran/fenêtré si écran VRR) dans le Base Profile. Origine mémorisée une fois,
    écriture relue. Retourne (ok, message) ; 'NEED_ADMIN' si pas élevé."""
    if not npi_exe or not os.path.isfile(npi_exe):
        return False, "nvidiaProfileInspector.exe introuvable."
    if not nvcp.is_admin():
        return False, "NEED_ADMIN : nvidiaProfileInspector exige les droits admin."
    try:
        os.makedirs(out_dir, exist_ok=True)
        text = nvcp._export_text(npi_exe)
        if not text:
            return False, "Export NVIDIA vide, rien modifié."
        try:
            with open(_fg_path(out_dir), encoding="utf-8") as f:
                prev = json.load(f)
        except (OSError, ValueError):
            prev = {}
        if "originals" not in prev:               # l'origine n'est mémorisée qu'une fois (ré-optimiser ne l'écrase pas)
            profile = nvcp._global_name(nvcp._parse_profiles_text(text))
            prev = {"profile": profile, "originals": {str(s): nvcp._profile_dword(text, profile, s) for s in FG_LABELS}}
            with open(_fg_path(out_dir), "w", encoding="utf-8") as f:     # AVANT l'import : origine toujours récupérable
                json.dump(prev, f)
        ch = fg_global_changes(text, vrr)
        nip = os.path.join(out_dir, "yogomfg_fg_global.nip")
        with open(nip, "w", encoding="utf-16") as f:
            f.write(nvcp._wrap(nvcp._merge_xml(text, prev["profile"], None, ch)))
        subprocess.run([npi_exe, "-silentImport", nip], timeout=30,
                       cwd=os.path.dirname(npi_exe), creationflags=nvcp._NO_WINDOW)
        after = nvcp._export_text(npi_exe)
        bad = [FG_LABELS[s] for s, (_, v) in ch.items() if nvcp._profile_dword(after, prev["profile"], s) != v]
    except (OSError, subprocess.SubprocessError) as ex:
        return False, f"Profil global : {ex}"
    if bad or not after:
        return False, "Profil global NON vérifié : " + (", ".join(bad) or "relecture impossible")
    skipped = vrr and len(ch) == 1
    return True, ("Profil global : plafond DLSS-G x6" + (" + VRR plein écran/fenêtré" if len(ch) > 1 else "")
                  + (" (VRR global non écrit : ID non confirmé par l'export du pilote)" if skipped else "") + ".")


def revert_fg_global(npi_exe, out_dir):
    """Remet les valeurs globales d'origine. Une clé absente à l'origine ne peut pas être supprimée par un .nip :
    plafond DLSS-G -> valeur NVIDIA (4X), clés VRR -> laissées (signalé)."""
    try:
        with open(_fg_path(out_dir), encoding="utf-8") as f:
            prev = json.load(f)
    except (OSError, ValueError):
        return False, "Aucun réglage global YogoMFG à annuler."
    if not npi_exe or not os.path.isfile(npi_exe):
        return False, "nvidiaProfileInspector.exe introuvable."
    if not nvcp.is_admin():
        return False, "NEED_ADMIN : nvidiaProfileInspector exige les droits admin."
    try:
        text = nvcp._export_text(npi_exe)
        if not text:
            return False, "Export des profils NVIDIA vide : rien modifié."
        ch, left = {}, []
        for s_, o in prev["originals"].items():
            sid = int(s_)
            if o is not None:
                ch[sid] = (FG_LABELS[sid], o)
            elif sid == nvcp.ID_MFG_DYN_MAX:
                ch[sid] = (FG_LABELS[sid], nvcp.MFG_STOCK)
            elif nvcp._profile_dword(text, prev["profile"], sid) is not None:
                left.append(FG_LABELS[sid])
        nip = os.path.join(out_dir, "yogomfg_fg_global_revert.nip")
        with open(nip, "w", encoding="utf-16") as f:
            f.write(nvcp._wrap(nvcp._merge_xml(text, prev["profile"], None, ch)))
        subprocess.run([npi_exe, "-silentImport", nip], timeout=30,
                       cwd=os.path.dirname(npi_exe), creationflags=nvcp._NO_WINDOW)
        after = nvcp._export_text(npi_exe)
        bad = [FG_LABELS[s] for s, (_, v) in ch.items() if nvcp._profile_dword(after, prev["profile"], s) != v]
        if bad or not after:
            return False, "Retour arrière global NON vérifié (sauvegarde conservée) : " + (", ".join(bad) or "relecture")
        os.remove(_fg_path(out_dir))
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as ex:
        return False, f"Retour arrière global échoué : {ex}"
    return True, "Profil global remis comme avant" + (
        f" (absent à l'origine, non supprimable : {', '.join(left)})." if left else ".")
