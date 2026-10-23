"""Détecte si un jeu intègre DLSS-G / Streamline (frame generation NVIDIA)."""
import os

# DLL Streamline/DLSS-G -> le jeu expose le Frame Generation NVIDIA.
_MARKERS = ("sl.dlss_g.dll", "nvngx_dlssg.dll", "sl.interposer.dll",
            "sl.dlss.dll", "nvngx.dll", "sl.common.dll")


def supports(game_dir):
    """'yes' si marqueurs Streamline/DLSS-G trouvés, sinon 'unknown'."""
    for dp, _, files in os.walk(game_dir):
        if dp.count(os.sep) - game_dir.count(os.sep) > 4:
            continue
        low = {f.lower() for f in files}
        if low & set(_MARKERS):
            return "yes"
    return "unknown"


def web_query(name):
    """URL de recherche web pour lever le doute sur le support FG."""
    return "https://www.google.com/search?q=" + name.replace(" ", "+") + "+DLSS+Frame+Generation"
