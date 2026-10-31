# RobotLab Web — Virtual Robotics Design Studio

🇫🇷 [Français](#-français) · 🇬🇧 [English](#-english)

> **Handoff note / Note de passation** — This README is written so that another engineer or AI assistant can continue the project. Read sections *Rules*, *Architecture* and *Status* first.

---

## 🇫🇷 Français

### 1. L'idée en une phrase

**RobotLab Web est un atelier d'ingénierie robotique virtuel qui permet de concevoir, calculer, tester et valider un robot avant sa construction physique.**

### 2. Vision

Idée → Conception → Dimensionnement → Simulation → Vérification → Fabrication → Tests physiques.

### 3. Robot cible

Le robot visé est un **robot médiateur mobile** évoluant parmi des visiteurs. Les dimensions, composants réels et conditions d'usage détaillées ne sont pas encore confirmés : ne pas les inventer.

### 4. Règles non négociables

1. Exactitude des calculs avant esthétique.
2. Architecture modulaire ; séparation interface / logique métier / calculs.
3. Unités SI en interne.
4. Validation des entrées et gestion des cas limites.
5. Traçabilité de chaque calcul via `CalcResult`.
6. Donnée technique inconnue = `None`, jamais zéro ou valeur par défaut.
7. Bibliothèque de composants vide tant que les datasheets ne sont pas vérifiées.
8. Ne jamais présenter une estimation comme une mesure.
9. Aucune fonctionnalité déclarée terminée sans tests exécutés.
10. Le frontend n'est jamais la source de vérité des calculs.
11. Décision importante ou hypothèse non confirmée : demander validation.

### 5. Architecture

- `backend/` : Python 3.13, FastAPI, Pydantic, SQLAlchemy.
- `frontend/` : React, TypeScript, Vite, Tailwind, Vitest, i18n FR/EN.
- `docs/` : plan, conventions et décisions d'architecture.

Les moteurs de calcul restent des fonctions pures, indépendantes de la base et de FastAPI.

### 6. Format de projet

Les projets sont stockés dans un document JSON versionné par `schema_version`. La première version est `1`. Les imports d'une version inconnue sont refusés explicitement. Le contenu de conception démarre vide ; aucune caractéristique matérielle n'est préremplie.

### 7. État d'avancement

Source unique : `docs/PLAN.md`.

- **Étape 0 — Fondations : terminée par Claude.**
- **Étape 1 — Gestion des projets : en cours.** API CRUD, duplication, import/export JSON, historique de révisions, endpoint autosave et écrans de liste/détail ajoutés. L'exécution des tests et leur validation CI restent nécessaires avant de déclarer l'étape terminée.

### 8. Démarrage rapide

Backend :

```bash
cd backend
python3.13 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check . && ruff format --check . && mypy app
uvicorn app.main:app --reload
```

Frontend :

```bash
cd frontend
npm ci
npm test
npm run lint
npm run typecheck
npm run build
npm run dev
```

API : `http://localhost:8000/docs` · Frontend : `http://localhost:5173`.

---

## 🇬🇧 English

RobotLab Web is a virtual robotics engineering studio for designing, calculating, testing and validating a robot before physical construction.

### Rules

- Calculation correctness before aesthetics.
- Strict separation of UI, application logic, domain and calculation engines.
- SI units internally and traceable `CalcResult` outputs.
- Unknown technical data stays `None`; never invent specifications.
- The component library starts empty and must be populated from verified datasheets.
- No feature is marked done until tests have been executed.
- The frontend is not the source of truth for calculations.

### Architecture

- `backend/`: Python 3.13, FastAPI, Pydantic, SQLAlchemy.
- `frontend/`: React, TypeScript, Vite, Tailwind, Vitest, FR/EN i18n.
- `docs/`: development plan, conventions and architecture decisions.

### Project format

Projects use versioned JSON documents (`schema_version: 1`). Unsupported schema versions are rejected. New design data is empty by default.

### Status

See `docs/PLAN.md`. Step 0 is complete. Step 1 is implemented but remains in progress until backend/frontend tests, linters and builds pass in CI.
