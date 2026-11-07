"""Analyse les logs du mod après une session de jeu.

Le mod 0.4.1 écrit dans <dossier .exe>\\dlssg_sm86\\logs\\ : dlssg_sm86.log (une ligne « heure pid EXE niveau {json} »
par événement, Level>=2) et frame_timing.txt (FrameTiming=1). Les *.jsonl du mod 0.4.0 restent lus en repli.
Schéma non garanti -> parsing tolérant : on agrège tout champ numérique 'fps'/'ms',
on remonte les warnings/erreurs, et on compare au FPS cible pour guider l'utilisateur.
"""
import os, re, glob, json, statistics
from core import i18n


def _logs_dir(exe_path):
    return os.path.join(os.path.dirname(exe_path), "dlssg_sm86", "logs")


def _log_files(exe_path, *patterns):
    """Le journal unique du mod 0.4.1 s'il existe, sinon les *.jsonl du 0.4.0 (le plus récent en tête)."""
    d = _logs_dir(exe_path)
    one = os.path.join(d, "dlssg_sm86.log")
    if os.path.isfile(one):
        return [one]
    return sorted((f for p in patterns for f in glob.glob(os.path.join(d, p))), key=os.path.getmtime, reverse=True)


def _obj(line):
    """dict JSON d'une ligne de log (préfixe « heure pid EXE niveau » du 0.4.1 ignoré), ou None."""
    i = line.find("{")
    if i < 0:
        return None
    try:
        o = json.loads(line[i:])
    except ValueError:
        return None
    return o if isinstance(o, dict) else None


def read(exe_path, max_lines=20000):
    """Retourne {found, files, fps[], gen_ms[], warnings[], errors[]}."""
    res = {"found": False, "files": [], "fps": [], "gen_ms": [], "warnings": [], "errors": []}
    files = _log_files(exe_path, "backend_*.jsonl", "loader_*.jsonl")   # pas frames_*.jsonl : autre format, autre analyse
    if not files:
        return res
    res["found"] = True
    res["files"] = [os.path.basename(f) for f in files[:5]]
    n = 0
    for fp in files[:5]:
        try:
            for line in open(fp, encoding="utf-8", errors="ignore"):
                n += 1
                if n > max_lines:
                    break
                o = _obj(line)
                if o is not None:
                    _collect(o, res)
        except OSError:
            continue
    return res


def _collect(o, res):
    if not isinstance(o, dict):
        return
    for k, v in o.items():
        lk = str(k).lower()
        if isinstance(v, (int, float)):
            if "fps" in lk or "framerate" in lk:
                res["fps"].append(float(v))
            elif ("gen" in lk and "ms" in lk) or "generated_ms" in lk or lk in ("ms", "gpu_ms"):
                res["gen_ms"].append(float(v))
        elif isinstance(v, str):
            s = v.lower()
            if "configuration_warning" in s or lk == "warning":
                res["warnings"].append(v)
            elif lk in ("error", "level") and "error" in s:
                res["errors"].append(v)
    lvl = str(o.get("level", "")).lower()
    if lvl in ("warning", "warn"):
        res["warnings"].append(o.get("message", json.dumps(o))[:160])
    elif lvl in ("error", "fatal"):
        res["errors"].append(o.get("message", json.dumps(o))[:160])


def _n(v):
    """int ou None : le schéma des logs n'est pas garanti."""
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


_VERD = {
    "fr": {"drs": "Plafond pilote NVIDIA : %dX", "drs_block": "  ← bloque le 5X/6X (active « Multiplicateur imposé »)",
           "ceiling": "Plafond annoncé au jeu : %dX", "asked": "Multiplicateur demandé par le jeu : %dX",
           "created": "✓ Frame Gen créée à : %dX", "forced": "Forçage du plugin pris en compte → %dX",
           "unrec": "Forçage ignoré : plugin du jeu non reconnu (plafond du jeu = 4X)."},
    "en": {"drs": "NVIDIA driver ceiling: %dX", "drs_block": "  ← blocks 5X/6X (turn on \"Enforced multiplier\")",
           "ceiling": "Ceiling announced to the game: %dX", "asked": "Multiplier requested by the game: %dX",
           "created": "✓ Frame Generation created at: %dX", "forced": "Plugin patch applied → %dX",
           "unrec": "Patch ignored: game plugin not recognized (game ceiling = 4X)."},
}


