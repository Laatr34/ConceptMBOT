# Development plan / Plan de développement

Single source of truth for progress. Update at the end of every step.
Source unique de l'avancement. À mettre à jour à chaque étape.

Status legend: `TODO`, `IN PROGRESS`, `DONE` (DONE = tests executed and passing).

| # | Step | Status | Notes |
|---|------|--------|-------|
| 0 | Foundations: monorepo, tooling, `CalcResult`, SI units, i18n, CI | DONE | |
| 1 | Data models and project management (versioned schema, CRUD, duplicate, import/export, history, autosave) | DONE | GitHub Actions: 24 backend tests and 9 frontend tests passed; Ruff, mypy, frontend lint/typecheck/build passed |
| 2 | Component library (structured datasheet, verified/custom/incomplete status, import/export) | DONE | Empty library, structured parameter records, missing-field tracking, explicit user-declared status, CRUD and JSON import/export; CI passed with 29 backend and 9 frontend tests |
| 3 | Electrical engine (rails, P=UI, regulators, efficiency, voltage drop, anomaly detection) | DONE | Pure DC functions, explicit missing-input results, regulator efficiency, rail aggregation, voltage-drop calculation and limit checks; 47 backend tests pass |
| 4 | Battery engine (series/parallel, Wh, usable energy, autonomy theoretical/estimated/measured) | DONE | Series/parallel pack voltage and charge, nominal/usable energy in J, theoretical/estimated/measured autonomy; Peukert, temperature and aging limits documented; 65 backend tests pass |
| 5 | Motorization engine (differential drive, torque, traction, slope, current) | TODO | Never use stall current as running current |
| 6 | Mechanical design (mass, CoG, wheel load, static stability, 2D then 3D view) | TODO | |
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
