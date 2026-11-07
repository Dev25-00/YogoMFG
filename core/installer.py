"""Pose/retire les fichiers du mod à côté du .exe de rendu, avec sauvegarde vérifiée des fichiers d'origine.

Le mod installé est « dlssg_for_sm86 / SM75 » de sdli1995 (https://github.com/sdli1995/dlssg_for_sm86).

Sauvegarde : avant d'écrire, chaque fichier du jeu qui serait écrasé est DÉPLACÉ dans <dossier du .exe>\\YogoMFG_backup\\
(même chemin relatif) et noté dans manifest.json : {path, sha256, action: replaced|added} + les dossiers créés.
Retirer supprime ce qui a été ajouté, remet chaque fichier remplacé, vérifie son sha256, puis supprime la sauvegarde.
Les installations 0.6.x (sauvegarde « <dll>.yogobak » à côté de la DLL) sont reconnues et restaurées aussi.
"""
import os, re, json, shutil, struct, hashlib

PROXIES = ("version.dll", "dxgi.dll", "d3d12.dll", "dinput8.dll", "winmm.dll", "dbghelp.dll")
# Ordre de préférence du proxy : une DLL « neutre » d'abord, les DLL graphiques en dernier recours
# (un proxy dxgi/d3d12 qui reforwarde mal casse le rendu, pas seulement la Frame Generation).
PREFER = ("version.dll", "winmm.dll", "dinput8.dll", "dbghelp.dll", "dxgi.dll", "d3d12.dll")
BACKUP = "YogoMFG_backup"
MANIFEST = "manifest.json"
INI = "dlssg_sm86.ini"
FOLDER = "dlssg_sm86"
_MARK = "; Généré par YogoMFG"


def pe_imports(exe_path):
    """Noms (minuscules) des DLL importées par un .exe, lus dans sa table d'imports PE. [] si illisible."""
    try:
        with open(exe_path, "rb") as f:
            d = f.read()
        if d[:2] != b"MZ":
            return []
        pe = struct.unpack_from("<I", d, 0x3C)[0]
        if d[pe:pe + 4] != b"PE" + bytes(2):
            return []
        coff = pe + 4
        nsec, = struct.unpack_from("<H", d, coff + 2)
        opt_size, = struct.unpack_from("<H", d, coff + 16)
        opt = coff + 20
        magic, = struct.unpack_from("<H", d, opt)
        imp_rva = struct.unpack_from("<I", d, opt + (96 if magic == 0x10B else 112) + 8)[0]
        if not imp_rva:
            return []
        secs = []
        for i in range(nsec):
            s = opt + opt_size + i * 40
            vsize, vaddr, rsize, raddr = struct.unpack_from("<IIII", d, s + 8)
            secs.append((vaddr, max(vsize, rsize), raddr))

        def off(rva):
            for vaddr, size, raddr in secs:
                if vaddr <= rva < vaddr + size:
                    return raddr + (rva - vaddr)
            return None

        out, q = [], off(imp_rva)
        if q is None:
            return []
        while True:
            desc = d[q:q + 20]
            if len(desc) < 20 or desc == bytes(20):
                break
            o = off(struct.unpack_from("<I", desc, 12)[0])
            if o is not None and 0 <= o < len(d):
                end = d.find(bytes(1), o)
                if end > o:
                    out.append(d[o:end].decode("ascii", "replace").lower())
            q += 20
        return out
    except Exception:
        return []


def pick_proxy(exe_path):
    """Quelle DLL proxy poser pour CE jeu : la première de PREFER que l'exe importe vraiment.

    Poser `version.dll` à un jeu qui ne l'importe pas ne charge RIEN : pas de spoof d'architecture, donc
    le jeu croit voir une RTX 20/30 et ne propose même plus la Frame Generation NVIDIA (vécu sur
    CONTROL Resonant, qui importe winmm.dll, et sur Crimson Desert). Repli sur version.dll si le PE est illisible.
    """
    imported = set(pe_imports(exe_path))
    if not imported:
        return "version.dll"
    return next((p for p in PREFER if p in imported), "version.dll")


