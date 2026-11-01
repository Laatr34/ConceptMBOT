# Development plan / Plan de développement

Single source of truth for progress. Update at the end of every step.
Source unique de l'avancement. À mettre à jour à chaque étape.

Status legend: `TODO`, `IN PROGRESS`, `DONE` (DONE = tests executed and passing).

| # | Step | Status | Notes |
|---|------|--------|-------|
| 0 | Foundations: monorepo, tooling, `CalcResult`, SI units, i18n, CI | DONE | |
| 1 | Data models and project management (versioned schema, CRUD, duplicate, import/export, history, autosave) | DONE | v1 → v2 project schema migration added for the mechanical layout; existing project data is preserved |
| 2 | Component library (structured datasheet, verified/custom/incomplete status, import/export) | DONE | Empty library, structured parameter records, missing-field tracking, explicit user-declared status, CRUD and JSON import/export |
| 3 | Electrical engine and analysis workflow (rails, P=UI, regulators, efficiency, voltage drop, anomaly detection) | DONE | Pure engine, `POST /api/electrical/analyze`, bilingual React page, rail load editing, explicit-limit anomaly display and API/page tests; CI passed |
| 4 | Battery engine (series/parallel, Wh, usable energy, autonomy theoretical/estimated/measured) | IN PROGRESS | Engine only; HTTP API and frontend page are still missing |
| 5 | Motorization engine and analysis workflow (differential drive, torque, traction, slope, current) | DONE | Engine, `POST /api/motorization/analyze`, bilingual React page, shared `CalcResultTable` and tests are implemented. Blank inputs remain null; the current estimate is torque-producing current only. Project-linked motor/drivetrain selection is a future integration. Never use stall current as running current |
| 6 | Mechanical design (mass, CoG, wheel load, static stability, 2D then 3D view) | IN PROGRESS | Engine, API and 2D page are linked to a versioned project layout. Selected-project load/save, optional component-library links, owner-verified kg mass resolution and visible mass provenance are implemented. Still in progress: automated component placement, 3D view, broader project workflow coverage and mechanical-model validation |
| 7 | Diagnostics center (severities, full warning structure) | TODO | |
| 8 | Visual circuit editor (graph of nodes/pins/nets) | TODO | |
| 9 | Sensors and interface compatibility (logic levels, GPIO limits) | TODO | |
| 10 | 2D simulation (fixed step, seeded, SAT collisions, LiDAR raycast) | TODO | Engine independent from UI |
| 11 | Reports (PDF + CSV) | TODO | Choose ReportLab vs WeasyPrint |
| 12 | Full UI (13 navigation entries, properties panel, confirmations) | TODO | |

## Technical risks / Risques techniques

1. Component data cannot be verified by the assistant: the library must be filled by the owner from datasheets.
2. DC motor current estimation depends on the model; assumptions must be displayed.
3. Autonomy depends on a load profile; Peukert/temperature/aging are documented limits unless data is provided.
4. Static stability is rigid-body on flat ground; it is not a structural analysis.
5. The circuit editor is the most expensive UI part: build a solid graph model before drawing.
6. Results are design aids, never certified calculations.
