# YogoMFG 0.6.2 beta — Frame Generation jusqu'à x6 sur RTX 20 / 30

> ⛔ **Jeux solo / hors ligne uniquement.** N'utilise jamais YogoMFG sur un jeu en ligne ou avec anti-cheat :
> risque de bannissement définitif. Détails (FR, EN, ES, DE, PT, IT, 中文) dans [ANTICHEAT.md](ANTICHEAT.md).

## Ce que c'est
YogoMFG installe pour toi, en quelques clics, le mod open source **dlssg_for_sm86** (Frame Generation NVIDIA sur RTX 20/30)
dans un jeu Steam, règle le profil NVIDIA du jeu (cap FPS, G-Sync) et te laisse choisir le multiplicateur **de x2 à x6**.
Il mesure aussi ta session de jeu pour t'expliquer ce qui te limite.

Testé par l'auteur : RTX 3070 8 Go, Ryzen 7 8700F, écran 1440p 180 Hz G-Sync, **Crimson Desert** en x6 ≈ 160 FPS affichés,
sans micro-saccade en régime stable. Tes résultats dépendent de ton jeu, de ta carte et de tes réglages.

## Ce qu'il te faut
Windows 10/11 64 bits · carte NVIDIA RTX 20 ou 30 · pilote NVIDIA récent · droits administrateur · un jeu Steam avec
Frame Generation (DLSS-G / Streamline).

## Installation et utilisation
1. Lance `YogoMFG-Setup-0.6.2-beta.exe` (ou le `YogoMFG.exe` portable) et accepte l'avertissement anti-cheat.
2. Clique la **jaquette** de ton jeu. L'appli dit si le jeu supporte la Frame Generation et quel plafond il a.
3. **Options & Appliquer** → choisis le multiplicateur → **Optimiser**. (« Avancé » : réglages fins, tout est expliqué.)
4. Lance le jeu avec le bouton **Launch** de YogoMFG. Pour changer de multiplicateur ensuite : la ligne
   « Changer vite le multiplicateur » de la fiche du jeu, puis relance le jeu.
5. **Retirer** remet les fichiers d'origine du jeu.

## À savoir (beta)
- **x5 / x6** demandent un jeu avec un plugin DLSS-G récent (≥ 2.11.1). Sinon le jeu plafonne à x4 ou moins.
- Avec « Multiplicateur imposé » (activé par défaut), **ne change pas la Frame Generation dans le menu du jeu** et
  n'utilise pas « Dynamique » : change-la dans YogoMFG.
- Avec un écran G-Sync / FreeSync, YogoMFG **ne force jamais le V-Sync**.
- Un autre mod de Frame Generation dans le dossier du jeu (OptiScaler, dlssg-to-fsr3, DLSS Enabler…) bloque l'application :
  retire-le d'abord.
- Le x6 sur une carte 8 Go demande de la mémoire vidéo : baisse les textures si tu as des saccades.
- L'outil écrit dans le **pilote NVIDIA** (profil du jeu). Il relit et vérifie ses écritures. N'utilise pas le bouton
  « Delete » de NVIDIA Profile Inspector sur un profil de jeu.

## Un problème ? Envoie un rapport
Joue 3 à 5 minutes avec « Avancé → Mesurer la session » coché et le jeu lancé par **Launch**, ferme le jeu, puis
**Analyser → 📦 Exporter le rapport**. Envoie le `.zip` (réglages et logs, sans ton nom d'utilisateur).

## Prochaine fonctionnalité
Frame Generation pour les **jeux qui ne la supportent pas** (anciens jeux), façon Lossless Scaling : très fluide, sans perte
de qualité visible. Prévue après une semaine de tests élargis : tes rapports comptent.

## Merci
Projet gratuit et à but non lucratif, fait pour l'entraide et pour prolonger la vie des anciennes cartes. Merci aux testeurs !
Mod original SM86/SM75 : **sdli1995** — https://github.com/sdli1995/dlssg_for_sm86 · développé avec Claude Code (extension VS Code).
Plus de détails : [README.md](README.md) · [README.fr.md](README.fr.md).

## Légal
YogoMFG (code) : licence MIT. Il embarque le mod **dlssg_sm86** (code MIT, mais DLL NVIDIA et noyaux fournis en binaire,
non couverts par la licence MIT) et **NVIDIA Profile Inspector** (MIT). Voir le dossier `legal\`. Projet indépendant, non
affilié à NVIDIA, AMD ou Intel. Utilisation à tes risques, sans garantie.

---

# YogoMFG 0.6.2 beta — Frame Generation up to x6 on RTX 20 / 30 (English)

> ⛔ **Single-player / offline games only.** Never use YogoMFG in online games or games with anti-cheat: permanent-ban
> risk. See [ANTICHEAT.md](ANTICHEAT.md).

**What it is:** a one-click installer for the open-source **dlssg_for_sm86** mod (NVIDIA Frame Generation on RTX 20/30),
plus per-game NVIDIA profile tuning (FPS cap, G-Sync) and a free **x2 to x6** multiplier. It also measures your play
session and explains what limits you.

**Needs:** Windows 10/11 64-bit, NVIDIA RTX 20/30, recent NVIDIA driver, administrator rights, a Steam game with
DLSS-G / Streamline Frame Generation.

**Use:** run the installer → click your game's cover → *Options & Apply* → pick the multiplier → *Optimize* → start the
game with **Launch**. Change multiplier later with the quick row on the game's card. *Remove* restores the original files.

**Good to know:** x5/x6 need a game DLSS-G plugin ≥ 2.11.1 · with the enforced multiplier, do not change Frame Generation
in the game menu · YogoMFG never forces V-Sync on G-Sync/FreeSync screens · other FG mods in the game folder block
applying · 8 GB cards: lower textures if you stutter · it writes the NVIDIA driver profile (verified by reading back).

**Problem?** *Analyze → 📦 Export report* and send the `.zip` (settings and logs, user name removed).

**Next feature:** Frame Generation for games that do not support it (Lossless Scaling style, smooth, no visible quality loss).

**Thanks:** free, non-profit project. Original SM86/SM75 mod by **sdli1995** — https://github.com/sdli1995/dlssg_for_sm86 ·
built with Claude Code (VS Code extension).

**Legal:** code MIT; bundles the **dlssg_sm86** mod (MIT code, NVIDIA DLLs/kernels binary-only, not MIT) and
**NVIDIA Profile Inspector** (MIT) — see `legal\`. Independent project, not affiliated with NVIDIA, AMD or Intel.
Use at your own risk, no warranty.
