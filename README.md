# RobotLab Web — Virtual Robotics Design Studio

🇫🇷 [Français](#-français) · 🇬🇧 [English](#-english)

> **Handoff note / Note de passation** — This README is written so that another engineer or AI assistant (e.g. ChatGPT) can understand the project and continue it without prior context. Read sections *Rules*, *Architecture* and *Status* first. / Ce README est écrit pour qu'un autre ingénieur ou assistant IA (ex. ChatGPT) comprenne le projet et le poursuive sans contexte préalable. Lire d'abord *Règles*, *Architecture* et *État d'avancement*.

---

## 🇫🇷 Français

### 1. L'idée en une phrase

**RobotLab Web est un atelier d'ingénierie robotique virtuel qui permet de concevoir, calculer, tester et valider un robot avant sa construction physique.**

### 2. Vision

RobotLab Web doit couvrir à terme tout le cycle de développement d'un robot :

```
Idée → Conception → Dimensionnement → Simulation → Vérification → Fabrication → Tests physiques
```

Ambition : réduire les erreurs de conception, les dépenses inutiles et les modifications matérielles coûteuses.

### 3. Robot cible

Le robot visé par le projet est un **robot médiateur** (robot mobile évoluant parmi des visiteurs). Cela justifie notamment : robot différentiel, capteurs d'environnement (LiDAR 2D, ultrasons, caméra), zones interdites, simulation de déplacements de visiteurs, sécurité des personnes. Le détail du cahier des charges du robot (dimensions, composants réels, lieu d'usage) **n'est pas encore fourni** : ne pas l'inventer.

### 4. Règles non négociables

1. Exactitude des calculs avant esthétique.
2. Architecture modulaire ; séparation stricte interface / logique métier / calculs.
3. Unités physiques explicites (SI par défaut : V, A, W, N·m, kg, m, s).
4. Validation de toutes les entrées ; gestion des cas limites.
5. **Traçabilité** : chaque résultat porte valeur, unité, formule, entrées, hypothèses, statut, limites (`CalcResult`).
6. **Aucune valeur technique inventée.** Donnée inconnue = `None`, jamais `0` ni valeur par défaut. Le calcul renvoie alors « non évaluable » avec la liste des champs manquants.
7. Ne jamais attribuer de caractéristiques à une référence commerciale sans source vérifiable. La bibliothèque de composants démarre **vide**.
8. Ne jamais présenter une estimation comme une mesure réelle ; ne jamais prétendre qu'un calcul est certifié.
9. Aucune fonctionnalité déclarée terminée sans tests exécutés.
10. Ne jamais masquer un avertissement pour embellir l'interface.
11. Le frontend n'est **jamais** la source de vérité des calculs : tout calcul technique vit dans le backend.
12. Décision importante, changement incompatible ou hypothèse non confirmée → demander validation au propriétaire du projet.

### 5. Architecture

Monorepo :

```
backend/      Python 3.13 + FastAPI + Pydantic + SQLAlchemy
  app/
    api/             Présentation HTTP (routes, schémas)
    application/     Cas d'utilisation, services
    domain/          Modèles métier, grandeurs physiques, CalcResult
    engines/         Moteurs de calcul purs (électrique, batterie, motorisation, mécanique, diagnostic)
    simulation/      Simulateur 2D, indépendant de toute interface
    infrastructure/  Base de données, import/export, rapports
  tests/             unit/, integration/, reference/, regression/
frontend/     React + TypeScript + Vite + Tailwind + Vitest (i18n FR/EN)
docs/         PLAN, CONVENTIONS, ADR
```

Les moteurs (`engines/`) sont des **fonctions pures** : pas d'accès base de données, pas de FastAPI.

### 6. Décisions techniques actées

- Grandeurs physiques : types explicites, stockage en **unités SI**, conversion aux frontières uniquement. Pas de `pint` (voir `docs/adr/0001`).
- `CalcResult` obligatoire pour tout résultat de calcul (voir `docs/CONVENTIONS.md`).
- Données manquantes : `None` + résultat « non évaluable ».
- Projet stocké en JSON versionné (`schema_version`) avec migrations explicites.
- Simulation : pas de temps fixe, graine aléatoire explicite, reproductible.
- Interface bilingue FR/EN dès le départ (i18n), aucun texte en dur dans les composants.

### 7. Plan de développement (ordre de priorité)

