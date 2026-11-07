"""Génère dlssg_sm86.ini (mod 0.4.1) et décide le multiplicateur automatiquement.

Format du mod « dlssg_for_sm86 / SM75 » de sdli1995 (https://github.com/sdli1995/dlssg_for_sm86).
Clés et valeurs vérifiées dans docs/INSTALL.en.md de la release 0.4.1 ; une clé absente prend le défaut validé du mod.
Une valeur invalide n'est jamais remplacée par un défaut : le mod coupe la fonction concernée. D'où des valeurs FIXES.
"""
import re, math

MARK = "; Généré par YogoMFG"

# Seules clés écrites. Preset=A : « Auto » a été supprimé le 2026-10-22 (il tourne comme A avec un avertissement).
# Optimized=1 = sortie identique bit à bit au runtime NVIDIA officiel (2 et 3 sont avec pertes).
ALLOWED = {
    "FrameGeneration": {"Engine", "MaxGeneratedFrames"},
    "DLSSG": {"Optimized", "Preset"},
    "Logging": {"Level", "Directory", "FrameTiming"},
    "Runtime": {"Mode"},
    "SuperResolution": {"Mode"},
}

FIRST_RUN_BASE = 55  # sans mesure : ~55 images réelles visées (180 Hz VRR -> T=177 -> x3, 59 réelles)
MIN_BASE = 45        # base réelle visée ; en dessous, les images générées se voient : on prévient
WEAK_BASE = 30       # cartes faibles (RTX 2050/2060, ou base mesurée sous 45) : 30 images réelles acceptées
MIN_MULT = 3         # x2 est laissé à la Frame Generation FSR d'AMD : YogoMFG va de x3 à x6
MIN_SECONDS = 60     # au moins une minute de jeu avec la Frame Generation pour calibrer
MOD_MAX = 6          # le runtime embarqué (310.9.16) va jusqu'à 6X (MaxGeneratedFrames=5)


def make(mult):
    """Texte complet de dlssg_sm86.ini pour un multiplicateur 2..6."""
    mgf = max(1, min(MOD_MAX - 1, int(mult) - 1))
    return (f"{MARK}\n\n"
            "[FrameGeneration]\nEngine=DLSS\n"
            f"MaxGeneratedFrames={mgf}\n\n"
            "[DLSSG]\nOptimized=1\nPreset=A\n\n"
            "[Logging]\nLevel=2\nDirectory=dlssg_sm86\\logs\nFrameTiming=1\n\n"
            "[Runtime]\nMode=Bundled\n\n"
            "[SuperResolution]\nMode=Off\n")


def plan(refresh_hz, vrr, stats=None, ceiling=MOD_MAX, weak=False, user_cap=None):
    """Image propre d'abord : (multiplicateur, cible T = cap FPS du profil du jeu | None, avertissement, calibré).

    T = fréquence - 3 sur écran VRR (reste dans la plage G-Sync/FreeSync), la fréquence sinon. M toujours dans
    [3, plafond] (plafond = prouvé par une session, x6 au plus ; jamais sous 3 même si le jeu a prouvé moins).
    - pas de session mesurée (moins de MIN_SECONDS de jeu avec la FG) : M = arrondi(T / 55) ;
    - FPS réels figés par un limiteur L (plateau, GPU < 95 %) : M = arrondi(T / L) ; si ce plateau est NOTRE cap
      (L x multiplicateur mesuré ~ T), on garde ce multiplicateur (pas d'aller-retour) ;
    - sinon : le plus petit M tel que T / M <= base basse mesurée (10e centile) ; si même le plafond n'y suffit pas,
      le plafond (l'écran VRR absorbe l'écart).
    Avertissement si T / M < 45 images réelles (30 sur carte faible ; une base mesurée sous 45 compte comme faible).
    """
    hz = int(refresh_hz or 0)
    top = max(MIN_MULT, min(MOD_MAX, int(ceiling or MOD_MAX)))
    if hz <= 0:
        return MIN_MULT, None, False, False
    t = hz - 3 if vrr else hz
    if user_cap and 20 <= int(user_cap) < t:   # the player's own fps limit (NVIDIA app / profile) wins: never go above it
        t = int(user_cap)
    cal = bool(stats and stats.get("seconds", 0) >= MIN_SECONDS and (stats.get("low") or 0) > 0)
    if not cal:
        m = round(t / FIRST_RUN_BASE)
    elif stats.get("plateau"):
        lim, got = stats["plateau"], stats.get("mult") or 1
        m = round(got) if got > 1 and abs(lim * got - t) <= 0.03 * t else round(t / lim)
    else:
        low = stats["low"]
        # Session tenue par un plafond d'affichage : « low » n'est alors que ce plafond divisé par le multiplicateur,
        # pas la capacité du moteur. S'y fier bouclait (cap 120 + x5 -> 24 réelles -> « low » 24 -> x5 à nouveau, à
        # vie). On prend la capacité démontrée, qui ne dépasse « low » que si plusieurs valeurs de n ont été tenues.
        dp, best = stats.get("disp_plateau"), stats.get("best")
        if dp and best and best > low:
            low = best
        weak = weak or low < MIN_BASE
        m = next((k for k in range(MIN_MULT, top + 1) if t / k <= low), top)
    m = max(MIN_MULT, min(top, int(m)))
    return m, t, t / m < (WEAK_BASE if weak else MIN_BASE), cal


