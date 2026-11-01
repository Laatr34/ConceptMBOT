import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import i18n from '../i18n'
import MechanicalPage from './MechanicalPage'

const calc = (name: string, value: number | null, unit: string, extra: object = {}) => ({
  name, value, unit, formula: 'F', inputs: {}, assumptions: [], limits: [], missing_inputs: [],
  status: value === null ? 'not_evaluable' : 'theoretical', confidence: 'high', ...extra,
})

const stableResponse = {
  center_of_gravity: {
    total_mass: calc('mechanical.total_mass', 2, 'kg'),
    x_m: calc('mechanical.center_of_gravity_x', 0, 'm'),
    y_m: calc('mechanical.center_of_gravity_y', 0, 'm'),
    z_m: calc('mechanical.center_of_gravity_z', 0.2, 'm'),
  },
  wheel_loads: {
    front_left_n: calc('mechanical.front_left_n', 4.9, 'N', { assumptions: ['equal stiffness'] }),
    front_right_n: calc('mechanical.front_right_n', 4.9, 'N'),
    rear_left_n: calc('mechanical.rear_left_n', 4.9, 'N'),
    rear_right_n: calc('mechanical.rear_right_n', 4.9, 'N'),
  },
  stability: {
    margin_x_m: calc('mechanical.stability_margin_x', 0.25, 'm'),
    margin_y_m: calc('mechanical.stability_margin_y', 0.2, 'm'),
    overall_margin_m: calc('mechanical.stability_margin', 0.2, 'm'),
    status: 'stable',
  },
}

const unknownResponse = {
  center_of_gravity: {
    total_mass: calc('mechanical.total_mass', null, 'kg', { missing_inputs: ['mass_kg'] }),
    x_m: calc('mechanical.center_of_gravity_x', null, 'm', { missing_inputs: ['mass_kg'] }),
    y_m: calc('mechanical.center_of_gravity_y', null, 'm', { missing_inputs: ['mass_kg'] }),
    z_m: calc('mechanical.center_of_gravity_z', null, 'm', { missing_inputs: ['mass_kg'] }),
  },
  wheel_loads: {
    front_left_n: calc('mechanical.front_left_n', null, 'N', { missing_inputs: ['mass_kg'] }),
    front_right_n: calc('mechanical.front_right_n', null, 'N', { missing_inputs: ['mass_kg'] }),
    rear_left_n: calc('mechanical.rear_left_n', null, 'N', { missing_inputs: ['mass_kg'] }),
    rear_right_n: calc('mechanical.rear_right_n', null, 'N', { missing_inputs: ['mass_kg'] }),
  },
  stability: {
    margin_x_m: calc('mechanical.stability_margin_x', null, 'm', { missing_inputs: ['cg_x_m'] }),
    margin_y_m: calc('mechanical.stability_margin_y', null, 'm', { missing_inputs: ['cg_x_m'] }),
    overall_margin_m: calc('mechanical.stability_margin', null, 'm', { missing_inputs: ['cg_x_m'] }),
    status: 'unknown',
  },
}

function mockFetch(body: unknown, ok = true) {
  const fn = vi.fn().mockResolvedValue({ ok, status: ok ? 200 : 500, json: async () => body, text: async () => 'boom' })
  vi.stubGlobal('fetch', fn)
  return fn
}

