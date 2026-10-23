"""Détection matériel: GPU via nvidia-smi, CPU/RAM via CIM. Lecture seule."""
import subprocess, re, json


def _run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=15,
                              creationflags=0x08000000).stdout  # no console window
    except Exception:
        return ""


def gpu():
    """Retourne dict GPU ou {} si pas de GPU NVIDIA / nvidia-smi absent."""
    out = _run(["nvidia-smi",
                "--query-gpu=name,memory.total,driver_version,utilization.gpu,clocks.gr",
                "--format=csv,noheader,nounits"])
    if not out.strip():
        return {}
    name, vram, drv, util, clk = [x.strip() for x in out.strip().splitlines()[0].split(",")]
    series = _series(name)
    return {"name": name, "vram_mb": int(float(vram)), "driver": drv,
            "util_pct": util, "clock_mhz": clk, "series": series,
            "sm": {"20": "SM75", "30": "SM86"}.get(series, "")}


def _series(name):
    m = re.search(r"RTX\s*(\d)0\d0", name)  # RTX 3070 -> "30", 4080 -> "40"
    return (m.group(1) + "0") if m else ""


def cpu_ram():
    ps = ("$c=Get-CimInstance Win32_Processor;"
          "$m=(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory;"
          "ConvertTo-Json @{cpu=$c.Name;ram=$m}")
    out = _run(["powershell", "-NoProfile", "-Command", ps])
    try:
        d = json.loads(out)
        return {"cpu": str(d.get("cpu", "")).strip(),
                "ram_gb": round(int(d.get("ram", 0)) / 1024**3)}
    except Exception:
        return {"cpu": "", "ram_gb": 0}


def refresh_hz():
    """Taux de rafraîchissement du moniteur principal (Hz), 0 si inconnu."""
    out = _run(["powershell", "-NoProfile", "-Command",
                "(Get-CimInstance Win32_VideoController | "
                "Where-Object CurrentRefreshRate | "
                "Select-Object -First 1).CurrentRefreshRate"])
    try:
        return int(out.strip().splitlines()[0])
    except (ValueError, IndexError):
        return 0


def summary():
    g, c = gpu(), cpu_ram()
    g.update(c)
    # Compatibilité mod: séries 20/30 seulement.
    if g.get("series") in ("40", "50"):
        g["warn"] = "Série 40/50: Frame Generation est natif, ce mod est inutile."
    elif g.get("series") not in ("20", "30"):
        g["warn"] = "GPU non reconnu comme RTX série 20/30 (SM75/SM86). Mod probablement inutile."
    else:
        g["warn"] = ""
    return g