def weak_gpu(name):
    """Cartes d'entrée de gamme pour qui 30 images réelles sont acceptables (liste courte, à compléter par mesures)."""
    return any(k in (name or "").upper() for k in ("RTX 2050", "RTX 2060"))


def keys_of(text):
    """{section: {clé}} lu dans un INI (pour le contrôle des clés autorisées)."""
    out, sec = {}, None
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        m = re.match(r"\[(.+)\]$", line)
        if m:
            sec = m.group(1)
            out.setdefault(sec, set())
        elif "=" in line:
            out.setdefault(sec, set()).add(line.split("=", 1)[0].strip())
    return out


# Conseils d'analyse (écran Analyser) : profil DLSS SR que l'utilisateur règle dans le jeu.
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
    return {"fps_target": fps_target, "dlss_quality": recommend_quality(fps_target)}


def _selftest():
    def s(low, plateau=None, mult=3, seconds=180, disp_plateau=None, best=None):
        return {"low": low, "plateau": plateau, "mult": mult, "seconds": seconds,
                "disp_plateau": disp_plateau, "best": best}
    # première fois (aucune mesure) : arrondi(T / 55) dans [3, plafond]
    assert plan(180, True) == (3, 177, False, False)                   # 59 réelles
    assert plan(240, True)[0] == 4 and plan(360, True)[0] == 6
    assert plan(144, False)[:2] == (3, 144)                            # 48 réelles, jamais x2
    assert plan(180, True, user_cap=120) == (3, 120, True, False)      # plafond du joueur respecté : 40 réelles, avertissement
    assert plan(180, True, user_cap=200)[1] == 177                     # un plafond au-dessus de l'écran ne compte pas
    assert plan(120, False)[0] == 3 and plan(60, False)[0] == 3
    assert plan(180, True, s(65, seconds=30))[0] == 3                  # session trop courte : pas de calibrage
    # limiteur du jeu L : arrondi(T / L)
    assert plan(180, True, s(59, plateau=60.0, mult=4))[0] == 3
    assert plan(180, True, s(29, plateau=30.0))[0] == 6
    assert plan(180, True, s(44, plateau=45.0))[0] == 4
    assert plan(180, True, s(58, plateau=59.0, mult=3))[0] == 3        # plateau = notre propre cap : on garde x3
    # base mesurée : plus petit M dans [3, plafond] avec T / M <= base
    assert plan(180, True, s(95)) == (3, 177, False, True)             # x2 suffirait, mais x3 minimum
    assert plan(180, True, s(50)) == (4, 177, True, True)              # 44 réelles < 45 : appliqué + conseil
    assert plan(240, True, s(48))[:3] == (5, 237, False)               # 47 réelles
    assert plan(180, True, s(20)) == (6, 177, True, True)              # même x6 ne suffit pas : plafond + avertissement
    assert plan(180, True, s(20), ceiling=4)[:3] == (4, 177, False)    # RE Requiem x4 : 44 cibles >= 30 (base faible)
    assert plan(360, True, s(70))[0] == 6 and plan(360, True, s(70), ceiling=4)[0] == 4
    assert plan(180, True, s(40))[2] is False                          # base 40 < 45 : carte faible, 30 acceptées
    assert plan(180, True, s(46), weak=True)[2] is False               # RTX 2060 : 30 acceptées
    assert plan(180, True, ceiling=2)[0] == 3                          # plafond prouvé x2 : on reste à x3
    # plafond d'AFFICHAGE : « low » n'est que le cap / multiplicateur. Cas réel CONTROL Resonant, cap 120, x5
    # obtenu, 24 réelles mesurées, mais 58,8 démontrées à n=1. Sans le correctif, le plan bouclait sur x5 à vie.
    cb = s(23.98, mult=5, disp_plateau=120.0, best=58.79)
    assert plan(120, True, cb, user_cap=120)[0] == 3, plan(120, True, cb, user_cap=120)
    assert plan(144, True, cb)[:2] == (3, 141), plan(144, True, cb)     # 47 réelles, et non x6 / 24
    assert plan(120, True, s(23.98, mult=5, disp_plateau=120.0))[0] == 5   # sans capacité démontrée : comportement inchangé
    assert plan(120, True, s(23.98, mult=5, best=58.79))[0] == 5           # sans plateau d'affichage : inchangé
    assert plan(120, True, s(58.79, mult=2, disp_plateau=120.0, best=58.79))[0] == 3   # best == low : rien ne change
    assert plan(0, True) == (3, None, False, False) and plan(500, False)[0] == 6
    assert weak_gpu("NVIDIA GeForce RTX 2060 SUPER") and not weak_gpu("NVIDIA GeForce RTX 3070")
    for m in (2, 3, 4, 5, 6):
        txt = make(m)
        ks = keys_of(txt)
        assert ks == ALLOWED, ks
        assert f"MaxGeneratedFrames={m - 1}\n" in txt and txt.startswith(MARK)
        assert "Optimized=1\n" in txt and "Preset=A\n" in txt and "Auto" not in txt
    print("inimaker selftest OK")


if __name__ == "__main__":
    _selftest()
