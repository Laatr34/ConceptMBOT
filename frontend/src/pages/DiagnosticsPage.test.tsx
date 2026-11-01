import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import i18n from '../i18n'
import DiagnosticsPage from './DiagnosticsPage'

const project = {
  id: '00000000-0000-0000-0000-000000000123',
  name: 'Museum robot',
  description: null,
  created_at: '2026-10-01T00:00:00Z',
  updated_at: '2026-10-01T00:00:00Z',
}

const report = {
  project_id: project.id,
  project_name: project.name,
  scope: 'mechanical_static',
  generated_at: '2026-10-01T12:00:00Z',
  status: 'attention',
  diagnostics: [{
    code: 'mechanical.static_support_unstable',
    component: 'Robot support polygon',
    problem: 'The projected centre of gravity is outside the support polygon.',
    value: -0.05,
    unit: 'm',
    limit: 0,
    limit_source: 'Convex hull computed from project ground-contact coordinates.',
    explanation: 'The signed geometric margin is negative.',
    correction: 'Review the measured mass-point positions and support geometry.',
    severity: 'critical',
    source_result: 'mechanical.support_polygon_margin',
    missing_inputs: [],
  }],
}

function mockFetch(reportBody: unknown, projects: unknown[] = [project]) {
  const fetchMock = vi.fn().mockImplementation((url: string) => {
    if (url === '/api/projects') {
      return Promise.resolve({ ok: true, status: 200, json: async () => projects, text: async () => '' })
    }
    return Promise.resolve({
      ok: true,
      status: 200,
      json: async () => reportBody,
      text: async () => '',
    })
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

describe('DiagnosticsPage', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('en')
  })
  afterEach(() => vi.unstubAllGlobals())

  it('loads a project and displays every structured diagnostic field', async () => {
    const fetchMock = mockFetch(report)
    render(<DiagnosticsPage />)
    await screen.findByRole('option', { name: 'Museum robot' })
    await userEvent.click(screen.getByRole('button', { name: 'Analyze project' }))

    expect(await screen.findByText('The projected centre of gravity is outside the support polygon.')).toBeInTheDocument()
    expect(screen.getByText('Critical')).toBeInTheDocument()
    expect(screen.getByText('Robot support polygon')).toBeInTheDocument()
    expect(screen.getByText('Convex hull computed from project ground-contact coordinates.')).toBeInTheDocument()
    expect(screen.getByText('Review the measured mass-point positions and support geometry.')).toBeInTheDocument()
    expect(fetchMock.mock.calls[1][0]).toBe('/api/diagnostics/projects/00000000-0000-0000-0000-000000000123/analyze')
  })

  it('explains when no projects are available', async () => {
    mockFetch(null, [])
    render(<DiagnosticsPage />)
    expect(await screen.findByText('Create a project before running project diagnostics.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Analyze project' })).toBeDisabled()
  })

  it('is available in French', async () => {
    await i18n.changeLanguage('fr')
    mockFetch(report)
    render(<DiagnosticsPage />)
    expect(screen.getByRole('heading', { name: 'Diagnostics' })).toBeInTheDocument()
    expect(screen.getByText('Périmètre actuel des diagnostics')).toBeInTheDocument()
  })
})
