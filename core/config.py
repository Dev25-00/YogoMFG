"""config.json : réglages globaux + override par jeu (appid)."""
import os, sys, json
from core import inimaker

# écrivable : %LOCALAPPDATA%\YogoMFG si gelé (PyInstaller onefile), sinon racine du projet.
if getattr(sys, "frozen", False):
    _BASE = os.path.join(os.environ.get("LOCALAPPDATA") or os.path.dirname(sys.executable), "YogoMFG")
    os.makedirs(_BASE, exist_ok=True)
else:
    _BASE = os.path.dirname(os.path.dirname(__file__))
_PATH = os.path.join(_BASE, "config.json")


def load():
    try:
        return json.load(open(_PATH, encoding="utf-8"))
    except (OSError, ValueError):
        return {"global": inimaker.default_cfg(), "per_game": {}, "npi_exe": "", "proxy": "version.dll"}


def save(cfg):
    """Écriture atomique (fichier temporaire puis remplacement) : jamais de config.json tronqué. False si échec."""
    tmp = _PATH + ".part"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        os.replace(tmp, _PATH)
        return True
    except OSError:
        return False


def for_game(cfg, appid):
    """Override par jeu s'il existe, sinon la config globale."""
    return cfg["per_game"].get(appid, cfg["global"])
