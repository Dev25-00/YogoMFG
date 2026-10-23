"""Conseils d'optimisation in-game selon la cible FPS et le GPU. Texte seul."""


def advise(fps_target, vram_mb=0, series="30", dlss_quality=""):
    """Retourne une liste de conseils à afficher (in-game + pilote)."""
    from core.inimaker import QUALITY_FR
    t = []
    if dlss_quality:
        t.append(f"DLSS Super Resolution : applique le profil « {QUALITY_FR.get(dlss_quality, dlss_quality)} » "
                 "dans les options du jeu (c'est ton choix).")
    elif fps_target <= 60:
        t.append("DLSS : mode Qualité suffit pour 60 FPS.")
    elif fps_target <= 120:
        t.append("DLSS : Balanced / Performance pour 120 FPS.")
    else:
        t.append("DLSS : Performance / Ultra Performance + baisser le path tracing pour 180+ FPS.")
    # Le Frame Generation a besoin d'un bon frame-rate de base, sinon artefacts.
    t.append("Frame Generation x4 part d'un frame-rate de base : vise ≥ 40-50 FPS réels "
             "avant génération, sinon baisse RT/PT ou la résolution de rendu.")
    t.append("Active Reflex (On+Boost) dans le jeu pour compenser la latence du FG.")
    t.append("V-Sync in-game : OFF (la synchro est gérée côté pilote).")
    if vram_mb and vram_mb <= 8192:
        t.append(f"VRAM {vram_mb} Mo : limite les textures en Ultra en 4K ; "
                 "Haute/Très haute tient mieux dans 8 Go.")
    t.append("Pilote : Mode de gestion de l'alimentation = Performances maximales (appliqué par YogoMFG).")
    t.append("Pilote : laisse le Mode faible latence sur Désactivé (Reflex gère déjà).")
    return t
