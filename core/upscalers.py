"""Détecte et met à jour les DLL d'upscaling dans un jeu (NVIDIA/AMD/Intel).

On NE télécharge PAS en silence (ToS + fragilité des sources). On :
  - détecte les DLL présentes + leur version,
  - ouvre la page de téléchargement officielle (TechPowerUp),
  - remplace une DLL par un fichier fourni par l'utilisateur (avec backup .yogobak).
"""
import os, re, shutil, subprocess

# nom de fichier (minuscule) -> (marque, rôle)
KNOWN = {
    "nvngx_dlss.dll":      ("NVIDIA", "DLSS Super Resolution"),
    "nvngx_dlssg.dll":     ("NVIDIA", "DLSS Frame Generation"),
    "nvngx_dlssd.dll":     ("NVIDIA", "DLSS Ray Reconstruction"),
    "libxess.dll":         ("Intel",  "XeSS Super Resolution"),
    "libxess_fg.dll":      ("Intel",  "XeSS Frame Generation"),
    "amd_fidelityfx_dx12.dll": ("AMD", "FSR 3 (DX12)"),
    "amd_fidelityfx_vk.dll":   ("AMD", "FSR 3 (Vulkan)"),
    "amdxcffx64.dll":      ("AMD",    "FSR 4"),
    "ffx_fsr2_api_dx12.dll": ("AMD",  "FSR 2 (DX12)"),
}

DOWNLOAD = {
    "NVIDIA": "https://www.techpowerup.com/download/nvidia-dlss-dll/",
    "Intel":  "https://www.techpowerup.com/download/intel-xess-dll/",
    "AMD":    "https://www.techpowerup.com/download/amd-fidelityfx-super-resolution-dll/",
}

# CDN fiable et maintenu : manifeste DLSS Swapper (open-source). Liste toutes les versions
# DLSS/FSR/XeSS + URL de téléchargement (ZIP) + md5. Vérifié en direct.
MANIFEST_URL = "https://dlss-swapper-downloads.beeradmoore.com/manifest.json"
# nom de DLL du jeu -> clé du manifeste
MANIFEST_KEY = {
    "nvngx_dlss.dll": "dlss", "nvngx_dlssg.dll": "dlss_g", "nvngx_dlssd.dll": "dlss_d",
    "libxess.dll": "xess", "libxess_fg.dll": "xess_fg",
    "amd_fidelityfx_dx12.dll": "fsr_31_dx12", "amd_fidelityfx_vk.dll": "fsr_31_vk",
}
_UA = "Mozilla/5.0"   # le CDN refuse Python-urllib ; UA navigateur requis


def _get(url, timeout=20):
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    return urllib.request.urlopen(req, timeout=timeout).read()


def _cache_dir():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    d = os.path.join(base, "YogoMFG", "_cache")
    os.makedirs(d, exist_ok=True)
    return d


_FAIL_TS = 0.0   # dernier échec réseau : évite d'attendre le timeout à chaque changement de jeu hors ligne


def _valid_manifest(d):
    return isinstance(d, dict) and any(k in d for k in MANIFEST_KEY.values())


def _manifest_json(url, ttl=6 * 3600):
    """Manifeste en cache disque (6 h) : démarrage instantané ; repli sur le cache périmé si hors ligne."""
    global _FAIL_TS
    import json, time
    path = os.path.join(_cache_dir(), "manifest.json")

    def disk():
        try:
            with open(path, encoding="utf-8") as f:
                d = json.load(f)
            return d if _valid_manifest(d) else {}
        except (OSError, ValueError):
            return {}

    try:
        if time.time() - os.path.getmtime(path) < ttl and disk():
            return disk()
    except OSError:
        pass
    if time.time() - _FAIL_TS < 300:      # hors ligne récemment : cache périmé sans retenter
        return disk()
    try:
        raw = _get(url, timeout=8).decode("utf-8")
        d = json.loads(raw)
        if not _valid_manifest(d):
            raise ValueError("manifeste inattendu")
        tmp = path + ".part"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(raw)
        os.replace(tmp, path)
        return d
    except Exception:
        _FAIL_TS = time.time()
        return disk()


def latest(manifest_url=MANIFEST_URL):
    """Retourne {dllname: {version, url, md5}} = dernière version par DLL. {} si injoignable."""
    d = _manifest_json(manifest_url)
    out = {}
    for dll, key in MANIFEST_KEY.items():
        lst = d.get(key) or []
        if lst:
            e = lst[-1]   # trié croissant -> dernier = plus récent
            out[dll] = {"version": e.get("version", "?"),
                        "url": e.get("download_url", ""), "md5": (e.get("md5_hash") or "").lower()}
    return out


