"""Panneau NVIDIA via nvidiaProfileInspector (NPI). EXPÉRIMENTAL.

IDs/valeurs tirés des profils RÉELS exportés par le driver (ground truth) :
  - Frame Rate Limiter 0x10835002 = "Max Frame Rate" du panneau NVIDIA, valeur = fps brut
  - Frame Rate Limiter for NVCPL 0x1083500A (valeur du curseur affiché)
  - VRR requested state 0x1094F1F7 = 2 (G-Sync/FreeSync, plein écran ET fenêtré)
  - Enable G-SYNC globally 0x1194F158 = 2

Clé de fiabilité : on écrit dans les VRAIS profils existants (noms exacts lus dans l'export),
pas dans un profil inventé. On vise le profil global ET, si trouvé, le profil du jeu, pour
battre un éventuel cap réglé à la main (ex. 55) dans l'un ou l'autre.
V-Sync / Power management non écrits (pas d'ID fiable) -> conseillés.
"""
import os, re, glob, ctypes, subprocess

ID_FPS_LIMIT = 0x10835002
ID_FPS_NVCPL = 0x1083500A
ID_VRR = 0x1094F1F7
ID_GSYNC_GLOBAL = 0x1194F158
GLOBAL_FALLBACK = "Base Profile"   # nom du profil global tel que NPI l'exporte sur cette machine
_NO_WINDOW = 0x08000000

MANUAL = (
    "Réglages à faire à la main (YogoMFG ne les écrit pas) :\n"
    "  Synchronisation verticale : Activée seulement sans G-Sync/FreeSync.\n"
    "  Mode faible latence = Désactivé (Reflex gère).\n"
    "  Mode gestion de l'alimentation = Performances maximales."
)


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _fps_value(fps):
    return max(0, int(fps))


def _setting(name, sid, val):
    return (f"  <ProfileSetting>\n"
            f"   <SettingNameInfo>{name}</SettingNameInfo>\n"
            f"   <SettingID>{sid}</SettingID>\n"
            f"   <SettingValue>{val}</SettingValue>\n"
            f"   <ValueType>Dword</ValueType>\n"
            f"  </ProfileSetting>\n")


def _profile_xml(name, exe_name, settings_xml):
    execs = (f" <Executeables>\n  <string>{exe_name}</string>\n </Executeables>\n"
             if exe_name else "")
    return (f" <Profile>\n  <ProfileName>{name}</ProfileName>\n{execs}"
            f"  <Settings>\n{settings_xml}  </Settings>\n </Profile>\n")


def _wrap(profiles_xml):
    return ('<?xml version="1.0" encoding="utf-16"?>\n'
            '<ArrayOfProfile xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n'
            + profiles_xml + '</ArrayOfProfile>\n')


def _cap_settings(fps_cap, vrr_on):
    s = _setting("Frame Rate Limiter", ID_FPS_LIMIT, _fps_value(fps_cap))
    s += _setting("Frame Rate Limiter for NVCPL", ID_FPS_NVCPL, _fps_value(fps_cap))
    if vrr_on:
        s += _setting("VRR requested state", ID_VRR, 2)
        s += _setting("Enable G-SYNC globally", ID_GSYNC_GLOBAL, 2)
    return s


def build_nip(profile_name, exe_name, fps_cap, vrr_on):
    """Compat : un seul profil."""
    return _wrap(_profile_xml(profile_name, None if _is_global(profile_name) else exe_name,
                              _cap_settings(fps_cap, vrr_on)))


def _is_global(name):
    n = (name or "").lower()
    return "base profile" in n or "global" in n


def _decode(path):
    raw = open(path, "rb").read()
    for enc in ("utf-8-sig", "utf-16", "utf-8"):
        try:
            t = raw.decode(enc)
            if "<Profile" in t:
                return t
        except Exception:
            pass
    return ""


def _parse_profiles(path):
    """[(name, [exes_lower])] depuis un .nip exporté."""
    t = _decode(path)
    out = []
    for p in re.findall(r"<Profile>(.*?)</Profile>", t, re.S):
        nm = re.search(r"<ProfileName>(.*?)</ProfileName>", p)
        exes = [e.lower() for e in re.findall(r"<string>(.*?)</string>", p)]
        out.append((nm.group(1) if nm else "", exes))
    return out


