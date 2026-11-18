"""Quelle version du mod de sdli1995 est posée dans un jeu ? (lecture seule)

Le mod n'écrit aucun numéro de version dans le jeu : on reconnaît la DLL proxy par son SHA-256 (empreintes calculées
sur les zips officiels des releases GitHub). À chaque nouvelle release embarquée : changer PAYLOAD et ajouter les
empreintes des six proxys de la version précédente dans OLD (l'auto-test refuse un PAYLOAD qui ne correspond pas au dossier mod/).
"""
import hashlib
import os

PAYLOAD = "0.4.2"          # version du mod embarqué dans ce YogoMFG (dossier mod/)
PROXIES = ("version.dll", "winmm.dll", "dbghelp.dll", "dinput8.dll", "dxgi.dll", "d3d12.dll")

# sha256 d'une DLL proxy -> version du mod (0.4.0 et 0.4.1 : releases publiées ; les anciennes restent « inconnue »)
OLD = {
    "c4b6f6320a8ad465334514161911941f769d541f8e8d5186171fbe0027ea1ddc": "0.4.0",  # d3d12.dll
    "33653ddcb57872e275548c4d39c29a3f47c39b1637eea08d62b55953826e839f": "0.4.0",  # dbghelp.dll
    "19f2e77303c11b40e773eed6b90e17df54997b57472127438f9fedd7a5ddc677": "0.4.0",  # dinput8.dll
    "2048988dd9cad19e9f25610538edf530b35b036c6701378cf663d7ddf251f5ed": "0.4.0",  # dxgi.dll
    "7b3f90435be4f94348bf8d128c84871c7f904c704f7690601a263277c327a7b2": "0.4.0",  # version.dll
    "c86bd90c0fbaf3db0b5cc17c5bbece40eb34a6a3327fe2c0dd8ab455ba985203": "0.4.0",  # winmm.dll
    "e188a992d1ff1ef1ebb51bfc544ac132536d717f2fa2ec77642f9d506cdea58e": "0.4.1",  # d3d12.dll
    "82c04383044657bcb4bb45b7061d8fb27a753bc222b37f6712c5affb20848f5f": "0.4.1",  # dbghelp.dll
    "8181129b3754bbea4a91bcc61f50a7e28f6fb939b880e2d38eb7a5b4ffbcc8ad": "0.4.1",  # dinput8.dll
    "96e05da6572f6e4808b7f7402ccc9c584fc2257d7e5ea2478fc725663bdc27b4": "0.4.1",  # dxgi.dll
    "275ffa781b2d244ad269d1d65d4e5b68a12a3f89ff2baaec58d100eb5a1ff411": "0.4.1",  # version.dll
    "1a584a9b0333e0c3be4ab32e00901c545ca16a620a56784a67cacf003c041739": "0.4.1",  # winmm.dll
}


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def payload_hashes(mod_root):
    """Empreintes des six proxys du mod embarqué (version.dll à la racine, les autres dans alternatives/)."""
    out = {}
    for p in PROXIES:
        f = os.path.join(mod_root, p if p == "version.dll" else os.path.join("alternatives", p))
        if os.path.isfile(f):
            out[_sha(f)] = PAYLOAD
    return out


def installed(game_dir, mod_root):
    """Version du mod posée dans ce dossier de jeu : \"0.4.1\", PAYLOAD, ou None si la DLL n'est pas reconnue."""
    known = dict(OLD, **payload_hashes(mod_root))
    for p in PROXIES:
        f = os.path.join(game_dir, p)
        if os.path.isfile(f):
            try:
                v = known.get(_sha(f))
            except OSError:
                continue
            if v:
                return v
    return None


def _selftest():
    import tempfile
    here = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mod")
    if os.path.isdir(here):
        ph = payload_hashes(here)
        assert len(ph) == 6, "les six proxys du mod embarqué doivent exister"
        assert not (set(ph) & set(OLD)), "PAYLOAD pas mis à jour : le mod embarqué est encore une version OLD"
        assert installed(os.path.join(here, "alternatives"), here) == PAYLOAD, "reconnaît un proxy alternatif"
    with tempfile.TemporaryDirectory() as t:
        mod, game = os.path.join(t, "mod"), os.path.join(t, "game")
        os.makedirs(mod)
        os.makedirs(game)
        open(os.path.join(mod, "version.dll"), "wb").write(b"NEW")
        assert installed(game, mod) is None
        open(os.path.join(game, "version.dll"), "wb").write(b"NEW")
        assert installed(game, mod) == PAYLOAD
        open(os.path.join(game, "version.dll"), "wb").write(b"inconnu")
        assert installed(game, mod) is None, "DLL étrangère : jamais présentée comme une version du mod"
    print("modversion selftest OK")


if __name__ == "__main__":
    _selftest()
