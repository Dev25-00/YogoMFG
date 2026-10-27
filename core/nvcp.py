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
import os, re, glob, json, ctypes, subprocess
from xml.sax.saxutils import escape as _esc, unescape as _unesc

ID_FPS_LIMIT = 0x10835002
ID_FPS_NVCPL = 0x1083500A
ID_VRR = 0x1094F1F7
ID_GSYNC_GLOBAL = 0x1194F158
# Plafond multi-frame du PILOTE (lu par le plugin DLSS-G du jeu ; unité = images générées, 3 = 4X, 5 = 6X).
# Vérifié : noms exportés par NPI sur cette machine + log du mod (drs_dlssg, plugin_limit) ; absents de Reference.xml.
ID_MFG_COUNT = 0x104D6667      # "Override DLSSG multi-frame count"
ID_MFG_DYN_MAX = 0x10562D0F    # "Override maximum DLSSG dynamic multi frame count"
MFG_STOCK = 3                  # valeur écrite par l'appli NVIDIA (4X)
GLOBAL_FALLBACK = "Base Profile"   # nom du profil global tel que NPI l'exporte sur cette machine
_NO_WINDOW = 0x08000000

MANUAL = (
    "Réglages à faire à la main (YogoMFG ne les écrit pas) :\n"
    "  Synchronisation verticale : Activée — avec Frame Gen, garde-la ON même en G-Sync/FreeSync\n"
    "    (+ cap FPS sous le refresh via Reflex) pour couper le tearing (bas de l'image + HUD).\n"
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


def _merge_xml(text, name, exe, changes):
    """<Profile> en LECTURE-MODIFICATION-ÉCRITURE.

    `nvidiaProfileInspector -silentImport` REMPLACE les réglages ET la liste d'exe d'un profil présent dans
    le fichier (constaté : un import de 2 clés effaçait les ~15 autres réglages du Base Profile). On relit donc
    l'export `text`, on garde tout l'existant et on n'applique que `changes` = {SettingID: (libellé, valeur)}.
    """
    body = None
    for b in re.findall(r"<Profile>(.*?)</Profile>", text, re.S):
        m = re.search(r"<ProfileName>(.*?)</ProfileName>", b)
        if m and m.group(1) == _esc(name):
            body = b
            break
    exes, kept = [], []
    if body:
        exes = re.findall(r"<string>(.*?)</string>", body)
        for blk in re.findall(r"<ProfileSetting>.*?</ProfileSetting>", body, re.S):
            m = re.search(r"<SettingID>(\d+)</SettingID>", blk)
            if m and int(m.group(1)) not in changes:
                kept.append(blk)
    if exe and _esc(exe).lower() not in [e.lower() for e in exes]:
        exes.append(_esc(exe))
    new = "".join(_setting(lbl, sid, val) for sid, (lbl, val) in changes.items())
    xml = f" <Profile>\n  <ProfileName>{_esc(name)}</ProfileName>\n"
    if exes:
        xml += " <Executeables>\n" + "".join(f"  <string>{e}</string>\n" for e in exes) + " </Executeables>\n"
    return xml + "  <Settings>\n" + "".join(b + "\n" for b in kept) + new + "  </Settings>\n </Profile>\n"


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
    return _parse_profiles_text(_decode(path))


def _parse_profiles_text(t):
    out = []
    for p in re.findall(r"<Profile>(.*?)</Profile>", t, re.S):
        nm = re.search(r"<ProfileName>(.*?)</ProfileName>", p)
        exes = [_unesc(e).lower() for e in re.findall(r"<string>(.*?)</string>", p)]
        out.append((_unesc(nm.group(1)) if nm else "", exes))
    return out


def _global_name(profiles):
    # Le vrai profil global NVIDIA s'appelle "Base Profile". "_GLOBAL_DRIVER_PROFILE" est un profil
    # fantôme (créé par un import antérieur) : l'écrire ne change rien -> le cap 120 du Base Profile restait.
    for n, exes in profiles:
        if not exes and n.strip().lower() == "base profile":
            return n
    for n, exes in profiles:
        if n.startswith("_GLOBAL"):
            continue
        if not exes and _is_global(n):
            return n
    for n, exes in profiles:
        if not exes and not n.startswith("_GLOBAL"):
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
    if exe_name:                                       # le profil du JEU seulement : le global touche tous les autres jeux
        gm = _game_name(profiles, exe_name)
        targets = [(gm, None if _is_global(gm) else exe_name)]
    else:
        targets = [(gname, None)]

    btext = _decode(backup) if backup else ""
    if not btext:
        return False, "Export des profils NVIDIA vide : rien appliqué (pour ne rien écraser).\n" + MANUAL
    changes = {ID_FPS_LIMIT: ("Frame Rate Limiter", _fps_value(fps_cap)),
               ID_FPS_NVCPL: ("Frame Rate Limiter for NVCPL", _fps_value(fps_cap))}
    if vrr_on:
        changes[ID_VRR] = ("VRR requested state", 2)
        changes[ID_GSYNC_GLOBAL] = ("Enable G-SYNC globally", 2)
    prev = []     # valeurs d'avant, pour revert() : [nom, exe, {sid: ancienne valeur | None}]
    for n, e in targets:
        prev.append([n, e, {str(sid): _profile_dword(btext, n, sid) for sid in changes}])
    try:
        with open(os.path.join(out_dir, "nvcp_applied.json"), "w", encoding="utf-8") as f:
            json.dump(prev, f)
    except OSError as e:
        return False, f"Sauvegarde du revert impossible, rien appliqué: {e}"
    nip = os.path.join(out_dir, "yogomfg_apply.nip")
    with open(nip, "w", encoding="utf-16") as f:
        f.write(_wrap("".join(_merge_xml(btext, n, e, changes) for n, e in targets)))

    try:
        subprocess.run([npi_exe, "-silentImport", nip], timeout=30, cwd=npi_dir, creationflags=_NO_WINDOW)
    except Exception as e:
        return False, f"Import échoué: {e}\n" + MANUAL
    names = ", ".join(n for n, _ in targets)
    extra = " + VRR/G-Sync (plein écran & fenêtré)" if vrr_on else ""
    bk = f"\nBackup profils: {backup}" if backup else ""
    return True, f"Max Frame Rate={fps_cap} écrit dans : {names}{extra}.{bk}"


def revert(npi_exe, out_dir):
    """Remet cap FPS / VRR / G-SYNC comme avant apply() (cap absent -> 0 = off), sans toucher au reste du profil."""
    path = os.path.join(out_dir, "nvcp_applied.json")
    if not os.path.isfile(path):
        return False, "Aucun revert enregistré (applique d'abord)."
    if not npi_exe or not os.path.isfile(npi_exe):
        return False, "nvidiaProfileInspector.exe introuvable."
    if not is_admin():
        return False, "NEED_ADMIN : nvidiaProfileInspector exige les droits admin."
    try:
        with open(path, encoding="utf-8") as f:
            prev = json.load(f)
        text = _export_text(npi_exe)
        if not text:
            return False, "Export des profils NVIDIA vide : rien modifié."
        labels = {ID_FPS_LIMIT: "Frame Rate Limiter", ID_FPS_NVCPL: "Frame Rate Limiter for NVCPL",
                  ID_VRR: "VRR requested state", ID_GSYNC_GLOBAL: "Enable G-SYNC globally"}
        blocks = []
        for n, e, old in prev:
            ch = {}
            for sid_s, v in old.items():
                sid = int(sid_s)
                if v is not None:
                    ch[sid] = (labels[sid], v)
                elif sid in (ID_FPS_LIMIT, ID_FPS_NVCPL):
                    ch[sid] = (labels[sid], 0)          # cap absent avant -> off
            blocks.append(_merge_xml(text, n, e, ch))
        nip = os.path.join(out_dir, "yogomfg_revert.nip")
        with open(nip, "w", encoding="utf-16") as f:
            f.write(_wrap("".join(blocks)))
        subprocess.run([npi_exe, "-silentImport", nip], timeout=30,
                       cwd=os.path.dirname(npi_exe), creationflags=_NO_WINDOW)
        os.remove(path)
    except (OSError, ValueError, subprocess.SubprocessError) as e:
        return False, f"Revert échoué: {e}"
    return True, "Cap FPS / VRR / G-SYNC remis comme avant sur les profils modifiés."


def _export_text(npi_exe):
    """Exporte les profils personnalisés ; retourne le texte ("" si échec).

    NPI nomme l'export à la seconde : on compare chemin ET mtime, sinon deux exports dans la même
    seconde écrasent le fichier et paraissent « absents ». Notre export est supprimé après lecture
    (sauf s'il a écrasé un fichier existant, ex. le backup d'apply()), pour ne pas remplir tools/npi.
    """
    npi_dir = os.path.dirname(npi_exe)
    snap = {p: os.path.getmtime(p) for p in glob.glob(os.path.join(npi_dir, "*.nip"))}
    subprocess.run([npi_exe, "-exportCustomized"], timeout=30, cwd=npi_dir, creationflags=_NO_WINDOW)
    new = [p for p in glob.glob(os.path.join(npi_dir, "*.nip"))
           if p not in snap or os.path.getmtime(p) != snap[p]]
    if not new:
        return ""
    path = max(new, key=os.path.getmtime)
    text = _decode(path)
    if path not in snap:
        try:
            os.remove(path)
        except OSError:
            pass
    return text


def _profile_dword(text, profile, sid):
    """Valeur Dword de SettingID `sid` dans le profil `profile` (texte d'export), ou None."""
    for body in re.findall(r"<Profile>(.*?)</Profile>", text, re.S):
        nm = re.search(r"<ProfileName>(.*?)</ProfileName>", body)
        if nm and nm.group(1) == _esc(profile):
            m = re.search(r"<SettingID>%d</SettingID>\s*<SettingValue>(\d+)</SettingValue>" % sid, body)
            return int(m.group(1)) if m else None
    return None


def _mfg_block(text, profile, exe, count, dyn):
    return _merge_xml(text, profile, exe, {ID_MFG_COUNT: ("Override DLSSG multi-frame count", count),
                                           ID_MFG_DYN_MAX: ("Override maximum DLSSG dynamic multi frame count", dyn)})


def _import_verified(npi_exe, nip, expect):
    """Importe `nip` puis RE-EXPORTE pour vérifier. expect = {profil: (count, dyn)}. Retourne (ok, détail)."""
    r = subprocess.run([npi_exe, "-silentImport", nip], timeout=30,
                       cwd=os.path.dirname(npi_exe), creationflags=_NO_WINDOW)
    text = _export_text(npi_exe)
    if not text:
        return False, "relecture des profils impossible"
    for prof, (cnt, dyn) in expect.items():
        got = (_profile_dword(text, prof, ID_MFG_COUNT), _profile_dword(text, prof, ID_MFG_DYN_MAX))
        if got != (cnt, dyn):
            return False, f"« {prof} » vaut {got} au lieu de {(cnt, dyn)} (code NPI {r.returncode})"
    return True, ""


def _load_prev(path):
    """mfg_prev.json -> {"profiles": {...}} ; un fichier absent donne {}, un fichier corrompu est mis de côté."""
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict) and isinstance(d.get("profiles"), dict):
            return d
    except (OSError, ValueError):
        pass
    try:
        os.replace(path, path + ".corrupt")
    except OSError:
        pass
    return {}