def install_latest(dll_path, manifest=None, manifest_url=MANIFEST_URL):
    """Télécharge la dernière DLL (ZIP DLSS Swapper), extrait, vérifie le md5, installe (backup).
    Retourne (ok, message)."""
    import tempfile, zipfile, io, hashlib
    man = manifest if manifest is not None else latest(manifest_url)
    name = os.path.basename(dll_path).lower()
    entry = man.get(name)
    if not entry or not entry.get("url"):
        return False, f"Pas de version en ligne pour {name}."
    try:
        # cache disque par version : une DLL déjà téléchargée et vérifiée s'installe instantanément
        safe_ver = re.sub(r"[^\w.\-]", "_", str(entry.get("version") or "x"))   # version vient du réseau
        cached = os.path.join(_cache_dir(), f"{safe_ver}-{name}")
        data = None
        if entry.get("md5") and os.path.isfile(cached):     # sans md5 on ne fait PAS confiance au cache
            with open(cached, "rb") as f:
                data = f.read()
            if hashlib.md5(data).hexdigest().lower() != entry["md5"]:
                data = None
        if data is None:
            zf = zipfile.ZipFile(io.BytesIO(_get(entry["url"], timeout=60)))
            member = next((m for m in zf.namelist() if m.lower().endswith(name)), None)
            if not member:
                return False, "DLL absente du ZIP téléchargé."
            data = zf.read(member)
            if entry.get("md5") and hashlib.md5(data).hexdigest().lower() != entry["md5"]:
                return False, "Intégrité (md5) invalide, installation annulée."
            if entry.get("md5"):
                with open(cached + ".part", "wb") as f:       # écriture atomique : jamais de DLL tronquée en cache
                    f.write(data)
                os.replace(cached + ".part", cached)
        tmp = os.path.join(tempfile.gettempdir(), os.path.basename(dll_path))
        with open(tmp, "wb") as f:
            f.write(data)
        msg = swap(dll_path, tmp)
        return True, f"{msg} → v{entry.get('version', '?')} (DLSS Swapper)"
    except Exception as e:
        return False, f"Téléchargement échoué: {e}"


def _version(path):
    """Version du DLL via l'API Windows (fiable). Ex: '3.7.20.0'. '?' si absent."""
    import ctypes
    from ctypes import wintypes, byref, c_uint, c_void_p
    try:
        ver = ctypes.windll.version
        size = ver.GetFileVersionInfoSizeW(ctypes.c_wchar_p(path), None)
        if not size:
            return "?"
        buf = ctypes.create_string_buffer(size)
        if not ver.GetFileVersionInfoW(ctypes.c_wchar_p(path), 0, size, buf):
            return "?"
        r, ln = c_void_p(), c_uint()
        if not ver.VerQueryValueW(buf, ctypes.c_wchar_p("\\"), byref(r), byref(ln)) or not r.value:
            return "?"
        import struct
        data = ctypes.string_at(r.value, ln.value)
        _, _, fvms, fvls = struct.unpack("<LLLL", data[:16])
        return f"{fvms >> 16}.{fvms & 0xFFFF}.{fvls >> 16}.{fvls & 0xFFFF}"
    except Exception:
        return "?"


def restore(dll_path):
    """Restaure le DLL d'origine depuis .yogobak. Retourne message."""
    bak = dll_path + ".yogobak"
    if not os.path.isfile(bak):
        raise FileNotFoundError("Aucune sauvegarde (.yogobak) pour ce DLL.")
    shutil.copy2(bak, dll_path)
    return f"Restauré {os.path.basename(dll_path)} (version d'origine du jeu)."


def has_backup(dll_path):
    return os.path.isfile(dll_path + ".yogobak")


def library_match(dll_name, lib_dir):
    """Cherche dll_name dans une bibliothèque locale de DLL. Retourne (path, version) ou None."""
    if not lib_dir or not os.path.isdir(lib_dir):
        return None
    for dp, _, files in os.walk(lib_dir):
        for f in files:
            if f.lower() == dll_name.lower():
                p = os.path.join(dp, f)
                return (p, _version(p))
    return None


def scan(game_dir):
    """Liste des upscalers trouvés: [{name, vendor, role, version, path}]."""
    out, seen = [], set()
    for dp, _, files in os.walk(game_dir):
        if dp.count(os.sep) - game_dir.count(os.sep) > 4:
            continue
        for f in files:
            low = f.lower()
            if low in KNOWN and low not in seen:
                seen.add(low)
                p = os.path.join(dp, f)
                vendor, role = KNOWN[low]
                out.append({"name": f, "vendor": vendor, "role": role,
                            "version": _version(p), "path": p})
    return out


def swap(dll_path, new_dll):
    """Remplace dll_path par new_dll. Backup .yogobak si absent. Retourne message."""
    if os.path.basename(new_dll).lower() != os.path.basename(dll_path).lower():
        raise ValueError("Le nom du DLL fourni ne correspond pas à la cible.")
    bak = dll_path + ".yogobak"
    if os.path.isfile(dll_path) and not os.path.isfile(bak):
        shutil.copy2(dll_path, bak)
    shutil.copy2(new_dll, dll_path)
    return f"Remplacé {os.path.basename(dll_path)} (backup: {os.path.basename(bak)})"