def _src(mod_root, proxy):
    """version.dll est à la racine; les autres dans alternatives/."""
    return os.path.join(mod_root, proxy if proxy == "version.dll"
                        else os.path.join("alternatives", proxy))


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _read(path):
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            return f.read()
    except OSError:
        return ""


def _load_manifest(dst):
    try:
        with open(os.path.join(dst, BACKUP, MANIFEST), encoding="utf-8") as f:
            m = json.load(f)
        return m if isinstance(m, dict) and isinstance(m.get("files"), list) else None
    except (OSError, ValueError):
        return None


def _save_manifest(dst, man):
    os.makedirs(os.path.join(dst, BACKUP), exist_ok=True)
    p = os.path.join(dst, BACKUP, MANIFEST)
    with open(p + ".part", "w", encoding="utf-8") as f:
        json.dump(man, f, indent=1)
    os.replace(p + ".part", p)


def _is_legacy(dst):
    """Installation YogoMFG 0.6.x : une DLL .yogobak, ou un INI marqué, sans manifeste."""
    return (any(os.path.isfile(os.path.join(dst, p + ".yogobak")) for p in PROXIES)
            or _read(os.path.join(dst, INI)).startswith(_MARK))


def _check_unlocked(paths):
    """Refuse avant de toucher à quoi que ce soit si un fichier est verrouillé (jeu lancé)."""
    for p in paths:
        if os.path.isfile(p):
            try:
                open(p, "r+b").close()
            except PermissionError:
                raise RuntimeError(f"fichier utilisé (jeu lancé ?) : {os.path.basename(p)}")


def install(mod_root, exe_path, ini_text, proxy="version.dll"):
    """Copie proxy + INI + dossier dlssg_sm86\\ à côté du .exe. Retourne la liste des actions.

    Ré-optimiser garde le manifeste existant (les originaux déjà sauvegardés ne sont jamais écrasés par nos fichiers).
    """
    dst = os.path.dirname(exe_path)
    src_proxy, src_folder = _src(mod_root, proxy), os.path.join(mod_root, FOLDER)
    if not os.path.isfile(src_proxy):
        raise FileNotFoundError(src_proxy)
    if not os.path.isdir(src_folder):
        raise FileNotFoundError(src_folder)

    acts = []
    man = _load_manifest(dst)
    if man is None and _is_legacy(dst):              # ancienne install : on remet d'abord le jeu d'origine
        acts += legacy_uninstall(dst)
    man = man or {"version": 1, "files": [], "dirs": []}

    # plan : chemin relatif -> source (None = INI généré)
    plan = {proxy: src_proxy, INI: None}
    for root, _, files in os.walk(src_folder):
        for fn in files:
            full = os.path.join(root, fn)
            plan[os.path.relpath(full, mod_root)] = full
    _check_unlocked(os.path.join(dst, r) for r in plan)

    known = {e["path"].lower() for e in man["files"]}
    if not os.path.isdir(os.path.join(dst, FOLDER)) and FOLDER not in man["dirs"]:
        man["dirs"].append(FOLDER)                    # dossier créé par nous : Retirer le supprime en entier (logs compris)
    for rel in plan:
        if rel.lower() in known:
            continue
        cur = os.path.join(dst, rel)
        if os.path.isfile(cur):
            bak = os.path.join(dst, BACKUP, rel)
            os.makedirs(os.path.dirname(bak), exist_ok=True)
            man["files"].append({"path": rel, "sha256": _sha(cur), "action": "replaced"})
            os.replace(cur, bak)
            acts.append(f"sauvegarde {rel}")
        else:
            man["files"].append({"path": rel, "sha256": "", "action": "added"})
        _save_manifest(dst, man)                      # écrit à chaque pas : une coupure laisse un Retirer possible

    for rel, src in plan.items():
        out = os.path.join(dst, rel)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        if src is None:
            with open(out, "w", encoding="utf-8") as f:
                f.write(ini_text)
        else:
            shutil.copy2(src, out)
    for e in man["files"]:
        if e["action"] == "added" and os.path.isfile(os.path.join(dst, e["path"])):
            e["sha256"] = _sha(os.path.join(dst, e["path"]))
    _save_manifest(dst, man)
    acts.append(f"copie {proxy}, {INI}, {FOLDER}\\ ({len(plan)} fichiers)")
    return acts


