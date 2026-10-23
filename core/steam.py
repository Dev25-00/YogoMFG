"""Liste les jeux Steam. Parse libraryfolders.vdf + appmanifest_*.acf. Lecture seule."""
import os, re, glob, winreg


def steam_path():
    for root, key in ((winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"),
                      (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")):
        try:
            with winreg.OpenKey(root, key) as k:
                for name in ("SteamPath", "InstallPath"):
                    try:
                        return os.path.normpath(winreg.QueryValueEx(k, name)[0])
                    except FileNotFoundError:
                        pass
        except OSError:
            pass
    return r"C:\Program Files (x86)\Steam"


def _libraries(sp):
    vdf = os.path.join(sp, "steamapps", "libraryfolders.vdf")
    libs = {os.path.join(sp, "steamapps")}
    try:
        txt = open(vdf, encoding="utf-8", errors="ignore").read()
        for p in re.findall(r'"path"\s*"([^"]+)"', txt):
            libs.add(os.path.join(p.replace("\\\\", "\\"), "steamapps"))
    except OSError:
        pass
    return libs


def _render_exes(game_dir):
    """Exes candidats au moteur de rendu, tri par taille desc, bruit filtré."""
    noise = ("unins", "crashreport", "launcher", "setup", "redist", "vcredist",
             "dxsetup", "touchup", "benchmark", "config", "eac", "battleye")
    hits = []
    for dp, _, files in os.walk(game_dir):
        if dp.count(os.sep) - game_dir.count(os.sep) > 3:
            continue
        for f in files:
            if f.lower().endswith(".exe") and not any(n in f.lower() for n in noise):
                fp = os.path.join(dp, f)
                try:
                    hits.append((os.path.getsize(fp), fp))
                except OSError:
                    pass
    hits.sort(reverse=True)
    return [fp for _, fp in hits]


def cover_url(appid):
    """Jaquette verticale Steam (600x900) depuis le CDN."""
    return f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/library_600x900.jpg"


def fetch_cover(appid, dest):
    """Télécharge la jaquette dans dest (cache). Retourne dest ou None."""
    import urllib.request
    if os.path.isfile(dest) and os.path.getsize(dest) > 1000:
        return dest
    try:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        req = urllib.request.Request(cover_url(appid), headers={"User-Agent": "YogoMFG"})
        with urllib.request.urlopen(req, timeout=10) as r, open(dest, "wb") as f:
            f.write(r.read())
        return dest if os.path.getsize(dest) > 1000 else None
    except Exception:
        return None


def games():
    """Liste [{appid, name, dir, exes[]}] triée par nom."""
    sp = steam_path()
    out, seen = [], set()
    for lib in _libraries(sp):
        for acf in glob.glob(os.path.join(lib, "appmanifest_*.acf")):
            try:
                t = open(acf, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            appid = re.search(r'"appid"\s*"(\d+)"', t)
            name = re.search(r'"name"\s*"([^"]+)"', t)
            inst = re.search(r'"installdir"\s*"([^"]+)"', t)
            if not (appid and name and inst):
                continue
            if appid.group(1) in seen:
                continue
            gdir = os.path.join(lib, "common", inst.group(1))
            if not os.path.isdir(gdir):
                continue
            seen.add(appid.group(1))
            out.append({"appid": appid.group(1), "name": name.group(1),
                        "dir": gdir, "exes": _render_exes(gdir)})
    out.sort(key=lambda g: g["name"].lower())
    return out
