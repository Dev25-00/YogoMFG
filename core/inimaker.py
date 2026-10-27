"""Génère dlssg_sm86.ini selon la config. Clés valides mod 0.4.0 seulement.

Format du mod « dlssg_for_sm86 / SM75 » de sdli1995 (https://github.com/sdli1995/dlssg_for_sm86, MIT).

Non listé = défaut du mod. On n'écrit que ce qu'on change.
"""

# fps cible -> indice SuperResolution conseillé (texte, affiché à l'user).
SR_HINT = {60: "DLSS Quality suffit.",
           120: "DLSS Balanced/Performance.",
           180: "DLSS Performance/Ultra Performance + baisser le path tracing."}


def make(cfg):
    """cfg: dict avec clés multiplier(2/3/4/5/6), optimized, preset, catmull, sr_on, force_mfg, frame_timing."""
    chosen = {2: 1, 3: 2, 4: 3, 5: 4, 6: 5}.get(cfg.get("multiplier", 4), 3)  # multiplicateur N -> MaxGeneratedFrames N-1
    # Multiplicateur imposé par le pilote : le plafond du mod reste à 6X, sinon un changement rapide vers x5/x6
    # (sans réinstaller) serait rabaissé par le mod.
    mgf = 5 if cfg.get("max_ceiling") else chosen
    # force_mfg : patcher le plugin du jeu pour qu'il demande N (expérimental, 5X/6X seulement).
    # Doc mod : ForcePluginFrames réécrit le plafond 4X du plugin ; MfgProbe=1 journalise si ça prend.
    force = bool(cfg.get("force_mfg")) and chosen >= 4
    fg = ("[FrameGeneration]\n"
          "Engine=DLSS\n"
          f"MaxGeneratedFrames={mgf}\n"
          f"CatmullRomWarp={1 if cfg.get('catmull', True) else 0}\n")
    if force:
        fg += f"ForcePluginFrames={chosen}\n"
    return (
        "; Généré par YogoMFG\n"
        + fg + "\n"
        "[DLSSG]\n"
        f"Optimized={cfg.get('optimized', 2)}\n"
        f"Preset={cfg.get('preset', 'Auto')}\n\n"
        "[SuperResolution]\n"
        f"Mode={'On' if cfg.get('sr_on', True) else 'Off'}\n\n"
        "[Logging]\nLevel=2\n" + ("FrameTiming=1\n" if cfg.get("frame_timing") else "") + "\n"   # 2 = configuration + loading (runtime_redirect) -> multiplicateur/génération négociés lisibles
        "[Runtime]\nMode=Bundled\n"
        + ("\n[Debug]\nMfgProbe=1\n" if force else "")
    )


QUALITY = ["quality", "balanced", "performance", "ultra_performance"]
QUALITY_FR = {"quality": "Qualité", "balanced": "Équilibré",
              "performance": "Performance", "ultra_performance": "Ultra Performance"}


def recommend_quality(fps_target):
    """Profil DLSS SR conseillé pour atteindre la cible (simple recommandation)."""
    if fps_target <= 60:
        return "quality"
    if fps_target <= 120:
        return "balanced"
    if fps_target <= 165:
        return "performance"
    return "ultra_performance"


def default_cfg(fps_target=120):
    return {"fps_target": fps_target, "multiplier": 4, "optimized": 2,
            "preset": "Auto", "catmull": True, "sr_on": True,
            "sync_type": "gsync", "vsync": False,
            "dlss_quality": recommend_quality(fps_target)}


def fps_cap(fps_target, refresh):
    """Cap conseillé = sous le refresh ET sous la cible, -3. Jamais < 30."""
    base = min(fps_target, refresh) if refresh else fps_target
    return max(30, base - 3)
