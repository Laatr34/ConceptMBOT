import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import i18n from '../i18n'
import BatteryPage from './BatteryPage'

const calc = (name: string, value: number | null, unit: string, status = 'theoretical') => ({
  name,
  value,
  unit,
  formula: 'F',
  inputs: {},
  assumptions: [],
  status,
  confidence: value === null ? 'unknown' : 'high',
  limits: [],
  missing_inputs: value === null ? ['input'] : [],
})

const analysis = {
  pack_voltage: calc('battery.pack_voltage', 11.1, 'V'),
  pack_capacity_c: calc('battery.pack_capacity', 14400, 'C'),
  pack_capacity_ah: calc('battery.pack_capacity', 4, 'Ah'),
  nominal_energy_j: calc('battery.pack_energy', 159840, 'J'),
  nominal_energy_wh: calc('battery.pack_energy', 44.4, 'Wh'),
  usable_energy_j: calc('battery.usable_energy', 115084.8, 'J'),
  usable_energy_wh: calc('battery.usable_energy', 31.968, 'Wh'),
  theoretical_autonomy_s: calc('battery.autonomy_theoretical', 9590.4, 's'),
  theoretical_autonomy_h: calc('battery.autonomy_theoretical', 9590.4 / 3600, 'h'),
  estimated_autonomy_s: calc('battery.autonomy_estimated', 11508.48, 's', 'estimated'),
  estimated_autonomy_h: calc('battery.autonomy_estimated', 11508.48 / 3600, 'h', 'estimated'),
  measured_autonomy_s: calc('battery.autonomy_measured', 7200, 's', 'measured'),
  measured_autonomy_h: calc('battery.autonomy_measured', 2, 'h', 'measured'),
}

function mockFetch(body: unknown) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: async () => body,
    text: async () => '',
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

describe('BatteryPage', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('en')
  })
  afterEach(() => vi.unstubAllGlobals())

  it('sends unknown values as null and displays unevaluable results', async () => {
    const nullResult = (name: string, unit: string) => calc(name, null, unit, 'not_evaluable')
    const fetchMock = mockFetch({
      pack_voltage: nullResult('battery.pack_voltage', 'V'),
      pack_capacity_c: nullResult('battery.pack_capacity', 'C'),
      pack_capacity_ah: nullResult('battery.pack_capacity', 'Ah'),
      nominal_energy_j: nullResult('battery.pack_energy', 'J'),
      nominal_energy_wh: nullResult('battery.pack_energy', 'Wh'),
      usable_energy_j: nullResult('battery.usable_energy', 'J'),
      usable_energy_wh: nullResult('battery.usable_energy', 'Wh'),
      theoretical_autonomy_s: nullResult('battery.autonomy_theoretical', 's'),
      theoretical_autonomy_h: nullResult('battery.autonomy_theoretical', 'h'),
      estimated_autonomy_s: nullResult('battery.autonomy_estimated', 's'),
      estimated_autonomy_h: nullResult('battery.autonomy_estimated', 'h'),
      measured_autonomy_s: nullResult('battery.autonomy_measured', 's'),
      measured_autonomy_h: nullResult('battery.autonomy_measured', 'h'),
    })
    render(<BatteryPage />)
    await userEvent.click(screen.getByRole('button', { name: 'Analyze battery' }))
    expect(await screen.findByText('Battery and autonomy results')).toBeInTheDocument()
    const payload = JSON.parse(fetchMock.mock.calls[0][1].body)
    expect(payload).toEqual({
      cell_voltage_v: null,
      series_count: null,
      cell_capacity_ah: null,
      parallel_count: null,
      depth_of_discharge: null,
      efficiency: null,
      average_power_w: null,
      estimated_average_power_w: null,
      estimated_power_assumptions: [],
      measured_duration_s: null,
    })
    expect((await screen.findAllByText('Not evaluable')).length).toBeGreaterThan(8)
  })

  it('rejects fractional series and parallel counts before calling the API', async () => {
    const fetchMock = mockFetch(analysis)
    render(<BatteryPage />)
    await userEvent.type(screen.getByLabelText('Cells in series Ns (integer)'), '2.5')
    await userEvent.click(screen.getByRole('button', { name: 'Analyze battery' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Cells in series Ns (integer)')
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('sends Ah and explicit assumptions and displays both familiar and SI units', async () => {
    const fetchMock = mockFetch(analysis)
    render(<BatteryPage />)
    const values: Record<string, string> = {
      'Nominal cell voltage (V)': '3.7',
      'Cells in series Ns (integer)': '3',
      'Capacity per cell (Ah)': '2',
      'Parallel cell groups Np (integer)': '2',
      'Depth of discharge DoD (0–1)': '0.8',
      'Conversion efficiency η (0–1)': '0.9',
      'Theoretical average load power (W)': '12',
      'Estimated average load power (W)': '10',
      'Measured runtime (seconds)': '7200',
    }
    for (const [label, value] of Object.entries(values)) {
      await userEvent.type(screen.getByLabelText(label), value)
    }
    await userEvent.type(
      screen.getByLabelText('Assumptions supporting estimated average power'),
      'Average load estimated from a documented duty cycle.',
    )
    await userEvent.click(screen.getByRole('button', { name: 'Analyze battery' }))
    expect(await screen.findByText('4 Ah')).toBeInTheDocument()
    expect(screen.getByText('44.4 Wh')).toBeInTheDocument()
    expect(screen.getByText('2 h')).toBeInTheDocument()
    expect(fetchMock.mock.calls[0][0]).toBe('/api/battery/analyze')
    const payload = JSON.parse(fetchMock.mock.calls[0][1].body)
    expect(payload.cell_capacity_ah).toBe(2)
    expect(payload.estimated_power_assumptions).toEqual([
      'Average load estimated from a documented duty cycle.',
    ])
  })

  it('is available in French', async () => {
    await i18n.changeLanguage('fr')
    render(<BatteryPage />)
    expect(screen.getByRole('heading', { name: 'Batterie et autonomie' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Analyser la batterie' })).toBeInTheDocument()
  })
})
