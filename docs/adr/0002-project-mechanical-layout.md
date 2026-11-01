# ADR 0002 — Versioned mechanical layout in project documents

- Status: Accepted
- Date: 2026-11-01

## Context

The mechanical analysis page currently accepts mass points and ground contacts as temporary form state. It cannot reuse a saved robot project. A robot's mass distribution and support geometry are project-specific, while the component library stores reusable manufacturer/component information.

The museum robot uses a differential drive with two driven wheels and one caster: three ground contacts. The four-wheel rectangular model is not an appropriate default for this robot.

## Decision

Introduce a versioned project-data section named `mechanical` in the project document's `data` object.

The section stores:
- `mass_points`: project-specific mass-point entries with a stable name, optional component-library reference, and SI position (x, y, z) in metres;
- `contacts`: named ground-contact positions (x, y) in metres.

The component-library reference is optional so project-specific assemblies can be represented. A mass value is never copied from an unverified or incomplete source. When a library component is linked, the analysis layer may use only an unambiguous, numeric `mass` parameter whose unit is exactly `kg`; otherwise the mass remains unknown. Any explicit project-level mass override must be labelled as user-supplied and must not be presented as a verified datasheet value.

Unknown coordinates and masses remain null. The mechanical analysis returns non-evaluable results with missing-input details instead of replacing null with zero.

Project schema evolution must be explicit: support a deterministic v1 → v2 migration that preserves all existing `data` keys and adds an empty `mechanical` section. Unknown future schema versions remain rejected. Import/export and revision snapshots preserve the schema version and data.

## Coordinate convention

Use a right-handed robot-fixed frame:
- X: forward;
- Y: left;
- Z: upward;
- origin: chosen by the project author and documented in the project.

This is a coordinate convention, not a claim about the physical robot's dimensions or component locations. Contact and mass-point positions must be entered from measured/design data.

## Consequences

- The mechanical page can load and save its inputs through a selected project.
- The project remains portable JSON and can be analysed without relying on hidden frontend state.
- The component library remains reusable and does not contain project-specific placements.
- A missing or ambiguous component mass cannot silently produce a numerical centre of gravity.
- Existing v1 projects remain readable through an explicit migration.

## Out of scope

- Automatic extraction of dimensions or masses from manufacturer websites.
- Guessing component positions from the bill of materials.
- Dynamic stability, slope, acceleration, braking, suspension compliance, or structural analysis.
