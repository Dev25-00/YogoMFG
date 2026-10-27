"""Détecte si un jeu intègre DLSS-G / Streamline (frame generation NVIDIA)."""
import os, ctypes

# DLL Streamline/DLSS-G -> le jeu expose le Frame Generation NVIDIA.
_MARKERS = ("sl.dlss_g.dll", "nvngx_dlssg.dll", "sl.interposer.dll",
            "sl.dlss.dll", "nvngx.dll", "sl.common.dll")


def supports(game_dir):
    """'yes' si marqueurs Streamline/DLSS-G trouvés, sinon 'unknown'."""
    for dp, _, files in os.walk(game_dir):
        if dp.count(os.sep) - game_dir.count(os.sep) > 4:
            continue
        low = {f.lower() for f in files}
        if low & set(_MARKERS):
            return "yes"
    return "unknown"


def _find(game_dir, name):
    name = name.lower()
    for dp, _, files in os.walk(game_dir):
        if dp.count(os.sep) - game_dir.count(os.sep) > 4:
            continue
        for f in files:
            if f.lower() == name:
                return os.path.join(dp, f)
    return None


def _file_version(path):
    """(maj, min, build, rev) depuis les métadonnées Windows FileVersion, ou None."""
    try:
        ver = ctypes.windll.version
        size = ver.GetFileVersionInfoSizeW(path, None)
        if not size:
            return None
        buf = ctypes.create_string_buffer(size)
        ver.GetFileVersionInfoW(path, 0, size, buf)
        ptr = ctypes.c_void_p()
        ln = ctypes.c_uint()
        if not ver.VerQueryValueW(buf, "\\", ctypes.byref(ptr), ctypes.byref(ln)):
            return None
        ffi = ctypes.cast(ptr, ctypes.POINTER(ctypes.c_uint))  # VS_FIXEDFILEINFO
        ms, ls = ffi[2], ffi[3]  # dwFileVersionMS, dwFileVersionLS
        return ((ms >> 16) & 0xFFFF, ms & 0xFFFF, (ls >> 16) & 0xFFFF, ls & 0xFFFF)
    except Exception:
        return None


def mfg_capability(game_dir):
    """Capacité MFG du jeu selon la version du plugin DLSS-G (sl.dlss_g.dll).

    Le plafond du multiplicateur est fixé par CE plugin, pas par le GPU ni par le mod :
    >= 2.11.1 -> 6X natif possible (si le jeu propose Frame Gen Dynamique/Auto) ;
    plus ancien -> plafonné 4X (forcer 6X désactive la FG, cf. doc du mod).
    Retourne (max_mult:int, version_str|None, note_key).
    """
    dll = _find(game_dir, "sl.dlss_g.dll")
    if not dll:
        return (4, None, "mfg_noplugin")
    v = _file_version(dll)
    if not v:
        return (4, None, "mfg_noplugin")
    vs = ".".join(str(x) for x in v[:3])
    if (v[0], v[1], v[2]) >= (2, 11, 1):
        return (6, vs, "mfg_6x")
    return (4, vs, "mfg_4x")


# Plugins que le mod identifie exactement (doc : Wukong 2.7.4, Cyberpunk 2.7.1) + natifs >= 2.11.1.
_FORCEABLE = {(2, 7, 4), (2, 7, 1)}


def force_ok(game_dir):
    """(ok, version_str|None). Forcer 5X/6X n'a de sens que sur un plugin que le mod sait patcher.

    Ailleurs (ex. 2.7.2, 2.8.0) le mod log plugin_mfg_unrecognized (rien ne change) ou, pire,
    la FG se coupe (x1) -> on bloque la case plutôt que de laisser l'utilisateur tâtonner.
    """
    dll = _find(game_dir, "sl.dlss_g.dll")
    v = _file_version(dll) if dll else None
    if not v:
        return (False, None)
    vs = ".".join(str(x) for x in v[:3])
    return ((v[0], v[1], v[2]) >= (2, 11, 1) or (v[0], v[1], v[2]) in _FORCEABLE, vs)


