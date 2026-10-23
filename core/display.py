"""Détecte les moniteurs et change leur fréquence de rafraîchissement (Windows API).

Changer le refresh écrit dans le registre d'affichage (CDS_UPDATEREGISTRY) : réversible
(on peut remettre l'ancienne valeur), mais c'est une modification système, d'où un test
CDS_TEST avant application.
"""
import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32

ENUM_CURRENT_SETTINGS = -1
DM_PELSWIDTH = 0x00080000
DM_PELSHEIGHT = 0x00100000
DM_DISPLAYFREQUENCY = 0x00400000
CDS_UPDATEREGISTRY = 0x00000001
CDS_TEST = 0x00000002
DISP_CHANGE_SUCCESSFUL = 0


class DEVMODE(ctypes.Structure):
    _fields_ = [
        ("dmDeviceName", wintypes.WCHAR * 32),
        ("dmSpecVersion", wintypes.WORD),
        ("dmDriverVersion", wintypes.WORD),
        ("dmSize", wintypes.WORD),
        ("dmDriverExtra", wintypes.WORD),
        ("dmFields", wintypes.DWORD),
        ("dmOrientation", ctypes.c_short),
        ("dmPaperSize", ctypes.c_short),
        ("dmPaperLength", ctypes.c_short),
        ("dmPaperWidth", ctypes.c_short),
        ("dmScale", ctypes.c_short),
        ("dmCopies", ctypes.c_short),
        ("dmDefaultSource", ctypes.c_short),
        ("dmPrintQuality", ctypes.c_short),
        ("dmColor", ctypes.c_short),
        ("dmDuplex", ctypes.c_short),
        ("dmYResolution", ctypes.c_short),
        ("dmTTOption", ctypes.c_short),
        ("dmCollate", ctypes.c_short),
        ("dmFormName", wintypes.WCHAR * 32),
        ("dmLogPixels", wintypes.WORD),
        ("dmBitsPerPel", wintypes.DWORD),
        ("dmPelsWidth", wintypes.DWORD),
        ("dmPelsHeight", wintypes.DWORD),
        ("dmDisplayFlags", wintypes.DWORD),
        ("dmDisplayFrequency", wintypes.DWORD),
        ("dmICMMethod", wintypes.DWORD),
        ("dmICMIntent", wintypes.DWORD),
        ("dmMediaType", wintypes.DWORD),
        ("dmDitherType", wintypes.DWORD),
        ("dmReserved1", wintypes.DWORD),
        ("dmReserved2", wintypes.DWORD),
        ("dmPanningWidth", wintypes.DWORD),
        ("dmPanningHeight", wintypes.DWORD),
    ]


class DISPLAY_DEVICE(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("DeviceName", wintypes.WCHAR * 32),
        ("DeviceString", wintypes.WCHAR * 128),
        ("StateFlags", wintypes.DWORD),
        ("DeviceID", wintypes.WCHAR * 128),
        ("DeviceKey", wintypes.WCHAR * 128),
    ]


DISPLAY_DEVICE_ATTACHED = 0x00000001
DISPLAY_DEVICE_PRIMARY = 0x00000004


def monitors():
    """Liste des moniteurs actifs: [{index, device, name, model, res, hz, primary}].
    name = modèle du moniteur (ex. écran 27") pour les distinguer, pas l'adaptateur GPU."""
    out, i = [], 0
    while True:
        dd = DISPLAY_DEVICE(); dd.cb = ctypes.sizeof(dd)
        if not user32.EnumDisplayDevicesW(None, i, ctypes.byref(dd), 0):
            break
        if dd.StateFlags & DISPLAY_DEVICE_ATTACHED:
            # 2e appel sur l'adaptateur -> nom réel du moniteur branché.
            mon = DISPLAY_DEVICE(); mon.cb = ctypes.sizeof(mon)
            model = dd.DeviceString
            if user32.EnumDisplayDevicesW(dd.DeviceName, 0, ctypes.byref(mon), 0):
                model = mon.DeviceString or model
            cur = current(dd.DeviceName) or (0, 0, 0)
            out.append({"index": len(out) + 1, "device": dd.DeviceName,
                        "name": dd.DeviceString, "model": model,
                        "res": f"{cur[0]}x{cur[1]}", "hz": cur[2],
                        "primary": bool(dd.StateFlags & DISPLAY_DEVICE_PRIMARY)})
        i += 1
    return out


def _dm(device, mode=ENUM_CURRENT_SETTINGS):
    dm = DEVMODE(); dm.dmSize = ctypes.sizeof(dm)
    if user32.EnumDisplaySettingsW(device, mode, ctypes.byref(dm)):
        return dm
    return None


def current(device):
    """(width, height, refresh_hz) ou None."""
    dm = _dm(device)
    return (dm.dmPelsWidth, dm.dmPelsHeight, dm.dmDisplayFrequency) if dm else None


def refresh_rates(device):
    """Fréquences dispo à la résolution courante, triées."""
    cur = current(device)
    if not cur:
        return []
    w, h = cur[0], cur[1]
    rates, i = set(), 0
    while True:
        dm = _dm(device, i)
        if not dm:
            break
        if dm.dmPelsWidth == w and dm.dmPelsHeight == h and dm.dmDisplayFrequency > 1:
            rates.add(int(dm.dmDisplayFrequency))
        i += 1
    return sorted(rates)


def set_refresh(device, hz):
    """Change la fréquence du moniteur. Retourne (ok, message). Teste avant d'appliquer."""
    dm = _dm(device)
    if not dm:
        return False, "Moniteur introuvable."
    dm.dmFields = DM_PELSWIDTH | DM_PELSHEIGHT | DM_DISPLAYFREQUENCY
    dm.dmDisplayFrequency = int(hz)
    if user32.ChangeDisplaySettingsExW(device, ctypes.byref(dm), None, CDS_TEST, None) != DISP_CHANGE_SUCCESSFUL:
        return False, f"{hz} Hz non supporté par ce moniteur à cette résolution."
    r = user32.ChangeDisplaySettingsExW(device, ctypes.byref(dm), None, CDS_UPDATEREGISTRY, None)
    if r == DISP_CHANGE_SUCCESSFUL:
        return True, f"Refresh réglé sur {hz} Hz."
    return False, f"Échec du changement (code {r})."
