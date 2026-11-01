import { describe, expect, it } from 'vitest'
import { buildContactsInput, buildInput, parseOptionalNumber, type Row } from './input'

const row = (over: Partial<Row> = {}): Row => ({ id: 1, name: '', mass: '', x: '', y: '', z: '', ...over })

describe('parseOptionalNumber', () => {
  it('keeps empty input as null (unknown), never 0', () => {
    expect(parseOptionalNumber('')).toBeNull()
    expect(parseOptionalNumber('   ')).toBeNull()
  })
  it('parses decimals with dot or comma', () => {
    expect(parseOptionalNumber('1.5')).toBe(1.5)
    expect(parseOptionalNumber('1,5')).toBe(1.5)
    expect(parseOptionalNumber('0')).toBe(0)
    expect(parseOptionalNumber('-0.25')).toBe(-0.25)
  })
  it('rejects non-numbers and non-finite values', () => {
    for (const bad of ['abc', '1e999', 'NaN', 'Infinity', '1..2']) {
      expect(parseOptionalNumber(bad)).toBeUndefined()
    }
  })
})

describe('buildInput', () => {
  it('maps empty fields to null and names unnamed rows', () => {
    const built = buildInput([row({ mass: '2', x: '0.1' })], '', '0.4')
    expect(built).toEqual({
      input: {
        mass_points: [{ name: '#1', mass_kg: 2, x_m: 0.1, y_m: null, z_m: null }],
        wheelbase_m: null,
        track_width_m: 0.4,
      },
    })
  })
  it('reports every invalid field instead of sending partial data', () => {
    const built = buildInput([row({ mass: 'x', y: 'oops' })], 'abc', '')
    expect(built).toEqual({ invalid: ['#1 mass', '#1 y', 'wheelbase'] })
  })
})

describe('buildContactsInput', () => {
  const c = (name: string, x: string, y: string) => ({ id: 1, name, x, y })
  it('builds numeric contacts', () => {
    const built = buildContactsInput([row({ mass: '1', x: '0', y: '0', z: '0' })], [c('a', '0', '0.15'), c('b', '-0.2', '0')])
    expect(built).toEqual({
      input: {
        mass_points: [{ name: '#1', mass_kg: 1, x_m: 0, y_m: 0, z_m: 0 }],
        contacts: [{ name: 'a', x_m: 0, y_m: 0.15 }, { name: 'b', x_m: -0.2, y_m: 0 }],
      },
    })
  })
  it('rejects empty contact coordinates instead of using 0', () => {
    expect(buildContactsInput([], [c('caster', '', '0')])).toEqual({ invalid: ['caster x'] })
  })
})
