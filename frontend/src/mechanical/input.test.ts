import { describe, expect, it } from 'vitest'
import { buildInput, parseOptionalNumber, type Row } from './input'

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
