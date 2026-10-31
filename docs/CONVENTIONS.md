# Conventions

## Units / Unités
All internal values are **SI**: volt (V), ampere (A), watt (W), ohm (Ω), joule (J), watt-hour only at display/battery boundary (Wh = 3600 J), newton-metre (N·m), kilogram (kg), metre (m), second (s), radian (rad).
Conversions (mm, Ah, Wh, rpm, km/h, degrees) happen **only** at the API/UI boundary, through helpers in `app/domain/units.py`.

## CalcResult
Every calculation returns a `CalcResult` (`app/domain/calc_result.py`):

| Field | Meaning |
|-------|---------|
| `name` | Stable identifier, e.g. `electrical.rail_current` |
| `value` | Number, or `None` if not evaluable |
| `unit` | SI unit symbol |
| `formula` | Human-readable formula, e.g. `P = U × I` |
| `inputs` | Mapping of input name → value used |
| `assumptions` | List of assumptions |
| `status` | `theoretical`, `estimated`, `measured`, `not_evaluable` |
| `confidence` | `high`, `medium`, `low`, `unknown` |
| `limits` | Known limitations |
| `missing_inputs` | Names of missing inputs (when not evaluable) |

Invariants: `value is None` ⇔ `status == not_evaluable`; a `not_evaluable` result must list `missing_inputs` or `limits`.

## Rules for engines (`app/engines/`)
Pure functions. Document formulas and units in the docstring. Validate ranges (reject negative physical impossibilities via `InvalidInputError`). Return "not evaluable" for missing data. No premature rounding. Test edge cases and compare with independently computed reference values (`tests/reference/`).

## i18n
Frontend text lives in `frontend/src/i18n/{fr,en}.ts`. No hard-coded user-facing strings in components. Both locales must have identical keys (enforced by a test).

## Commits
Small, per feature, with tests. Update `docs/PLAN.md` and `README.md` at the end of a step.