def mfg_verdict(exe_path, lang="fr"):
    """Multiplicateur RÉEL négocié, lu dans les événements du mod (Level>=2). Liste de lignes ([] si rien).

    drs_dlssg.plugin_limit = plafond du pilote ; fg_gate_create_feature.parameters.multi_frame_count =
    ce que la FG a vraiment créé ; mfg_summary.max_count = ce que le jeu a demandé ;
    plugin_mfg_force / plugin_mfg_unrecognized = verdict du forçage.
    """
    files = _log_files(exe_path, "backend_*.jsonl")
    if not files:
        return []
    drs = created = created_max = asked = forced = None
    unrec = 0
    try:
        with open(files[0], encoding="utf-8", errors="ignore") as f:
            for line in f:
                if '"event"' not in line:
                    continue
                o = _obj(line)
                if o is None:
                    continue
                ev = o.get("event")
                if ev == "drs_dlssg":
                    drs = _n(o.get("plugin_limit"))
                elif ev == "fg_gate_create_feature":
                    pr = o.get("parameters") or {}
                    if not isinstance(pr, dict):
                        continue
                    if _n(pr.get("multi_frame_count")) is not None:
                        created = _n(pr["multi_frame_count"])
                    if _n(pr.get("multi_frame_count_max")) is not None:
                        created_max = _n(pr["multi_frame_count_max"])
                elif ev == "mfg_summary" and _n(o.get("max_count")):
                    asked = _n(o["max_count"])
                elif ev == "plugin_mfg_force":
                    forced = _n(o.get("to"))
                elif ev == "plugin_mfg_unrecognized":
                    unrec += 1
    except OSError:
        return []
    v = {**_VERD["en"], **(_VERD.get(lang) or i18n.section("VERDICT", lang))}
    out = []
    if drs is not None:
        out.append(v["drs"] % (drs + 1) + (v["drs_block"] if drs < 5 else ""))
    if created_max is not None:
        out.append(v["ceiling"] % (created_max + 1))
    if asked is not None:
        out.append(v["asked"] % (asked + 1))
    if created is not None:
        out.append(v["created"] % (created + 1))
    if forced is not None:
        out.append(v["forced"] % (forced + 1))
    elif unrec:
        out.append(v["unrec"])
    return out


_FT = {
    "fr": {
        "nolog": "Aucun log du mod trouvé : joue une session avec le mod chargé.",
        "none": "Pas de mesure : optimise le jeu, joue 2 minutes avec la Frame Generation active, puis reviens ici.",
        "fps": "Images réelles : %s par seconde. Affichées (x%d) : environ %s.",
        "gpu_full": "Ta carte graphique est à fond (%d %%). C'est elle qui limite, pas un plafond de FPS.",
        "gpu_low": "Ta carte n'est pas à fond (%d %%) : c'est le processeur ou le moteur du jeu qui limite, pas la carte.",
        "locked": "Les images réelles sont figées à %s/s : un limiteur est actif (V-Sync, limiteur du jeu, Reflex).",
        "cpu": "Pour monter : baisse les options qui chargent le processeur (simulation, densité de végétation, foules, effets).",
        "fg": "La Frame Generation coûte %s ms par image réelle.",
        "tip1": "Pour monter les FPS : baisse « Cinématique » vers « Élevé » (ombres, reflets, brouillard).",
        "tip2": "Ensuite essaie DLSS Performance, puis coupe le HDR pour comparer.",
        "tip3": "Vise au moins 30 images réelles par seconde pour bien profiter du x%d.",
        "cap": "Plafond probable : vérifie le limiteur de FPS du jeu et le V-Sync.",
    },
    "en": {
        "nolog": "No mod log found: play a session with the mod loaded.",
        "none": "No measurement: optimize the game, play 2 minutes with Frame Generation on, then come back.",
        "fps": "Real frames: %s per second. Displayed (x%d): about %s.",
        "gpu_full": "Your graphics card is maxed out (%d %%). It is the limit, not an FPS cap.",
        "gpu_low": "Your card is not maxed out (%d %%): the CPU or the game engine is the limit, not the card.",
        "locked": "Real frames are locked at %s/s: a limiter is active (V-Sync, in-game limiter, Reflex).",
        "cpu": "To gain FPS: lower the options that load the CPU (simulation, foliage density, crowds, effects).",
        "fg": "Frame Generation costs %s ms per real frame.",
        "tip1": "To gain FPS: lower \"Cinematic\" to \"High\" (shadows, reflections, fog).",
        "tip2": "Then try DLSS Performance, then turn HDR off to compare.",
        "tip3": "Aim for at least 30 real frames per second to enjoy x%d.",
        "cap": "Likely cap: check the game's FPS limiter and V-Sync.",
    },
}


