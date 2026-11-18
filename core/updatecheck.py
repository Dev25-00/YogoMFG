"""Cherche une version plus récente de YogoMFG sur GitHub (lecture seule, aucune donnée envoyée).

Ne télécharge ni n'installe rien : l'utilisateur ouvre la page de la release. /releases/latest ignore les
pré-releases (toutes nos versions sont « -beta »), d'où /releases?per_page=1. Auto-test : python -m core.updatecheck
"""
import json
import re
import urllib.request

API = "https://api.github.com/repos/Dev25-00/YogoMFG/releases?per_page=1"
MOD_API = "https://api.github.com/repos/sdli1995/dlssg_for_sm86/releases/latest"


def _nums(v):
    """'v0.7.6-beta' / '0.7.6 beta' -> (0, 7, 6) ; () si illisible."""
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", v or "")
    return tuple(int(x) for x in m.groups()) if m else ()


def newer(current, tag):
    n, c = _nums(tag), _nums(current)
    return bool(n and c and n > c)


def _release(url, timeout):
    req = urllib.request.Request(url, headers={"User-Agent": "YogoMFG", "Accept": "application/vnd.github+json"})
    try:
        rel = json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8"))
        rel = rel[0] if isinstance(rel, list) else rel
        return None if rel.get("draft") else (rel["tag_name"], rel["html_url"])
    except Exception:
        return None


def latest(timeout=8):
    """(tag, url) de la dernière release de YogoMFG, ou None si le réseau échoue."""
    return _release(API, timeout)


def latest_mod(timeout=8):
    """(tag, url) de la dernière release du mod de sdli1995 : sert à savoir qu'il faut mettre YogoMFG à jour."""
    return _release(MOD_API, timeout)


if __name__ == "__main__":
    assert _nums("v0.7.6-beta") == (0, 7, 6) and _nums("0.7.5 beta") == (0, 7, 5) and _nums("x") == ()
    assert newer("0.7.5 beta", "v0.7.6-beta") and newer("0.7.9 beta", "v0.8.0-beta")
    assert not newer("0.7.6 beta", "v0.7.6-beta") and not newer("0.7.6 beta", "v0.7.5-beta")
    assert not newer("0.7.6 beta", "n/a") and not newer("", "v0.7.6-beta")
    assert newer("0.7.9 beta", "v0.7.10-beta"), "comparaison numérique, pas alphabétique"
    print("updatecheck selftest OK")
