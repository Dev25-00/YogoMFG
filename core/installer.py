"""Pose/retire les fichiers du mod à côté du .exe de rendu.

Le mod installé est « dlssg_for_sm86 / SM75 » de sdli1995 (https://github.com/sdli1995/dlssg_for_sm86, MIT).
"""
import os, re, shutil

PROXIES = ("version.dll", "dxgi.dll", "d3d12.dll", "dinput8.dll", "winmm.dll", "dbghelp.dll")


def _src(mod_root, proxy):
    """version.dll est à la racine; les autres dans alternatives/."""
    return os.path.join(mod_root, proxy if proxy == "version.dll"
                        else os.path.join("alternatives", proxy))


def install(mod_root, exe_path, ini_text, proxy="version.dll"):
    """Copie proxy + ini généré + dossier dlssg_sm86\\ dans le dossier du .exe.
    Sauvegarde toute DLL homonyme en .yogobak. Retourne liste des actions."""
    dst = os.path.dirname(exe_path)
    src_proxy = _src(mod_root, proxy)
    src_folder = os.path.join(mod_root, "dlssg_sm86")
    if not os.path.isfile(src_proxy):
        raise FileNotFoundError(src_proxy)
    if not os.path.isdir(src_folder):
        raise FileNotFoundError(src_folder)

    acts = []
    dst_proxy = os.path.join(dst, proxy)
    if os.path.isfile(dst_proxy) and not os.path.isfile(dst_proxy + ".yogobak"):
        shutil.copy2(dst_proxy, dst_proxy + ".yogobak")  # backup DLL d'origine
        acts.append(f"backup {proxy} -> {proxy}.yogobak")
    shutil.copy2(src_proxy, dst_proxy)
    acts.append(f"copie {proxy}")

    with open(os.path.join(dst, "dlssg_sm86.ini"), "w", encoding="utf-8") as f:
        f.write(ini_text)
    acts.append("écrit dlssg_sm86.ini")

    dst_folder = os.path.join(dst, "dlssg_sm86")
    if os.path.isdir(dst_folder):
        shutil.rmtree(dst_folder, ignore_errors=True)
    shutil.copytree(src_folder, dst_folder)
    acts.append("copie dlssg_sm86\\")
    return acts


def uninstall(exe_path, proxy="version.dll"):
    """Retire les fichiers du mod, restaure la DLL d'origine si backup présent.

    SÉCURITÉ : une DLL proxy SANS .yogobak n'est supprimée que si le mod est bien
    présent (dlssg_sm86.ini ou dossier dlssg_sm86\\). Sinon on ne touche pas au proxy
    — c'est peut-être la DLL du jeu ou d'un autre mod.
    """
    dst = os.path.dirname(exe_path)
    acts = []
    ini = os.path.join(dst, "dlssg_sm86.ini")
    fd = os.path.join(dst, "dlssg_sm86")
    mod_present = os.path.isfile(ini) or os.path.isdir(fd)
    bak = os.path.join(dst, proxy + ".yogobak")
    p = os.path.join(dst, proxy)
    if os.path.isfile(bak):
        shutil.copy2(bak, p); os.remove(bak); acts.append(f"restauré {proxy}")
    elif mod_present and os.path.isfile(p):
        os.remove(p); acts.append(f"supprimé {proxy}")
    if os.path.isfile(ini):
        os.remove(ini); acts.append("supprimé dlssg_sm86.ini")
    if os.path.isdir(fd):
        shutil.rmtree(fd, ignore_errors=True); acts.append("supprimé dlssg_sm86\\")
    return acts or ["rien à retirer (mod non détecté ici)"]


def status(exe_path, hint=None):
    """État de l'installation YogoMFG à côté du .exe (lecture seule, instantané).

    {installed, mult, proxy, backups[]} ; installed = ini ou dossier dlssg_sm86/ présent.
    `hint` = proxy appliqué la dernière fois (config) pour nommer la bonne DLL.
    """
    dst = os.path.dirname(exe_path) if exe_path else ""
    ini = os.path.join(dst, "dlssg_sm86.ini")
    installed = bool(dst) and (os.path.isfile(ini) or os.path.isdir(os.path.join(dst, "dlssg_sm86")))
    mult = None
    if installed and os.path.isfile(ini):
        try:
            with open(ini, encoding="utf-8", errors="ignore") as f:
                m = re.search(r"^MaxGeneratedFrames\s*=\s*(\d+)", f.read(), re.M)
            mult = int(m.group(1)) + 1 if m else None
        except OSError:
            pass
    backups = [p for p in PROXIES if dst and os.path.isfile(os.path.join(dst, p + ".yogobak"))]
    present = [p for p in PROXIES if dst and os.path.isfile(os.path.join(dst, p))]
    proxy = hint if hint in present else next(iter(backups or present), None)
    return {"installed": installed, "mult": mult, "proxy": proxy if installed else None, "backups": backups}


_MARK = "; Généré par YogoMFG"


def _read(path):
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            return f.read()
    except OSError:
        return ""


def check_apply(mod_root, exe_path, proxy="version.dll", applied_proxy=None):
    """Peut-on (ré)appliquer ici sans rien casser ? Retourne (ok, code, détail).

    codes : ok | foreign_ini (config modifiée à la main, pas écrasée) | other_proxy (déjà installé avec une autre DLL)
            | locked (fichier utilisé : jeu lancé).
    Une config générée par YogoMFG, ou identique à celle d'usine du mod, est écrasable.
    """
    dst = os.path.dirname(exe_path)
    ini = os.path.join(dst, "dlssg_sm86.ini")
    if os.path.isfile(ini):
        txt = _read(ini).replace("\r\n", "\n").strip()
        factory = _read(os.path.join(mod_root, "dlssg_sm86.ini")).replace("\r\n", "\n").strip()
        if not (txt.startswith(_MARK) or (factory and txt == factory)):
            return False, "foreign_ini", ""
    if (applied_proxy and applied_proxy != proxy and os.path.isfile(os.path.join(dst, applied_proxy))
            and status(exe_path)["installed"]):          # sans installation, un vieux « applied » ne bloque rien
        return False, "other_proxy", applied_proxy
    for rel in (proxy, "dlssg_sm86.ini", os.path.join("dlssg_sm86", "backend", "sm86_backend.dll")):
        p = os.path.join(dst, rel)
        if os.path.isfile(p):
            try:
                open(p, "r+b").close()
            except PermissionError:
                return False, "locked", os.path.basename(rel)
            except OSError:
                pass
    return True, "ok", ""