| # | Étape | État |
|---|---|---|
| 0 | Fondations (monorepo, outillage, `CalcResult`, unités, i18n, CI) | **Fait (voir État d'avancement)** |
| 1 | Modèles de données et gestion des projets | **Fait** |
| 2 | Bibliothèque de composants | En cours |
| 3 | Moteur de calcul électrique | À faire |
| 4 | Moteur batterie et autonomie | À faire |
| 5 | Moteur motorisation | À faire |
| 6 | Conception mécanique | À faire |
| 7 | Centre de diagnostic | À faire |
| 8 | Éditeur de circuit visuel | À faire |
| 9 | Capteurs et compatibilité d'interfaces | À faire |
| 10 | Simulation 2D | À faire |
| 11 | Rapports PDF/CSV | À faire |
| 12 | Interface complète (13 entrées de navigation) | À faire |

Détail : `docs/PLAN.md`.

### 8. État d'avancement

Voir la section *Status* en anglais ci-dessous, tenue à jour à chaque étape (source unique : `docs/PLAN.md`). Étape 1 terminée : gestion de projets, import/export JSON, autosauvegarde et historique des révisions. CI verte : 24 tests backend et 9 tests frontend réussis. Étape 2 en cours : bibliothèque de composants vide avec fiches structurées, états de vérification et import/export JSON.

### 9. Démarrage rapide

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check . && mypy app
uvicorn app.main:app --reload     # http://localhost:8000/docs

# Frontend
cd frontend
npm install
npm test
npm run dev                        # http://localhost:5173
```

### 10. Pour continuer (checklist de reprise)

1. Lire ce README, `docs/CONVENTIONS.md`, `docs/PLAN.md`, `docs/adr/`.
2. Lancer les tests backend et frontend ; ils doivent passer avant toute modification.
3. Prendre la première étape « À faire » du plan, la développer avec ses tests.
4. Mettre à jour `docs/PLAN.md` et ce README à la fin de chaque étape.
5. Poser les questions ouvertes au propriétaire plutôt que d'inventer des données.

### 11. Questions ouvertes

- Dimensions, composants réels (références + datasheets) et lieu d'usage du robot médiateur.
- Choix du moteur PDF (ReportLab ou WeasyPrint), à trancher à l'étape 11.

---

## 🇬🇧 English

### 1. The idea in one sentence

**RobotLab Web is a virtual robotics engineering workshop that lets you design, calculate, test and validate a robot before physically building it.**

### 2. Vision

RobotLab Web should eventually cover the whole robot development cycle:

```
Idea → Design → Sizing → Simulation → Verification → Manufacturing → Physical testing
```

Ambition: reduce design errors, wasted spending and costly hardware changes.

### 3. Target robot

The target is a **mediator robot** (a mobile robot operating among visitors). This motivates: differential drive, environment sensing (2D LiDAR, ultrasonic, camera), forbidden zones, visitor-movement simulation, and people safety. The robot's detailed specification (dimensions, real components, place of use) has **not been provided yet** — do not invent it.

### 4. Non-negotiable rules

1. Calculation correctness before aesthetics.
2. Modular architecture; strict separation of UI / business logic / calculations.
3. Explicit physical units (SI by default: V, A, W, N·m, kg, m, s).
4. Validate every input; handle edge cases.
5. **Traceability**: every result carries value, unit, formula, inputs, assumptions, status, limits (`CalcResult`).
6. **Never invent technical values.** Unknown data = `None`, never `0` or a default. The calculation then returns "not evaluable" with the list of missing fields.
7. Never attach characteristics to a commercial part number without a verifiable source. The component library starts **empty**.
8. Never present an estimate as a measurement; never claim a calculation is certified.
9. No feature is "done" without executed tests.
10. Never hide a warning to make the UI look nicer.
11. The frontend is **never** the source of truth for calculations: all technical computation lives in the backend.
12. Important decision, breaking change or unconfirmed technical assumption → ask the project owner.

### 5. Architecture

See the tree in the French section. `engines/` contains **pure functions** (no database, no FastAPI). Layers: presentation → application → domain → engines → infrastructure.

### 6. Decisions already made

- Physical quantities: explicit types, **SI storage**, conversion at the boundaries only. No `pint` (see `docs/adr/0001`).
- `CalcResult` mandatory for any calculation output (see `docs/CONVENTIONS.md`).
- Missing data: `None` + "not evaluable" result.
- Project stored as versioned JSON (`schema_version`) with explicit migrations.
- Simulation: fixed time step, explicit random seed, reproducible.
- Bilingual FR/EN UI from day one (i18n); no hard-coded strings in components.

### 7. Status

Single source of truth: `docs/PLAN.md`.

**Step 0 — Foundations: DONE** (verified by running the test suites, linters and build — see commit history).

- Backend: FastAPI skeleton with `/health`, `CalcResult`, SI physical quantities (`domain/units.py`), tests passing.
- Frontend: Vite + React + TS + Tailwind, FR/EN i18n, the 13-entry side navigation (pages are placeholders **clearly labelled "not implemented yet"** — no fake features), Vitest passing.
- CI: GitHub Actions (backend + frontend).

**Step 1 — DONE** — versioned project management, SQLite persistence, CRUD, duplication, JSON import/export, autosave and revision history. GitHub Actions passed: 24 backend tests, 9 frontend tests, Ruff, mypy, frontend lint/typecheck/build.\n\n**Step 2 — IN PROGRESS** — empty component library with structured records, verification states and JSON import/export.

### 8. Quick start

See section 9 of the French part (commands are identical).

### 9. Handoff checklist

1. Read this README, `docs/CONVENTIONS.md`, `docs/PLAN.md`, `docs/adr/`.
2. Run backend and frontend tests; they must pass before any change.
3. Take the first "To do" step in the plan and implement it with tests.
4. Update `docs/PLAN.md` and this README at the end of each step.
5. Ask the owner open questions instead of inventing data.

### 10. Disclaimer

Results are **design aids**, not industrially certified calculations. Physical prototyping and measurement remain necessary.