_SEC = re.compile(r"^# second (\d+)\s.*?\bfps ([\d.]+)(?:.*?\bfg ([\d.]+))?(?:.*?\bn (\d+))?(?:.*?\bgpu (\d+)%)?")


def _summary(rows):
    """rows = [(fps réels, gpu %|None, fg ms|None, images générées|None)] par seconde, chargement exclu.

    Ne garde que les secondes où la Frame Generation tournait (menus, pauses, cinématiques la coupent), puis :
    real = médiane, low = 10e centile (base que le GPU tient sans faiblir), plateau = FPS réels figés (p10..p90 dans 3 %)
    avec un GPU sous 95 % -> un limiteur (jeu, utilisateur ou notre cap) tient les FPS, pas la carte.
    """
    if any(r[3] for r in rows):
        rows = [r for r in rows if r[3]]
    fps = [r[0] for r in rows]
    if not fps:
        return None
    gpu = [r[1] for r in rows if r[1] is not None]
    fg = [r[2] for r in rows if r[2] is not None]
    n = [r[3] for r in rows if r[3]]
    med = statistics.median(fps)
    q = statistics.quantiles(fps, n=10) if len(fps) >= 2 else [med] * 9
    g = statistics.median(gpu) if gpu else None
    flat = len(fps) >= 20 and med > 0 and (q[8] - q[0]) <= 0.03 * med
    return {"real": med, "low": q[0], "gpu": g, "fg": statistics.median(fg) if fg else None,
            "mult": (statistics.median(n) if n else 0) + 1, "seconds": len(fps),
            "plateau": med if flat and g is not None and g < 95 else None,
            "locked": len(fps) > 20 and statistics.pstdev(fps) < 0.3}


def _timing_stats(path):
    """Résumé des lignes « # second » de la DERNIÈRE session de frame_timing.txt (mod 0.4.1), ou None."""
    rows = []
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.startswith("# ==== session"):
                    rows = []                                 # nouvelle session : seule la dernière compte
                    continue
                m = _SEC.match(line) if line.startswith("# second") else None
                if not m or int(m.group(1)) < 6:              # saute le chargement
                    continue
                rows.append((float(m.group(2)), float(m.group(5)) if m.group(5) else None,
                             float(m.group(3)) if m.group(3) else None, int(m.group(4)) if m.group(4) else None))
    except OSError:
        return None
    return _summary(rows)


def _frame_stats(exe_path):
    """Résumé de la dernière session mesurée (voir _summary) ou None (pas de mesure)."""
    ft = os.path.join(_logs_dir(exe_path), "frame_timing.txt")
    if os.path.isfile(ft):
        return _timing_stats(ft)
    files = sorted(glob.glob(os.path.join(_logs_dir(exe_path), "frames_*.jsonl")),     # mod 0.4.0
                   key=os.path.getmtime, reverse=True)
    if not files:
        return None
    rows = []
    try:
        with open(files[0], encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f):
                if i > 600000:                      # garde-fou : fichier de mesure très long
                    break
                if '"t":"s"' not in line and '"t": "s"' not in line:
                    continue
                try:
                    o = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(o, dict) or (_n(o.get("s")) or 0) < 6 or not isinstance(o.get("fps"), (int, float)):
                    continue
                fg = o.get("fg")
                rows.append((float(o["fps"]), float(o["gpu"]) if isinstance(o.get("gpu"), (int, float)) else None,
                             float(fg["avg"]) if isinstance(fg, dict) and isinstance(fg.get("avg"), (int, float)) else None,
                             _n(o.get("n"))))
    except OSError:
        return None
    return _summary(rows)


