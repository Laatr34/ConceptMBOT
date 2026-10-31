# ADR 0001 — Units handling and stack confirmation

Status: accepted (step 0)

## Context
The product requires explicit, safe physical units and traceable calculations, with simulation loops that must stay fast.

## Decisions
1. **Stack**: kept as specified (React + TS + Vite + Tailwind; FastAPI + Pydantic + SQLAlchemy; Vitest; Pytest; OpenAPI).
2. **Units**: values are stored in SI as plain floats inside lightweight typed aliases/helpers (`app/domain/units.py`); conversion only at boundaries. `pint` is **not** adopted: heavier, slows simulation hot paths, and adds a runtime dependency on every calculation.
3. **Traceability**: every calculation returns `CalcResult`.
4. **Missing data**: `None` → "not evaluable", never a silent default.
5. **Component library**: starts empty; no commercial reference is prefilled without verifiable source.

## Consequences
Unit safety relies on naming conventions (`_v`, `_a`, `_w`, `_nm`, `_kg`, `_m`, `_s`), conversion helpers and tests rather than a runtime unit library. To be revisited if unit errors appear.
