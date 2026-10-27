# YogoMFG

**DLSS Frame Generation jusqu'à x6 sur les cartes NVIDIA RTX 20 et 30 — en quelques clics.**

🇬🇧 [Read in English](README.md)

YogoMFG installe le **mod Frame Generation SM86 / SM75** (open source) dans tes jeux Steam, règle le profil NVIDIA du jeu
(cap FPS, G-Sync / FreeSync) et te laisse choisir le multiplicateur de **x2 à x6**. Il mesure ensuite ta session de jeu et
t'explique, en mots simples, ce qui limite tes FPS.

> Testé par l'auteur : RTX 3070 8 Go, Ryzen 7 8700F, écran 1440p 180 Hz G-Sync, **Crimson Desert** en x6 ≈ 160 FPS
> affichés, fluide en régime stable. Tes résultats dépendent de ton jeu, de ta carte et de tes réglages.

> ⛔ **Jeux solo / hors ligne uniquement.** N'utilise jamais YogoMFG sur un jeu en ligne ou avec anti-cheat :
> risque de bannissement définitif. Lis [ANTICHEAT.md](ANTICHEAT.md) (FR, EN, ES, DE, PT-BR, IT, 中文).

---

## Un projet gratuit, fait pour aider

YogoMFG est un projet **à but non lucratif et gratuit**. Il existe par entraide : améliorer le confort de jeu de chacun et
**prolonger la vie des anciennes cartes graphiques** au lieu de les jeter.

Un grand **merci** à toutes celles et ceux qui téléchargent, testent et partagent. C'est une bêta : vos retours la font progresser.

