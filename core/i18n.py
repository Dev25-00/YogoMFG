"""Langues de l'interface : détection de la langue de Windows, liste, accès aux textes traduits.

FR et EN vivent dans yogomfg.py / les modules d'analyse (textes d'origine). Les autres langues sont dans
core/lang_<code>.py ; chacune expose TR (interface), TIPS (infobulles), FT / VERDICT / PROBE / REASONS (analyse)
et INFO (presets NVIDIA). Toute clé absente retombe sur l'anglais : l'appli ne montre jamais un nom de clé brut.
"""
import ctypes

from core import lang_zh, lang_es, lang_ru, lang_pt, lang_de

LANGS = [("fr", "Français"), ("en", "English"), ("zh", "中文 (简体)"), ("es", "Español"),
         ("ru", "Русский"), ("pt", "Português (BR)"), ("de", "Deutsch")]
CODES = [c for c, _ in LANGS]
NAMES = dict(LANGS)
_MODS = {"zh": lang_zh, "es": lang_es, "ru": lang_ru, "pt": lang_pt, "de": lang_de}

# identifiants de langue Windows (octet bas de LANGID) -> code
_LANGID = {0x0C: "fr", 0x09: "en", 0x04: "zh", 0x0A: "es", 0x19: "ru", 0x16: "pt", 0x07: "de"}


def detect(default="en"):
    """Langue de l'interface Windows de l'utilisateur, ramenée à une langue supportée."""
    try:
        lid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
    except (AttributeError, OSError):
        return default
    return _LANGID.get(lid & 0xFF, default)


def section(name, lang):
    """Dictionnaire `name` (TR, TIPS, FT, VERDICT, PROBE, REASONS, INFO) de la langue, ou {} si absent."""
    mod = _MODS.get(lang)
    return getattr(mod, name, {}) if mod else {}
