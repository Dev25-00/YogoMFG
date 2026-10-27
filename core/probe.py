"""Sonde de session : enregistre le GPU (nvidia-smi) et chaque cœur du processeur pendant que tu joues,
puis explique les chutes de puissance (mémoire vidéo pleine, chaleur, limite de puissance, un cœur CPU à fond,
lien PCIe réduit). Aucune écriture dans le pilote, aucun fichier du jeu touché.
"""
import os, ctypes, subprocess, threading, statistics
from core import i18n

_NO_WINDOW = 0x08000000
_Q = ("power.draw,clocks.gr,temperature.gpu,utilization.gpu,memory.used,memory.total,"
      "pcie.link.gen.current,pcie.link.gen.max,pcie.link.width.current,pcie.link.width.max,"
      "clocks_throttle_reasons.active")
_MAX_SAMPLES = 2400          # 40 min à 1 échantillon / s

# bits NVML « clocks throttle reasons » -> (libellé FR, libellé EN) ; 0x1 (idle) et 0x2 sont ignorés
_REASONS = {0x4: ("limite de puissance", "power limit"), 0x8: ("ralentissement matériel", "hardware slowdown"),
            0x20: ("chaleur (logiciel)", "thermal (software)"), 0x40: ("chaleur (matériel)", "thermal (hardware)"),
            0x80: ("frein de puissance", "power brake")}


class _Cpu:
    """Charge de chaque cœur logique (NtQuerySystemInformation, classe 8) sans dépendance externe."""
    SIZE = 48

    def __init__(self):
        self.n = os.cpu_count() or 1
        self.prev = None

    def _read(self):
        buf = ctypes.create_string_buffer(self.SIZE * (self.n + 8))
        ret = ctypes.c_ulong(0)
        if ctypes.windll.ntdll.NtQuerySystemInformation(8, buf, len(buf), ctypes.byref(ret)) != 0:
            return None
        out = []
        for i in range(ret.value // self.SIZE):
            idle, kern, user = (int.from_bytes(buf.raw[i * self.SIZE + o:i * self.SIZE + o + 8], "little")
                                for o in (0, 8, 16))
            out.append((idle, kern + user))                     # KernelTime contient déjà l'idle
        return out

    def busy(self):
        """Liste des % d'occupation par cœur depuis le dernier appel ([] au premier)."""
        cur = self._read()
        res = []
        if cur and self.prev and len(cur) == len(self.prev):
            for (i0, t0), (i1, t1) in zip(self.prev, cur):
                dt = t1 - t0
                res.append(max(0.0, min(100.0, 100.0 * (1 - (i1 - i0) / dt))) if dt > 0 else 0.0)
        self.prev = cur
        return res


def _num(s, default=0.0):
    try:
        return float(s)
    except (TypeError, ValueError):
        return default


class Probe:
    """Démarre/arrête l'enregistrement ; `rows` = [dict] une ligne par seconde."""

    def __init__(self):
        self.rows = []
        self._stop = threading.Event()
        self._thread = None

    @property
    def running(self):
        return bool(self._thread and self._thread.is_alive())

    def start(self):
        if self.running:
            return
        self.rows, self._stop = [], threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        p = getattr(self, "_proc", None)
        if p is not None:
            try:
                p.terminate()          # débloque la lecture même si nvidia-smi ne répond plus
            except OSError:
                pass
        if self._thread:
            self._thread.join(2)

    def _run(self):
        cpu = _Cpu()
        cpu.busy()
        try:
            p = subprocess.Popen(["nvidia-smi", "--query-gpu=" + _Q, "--format=csv,noheader,nounits", "-lms", "1000"],
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                                 creationflags=_NO_WINDOW)
        except OSError:
            return
        self._proc = p
        try:
            for line in p.stdout:
                if self._stop.is_set() or len(self.rows) >= _MAX_SAMPLES:
                    break
                f = [x.strip() for x in line.split(",")]
                if len(f) < 11:
                    continue
                cores = cpu.busy()
                try:
                    thr = int(f[10], 16)
                except ValueError:
                    thr = 0
                self.rows.append({
                    "power": _num(f[0]), "clk": _num(f[1]), "temp": _num(f[2]), "util": _num(f[3]),
                    "vram": _num(f[4]), "vram_tot": _num(f[5], 1), "gen": _num(f[6]), "gen_max": _num(f[7]),
                    "w": _num(f[8]), "w_max": _num(f[9]), "thr": thr,
                    "cpu_max": max(cores) if cores else 0.0,
                    "cpu_avg": (sum(cores) / len(cores)) if cores else 0.0})
        finally:
            try:
                p.terminate()
                p.wait(2)
                p.stdout.close()
            except (OSError, subprocess.SubprocessError, ValueError):
                pass

    def save_csv(self, path):
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("power_w,clock_mhz,temp_c,gpu_util,vram_mb,vram_total_mb,pcie_gen,pcie_w,throttle,cpu_max,cpu_avg\n")
                for r in self.rows:
                    f.write(",".join(str(round(r[k], 1)) if k != "thr" else hex(r[k]) for k in
                                     ("power", "clk", "temp", "util", "vram", "vram_tot", "gen", "w", "thr",
                                      "cpu_max", "cpu_avg")) + "\n")
        except OSError:
            pass


_T = {
    "fr": {
        "few": "Sonde : pas assez de données (joue au moins 1 minute avec la sonde active, puis clique Analyser).",
        "head": "Sonde : %d s de jeu, puissance habituelle %d W, température max %d °C, mémoire vidéo max %d/%d Mo.",
        "nodrop": "Aucune chute de puissance marquée pendant cette session.",
        "drops": "%d chute(s) de puissance, %d s au total (en dessous de %d W). Pendant les chutes : GPU %d %%, mémoire %d %%, cœur CPU max %d %%.",
        "vram": "→ Mémoire vidéo pleine : la carte attend la mémoire du PC. Baisse les textures ou le ray tracing.",
        "thr": "→ Limite active pendant les chutes : %s.",
        "cpu": "→ Un cœur du processeur est à fond : c'est le processeur ou le moteur du jeu qui limite.",
        "none": "→ Pas de cause matérielle claire (mémoire, chaleur, limite de puissance, processeur) : le jeu lui-même ralentit la carte (chargement de zone, moteur).",
        "pcie": "ℹ Lien PCIe en charge : PCIe %d x%d (maximum de la carte : PCIe %d x%d).",
        "pcie_warn": "⚠ Ta carte tourne en PCIe x%d au lieu de x%d : c'est trop étroit pour une carte de 8 Go (saccades dès que la mémoire déborde). Vérifie le slot (celui du haut, relié au processeur), que la carte est bien enfoncée, et le BIOS (réglage des lignes PCIe).",
    },
    "en": {
        "few": "Probe: not enough data (play at least 1 minute with the probe on, then click Analyze).",
        "head": "Probe: %d s of play, usual power %d W, max temperature %d °C, max video memory %d/%d MB.",
        "nodrop": "No marked power drop during this session.",
        "drops": "%d power drop(s), %d s in total (below %d W). During drops: GPU %d %%, memory %d %%, max CPU core %d %%.",
        "vram": "→ Video memory is full: the card waits for system memory. Lower textures or ray tracing.",
        "thr": "→ Active limit during drops: %s.",
        "cpu": "→ One CPU core is maxed out: the CPU or the game engine is the limit.",
        "none": "→ No clear hardware cause (memory, heat, power limit, CPU): the game itself slows the card down (zone loading, engine).",
        "pcie": "ℹ PCIe link under load: PCIe %d x%d (card maximum: PCIe %d x%d).",
        "pcie_warn": "⚠ Your card runs at PCIe x%d instead of x%d: too narrow for an 8 GB card (stutter as soon as video memory overflows). Check the slot (the top one, wired to the CPU), that the card is fully seated, and the BIOS (PCIe lane settings).",
    },
}


def _pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(len(xs) * q))] if xs else 0.0


