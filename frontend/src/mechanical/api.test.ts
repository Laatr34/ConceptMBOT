import { afterEach, describe, expect, it, vi } from 'vitest'
import { mechanicalApi } from './api'

const payload = { mass_points: [], wheelbase_m: 0.5, track_width_m: 0.4 }

describe('mechanical API client', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('posts the analysis input as JSON', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({ ok: 1 }) })
    vi.stubGlobal('fetch', fetchMock)
    await mechanicalApi.analyze(payload)
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/mechanical/analyze',
      expect.objectContaining({ method: 'POST', body: JSON.stringify(payload) }),
    )
  })

  it('surfaces API errors', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 422, text: async () => 'bad input' }))
    await expect(mechanicalApi.analyze(payload)).rejects.toThrow('bad input')
  })
})
