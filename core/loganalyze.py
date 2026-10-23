"""Analyse les logs du mod après une session de jeu.

Le mod écrit dans <dossier .exe>\\dlssg_sm86\\logs\\*.jsonl (Level>=2, FrameTiming=1).
Schéma non garanti -> parsing tolérant : on agrège tout champ numérique 'fps'/'ms',
on remonte les warnings/erreurs, et on compare au FPS cible pour guider l'utilisateur.
"""
import os, glob, json, statistics


def _logs_dir(exe_path):
    return os.path.join(os.path.dirname(exe_path), "dlssg_sm86", "logs")


def read(exe_path, max_lines=20000):
    """Retourne {found, files, fps[], gen_ms[], warnings[], errors[]}."""
    d = _logs_dir(exe_path)
    res = {"found": False, "files": [], "fps": [], "gen_ms": [], "warnings": [], "errors": []}
    files = sorted(glob.glob(os.path.join(d, "*.jsonl")), key=os.path.getmtime, reverse=True)
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
                line = line.strip()
                if not line:
                    continue
                try:
                    o = json.loads(line)
                except ValueError:
                    continue
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


def _med(xs):
    return round(statistics.median(xs), 1) if xs else None


def analyze(exe_path, fps_target, goal="fps", did=None):
    """Lit + synthétise. goal: 'fps' ou 'quality'. did: ce que l'utilisateur a fait in-game
    (dict bool: fg, reflex, rt, pt, vsync_off ; str: dlss). Retourne (lines, reco_cfg_delta)."""
    did = did or {}
    r = read(exe_path)
    lines, delta = [], {}
    if not r["found"]:
        lines = ["Aucun log mesuré trouvé (joue une session avec le mod chargé pour des chiffres réels)."]
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
