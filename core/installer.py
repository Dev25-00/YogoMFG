"""Pose/retire les fichiers du mod à côté du .exe de rendu."""
import os, shutil

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
    """Retire les fichiers du mod, restaure la DLL d'origine si backup présent."""
    dst = os.path.dirname(exe_path)
    acts = []
    bak = os.path.join(dst, proxy + ".yogobak")
    p = os.path.join(dst, proxy)
    if os.path.isfile(bak):
        shutil.copy2(bak, p); os.remove(bak); acts.append(f"restauré {proxy}")
    elif os.path.isfile(p):
        os.remove(p); acts.append(f"supprimé {proxy}")
    for f in ("dlssg_sm86.ini",):
        fp = os.path.join(dst, f)
        if os.path.isfile(fp):
            os.remove(fp); acts.append(f"supprimé {f}")
    fd = os.path.join(dst, "dlssg_sm86")
    if os.path.isdir(fd):
        shutil.rmtree(fd, ignore_errors=True); acts.append("supprimé dlssg_sm86\\")
    return acts
