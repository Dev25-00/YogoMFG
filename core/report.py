"""Rapport de test : un .zip que le testeur peut envoyer pour aider à corriger un problème.

Contient l'INI du mod, les derniers logs (mod + mesure image par image + sonde), un résumé de la machine et de
l'installation. Les chemins personnels (dossier utilisateur) sont remplacés par USER. Rien n'est envoyé
automatiquement : l'utilisateur choisit où enregistrer le fichier et à qui l'envoyer.
"""
import os, re, glob, zipfile, platform, subprocess, datetime

_MAX = 2 * 1024 * 1024     # un fichier de log est tronqué à ses 2 derniers Mo (le zip reste léger à envoyer)
_NO_WINDOW = 0x08000000


def _clean(text):
    home = os.path.expanduser("~")
    user = os.path.basename(home)
    for h in (home, home.replace("\\", "\\\\"), home.replace("\\", "/")):
        text = re.sub(re.escape(h), "USER", text, flags=re.I)        # insensible à la casse
    if len(user) >= 3:
        text = re.sub(r"(?i)(Users[\\/]+)" + re.escape(user), r"\1USER", text)
    return text


def _read_tail(path):
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as f:
            if size > _MAX:
                f.seek(size - _MAX)
            return _clean(f.read().decode("utf-8", errors="ignore"))
    except OSError:
        return ""


def _smi():
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=name,driver_version,memory.total,pcie.link.gen.current,"
                              "pcie.link.width.current,pcie.link.width.max,power.limit", "--format=csv"],
                             capture_output=True, text=True, timeout=10, creationflags=_NO_WINDOW)
        return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "nvidia-smi indisponible"


def build(zip_path, info, exe_path, data_dir, extra_lines=None):
    """Écrit le zip. info = dict de la machine/appli (voir yogomfg._report_info). Retourne la liste des fichiers inclus."""
    game_dir = os.path.dirname(exe_path) if exe_path else ""
    logs = os.path.join(game_dir, "dlssg_sm86", "logs") if game_dir else ""
    added = []
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        lines = [f"Rapport YogoMFG — {datetime.datetime.now():%Y-%m-%d %H:%M}", "",
                 f"Windows : {platform.platform()}", "", "[Application]"]
        lines += [f"{k} : {v}" for k, v in info.items()]
        lines += ["", "[GPU / nvidia-smi]", _smi()]
        if extra_lines:
            lines += ["", "[Analyse]"] + list(extra_lines)
        z.writestr("resume.txt", _clean("\n".join(str(x) for x in lines)))
        added.append("resume.txt")
        ini = os.path.join(game_dir, "dlssg_sm86.ini") if game_dir else ""
        if ini and os.path.isfile(ini):
            z.writestr("dlssg_sm86.ini", _read_tail(ini))
            added.append("dlssg_sm86.ini")
        def mtime(path):
            try:
                return os.path.getmtime(path)
            except OSError:
                return 0
        for pat in ("loader_*.jsonl", "backend_*.jsonl", "frames_*.jsonl") if logs else ():
            # glob.escape : un dossier de jeu « Game [GOTY] » ne doit pas être lu comme un motif
            for p in sorted(glob.glob(os.path.join(glob.escape(logs), pat)), key=mtime)[-2:]:
                z.writestr("logs/" + os.path.basename(p), _read_tail(p))
                added.append("logs/" + os.path.basename(p))
        probe = os.path.join(data_dir, "probe_last.csv")
        if os.path.isfile(probe):
            z.writestr("probe_last.csv", _read_tail(probe))
            added.append("probe_last.csv")
    return added