def uninstall(exe_path, proxy="version.dll"):
    """Retire tout et remet les fichiers d'origine (manifeste + .yogobak 0.6.x). Retourne la liste des actions.

    Lève RuntimeError si un fichier est verrouillé ou si une restauration ne correspond pas à son sha256
    (la sauvegarde est alors conservée).
    """
    dst = os.path.dirname(exe_path)
    man = _load_manifest(dst)
    acts = []
    if man is not None:
        _check_unlocked(os.path.join(dst, e["path"]) for e in man["files"])
        for e in man["files"]:
            if e["action"] == "added":
                p = os.path.join(dst, e["path"])
                if os.path.isfile(p):
                    os.remove(p)
                    acts.append(f"supprimé {e['path']}")
        for d in man.get("dirs", []):
            shutil.rmtree(os.path.join(dst, d), ignore_errors=True)
            acts.append(f"supprimé {d}\\")
        bad = []
        for e in man["files"]:
            if e["action"] != "replaced":
                continue
            bak, p = os.path.join(dst, BACKUP, e["path"]), os.path.join(dst, e["path"])
            if os.path.isfile(bak):
                os.makedirs(os.path.dirname(p), exist_ok=True)
                os.replace(bak, p)
            if not (os.path.isfile(p) and _sha(p) == e["sha256"]):
                bad.append(e["path"])
            else:
                acts.append(f"restauré {e['path']}")
        if bad:
            raise RuntimeError("restauration non vérifiée (sauvegarde conservée dans "
                               f"{BACKUP}) : " + ", ".join(bad))
        shutil.rmtree(os.path.join(dst, BACKUP), ignore_errors=True)
        acts.append(f"supprimé {BACKUP}\\")
    if any(os.path.isfile(os.path.join(dst, p + ".yogobak")) for p in PROXIES) or (
            man is None and (os.path.isfile(os.path.join(dst, INI)) or os.path.isdir(os.path.join(dst, FOLDER)))):
        acts += legacy_uninstall(dst, proxy)
    return acts or ["rien à retirer (mod non détecté ici)"]


def legacy_uninstall(dst, proxy="version.dll"):
    """Installations 0.6.x : remet chaque <dll>.yogobak, supprime l'INI et dlssg_sm86\\.

    SÉCURITÉ : une DLL proxy SANS .yogobak n'est supprimée que si le mod est bien présent (INI ou dossier).
    Sinon on n'y touche pas : c'est peut-être la DLL du jeu ou d'un autre mod.
    """
    acts = []
    ini, fd = os.path.join(dst, INI), os.path.join(dst, FOLDER)
    mod_present = os.path.isfile(ini) or os.path.isdir(fd)
    _check_unlocked([os.path.join(dst, p) for p in PROXIES] + [ini])
    restored = False
    for p in PROXIES:
        bak = os.path.join(dst, p + ".yogobak")
        if os.path.isfile(bak):
            os.replace(bak, os.path.join(dst, p))
            acts.append(f"restauré {p} (.yogobak)")
            restored = True
    pp = os.path.join(dst, proxy)
    if not restored and mod_present and os.path.isfile(pp):
        os.remove(pp)
        acts.append(f"supprimé {proxy}")
    if os.path.isfile(ini):
        os.remove(ini)
        acts.append(f"supprimé {INI}")
    if os.path.isdir(fd):
        shutil.rmtree(fd, ignore_errors=True)
        acts.append(f"supprimé {FOLDER}\\")
    return acts


