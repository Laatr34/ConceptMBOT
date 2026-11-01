import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import i18n from '../i18n'
import MotorizationPage from './MotorizationPage'

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
  differential_drive: {
    left_linear_speed: calc('motorization.left_linear_speed', 1, 'm/s'),
    right_linear_speed: calc('motorization.right_linear_speed', 1, 'm/s'),
    left_wheel_angular_speed: calc('motorization.left_wheel_angular_speed', 10, 'rad/s'),
    right_wheel_angular_speed: calc('motorization.right_wheel_angular_speed', 10, 'rad/s'),
  },
  slope_force: calc('motorization.slope_force', 4, 'N'),
  required_wheel_torque: calc('motorization.required_wheel_torque', 0.2, 'N·m'),
  gearbox_output_torque: calc('motorization.gearbox_output_torque', 1.6, 'N·m'),
  max_traction_force: calc('motorization.max_traction_force', 50, 'N'),
  traction_margin: calc('motorization.traction_margin', 46, 'N'),
  torque_current: calc('motorization.torque_current', 4, 'A'),
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

describe('MotorizationPage', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('en')
  })
  afterEach(() => vi.unstubAllGlobals())

  it('sends blank fields as null and displays unevaluable results', async () => {
    const fetchMock = mockFetch({
      differential_drive: {
        left_linear_speed: calc('motorization.left_linear_speed', null, 'm/s'),
        right_linear_speed: calc('motorization.right_linear_speed', null, 'm/s'),
        left_wheel_angular_speed: calc('motorization.left_wheel_angular_speed', null, 'rad/s'),
        right_wheel_angular_speed: calc('motorization.right_wheel_angular_speed', null, 'rad/s'),
      },
      slope_force: calc('motorization.slope_force', null, 'N'),
      required_wheel_torque: calc('motorization.required_wheel_torque', null, 'N·m'),
      gearbox_output_torque: calc('motorization.gearbox_output_torque', null, 'N·m'),
      max_traction_force: calc('motorization.max_traction_force', null, 'N'),
      traction_margin: calc('motorization.traction_margin', null, 'N'),
      torque_current: calc('motorization.torque_current', null, 'A'),
    })
    render(<MotorizationPage />)
    await userEvent.click(screen.getByRole('button', { name: 'Analyze motorization' }))
    expect(await screen.findByText('Motorization results')).toBeInTheDocument()
    const payload = JSON.parse(fetchMock.mock.calls[0][1].body)
    expect(Object.values(payload).every((value) => value === null)).toBe(true)
    expect((await screen.findAllByText('Not evaluable')).length).toBeGreaterThan(5)
  })

  it('rejects a fractional driven-wheel count before calling the API', async () => {
    const fetchMock = mockFetch(analysis)
    render(<MotorizationPage />)
    await userEvent.type(screen.getByLabelText('Number of driven wheels (integer)'), '2.5')
    await userEvent.click(screen.getByRole('button', { name: 'Analyze motorization' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Number of driven wheels (integer)')
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('sends entered SI values and renders backend results', async () => {
    const fetchMock = mockFetch(analysis)
    render(<MotorizationPage />)
    const values: Record<string, string> = {
      'Linear speed v (m/s)': '1',
      'Angular speed ω (rad/s)': '0',
      'Track width (m)': '0.5',
      'Wheel radius r (m)': '0.1',
      'Total robot mass (kg)': '10',
      'Slope angle θ (rad)': '0.1',
      'Rolling resistance coefficient Crr': '0.02',
      'Number of driven wheels (integer)': '2',
      'Motor torque at operating point (N·m)': '0.2',
      'Gear ratio': '10',
      'Gearbox efficiency (0–1)': '0.8',
      'Ground friction coefficient μ': '0.5',
      'Normal load on driven wheels (N)': '100',
      'Motor torque constant Kt (N·m/A)': '0.05',
    }
    for (const [label, value] of Object.entries(values)) {
      await userEvent.type(screen.getByLabelText(label), value)
    }
    await userEvent.click(screen.getByRole('button', { name: 'Analyze motorization' }))
    expect(await screen.findByText('10 rad/s')).toBeInTheDocument()
    expect(screen.getByText('1.6 N·m')).toBeInTheDocument()
    expect(fetchMock.mock.calls[0][0]).toBe('/api/motorization/analyze')
    const payload = JSON.parse(fetchMock.mock.calls[0][1].body)
    expect(payload).toEqual({
      linear_speed_m_s: 1,
      angular_speed_rad_s: 0,
      track_width_m: 0.5,
      wheel_radius_m: 0.1,
      mass_kg: 10,
      slope_angle_rad: 0.1,
      rolling_resistance_coefficient: 0.02,
      driven_wheel_count: 2,
      motor_torque_nm: 0.2,
      gear_ratio: 10,
      gearbox_efficiency: 0.8,
      friction_coefficient: 0.5,
      driven_normal_load_n: 100,
      torque_constant_nm_per_a: 0.05,
    })
  })
})
