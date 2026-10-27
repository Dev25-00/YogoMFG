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


_UA = {"User-Agent": "Mozilla/5.0"}


def _download(url, dest, timeout=8):
    """Télécharge `url` vers `dest` (écriture atomique). True si on a obtenu une vraie image."""
    import urllib.request
    import threading
    tmp = f"{dest}.{threading.get_ident()}.part"           # nom unique : deux threads ne se marchent plus dessus
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=_UA), timeout=timeout) as r, open(tmp, "wb") as f:
            f.write(r.read())
        with open(tmp, "rb") as f:
            head = f.read(4)
        if os.path.getsize(tmp) > 1000 and head[:2] in (b"\xff\xd8", b"\x89P"):      # JPEG ou PNG
            os.replace(tmp, dest)
            return True
    except Exception:
        pass
    try:
        os.remove(tmp)
    except OSError:
        pass
    return False


def _store_api_cover(appid):
    """URL de jaquette via l'API officielle du magasin Steam (les jeux récents ont des liens à hash)."""
    import json, urllib.parse, urllib.request
    q = json.dumps({"ids": [{"appid": int(appid)}], "context": {"language": "english", "country_code": "US"},
                    "data_request": {"include_assets": True}})
    u = "https://api.steampowered.com/IStoreBrowseService/GetItems/v1?input_json=" + urllib.parse.quote(q)
    try:
        d = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=_UA), timeout=8).read())
        a = d["response"]["store_items"][0]["assets"]
        for key in ("library_capsule", "library_capsule_2x"):
            if a.get(key):
                return ("https://shared.cloudflare.steamstatic.com/store_item_assets/"
                        + a["asset_url_format"].replace("${FILENAME}", a[key]))
    except Exception:
        pass
    return None


def _local_cover(appid):
    """Jaquette déjà présente dans le cache de la bibliothèque Steam (hors ligne, instantané)."""
    try:
        root = os.path.join(steam_path(), "appcache", "librarycache", str(appid))
    except Exception:
        return None
    best = None
    for dp, _, files in os.walk(root):
        for f in files:
            low = f.lower()
            rank = 0 if low == "library_600x900.jpg" else 1 if low == "library_capsule.jpg" else None
            if rank is not None and (best is None or rank < best[0]):
                best = (rank, os.path.join(dp, f))
    return best[1] if best else None


def _banner_to_card(path):
    """Image paysage (header) -> carte portrait 600x900 sombre avec la bannière au centre."""
    from PIL import Image
    im = Image.open(path).convert("RGB")
    if im.width <= im.height * 0.9:
        return
    card = Image.new("RGB", (600, 900), (31, 31, 39))
    h = round(im.height * 600 / im.width)
    card.paste(im.resize((600, h)), (0, (900 - h) // 2))
    card.save(path + ".card", "JPEG", quality=90)
    os.replace(path + ".card", path)                      # jamais d'image à moitié écrite dans le cache


def fetch_cover(appid, dest):
    """Jaquette dans `dest` (cache) avec secours en cascade. Retourne dest ou None.

    Ordre : cache disque -> API du magasin Steam (liens à hash, jeux récents) -> anciens liens CDN
    -> cache local de la bibliothèque Steam -> bannière header recadrée en carte. Un échec total est
    mémorisé 12 h (`dest.none`) pour ne pas retélécharger à chaque ouverture.
    """
    import shutil, time
    if os.path.isfile(dest) and os.path.getsize(dest) > 1000:
        return dest
    none = dest + ".none"
    try:
        if time.time() - os.path.getmtime(none) < 12 * 3600:
            return None
    except OSError:
        pass
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    loc = _local_cover(appid)
    if loc:
        try:
            shutil.copyfile(loc, dest + ".part")
            os.replace(dest + ".part", dest)
            return dest
        except OSError:
            pass
    urls = []
    api = _store_api_cover(appid)
    if api:
        urls.append(api)
    urls += [f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/library_600x900.jpg",
             f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/library_600x900.jpg",
             f"https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps/{appid}/library_600x900.jpg"]
    for u in urls:
        if _download(u, dest):
            return dest
    if _download(f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/header.jpg", dest):
        try:
            _banner_to_card(dest)
        except Exception:
            pass
        return dest
    try:
        open(none, "w").close()
    except OSError:
        pass
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


def game_from_dir(d):
    """Un jeu isolé (dossier choisi à la main) -> même structure que games()."""
    d = os.path.normpath(d)
    return {"appid": "manual:" + d, "name": os.path.basename(d), "dir": d, "exes": _render_exes(d)}


def games_in(folder):
    """Jeux d'un dossier ajouté à la main : chaque sous-dossier avec un .exe = un jeu ; sinon le dossier lui-même."""
    out = []
    try:
        names = sorted(os.listdir(folder))
    except OSError:
        return out
    noise = ("unins", "crashreport", "setup", "redist", "vcredist")
    if any(n.lower().endswith(".exe") and not any(x in n.lower() for x in noise) for n in names):
        g = game_from_dir(folder)            # le dossier est lui-même un jeu : ses sous-dossiers ne sont pas d'autres jeux
        return [g] if g["exes"] else out
    subs = [os.path.join(folder, n) for n in names]
    for sd in subs:
        if os.path.isdir(sd):
            g = game_from_dir(sd)
            if g["exes"]:
                out.append(g)
    if not out:
        g = game_from_dir(folder)
        if g["exes"]:
            out.append(g)
    return out