def report(rows, lang="fr"):
    """Lignes d'explication en mots simples à partir des échantillons."""
    t = {**_T["en"], **(_T.get(lang) or i18n.section("PROBE", lang))}
    names = i18n.section("REASONS", lang)
    game = [r for r in rows if r["power"] >= 60]           # sous 60 W : bureau, pas du jeu
    if len(game) < 30:
        return [t["few"]]
    ref = _pct([r["power"] for r in game], 0.90)
    lim = 0.75 * ref
    low = [r for r in game if r["power"] < lim]
    episodes, run = 0, 0
    for r in rows:
        if 60 <= r["power"] < lim:
            run += 1
        else:
            episodes += run >= 2
            run = 0
    episodes += run >= 2
    vmax = max(r["vram"] for r in game)
    out = [t["head"] % (len(game), ref, max(r["temp"] for r in game), vmax, game[0]["vram_tot"])]
    load = [r for r in game if r["util"] >= 60]
    if load:
        out.append(t["pcie"] % (statistics.median(r["gen"] for r in load), statistics.median(r["w"] for r in load),
                                load[0]["gen_max"], load[0]["w_max"]))
        wmed = statistics.median(r["w"] for r in load)
        if wmed <= 4 and load[0]["w_max"] >= 8:
            out.append(t["pcie_warn"] % (wmed, load[0]["w_max"]))
    if len(low) < 3:
        return out + [t["nodrop"]]
    vp = statistics.median(100.0 * r["vram"] / max(r["vram_tot"], 1) for r in low)
    cm = statistics.median(r["cpu_max"] for r in low)
    ut = statistics.median(r["util"] for r in low)
    out.append(t["drops"] % (episodes, len(low), lim, ut, vp, cm))
    reasons = {}
    for r in low:
        for bit, names in _REASONS.items():
            if r["thr"] & bit:
                reasons[bit] = reasons.get(bit, 0) + 1
    why = False
    if vp >= 93 or vmax >= 0.97 * game[0]["vram_tot"]:
        out.append(t["vram"]); why = True
    act = [b for b, n in reasons.items() if n >= 0.3 * len(low)]
    if act:
        out.append(t["thr"] % ", ".join(names.get(b) or _REASONS[b][0 if lang == "fr" else 1] for b in act)); why = True
    if cm >= 88 and ut < 85:
        out.append(t["cpu"]); why = True
    if not why:
        out.append(t["none"])
    return out
