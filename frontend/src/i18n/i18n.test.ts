import { describe, expect, it } from 'vitest'
import en from './en'
import fr from './fr'
import { NAV_ITEMS } from '../navigation'

function keys(obj: Record<string, unknown>, prefix = ''): string[] {
  return Object.entries(obj).flatMap(([k, v]) =>
    typeof v === 'object' && v !== null
      ? keys(v as Record<string, unknown>, `${prefix}${k}.`)
      : [`${prefix}${k}`],
  )
}

describe('i18n', () => {
  it('FR and EN have identical keys', () => {
    expect(keys(fr).sort()).toEqual(keys(en).sort())
  })

  it('no empty translation', () => {
    for (const dict of [en, fr]) {
      for (const k of keys(dict)) {
        const value = k.split('.').reduce<unknown>((o, p) => (o as Record<string, unknown>)[p], dict)
        expect(value, k).toBeTruthy()
      }
    }
  })

  it('every navigation label exists in both languages', () => {
    const enKeys = new Set(keys(en))
    const frKeys = new Set(keys(fr))
    for (const item of NAV_ITEMS) {
      expect(enKeys.has(item.labelKey), item.labelKey).toBe(true)
      expect(frKeys.has(item.labelKey), item.labelKey).toBe(true)
    }
  })

  it('has the 14 navigation entries', () => {
    expect(NAV_ITEMS).toHaveLength(14)
  })
})
