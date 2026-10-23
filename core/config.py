"""config.json : réglages globaux + override par jeu (appid)."""
import os, sys, json
from core import inimaker

# écrivable : à côté du .exe si gelé (PyInstaller), sinon racine du projet.
_BASE = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) \
    else os.path.dirname(os.path.dirname(__file__))
_PATH = os.path.join(_BASE, "config.json")


def load():
    try:
        return json.load(open(_PATH, encoding="utf-8"))
    except (OSError, ValueError):
        return {"global": inimaker.default_cfg(), "per_game": {}, "npi_exe": "", "proxy": "version.dll"}


def save(cfg):
    json.dump(cfg, open(_PATH, "w", encoding="utf-8"), indent=2, ensure_ascii=False)


def for_game(cfg, appid):
    """Override par jeu s'il existe, sinon la config globale."""
    return cfg["per_game"].get(appid, cfg["global"])
