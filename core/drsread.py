"""Quel profil NVIDIA le pilote applique-t-il à un .exe ? Lecture seule (NVAPI DRS), sans droits admin.

nvidiaProfileInspector -exportCustomized n'exporte que les profils déjà modifiés : un jeu dont le profil NVIDIA
est celui d'origine (ex. God of War Ragnarök) n'y figure pas, et YogoMFG créait alors un profil « GoWR » que le
pilote ignorait (le jeu garde son profil prédéfini). On interroge donc le pilote lui-même, comme le fait le mod.
"""
import ctypes as C

_INIT, _CREATE, _LOAD = 0x0150E828, 0x0694D52E, 0x375DBD6B
_FIND, _INFO, _DESTROY = 0xEEE566B2, 0x61CD6FD6, 0xDAD9CFF8


class _Profile(C.Structure):
    _fields_ = [("version", C.c_uint), ("name", C.c_wchar * 2048), ("gpu", C.c_uint), ("predef", C.c_uint),
                ("apps", C.c_uint), ("settings", C.c_uint)]


class _App(C.Structure):
    _fields_ = [("version", C.c_uint), ("predef", C.c_uint), ("appName", C.c_wchar * 2048),
                ("friendly", C.c_wchar * 2048), ("launcher", C.c_wchar * 2048),
                ("fileInFolder", C.c_wchar * 2048), ("flags", C.c_uint), ("cmd", C.c_wchar * 2048)]


def profile_for(exe_name):
    """Nom du profil que le pilote applique à `exe_name` (ex. « GoWR.exe »), ou None (inconnu / pas de NVAPI)."""
    session = C.c_void_p()
    try:
        nv = C.WinDLL("nvapi64.dll")
        qi = nv.nvapi_QueryInterface
        qi.restype, qi.argtypes = C.c_void_p, [C.c_uint]

        def fn(i, *a):
            return C.CFUNCTYPE(C.c_int, *a)(qi(i))
        if fn(_INIT)() != 0 or fn(_CREATE, C.POINTER(C.c_void_p))(C.byref(session)) != 0:
            return None
        try:
            if fn(_LOAD, C.c_void_p)(session) != 0:
                return None
            h, app = C.c_void_p(), _App()
            app.version = C.sizeof(_App) | (4 << 16)
            if fn(_FIND, C.c_void_p, C.c_wchar_p, C.POINTER(C.c_void_p), C.c_void_p)(
                    session, exe_name, C.byref(h), C.byref(app)) != 0:
                return None
            p = _Profile()
            p.version = C.sizeof(_Profile) | (1 << 16)
            if fn(_INFO, C.c_void_p, C.c_void_p)(h, C.byref(p)) != 0 if False else \
                    fn(_INFO, C.c_void_p, C.c_void_p, C.c_void_p)(session, h, C.byref(p)) != 0:
                return None
            return p.name or None
        finally:
            fn(_DESTROY, C.c_void_p)(session)
    except Exception:
        return None