def session_stats(exe_path):
    """Résumé de la dernière session (real, low, plateau, mult, seconds, gpu…) pour le calibrage, ou None."""
    return _frame_stats(exe_path)


def measured_mult(exe_path):
    """Multiplicateur réellement obtenu à la dernière session (2…6), ou None si la Frame Generation n'a pas tourné."""
    st = _frame_stats(exe_path)
    return int(round(st["mult"])) if st and st["mult"] > 1 else None


def real_fps(exe_path):
    """FPS réels médians mesurés (sans génération d'images), ou None."""
    st = _frame_stats(exe_path)
    return st["real"] if st else None


def frame_report(exe_path, lang="fr"):
    """Verdict en mots simples, lu dans frames_<pid>.jsonl (réglage FrameTiming=1)."""
    t = {**_FT["en"], **(_FT.get(lang) or i18n.section("FT", lang))}
    st = _frame_stats(exe_path)
    if not st:
        return [t["none"]]
    real, g, mult = st["real"], st["gpu"], st["mult"]
    out = [t["fps"] % (round(real, 1), int(mult), round(real * mult))]
    if g is not None:
        out.append(t["gpu_full"] % g if g >= 90 else t["gpu_low"] % g)
    if st["fg"]:
        out.append(t["fg"] % round(st["fg"], 1))
    if g is not None and g >= 90:
        out += [t["tip1"], t["tip2"], t["tip3"] % int(mult)]
    elif g is not None:
        out.append(t["cpu"])
    if st["locked"]:
        out.append(t["locked"] % round(real, 1))
    return out


def _med(xs):
    return round(statistics.median(xs), 1) if xs else None


def analyze(exe_path, fps_target, goal="fps", did=None, lang="fr"):
    """Lit + synthétise. goal: 'fps' ou 'quality'. did: ce que l'utilisateur a fait in-game
    (dict bool: fg, reflex, rt, pt, vsync_off ; str: dlss). Retourne (lines, reco_cfg_delta)."""
    did = did or {}
    r = read(exe_path)
    lines, delta = mfg_verdict(exe_path, lang), {}
    if lines:
        lines.append("")
    lines += frame_report(exe_path, lang) + [""]
    if not r["found"]:
        lines += [({**_FT["en"], **(_FT.get(lang) or i18n.section("FT", lang))})["nolog"]]
        lines += _from_checklist(did, fps_target, goal, delta)
        lines += _baseline(fps_target, goal)
        return lines, delta
    med_fps, med_ms = _med(r["fps"]), _med(r["gen_ms"])
    if med_fps is not None:
        lines.append(f"FPS médian mesuré : {med_fps}")
    if med_ms is not None:
        lines.append(f"GPU par frame générée : {med_ms} ms (médian)")
    if r["warnings"]:
        lines.append(f"⚠ {len(r['warnings'])} warning(s) config — ex: {r['warnings'][0][:120]}")
    if r["errors"]:
        lines.append(f"✖ {len(r['errors'])} erreur(s) — ex: {r['errors'][0][:120]}")

    # Guidance selon l'écart cible / objectif.
    if med_fps is not None:
        if med_fps < fps_target * 0.9:
            lines.append(f"Sous la cible {fps_target}. Pour gagner des FPS :")
            lines.append("  → DLSS plus agressif (Performance/Ultra Perf), baisse RT/PT, "
                         "ou garde x4 mais descends la résolution de rendu.")
            delta = {"dlss_quality": "performance"}
        elif med_fps > fps_target * 1.15 and goal == "quality":
            lines.append(f"Au-dessus de {fps_target} : marge pour +qualité :")
            lines.append("  → DLSS Qualité, remonte RT/PT, ou passe le preset DLSS-G sur Auto.")
            delta = {"dlss_quality": "quality"}
        else:
            lines.append(f"Proche de la cible {fps_target}. Réglages cohérents.")
    lines += _from_checklist(did, fps_target, goal, delta)
    lines += _baseline(fps_target, goal)
    return lines, delta


def _baseline(fps_target, goal):
    """Conseils de base, toujours présents, selon la cible et l'objectif."""
    from core.optadvice import advise
    out = ["", "Pistes générales :"]
    if goal == "quality":
        out.append("  • Image : DLSS vers Qualité, preset DLSS-G Auto, remonte RT/Path Tracing "
                   "tant que tu restes proche de ta cible FPS.")
    out += ["  • " + a for a in advise(fps_target)[:4]]
    return out


