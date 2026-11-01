import { describe, expect, it } from 'vitest'
import { convexHull, isPositiveFinite, makeTransform } from './geometry'

describe('2D view transform', () => {
  it('puts the origin at the centre of the view', () => {
    const t = makeTransform([], 0.5, 0.4)
    expect(t.toSvg({ x_m: 0, y_m: 0 })).toEqual({ x: 210, y: 210 })
  })

  it('draws forward (+x) upwards and left (+y) to the left', () => {
    const t = makeTransform([], 0.5, 0.4)
    const p = t.toSvg({ x_m: 0.1, y_m: 0.1 })
    expect(p.y).toBeLessThan(210)
    expect(p.x).toBeLessThan(210)
  })

  it('keeps proportions: same scale on both axes', () => {
    const t = makeTransform([], 1, 1)
    const a = t.toSvg({ x_m: 0, y_m: 0 })
    const right = t.toSvg({ x_m: 0, y_m: -0.5 })
    const up = t.toSvg({ x_m: 0.5, y_m: 0 })
    expect(right.x - a.x).toBeCloseTo(a.y - up.y)
  })

  it('fits points that lie outside the wheel rectangle', () => {
    const t = makeTransform([{ x_m: 2, y_m: 0 }], 0.5, 0.4)
    const p = t.toSvg({ x_m: 2, y_m: 0 })
    expect(p.y).toBeGreaterThanOrEqual(0)
    expect(p.y).toBeLessThanOrEqual(t.height)
  })

  it('ignores non-finite coordinates', () => {
    const t = makeTransform([{ x_m: Number.NaN, y_m: Number.POSITIVE_INFINITY }], 0.5, 0.4)
    expect(Number.isFinite(t.scale)).toBe(true)
  })

  it('validates strictly positive finite dimensions', () => {
    expect(isPositiveFinite(0.5)).toBe(true)
    for (const v of [0, -1, null, undefined, Number.NaN, Number.POSITIVE_INFINITY]) {
      expect(isPositiveFinite(v)).toBe(false)
    }
  })
})

describe('convexHull (drawing only)', () => {
  it('drops interior and duplicate points', () => {
    const hull = convexHull([
      { x_m: 0, y_m: 0 }, { x_m: 1, y_m: 0 }, { x_m: 1, y_m: 1 }, { x_m: 0, y_m: 1 },
      { x_m: 0.5, y_m: 0.5 }, { x_m: 1, y_m: 1 },
    ])
    expect(hull).toHaveLength(4)
  })
  it('returns a triangle for three contacts', () => {
    const hull = convexHull([{ x_m: 0, y_m: 0.15 }, { x_m: 0, y_m: -0.15 }, { x_m: -0.2, y_m: 0 }])
    expect(hull).toHaveLength(3)
  })
})
