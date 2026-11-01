import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import i18n from '../i18n'
import ElectricalPage from './ElectricalPage'

const calc = (name: string, value: number | null, unit: string) => ({
  name,
  value,
  unit,
  formula: 'F',
  inputs: {},
  assumptions: [],
  status: value === null ? 'not_evaluable' : 'theoretical',
  confidence: value === null ? 'unknown' : 'high',
  limits: [],
  missing_inputs: value === null ? ['input'] : [],
})

const analysis = {
  power: calc('electrical.power', 24, 'W'),
  current: calc('electrical.current', 2, 'A'),
  voltage_drop: calc('electrical.voltage_drop', 1, 'V'),
  regulator_output_power: calc('electrical.regulator_output_power', 10, 'W'),
  regulator_input_current: calc('electrical.regulator_input_current', 1.041667, 'A'),
  regulator_power_loss: calc('electrical.regulator_power_loss', 2.5, 'W'),
  rail_current: calc('electrical.rail_current', 2, 'A'),
  anomalies: [],
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

describe('ElectricalPage', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('en')
  })
  afterEach(() => vi.unstubAllGlobals())

  it('sends blank scalar fields as null and leaves an empty rail load unevaluable', async () => {
    const fetchMock = mockFetch({
      ...analysis,
      power: calc('electrical.power', null, 'W'),
      current: calc('electrical.current', null, 'A'),
      voltage_drop: calc('electrical.voltage_drop', null, 'V'),
      regulator_output_power: calc('electrical.regulator_output_power', null, 'W'),
      regulator_input_current: calc('electrical.regulator_input_current', null, 'A'),
      regulator_power_loss: calc('electrical.regulator_power_loss', null, 'W'),
      rail_current: calc('electrical.rail_current', null, 'A'),
      anomalies: [{ code: 'current_limit_not_configured', severity: 'info',
        message: 'Current limit is not configured.', value: null, threshold: null, unit: 'A' }],
    })
    render(<ElectricalPage />)
    await userEvent.click(screen.getByRole('button', { name: 'Analyze electrical design' }))
    expect(await screen.findByText('Electrical results')).toBeInTheDocument()
    const payload = JSON.parse(fetchMock.mock.calls[0][1].body)
    expect(payload.voltage_v).toBeNull()
    expect(payload.current_a).toBeNull()
    expect(payload.regulator).toEqual({
      input_voltage_v: null,
      output_voltage_v: null,
      output_current_a: null,
      efficiency: null,
    })
    expect(payload.rail.voltage_v).toBeNull()
    expect(payload.rail.loads).toEqual([{ name: 'Load 1', current_a: null, power_w: null }])
    expect(screen.getAllByText('Not evaluable').length).toBeGreaterThan(4)
    expect(screen.getByText(/Information \/ not checked/)).toBeInTheDocument()
  })

  it('rejects a load with both current and power before calling the API', async () => {
    const fetchMock = mockFetch(analysis)
    render(<ElectricalPage />)
    await userEvent.type(screen.getByLabelText('Current (A) 1'), '1')
    await userEvent.type(screen.getByLabelText('Power (W) 1'), '12')
    await userEvent.click(screen.getByRole('button', { name: 'Analyze electrical design' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('enter either current or power, not both')
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('sends SI values and renders calculation results and anomaly checks', async () => {
    const fetchMock = mockFetch({
      ...analysis,
      anomalies: [{
        code: 'rail_overcurrent',
        severity: 'error',
        message: 'Rail current is above the configured current limit.',
        value: 3,
        threshold: 2,
        unit: 'A',
      }],
    })
    render(<ElectricalPage />)
    await userEvent.type(screen.getByLabelText('Voltage U (V)'), '12')
    await userEvent.type(screen.getByLabelText('Current I (A)'), '2')
    await userEvent.type(screen.getByLabelText('Power P (W)'), '24')
    await userEvent.type(screen.getByLabelText('Wire or path resistance R (Ω)'), '0.5')
    await userEvent.type(screen.getByLabelText('Regulator input voltage (V)'), '12')
    await userEvent.type(screen.getByLabelText('Regulator output voltage (V)'), '5')
    await userEvent.type(screen.getByLabelText('Regulator output current (A)'), '2')
    await userEvent.type(screen.getByLabelText('Regulator efficiency (0–1)'), '0.8')
    await userEvent.type(screen.getByLabelText('Rail voltage (V)'), '12')
    await userEvent.type(screen.getByLabelText('Measured rail current (A)'), '3')
    await userEvent.type(screen.getByLabelText('Configured minimum voltage (V)'), '10')
    await userEvent.type(screen.getByLabelText('Configured maximum voltage (V)'), '14')
    await userEvent.type(screen.getByLabelText('Configured current limit (A)'), '2')
    await userEvent.type(screen.getByLabelText('Current (A) 1'), '1')
    await userEvent.click(screen.getByRole('button', { name: 'Analyze electrical design' }))

    expect(await screen.findByText('24 W')).toBeInTheDocument()
    expect(screen.getByText('1 V')).toBeInTheDocument()
    expect(screen.getByText('Rail current is above the configured current limit.')).toBeInTheDocument()
    expect(fetchMock.mock.calls[0][0]).toBe('/api/electrical/analyze')
    const payload = JSON.parse(fetchMock.mock.calls[0][1].body)
    expect(payload.rail.loads).toEqual([{ name: 'Load 1', current_a: 1, power_w: null }])
    expect(payload.regulator.efficiency).toBe(0.8)
  })

  it('is available in French', async () => {
    await i18n.changeLanguage('fr')
    render(<ElectricalPage />)
    expect(screen.getByRole('heading', { name: 'Conception électrique' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Analyser la conception électrique' })).toBeInTheDocument()
  })
})