def status(exe_path, hint=None):
    """État de l'installation YogoMFG à côté du .exe (lecture seule, instantané).

    {installed, mult, proxy, backups[]} ; `hint` = proxy appliqué la dernière fois (config) pour nommer la bonne DLL.
    """
    dst = os.path.dirname(exe_path) if exe_path else ""
    if not dst:
        return {"installed": False, "mult": None, "proxy": None, "backups": []}
    ini = os.path.join(dst, INI)
    man = _load_manifest(dst)
    installed = man is not None or os.path.isfile(ini) or os.path.isdir(os.path.join(dst, FOLDER))
    m = re.search(r"^MaxGeneratedFrames\s*=\s*(\d+)", _read(ini), re.M) if installed else None
    backups = [e["path"] for e in (man or {}).get("files", []) if e["action"] == "replaced"] \
        + [p + ".yogobak" for p in PROXIES if os.path.isfile(os.path.join(dst, p + ".yogobak"))]
    present = [p for p in PROXIES if os.path.isfile(os.path.join(dst, p))]
    proxy = hint if hint in present else next(iter(present), None)
    return {"installed": installed, "mult": int(m.group(1)) + 1 if m else None,
            "proxy": proxy if installed else None, "backups": backups}


def up_to_date(mod_root, exe_path, ini_text, proxy="version.dll"):
    """True when the game holds exactly what YogoMFG would install now (same INI text, same proxy DLL as the payload):
    after a YogoMFG update the game shows « mettre à jour » instead of « déjà optimisé »."""
    dst = os.path.dirname(exe_path) if exe_path else ""
    if not dst or _read(os.path.join(dst, INI)).strip() != ini_text.strip():
        return False
    mine, theirs = os.path.join(mod_root, "version.dll"), os.path.join(dst, proxy)
    return os.path.isfile(theirs) and os.path.isfile(mine) and _sha(theirs) == _sha(mine)


def check_apply(mod_root, exe_path, proxy="version.dll", applied_proxy=None):
    """Peut-on (ré)appliquer ici sans rien casser ? Retourne (ok, code, détail).

    codes : ok | foreign_ini (config modifiée à la main, pas écrasée) | other_proxy (déjà installé avec une autre DLL)
            | locked (fichier utilisé : jeu lancé).
    Une config générée par YogoMFG, ou identique à celle d'usine du mod, est écrasable.
    """
    dst = os.path.dirname(exe_path)
    ini = os.path.join(dst, INI)
    if os.path.isfile(ini):
        txt = _read(ini).replace("\r\n", "\n").strip()
        factory = _read(os.path.join(mod_root, INI)).replace("\r\n", "\n").strip()
        if not (txt.startswith(_MARK) or (factory and txt == factory)):
            return False, "foreign_ini", ""
    if (applied_proxy and applied_proxy != proxy and os.path.isfile(os.path.join(dst, applied_proxy))
            and status(exe_path)["installed"]):          # sans installation, un vieux « applied » ne bloque rien
        return False, "other_proxy", applied_proxy
    for rel in (proxy, INI, os.path.join(FOLDER, "backend", "sm86_backend.dll")):
        p = os.path.join(dst, rel)
        if os.path.isfile(p):
            try:
                open(p, "r+b").close()
            except PermissionError:
                return False, "locked", os.path.basename(rel)
            except OSError:
                pass
    return True, "ok", ""