def _save_prev(path, data):
    tmp = path + ".part"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, path)


def unlock_mfg(npi_exe, out_dir, generated=5, exe_name=None):
    """Impose au pilote le multiplicateur `generated`+1 (5 = 6X, 1 = 2X) pour CE jeu.

    La clé « Override DLSSG multi-frame count » est une valeur DEMANDÉE au plugin (le menu du jeu est ignoré),
    pas un plafond. On l'écrit dans le profil du jeu s'il existe, SANS toucher au « Base Profile » (qui
    s'applique à tous les autres jeux) ; faute de profil du jeu, repli sur le Base Profile.
    Mémorise l'état d'origine par profil + les jeux demandeurs dans mfg_prev.json (origine jamais écrasée).
    Vérifie par relecture. Retourne (ok, message). 'NEED_ADMIN' si pas élevé.
    """
    if not npi_exe or not os.path.isfile(npi_exe):
        return False, "nvidiaProfileInspector.exe introuvable."
    if not is_admin():
        return False, "NEED_ADMIN : nvidiaProfileInspector exige les droits admin."
    generated = max(1, min(5, int(generated)))
    try:
        os.makedirs(out_dir, exist_ok=True)
        text = _export_text(npi_exe)
        if not text:
            return False, "Export NVIDIA vide, rien modifié."
        profiles = _parse_profiles_text(text)
        targets = []
        if exe_name:
            e = exe_name.lower()
            targets = [(n, exe_name) for n, exes in profiles if e in exes]
        if not targets and exe_name:
            # Jamais de repli sur le profil GLOBAL quand on cible un jeu : le x6 serait imposé à tous les autres jeux.
            return False, (f"Profil NVIDIA introuvable pour {exe_name} : active d'abord « Panneau NVIDIA » "
                           "(il crée le profil du jeu), puis réessaie.")
        if not targets:
            targets = [(_global_name(profiles), None)]
        prev_path = os.path.join(out_dir, "mfg_prev.json")
        prev = _load_prev(prev_path)
        saved = prev.setdefault("profiles", {})
        for n, exe in targets:     # l'origine n'est mémorisée qu'une fois ; on cumule les jeux demandeurs
            ent = saved.setdefault(n, {"count": _profile_dword(text, n, ID_MFG_COUNT),
                                       "dyn": _profile_dword(text, n, ID_MFG_DYN_MAX), "exe": exe, "games": []})
            if exe_name and exe_name.lower() not in [g.lower() for g in ent.setdefault("games", [])]:
                ent["games"].append(exe_name)
        _save_prev(prev_path, prev)
        nip = os.path.join(out_dir, "yogomfg_mfg_apply.nip")
        with open(nip, "w", encoding="utf-16") as f:
            f.write(_wrap("".join(_mfg_block(text, n, e, generated, generated) for n, e in targets)))
        ok, why = _import_verified(npi_exe, nip, {n: (generated, generated) for n, _ in targets})
    except (OSError, subprocess.SubprocessError) as ex:
        return False, f"Multiplicateur pilote : {ex}"
    if not ok:
        return False, "Multiplicateur pilote NON appliqué : " + why
    return True, f"Multiplicateur imposé par le pilote = {generated + 1}X dans : " + ", ".join(n for n, _ in targets) + "."