def _from_checklist(did, fps_target, goal, delta):
    """Guidance supplémentaire selon ce que l'utilisateur dit avoir fait en jeu."""
    if not did:
        return []
    out = ["", "D'après ce que tu as coché :"]
    if not did.get("fg"):
        out.append("  → Frame Generation PAS activé en jeu : active-le, c'est le gros gain de FPS.")
    if not did.get("reflex"):
        out.append("  → Reflex OFF : active Reflex On+Boost, ça réduit la latence du FG.")
    if not did.get("vsync_off"):
        out.append("  → V-Sync in-game encore ON : mets-la OFF, la synchro est gérée côté pilote.")
    if (did.get("rt") or did.get("pt")) and goal == "fps":
        out.append("  → RT/Path Tracing actifs : si tu manques de FPS, baisse-les en premier (gros coût).")
    cur = did.get("dlss")
    if cur:
        from core.inimaker import recommend_quality, QUALITY, QUALITY_FR
        reco = recommend_quality(fps_target)
        if cur != reco and QUALITY.index(cur) < QUALITY.index(reco) and goal == "fps":
            out.append(f"  → DLSS sur « {QUALITY_FR.get(cur,cur)} » : passe à « {QUALITY_FR[reco]} » "
                       f"pour viser {fps_target} FPS.")
            delta["dlss_quality"] = reco
        elif cur != reco and QUALITY.index(cur) > QUALITY.index(reco) and goal == "quality":
            out.append(f"  → Tu as de la marge : remonte DLSS vers « {QUALITY_FR[reco]} » pour une image plus nette.")
            delta["dlss_quality"] = reco
    return out if len(out) > 2 else []


def _selftest():
    """Lecture des logs du mod 0.4.1 (frame_timing.txt + dlssg_sm86.log) sur un faux dossier de jeu."""
    import tempfile
    with tempfile.TemporaryDirectory() as t:
        d = os.path.join(t, "dlssg_sm86", "logs")
        os.makedirs(d)
        sec = ("# second %d  frames 60  fps 61.2  dt 16.3 16.2 17.0 18.0  fg 2.683 2.828 2.957 2.957  n %d  "
               "gdt 1 1 1 1  gpu 97%%  fb 2%%\n")
        with open(os.path.join(d, "frame_timing.txt"), "w") as f:
            f.write("# ==== session  pid 1\n" + "".join(sec % (i, 5) for i in range(30))     # ancienne session ignorée
                    + "# ==== session  pid 2\n" + "".join(sec % (i, 2) for i in range(30)) + "# end  frames 1800\n")
        with open(os.path.join(d, "dlssg_sm86.log"), "w") as f:
            f.write('10:00:00.000 2 game.exe I {"event":"fg_gate_create_feature","parameters":{"multi_frame_count":2}}\n')
        exe = os.path.join(t, "game.exe")
        st = _frame_stats(exe)
        assert st and st["mult"] == 3 and abs(st["real"] - 61.2) < 1e-9 and st["gpu"] == 97 and abs(st["fg"] - 2.683) < 1e-9
        assert measured_mult(exe) == 3 and read(exe)["found"]
        assert any("3X" in x for x in mfg_verdict(exe, "en"))
        assert st["plateau"] is None                                   # GPU à 97 % : c'est la carte qui limite
    # menus/pauses (FG coupée, n=0) ignorés ; base basse = 10e centile
    menu = [(200.0, 40.0, None, 0)] * 30
    play = [(60.0 + (i % 20), 99.0, 3.0, 2) for i in range(100)]
    sm = _summary(menu + play)
    assert sm["seconds"] == 100 and 60 <= sm["low"] < 63 and sm["plateau"] is None and sm["mult"] == 3
    # limiteur : FPS réels figés à 60 avec un GPU à 70 % -> plateau 60
    cap = _summary([(60.0 + (i % 3) * 0.1, 70.0, 3.0, 2) for i in range(90)])
    assert cap["plateau"] and abs(cap["plateau"] - 60.1) < 0.2
    print("loganalyze selftest OK")


if __name__ == "__main__":
    _selftest()
