import { afterEach, describe, expect, it, vi } from 'vitest'
import { projectsApi } from './api'
describe('projects API client', () => {
  afterEach(() => vi.unstubAllGlobals())
  it('loads project summaries from the API', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => [{ id: 'p1', name: 'Demo' }] })
    vi.stubGlobal('fetch', fetchMock)
    const result = await projectsApi.list()
    expect(result).toEqual([{ id: 'p1', name: 'Demo' }])
    expect(fetchMock).toHaveBeenCalledWith('/api/projects', expect.objectContaining({
      headers: { 'Content-Type': 'application/json' },
    }))
  })
  it('surfaces API errors', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 500, text: async () => 'Internal error' }))
    await expect(projectsApi.list()).rejects.toThrow('Internal error')
  })
})