# Autres mods de FG déjà posés dans le dossier du jeu : deux proxies/FG en même temps = pacing et son cassés.
_FOREIGN = (("dlssg_to_fsr3", "dlssg-to-fsr3 (FSR3)"), ("optiscaler", "OptiScaler"),
            ("fakenvapi", "fakenvapi"), ("dlss-enabler", "DLSS Enabler"))


def conflicts(game_dir):
    """Noms des autres mods de FG détectés à côté du .exe (niveau racine du jeu + sous-dossiers proches)."""
    found = []
    for dp, dirs, files in os.walk(game_dir):
        if dp.count(os.sep) - game_dir.count(os.sep) > 3:
            dirs[:] = []
            continue
        low = " ".join(f.lower() for f in files if f.lower().endswith(".dll"))   # DLL seulement : un .log/.ini oublié n'est pas un mod
        for key, label in _FOREIGN:
            if key in low and label not in found:
                found.append(label)
    return found


# Anti-cheats connus : préfixes de noms de fichiers/dossiers (minuscules) ou noms exacts -> libellé.
# Préfixes uniquement (startswith) : « face-base.png » ou « ProbeClient.dll » ne doivent pas matcher.
_AC_PREFIX = (("easyanticheat", "EasyAntiCheat"), ("beservice", "BattlEye"), ("beclient", "BattlEye"),
              ("eaanticheat", "EA Javelin"), ("xigncode", "XIGNCODE3"), ("npggnt", "nProtect GameGuard"),
              ("gameguard", "nProtect GameGuard"), ("equ8_", "EQU8"), ("anticheatexpert", "Anti-Cheat Expert (Tencent)"),
              ("ace-base", "Anti-Cheat Expert (Tencent)"), ("pbsvc", "PunkBuster"))
_AC_EXACT = {"battleye": "BattlEye", "vgc.exe": "Riot Vanguard", "punkbuster": "PunkBuster"}


def _anticheat_label(name):
    if name in _AC_EXACT:
        return _AC_EXACT[name]
    for key, label in _AC_PREFIX:
        if name.startswith(key):
            return label
    return None


def scan(game_dir):
    """Un seul parcours du dossier (au lieu de 4) : support FG, plugin DLSS-G, conflits.

    Retourne {sup, cap, ver, note, force_ok, clash}. À appeler hors thread UI.
    """
    base = game_dir.count(os.sep)
    sup, plug, clash, ac = "unknown", None, [], []
    markers = set(_MARKERS)
    for dp, dirs, files in os.walk(game_dir):
        if dp.count(os.sep) - base >= 4:
            dirs[:] = []          # ne descend pas plus bas (les fichiers de ce niveau restent lus)
        low = {f.lower(): f for f in files}
        for name in list(low) + [d.lower() for d in dirs]:
            label = _anticheat_label(name)
            if label and label not in ac:
                ac.append(label)
        if markers & set(low):
            sup = "yes"
        if plug is None and "sl.dlss_g.dll" in low:
            plug = os.path.join(dp, low["sl.dlss_g.dll"])
        joined = " ".join(n for n in low if n.endswith(".dll"))
        for key, label in _FOREIGN:
            if key in joined and label not in clash:
                clash.append(label)
    v = _file_version(plug) if plug else None
    if not v:
        cap, vs, note, fok = 4, None, "mfg_noplugin", False
    else:
        vs = ".".join(str(x) for x in v[:3])
        native = (v[0], v[1], v[2]) >= (2, 11, 1)
        cap, note = (6, "mfg_6x") if native else (4, "mfg_4x")
        fok = native or (v[0], v[1], v[2]) in _FORCEABLE
    return {"sup": sup, "cap": cap, "ver": vs, "note": note, "force_ok": (fok, vs), "clash": clash,
            "anticheat": ac}


def web_query(name):
    """URL de recherche web pour lever le doute sur le support FG."""
    return "https://www.google.com/search?q=" + name.replace(" ", "+") + "+DLSS+Frame+Generation"