describe('MechanicalPage', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('en')
  })
  afterEach(() => vi.unstubAllGlobals())

  it('always shows the four-wheel model limitation', () => {
    render(<MechanicalPage />)
    expect(screen.getByRole('note')).toHaveTextContent('FOUR coplanar wheel contacts')
  })

  it('sends empty fields as null (unknown) and not as zero', async () => {
    const fetchMock = mockFetch(unknownResponse)
    render(<MechanicalPage />)
    await userEvent.click(screen.getByRole('button', { name: 'Analyze' }))
    await screen.findByText('Results')
    const body = JSON.parse(fetchMock.mock.calls[0][1].body)
    expect(body).toEqual({
      mass_points: [{ name: '#1', mass_kg: null, x_m: null, y_m: null, z_m: null }],
      wheelbase_m: null,
      track_width_m: null,
    })
  })

  it('shows "Not evaluable" with missing inputs and draws no centre of gravity', async () => {
    mockFetch(unknownResponse)
    render(<MechanicalPage />)
    await userEvent.click(screen.getByRole('button', { name: 'Analyze' }))
    expect((await screen.findAllByText('Not evaluable')).length).toBeGreaterThan(5)
    expect(screen.getAllByText(/Missing: mass_kg/).length).toBeGreaterThan(0)
    expect(screen.queryByTestId('cog')).not.toBeInTheDocument()
    expect(screen.getByText(/Enter wheelbase and track width/)).toBeInTheDocument()
  })

  it('renders values, units, formulas and assumptions, and the 2D view', async () => {
    mockFetch(stableResponse)
    render(<MechanicalPage />)
    await userEvent.type(screen.getByLabelText('Mass (kg) 1'), '2')
    await userEvent.type(screen.getByLabelText('x (m) 1'), '0')
    await userEvent.type(screen.getByLabelText('y (m) 1'), '0')
    await userEvent.type(screen.getByLabelText('Wheelbase L (m)'), '0.5')
    await userEvent.type(screen.getByLabelText('Track width W (m)'), '0.4')
    await userEvent.click(screen.getByRole('button', { name: 'Analyze' }))
    expect(await screen.findByText('2 kg')).toBeInTheDocument()
    expect(screen.getAllByText('4.9 N')).toHaveLength(4)
    expect(screen.getByText(/equal stiffness/)).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Static stability: Stable' })).toBeInTheDocument()
    expect(screen.getByRole('img')).toBeInTheDocument()
    expect(screen.getByTestId('support-rect')).toBeInTheDocument()
    expect(screen.getByTestId('cog')).toBeInTheDocument()
    expect(screen.getAllByTestId('mass-point')).toHaveLength(1)
  })

  it('blocks submission on an invalid number', async () => {
    const fetchMock = mockFetch(stableResponse)
    render(<MechanicalPage />)
    await userEvent.type(screen.getByLabelText('Mass (kg) 1'), 'abc')
    await userEvent.click(screen.getByRole('button', { name: 'Analyze' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid number in: #1 mass')
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('shows an error when the API fails', async () => {
    mockFetch({}, false)
    render(<MechanicalPage />)
    await userEvent.click(screen.getByRole('button', { name: 'Analyze' }))
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Analysis failed'))
  })

  it('adds and removes mass points', async () => {
    render(<MechanicalPage />)
    await userEvent.click(screen.getByRole('button', { name: '+ Add mass point' }))
    expect(screen.getAllByRole('button', { name: 'Remove' })).toHaveLength(2)
    await userEvent.click(screen.getAllByRole('button', { name: 'Remove' })[0])
    expect(screen.getAllByRole('button', { name: 'Remove' })).toHaveLength(1)
  })

  it('is available in French', async () => {
    await i18n.changeLanguage('fr')
    render(<MechanicalPage />)
    expect(screen.getByRole('heading', { name: 'Analyse mécanique' })).toBeInTheDocument()
    expect(screen.getByRole('note')).toHaveTextContent('QUATRE contacts')
  })

  describe('contacts mode (2 drive wheels + caster)', () => {
    const contactsResponse = {
      center_of_gravity: stableResponse.center_of_gravity,
      contact_loads: [
        calc('mechanical.contact_load.left_wheel', 36.8, 'N'),
        calc('mechanical.contact_load.right_wheel', 36.8, 'N'),
        calc('mechanical.contact_load.caster', 24.5, 'N'),
      ],
      stability: { margin_m: calc('mechanical.support_polygon_margin', 0.05, 'm'), status: 'stable' },
    }

    async function fillContacts() {
      await userEvent.click(screen.getByLabelText(/Contacts \(any layout/))
      const set = async (label: string, value: string) => userEvent.type(screen.getByLabelText(label), value)
      await set('x (m) Ground contacts 1', '0')
      await set('y (m) Ground contacts 1', '0.15')
      await set('x (m) Ground contacts 2', '0')
      await set('y (m) Ground contacts 2', '-0.15')
      await set('x (m) Ground contacts 3', '-0.2')
      await set('y (m) Ground contacts 3', '0')
    }

    it('shows the contacts note and hides the rectangle fields', async () => {
      render(<MechanicalPage />)
      await userEvent.click(screen.getByLabelText(/Contacts \(any layout/))
      expect(screen.getByRole('note')).toHaveTextContent('Exact loads for exactly 3 contacts')
      expect(screen.queryByLabelText('Wheelbase L (m)')).not.toBeInTheDocument()
      expect(screen.getByDisplayValue('caster')).toBeInTheDocument()
    })

    it('blocks submission while contact coordinates are empty (never defaulted to 0)', async () => {
      const fetchMock = mockFetch(contactsResponse)
      render(<MechanicalPage />)
      await userEvent.click(screen.getByLabelText(/Contacts \(any layout/))
      await userEvent.click(screen.getByRole('button', { name: 'Analyze' }))
      expect(await screen.findByRole('alert')).toHaveTextContent('left_wheel x')
      expect(fetchMock).not.toHaveBeenCalled()
    })

    it('posts contacts, draws the support polygon and lists each contact load', async () => {
      const fetchMock = mockFetch(contactsResponse)
      render(<MechanicalPage />)
      await userEvent.type(screen.getByLabelText('Mass (kg) 1'), '10')
      await userEvent.type(screen.getByLabelText('x (m) 1'), '-0.05')
      await userEvent.type(screen.getByLabelText('y (m) 1'), '0')
      await userEvent.type(screen.getByLabelText('z (m) 1'), '0.2')
      await fillContacts()
      await userEvent.click(screen.getByRole('button', { name: 'Analyze' }))
      expect(await screen.findByTestId('support-polygon')).toBeInTheDocument()
      expect(screen.queryByTestId('support-rect')).not.toBeInTheDocument()
      expect(fetchMock.mock.calls[0][0]).toBe('/api/mechanical/analyze-contacts')
      const body = JSON.parse(fetchMock.mock.calls[0][1].body)
      expect(body.contacts).toEqual([
        { name: 'left_wheel', x_m: 0, y_m: 0.15 },
        { name: 'right_wheel', x_m: 0, y_m: -0.15 },
        { name: 'caster', x_m: -0.2, y_m: 0 },
      ])
      expect(screen.getByText('Load on caster')).toBeInTheDocument()
      expect(screen.getByText('24.5 N')).toBeInTheDocument()
      expect(screen.getByText('0.05 m')).toBeInTheDocument()
      expect(screen.getByRole('heading', { name: 'Static stability: Stable' })).toBeInTheDocument()
    })
  })
})