- Un bug ? Un jeu qui se comporte bizarrement ? Une question ? **Dites-le-nous : nous sommes là pour résoudre vos problèmes.**
- Le plus simple pour signaler : joue 3 à 5 minutes avec *Avancé → Mesurer la session* coché, ferme le jeu, puis
  **Analyser → 📦 Exporter le rapport** et envoie-nous le `.zip` (réglages et logs, sans ton nom d'utilisateur Windows).
- Ouvre un ticket (issue) sur la page du projet, ou contacte directement l'auteur.

Si YogoMFG t'a aidé et que tu veux soutenir le travail : ☕ **[ko-fi.com/lahlouyoussef](https://ko-fi.com/lahlouyoussef)**
Le lien Ko-fi accepte **toutes sortes de soutiens** : un café, un **don** ponctuel, un abonnement mensuel, ou simplement un
message d'encouragement. Jamais obligatoire — l'outil reste gratuit.

---

![Fenêtre principale](docs/img/01-main.png)

*(Captures en anglais ; l'interface est disponible en français via le bouton globe.)*

## Ce qu'il fait

- **Une grille de jaquettes pour tous tes jeux** : bibliothèques Steam trouvées automatiquement, ajout d'un dossier ou d'un jeu isolé.
- **Te dit si un jeu supporte la Frame Generation**, et son vrai plafond (certains jeux plafonnent à x4).
- **Multiplicateur x2 → x6**, modifiable ensuite sans tout réinstaller. Règle l'override du pilote NVIDIA pour toi.
- **Mode simple** (un choix + un bouton) et panneau **Avancé** replié où chaque réglage est expliqué.
- **Réglage du profil NVIDIA** par jeu (cap FPS, VRR). Sauvegardes exportées d'abord, chaque écriture est relue et vérifiée.
- **Gestion des upscalers** : détecte DLSS / FSR / XeSS dans le jeu et met la DLL à jour.
- **Mesure et analyse de session** : FPS réels, temps GPU, lien PCIe, limites de puissance et de chaleur → un verdict clair.
- **7 langues** avec drapeaux : English, Français, Español, Deutsch, Português, Русский, 中文 (bouton globe).
- **Retrait propre** : *Retirer* remet les fichiers d'origine du jeu.

## Ce qu'il te faut

Windows 10/11 64 bits · carte NVIDIA **RTX 20 ou 30** · pilote NVIDIA récent · droits administrateur · un jeu Steam qui a
déjà la DLSS Frame Generation (Streamline `sl.dlss_g`).

Inutile sur RTX 40/50 : elles ont la Frame Generation en natif.

## Installation et utilisation

1. Lance `YogoMFG-Setup-<version>.exe` (ou le `YogoMFG.exe` portable) et accepte l'avertissement anti-cheat.
2. Clique la **jaquette** de ton jeu. YogoMFG dit si le jeu supporte la Frame Generation et quel est son plafond.
3. **Options & Appliquer** → choisis le multiplicateur → **Optimiser**.
4. Lance le jeu avec le bouton **Launch** de YogoMFG.
5. Pour changer de multiplicateur ensuite : la ligne rapide de la fiche du jeu, puis relance le jeu.

Tes réglages sont dans `%LOCALAPPDATA%\YogoMFG`.

### Pas à pas

1. **Choisis ton jeu** : clique sa jaquette. La fiche à droite dit si le jeu supporte la Frame Generation, son plugin DLSS-G (donc son plafond) et si YogoMFG est déjà installé.
   ![Fiche du jeu](docs/img/02-game.png)
2. **Choisis le multiplicateur** : *Options & Appliquer* pose une seule question. Le reste est décidé pour toi ; *Avancé* est replié et chaque réglage y est expliqué.
   ![Options](docs/img/03-options.png)
3. **(Facultatif) Optimiser NVIDIA** : un objectif, la liste claire de ce qui sera écrit, et un bouton pour tout remettre à l'origine. Sur écran G-Sync / FreeSync, le V-Sync n'est jamais touché.
   ![Profil NVIDIA](docs/img/04-nvidia.png)
4. **Joue, puis Analyse** : lance avec **Launch**, puis ouvre **Analyser**. *Exporter le rapport* crée le `.zip` à nous envoyer en cas de souci.
   ![Analyse](docs/img/05-analyze.png)
5. **Langue** : bouton globe en haut à droite.
   ![Langues](docs/img/06-languages.png)

## À savoir (bêta)

- **x5 / x6** demandent un jeu avec un plugin DLSS-G récent (≥ 2.11.1). Sinon le jeu plafonne à x4 ou moins.
- Avec le *multiplicateur imposé* (activé par défaut), **ne change pas** la Frame Generation dans le menu du jeu et
  n'utilise pas « Dynamique » : change-la dans YogoMFG.
- Sur écran G-Sync / FreeSync, YogoMFG **ne force jamais le V-Sync**.
- Un autre mod de Frame Generation dans le dossier du jeu (OptiScaler, dlssg-to-fsr3, DLSS Enabler…) bloque l'application :
  retire-le d'abord.
- Le x6 demande de la mémoire vidéo : sur une carte 8 Go, baisse les textures si tu as des saccades. La Frame Generation
  multiplie les FPS *réels* : vise 30+ FPS réels avant génération.
- YogoMFG écrit dans le **profil pilote NVIDIA** du jeu. N'utilise pas « Delete » sur un profil de jeu dans NVIDIA
  Profile Inspector.

## Feuille de route — prochaine fonctionnalité

**Frame Generation pour les jeux qui ne la supportent pas** (anciens jeux), dans l'esprit de Lossless Scaling : très
fluide, sans perte de qualité visible. C'est la prochaine mission, prévue après une semaine de tests élargis (plus de jeux,
plus de logs, dont Resident Evil Requiem). Vos rapports la façonnent directement.

## Crédits

Ce projet **repose sur le travail d'autres personnes**. Un grand merci à :

- **[sdli1995](https://github.com/sdli1995)** — créateur original du **mod Multi-Frame Generation SM86 / SM75**
  ([dlssg_for_sm86](https://github.com/sdli1995/dlssg_for_sm86)). Sans ce mod, rien de tout ça n'existerait.
  YogoMFG est une application construite autour de lui, elle ne le remplace pas — va mettre une étoile au dépôt d'origine.
- **[Coldwood1026](https://github.com/Coldwood1026/dlssg_for_sm75)** — la famille de kernels SM75 (RTX série 20).
- **[Orbmu2k](https://github.com/Orbmu2k/nvidiaProfileInspector)** — NVIDIA Profile Inspector, utilisé pour lire et écrire
  les profils pilote.
- **[beeradmoore](https://github.com/beeradmoore/dlss-swapper)** — DLSS Swapper, dont le manifeste public de DLL sert aux
  mises à jour d'upscalers.
- **Claude Code** (Anthropic) — contribution au développement de YogoMFG, via l'extension Visual Studio Code.
- Les **testeurs** et toutes les personnes qui envoient leurs retours.

## Licences et mentions légales

- Code source de YogoMFG : **MIT** — voir [LICENSE](LICENSE).
- Le code du mod **dlssg_sm86** est MIT ; les DLL NVIDIA et kernels compilés qu'il fournit sont binaires et **non** MIT.
- NVIDIA Profile Inspector : MIT. Logo Ko-fi © Ko-fi Labs.
- Textes complets et mentions : dossier [legal/](legal/).
- Projet indépendant, **non affilié à NVIDIA, AMD, Intel, Valve ni à un éditeur de jeux**. Utilisation à tes risques, sans garantie.

## Compiler depuis les sources

```
pip install -r requirements.txt
python yogomfg.py          # lancer
scripts\build.bat          # construit dist\YogoMFG\YogoMFG.exe (lancer en administrateur pour le panneau NVIDIA)
```

Le payload du mod (`mod/`) et `tools/npi/` ne sont pas dans le dépôt : place-les avant de compiler.