def restore_mfg(npi_exe, out_dir, exe_name=None):
    """Retire l'override YogoMFG. Avec `exe_name` : seulement pour ce jeu (le profil n'est remis à l'origine
    que quand plus aucun jeu YogoMFG ne l'utilise). Sans : tout. Sauvegarde supprimée après vérification.

    Une clé absente à l'origine ne peut pas être supprimée par un .nip : on remet la valeur héritée du
    Base Profile si elle existe, sinon 4X (valeur NVIDIA).
    """
    prev_path = os.path.join(out_dir, "mfg_prev.json")
    prev = _load_prev(prev_path)
    allsaved = prev.get("profiles", {})
    if not allsaved:
        return False, "Aucun override pilote YogoMFG à retirer."
    if not npi_exe or not os.path.isfile(npi_exe):
        return False, "nvidiaProfileInspector.exe introuvable."
    try:
        e = (exe_name or "").lower()
        to_restore, keep, changed = {}, {}, False
        for n, o in allsaved.items():
            games = [g for g in o.get("games", [])]
            if not e:
                to_restore[n] = o
                continue
            mine = e in [g.lower() for g in games] or (not games and (o.get("exe") or "").lower() == e)
            if not mine:
                keep[n] = o
                continue
            left = [g for g in games if g.lower() != e]
            if left:                                  # un autre jeu YogoMFG utilise encore ce profil
                o["games"] = left
                keep[n] = o
                changed = True
            else:
                to_restore[n] = o
        if not to_restore:
            if changed:
                _save_prev(prev_path, {"profiles": keep})
                return True, "Override pilote retiré pour ce jeu (profil partagé conservé pour les autres)."
            return False, "Aucun override pilote YogoMFG à retirer pour ce jeu."
        if not is_admin():
            return False, "NEED_ADMIN : nvidiaProfileInspector exige les droits admin."
        text = _export_text(npi_exe)
        if not text:
            return False, "Export NVIDIA vide, rien modifié."     # sinon le profil serait réécrit avec seulement 2 clés
        inherited = (_profile_dword(text, _global_name(_parse_profiles_text(text)), ID_MFG_COUNT),
                     _profile_dword(text, _global_name(_parse_profiles_text(text)), ID_MFG_DYN_MAX)) if text else (None, None)
        expect, blocks, absent = {}, [], False
        for n, o in to_restore.items():
            cnt, dyn = o.get("count"), o.get("dyn")
            if cnt is None or dyn is None:
                absent = True
            cnt = cnt if cnt is not None else (inherited[0] if inherited[0] is not None else MFG_STOCK)
            dyn = dyn if dyn is not None else (inherited[1] if inherited[1] is not None else MFG_STOCK)
            expect[n] = (cnt, dyn)
            blocks.append(_mfg_block(text, n, o.get("exe"), cnt, dyn))
        nip = os.path.join(out_dir, "yogomfg_mfg_revert.nip")
        with open(nip, "w", encoding="utf-16") as f:
            f.write(_wrap("".join(blocks)))
        ok, why = _import_verified(npi_exe, nip, expect)
        if not ok:
            return False, "Restauration NON vérifiée (sauvegarde conservée) : " + why
        if keep:
            _save_prev(prev_path, {"profiles": keep})
        else:
            os.remove(prev_path)
    except (OSError, ValueError, subprocess.SubprocessError) as ex:
        return False, f"Restauration échouée: {ex}"
    return True, "Override pilote retiré, valeur d'origine remise" + (
        " (clé absente à l'origine : non supprimable, valeur héritée du profil global)." if absent else ".")