def _selftest():
    """Aller-retour complet sur un faux jeu (dossier temporaire) : le jeu d'origine revient à l'octet près."""
    import sys, tempfile
    with tempfile.TemporaryDirectory() as t:
        mod = os.path.join(t, "mod")
        for rel, data in (("version.dll", b"MOD-PROXY"), (os.path.join(FOLDER, "backend", "sm86_backend.dll"), b"BE"),
                          (os.path.join(FOLDER, "runtime", "nvngx_dlssg.dll"), b"RT"), (INI, b"; factory\n")):
            os.makedirs(os.path.dirname(os.path.join(mod, rel)), exist_ok=True)
            open(os.path.join(mod, rel), "wb").write(data)

        def snap(d):
            return {os.path.relpath(os.path.join(r, f), d): _sha(os.path.join(r, f))
                    for r, _, fs in os.walk(d) for f in fs}

        # 1) jeu propre avec sa propre version.dll
        game = os.path.join(t, "game")
        os.makedirs(game)
        exe = os.path.join(game, "game.exe")
        open(exe, "wb").write(b"EXE")
        open(os.path.join(game, "version.dll"), "wb").write(os.urandom(4096))
        before = snap(game)
        # 0) table d'imports PE + choix du proxy
        assert pe_imports(exe) == [], "un faux .exe ne doit rien rendre"
        assert pick_proxy(exe) == "version.dll", "repli quand le PE est illisible"
        real = pe_imports(sys.executable)                       # python.exe : vrai PE, imports réels
        assert real and all(n.endswith(".dll") for n in real), real
        assert all(n == n.lower() for n in real), real
        _pe = pe_imports
        try:                                                    # l'ordre de PREFER décide, pas celui de l'exe
            globals()["pe_imports"] = lambda p: ["kernel32.dll", "d3d12.dll", "winmm.dll"]
            assert pick_proxy(exe) == "winmm.dll", pick_proxy(exe)
            globals()["pe_imports"] = lambda p: ["kernel32.dll", "dxgi.dll", "version.dll"]
            assert pick_proxy(exe) == "version.dll", pick_proxy(exe)
            globals()["pe_imports"] = lambda p: ["kernel32.dll", "user32.dll"]
            assert pick_proxy(exe) == "version.dll", "aucun candidat -> repli"
        finally:
            globals()["pe_imports"] = _pe

        assert check_apply(mod, exe)[0]
        install(mod, exe, _MARK + "\n[FrameGeneration]\nMaxGeneratedFrames=2\n")
        assert open(os.path.join(game, "version.dll"), "rb").read() == b"MOD-PROXY"
        assert status(exe)["installed"] and status(exe)["mult"] == 3 and status(exe)["backups"] == ["version.dll"]
        install(mod, exe, _MARK + "\n[FrameGeneration]\nMaxGeneratedFrames=1\n")     # ré-optimiser : l'original reste sauvé
        os.makedirs(os.path.join(game, FOLDER, "logs"), exist_ok=True)               # le mod écrit ses logs en jeu
        open(os.path.join(game, FOLDER, "logs", "dlssg_sm86.log"), "w").write("x")
        uninstall(exe)
        assert snap(game) == before, (snap(game), before)
        assert not status(exe)["installed"]

        # 2) installation 0.6.x (.yogobak) puis install 0.7 puis Retirer
        game2 = os.path.join(t, "game2")
        os.makedirs(os.path.join(game2, FOLDER))
        exe2 = os.path.join(game2, "game.exe")
        open(exe2, "wb").write(b"EXE")
        orig = os.urandom(2048)
        open(os.path.join(game2, "version.dll.yogobak"), "wb").write(orig)
        open(os.path.join(game2, "version.dll"), "wb").write(b"OLD-MOD")
        open(os.path.join(game2, INI), "w", encoding="utf-8").write(_MARK + "\n")
        install(mod, exe2, _MARK + "\n")
        uninstall(exe2)
        assert sorted(os.listdir(game2)) == ["game.exe", "version.dll"], os.listdir(game2)
        assert open(os.path.join(game2, "version.dll"), "rb").read() == orig

        # 3) installation 0.6.x retirée directement (sans repasser par 0.7)
        game3 = os.path.join(t, "game3")
        os.makedirs(os.path.join(game3, FOLDER))
        exe3 = os.path.join(game3, "game.exe")
        open(exe3, "wb").write(b"EXE")
        open(os.path.join(game3, "version.dll.yogobak"), "wb").write(orig)
        open(os.path.join(game3, "version.dll"), "wb").write(b"OLD-MOD")
        open(os.path.join(game3, INI), "w", encoding="utf-8").write(_MARK + "\n")
        uninstall(exe3)
        assert sorted(os.listdir(game3)) == ["game.exe", "version.dll"]
        assert open(os.path.join(game3, "version.dll"), "rb").read() == orig

        # 4) un INI écrit à la main n'est jamais écrasé
        game4 = os.path.join(t, "game4")
        os.makedirs(game4)
        open(os.path.join(game4, INI), "w").write("[General]\nEnabled=1\nHudFix=true\n")
        assert check_apply(mod, os.path.join(game4, "g.exe"))[1] == "foreign_ini"
    print("installer selftest OK")


if __name__ == "__main__":
    _selftest()
