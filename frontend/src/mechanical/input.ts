import type { ContactsAnalysisInput, MassPointInput, MechanicalAnalysisInput } from './api'

export interface Row {
  id: number
  name: string
  component_id?: string | null
  mass: string
  x: string
  y: string
  z: string
}

/** '' -> null (unknown, never 0). Returns undefined for text that is not a finite number. */
export function parseOptionalNumber(text: string): number | null | undefined {
  const trimmed = text.trim().replace(',', '.')
  if (trimmed === '') return null
  const value = Number(trimmed)
  return Number.isFinite(value) ? value : undefined
}

export function buildInput(
  rows: Row[],
  wheelbase: string,
  track: string,
): { input: MechanicalAnalysisInput } | { invalid: string[] } {
  const invalid: string[] = []
  const num = (label: string, text: string): number | null => {
    const v = parseOptionalNumber(text)
    if (v === undefined) {
      invalid.push(label)
      return null
    }
    return v
  }
  const mass_points: MassPointInput[] = rows.map((r, i) => ({
    name: r.name.trim() || `#${i + 1}`,
    mass_kg: num(`#${i + 1} mass`, r.mass),
    x_m: num(`#${i + 1} x`, r.x),
    y_m: num(`#${i + 1} y`, r.y),
    z_m: num(`#${i + 1} z`, r.z),
  }))
  const wheelbase_m = num('wheelbase', wheelbase)
  const track_width_m = num('track width', track)
  if (invalid.length > 0) return { invalid }
  return { input: { mass_points, wheelbase_m, track_width_m } }
}


export interface ContactRow {
  id: number
  name: string
  x: string
  y: string
}

/** Contact coordinates are required numbers: an empty field is reported, never replaced by 0. */
export function buildContactsInput(
  rows: Row[],
  contacts: ContactRow[],
): { input: ContactsAnalysisInput } | { invalid: string[] } {
  const base = buildInput(rows, '', '')
  const invalid: string[] = 'invalid' in base ? [...base.invalid] : []
  const out: ContactsAnalysisInput['contacts'] = []
  contacts.forEach((c, i) => {
    const name = c.name.trim() || `contact ${i + 1}`
    const x = parseOptionalNumber(c.x)
    const y = parseOptionalNumber(c.y)
    if (typeof x !== 'number') invalid.push(`${name} x`)
    if (typeof y !== 'number') invalid.push(`${name} y`)
    if (typeof x === 'number' && typeof y === 'number') out.push({ name, x_m: x, y_m: y })
  })
  if (invalid.length > 0 || !('input' in base)) return { invalid }
  return { input: { mass_points: base.input.mass_points, contacts: out } }
}
