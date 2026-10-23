"""Détecte et met à jour les DLL d'upscaling dans un jeu (NVIDIA/AMD/Intel).

On NE télécharge PAS en silence (ToS + fragilité des sources). On :
  - détecte les DLL présentes + leur version,
  - ouvre la page de téléchargement officielle (TechPowerUp),
  - remplace une DLL par un fichier fourni par l'utilisateur (avec backup .yogobak).
"""
import os, shutil, subprocess

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


def latest(manifest_url=MANIFEST_URL):
    """Retourne {dllname: {version, url, md5}} = dernière version par DLL. {} si injoignable."""
    import json
    try:
        d = json.loads(_get(manifest_url).decode("utf-8"))
    except Exception:
        return {}
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
        zbytes = _get(entry["url"], timeout=60)
        zf = zipfile.ZipFile(io.BytesIO(zbytes))
        member = next((m for m in zf.namelist() if m.lower().endswith(name)), None)
        if not member:
            return False, "DLL absente du ZIP téléchargé."
        data = zf.read(member)
        if entry.get("md5") and hashlib.md5(data).hexdigest().lower() != entry["md5"]:
            return False, "Intégrité (md5) invalide, installation annulée."
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