def _global_name(profiles):
    for n, exes in profiles:
        if not exes and _is_global(n):
            return n
    for n, exes in profiles:
        if not exes:
            return n
    return GLOBAL_FALLBACK


def _game_name(profiles, exe_name):
    if not exe_name:
        return None
    e = exe_name.lower()
    for n, exes in profiles:
        if e in exes:
            return n
    return os.path.splitext(exe_name)[0]   # nouveau profil si le jeu n'en a pas


def apply(npi_exe, out_dir, fps_cap, vrr_on, exe_name=None):
    """Backup, résout les vrais noms de profils, écrit le cap dans le profil global ET le
    profil du jeu, puis importe. Retourne (ok, message). 'NEED_ADMIN' si pas élevé."""
    if not npi_exe or not os.path.isfile(npi_exe):
        return False, "nvidiaProfileInspector.exe introuvable.\n" + MANUAL
    if not is_admin():
        return False, "NEED_ADMIN : nvidiaProfileInspector exige les droits admin."
    os.makedirs(out_dir, exist_ok=True)
    npi_dir = os.path.dirname(npi_exe)

    before = set(glob.glob(os.path.join(npi_dir, "*.nip")))
    backup, profiles = "", []
    try:
        subprocess.run([npi_exe, "-exportCustomized"], timeout=30, cwd=npi_dir, creationflags=_NO_WINDOW)
        new = [p for p in glob.glob(os.path.join(npi_dir, "*.nip")) if p not in before]
        if new:
            backup = max(new, key=os.path.getmtime)
            profiles = _parse_profiles(backup)
    except Exception as e:
        return False, f"Backup NVCP échoué, rien appliqué: {e}\n" + MANUAL

    gname = _global_name(profiles)
    targets = [(gname, None)]                         # profil global (vrai nom)
    if exe_name:
        gm = _game_name(profiles, exe_name)
        targets.append((gm, None if _is_global(gm) else exe_name))   # profil du jeu

    cap_x = _cap_settings(fps_cap, vrr_on)
    nip = os.path.join(out_dir, "yogomfg_apply.nip")
    with open(nip, "w", encoding="utf-16") as f:
        f.write(_wrap("".join(_profile_xml(n, e, cap_x) for n, e in targets)))

    off_x = _setting("Frame Rate Limiter", ID_FPS_LIMIT, 0) + _setting("Frame Rate Limiter for NVCPL", ID_FPS_NVCPL, 0)
    with open(os.path.join(out_dir, "yogomfg_revert.nip"), "w", encoding="utf-16") as f:
        f.write(_wrap("".join(_profile_xml(n, e, off_x) for n, e in targets)))

    try:
        subprocess.run([npi_exe, "-silentImport", nip], timeout=30, cwd=npi_dir, creationflags=_NO_WINDOW)
    except Exception as e:
        return False, f"Import échoué: {e}\n" + MANUAL
    names = ", ".join(n for n, _ in targets)
    extra = " + VRR/G-Sync (plein écran & fenêtré)" if vrr_on else ""
    bk = f"\nBackup profils: {backup}" if backup else ""
    return True, f"Max Frame Rate={fps_cap} écrit dans : {names}{extra}.{bk}"


def revert(npi_exe, out_dir):
    rv = os.path.join(out_dir, "yogomfg_revert.nip")
    if not os.path.isfile(rv):
        return False, "Aucun revert enregistré (applique d'abord)."
    if not is_admin():
        return False, "NEED_ADMIN : nvidiaProfileInspector exige les droits admin."
    try:
        subprocess.run([npi_exe, "-silentImport", rv], timeout=30,
                       cwd=os.path.dirname(npi_exe), creationflags=_NO_WINDOW)
    except Exception as e:
        return False, f"Revert échoué: {e}"
    return True, "Cap NVCP remis à 0 (off) sur les profils modifiés."
